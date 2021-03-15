import time
from datetime import datetime as dt
import logging

try:
    import ntpdshm
except ImportError:
    ntpdshm = None

from .util import nmea_coord_to_dec_deg, ion
from .datatypes import TPV, FixDimension, FixQuality, FAAMode

class NmeaError(ValueError):
    pass

class NmeaParser:
    def __init__(self):
        self.lgr = logging.getLogger(self.__class__.__name__)

        self.last_msg_ts = None
        self.msg_tdel = {}

        self.last_cmd = None
        self.rmc_count = 0

        self.incoming_tpv = TPV()
        self.parsers = {
            'RMC': self.parse_rmc,
            'GGA': self.parse_gga,
            'GSA': self.parse_gsa,
            'GSV': self.parse_gsv,
        }

        self.shm = None
        if ntpdshm:
            try:
                self.shm = ntpdshm.NtpdShm(unit=0)
            except OSError:
                self.shm = None

    def parse(self, line):
        '''
        Assumptions:
         - Messages will always be in the same order
        '''
        # Split into message and checksum
        try:
            (message, reported_csum) = line.split('*')
        except ValueError:
            return False

        message = message.split(',')
        name = message[0]
        msg_type = name[3:]
        if msg_type not in self.parsers:
            return False
        
        # Convert the checksum from string to int
        try:
            reported_csum = int(reported_csum, 16)
        except ValueError:
            return False

        # Calculate the checksum (characters after $ sign)
        # Dump if the line doesn't match
        #calced_csum = 0
        #for char in message[1:]:
        #    calced_csum ^= ord(char)
        #if calced_csum != reported_csum:
        #    raise NmeaError("Bad checksum")

        ts = time.monotonic()
        if self.last_msg_ts:
            self.msg_tdel[name] = (ts - self.last_msg_ts)
        self.last_msg_ts = ts

        # Find appropriate parsing function (if it exists)
        try:
            self.parsers[msg_type](message)
            ret = True
        except Exception as exc:
            raise NmeaError("Error parsing %s" % name) from exc

        self.check_for_complete_tpv(name)

        return ret

    def check_for_complete_tpv(self, cmd):
        '''
        Assumptions:
         - 1 Hz
        '''
        found_it = False

        if len(self.msg_tdel) < 2:
            return

        if not self.last_cmd:
            longest_msg = max(self.msg_tdel, key=self.msg_tdel.get)
            self.lgr.debug("Longest message: %s (%s)", longest_msg, self.msg_tdel[longest_msg])

            if self.rmc_count >= 2 and longest_msg == cmd:
                self.lgr.debug("Got msg_lock! First sentence: %s", cmd)
                self.last_cmd = cmd
                found_it = True
            else:
                self.lgr.debug("Not this one: %s", cmd)
        else:
            found_it = (cmd == self.last_cmd)

        if found_it:
            print(self.incoming_tpv)
            sats = sorted(self.incoming_tpv.satellites.values(),
                          key=lambda x: x.snr or -1000,
                          reverse=True)
            for sat in sats:
                print(' - %s' % sat)
            self.incoming_tpv = TPV()

    def parse_rmc(self, message):
        # Assumptions:
        #  - Lat and Lon format: HHMM.MMM
        #  - Hours may not be 0 filled, 1-3 characters
        #  - Minutes are 0 filled. (Otherwise, wat?)
        #  - We're past Y2K
        inc = self.incoming_tpv
        hour = minute = second = None
        day = month = year = None

        cmd = message[0]

        _time = message[1]
        if _time != '':
            hour = int(_time[0:2])
            minute = int(_time[2:4])
            second = int(_time[4:6])

        inc.warn = message[2] != 'A'

        lat = message[3]
        ns = message[4]
        lon = message[5]
        ew = message[6]

        inc.vel_knots = message[7]
        inc.vel_deg = message[8]

        if lat != '' and lon != '':
            inc.lat_dec = nmea_coord_to_dec_deg(lat, ns)
            inc.lon_dec = nmea_coord_to_dec_deg(lon, ew)

        date = message[9]
        if date != '':
            day = int(date[0:2])
            month = int(date[2:4])
            year = int(date[4:6]) + 2000

        # TODO: Mag Dev
        # message[10] = mag_dev degrees
        # message[11] = mag_dev E/W

        try:
            inc.faa = FAAMode(message[12])
        except ValueError:
            inc.faa = FAAMode.NOT_VALID

        if None in [year, month, day, hour, minute, second]:
            return

        inc.dt = dt(year, month, day, hour, minute, second)
        if not inc.warn and self.shm and cmd == '$GPRMC':
            self.shm.update(inc.unix_ts, precision=-2)

        self.rmc_count += 1

    def parse_gga(self, message):
        # Assumpions:
        # - lat / lon / time the same as GPRMC
        # - num_sats is the same as GPGSV
        # - hdop is in GPGSA
        # - No one cares about DGPS
        # - Alt and Height are in M
        inc = self.incoming_tpv

        cmd = message[0]

        _time = message[1]
        lat = message[2]
        ns = message[3]
        lon = message[4]
        ew = message[5]

        if lat != '' and lon != '':
            inc.lat_dec = nmea_coord_to_dec_deg(lat, ns)
            inc.lon_dec = nmea_coord_to_dec_deg(lon, ew)

        try:
            inc.fix_quality = FixQuality(message[6])
        except ValueError:
            inc.fix_quality = FixQuality.NOT_AVAIL

        inc.alt = message[9]
        inc.height_wgs84 = message[11]

    def parse_gsa(self, message):
        inc = self.incoming_tpv

        cmd = message[0]

        inc.forced = (message[1] == 'M')
        try:
            inc.fix_dim = FixDimension(message[2])
        except ValueError:
            inc.fix_dim = FixDimension.NONE

        for nmea_id in message[3:15]:
            try:
                nmea_id = int(nmea_id)
            except ValueError:
                return

            sat = inc.get_satellite(nmea_id)
            sat.used = True

        (inc.pdop, inc.hdop, inc.vdop) = message[15:18]

    def parse_gsv(self, message):
        # Assumptions:
        # - No duplicate nmea_id's
        message = list(map(ion, message[1:]))
        #(num_msgs, msg_idx, sat_count) = message[0:3]

        # Grab satellites in blocks of four
        for i in range(3, len(message), 4):
            (nmea_id, elevation, azimuth, snr) = message[i:i+4]
            if nmea_id is None or \
                elevation is None or \
                azimuth is None:
                return

            sat = self.incoming_tpv.get_satellite(nmea_id)
            sat.elevation = elevation
            sat.azimuth = azimuth
            sat.snr = snr

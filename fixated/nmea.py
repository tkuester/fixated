import time
from datetime import datetime
import traceback
import logging

from .util import nmea_coord_to_dec_deg, ion, flon
from .datatypes import TPV, Satellite, FixDimension, FixQuality, FAAMode

class NmeaParser(object):
    def __init__(self, realtime=True):
        self.lgr = logging.getLogger(self.__class__.__name__)

        self.realtime = realtime
        self.last_msg_ts = time.monotonic()
        self.msg_tdel = {}

        self.last_cmd = None
        self.msg_lock = False

        self.incoming_tpv = TPV()

    def parse(self, line):
        '''
        Assumptions:
         - Messages will always be in the same order
        '''
        # Skip messages that don't start with $
        if not line.startswith('$'):
            return

        ts = time.monotonic()
        tdel = (ts - self.last_msg_ts)

        # Split into message and checksum
        _line = line.split('*')
        if len(_line) != 2:
            return False
        (message, reported_csum) = _line
        
        # Convert the checksum from string to int
        try:
            reported_csum = int(reported_csum, 16)
        except ValueError as e:
            self.lgr.warn('Unable to parse checksum for line', line)
            return False

        # Calculate the checksum (characters after $ sign)
        # Dump if the line doesn't match
        calced_csum = 0
        for char in message[1:]:
            calced_csum ^= ord(char)
        if calced_csum != reported_csum:
            self.lgr.warn('Checksum Mismatch / %s / expected %02x', line, calced_csum)
            return False

        message = message.split(',')
        name = message[0][1:]

        self.lgr.debug('%0.3f - %s', tdel, line)
        if self.realtime:
            self.last_msg_ts = ts
            self.msg_tdel[name] = tdel

        # Find appropriate parsing function (if it exists)
        ret = False
        func = getattr(self, 'parse_%s' % name[2:], None)
        if func:
            try:
                func(message)
                ret = True
            except Exception as e:
                self.lgr.error('%s\n%s', line, e)
                self.lgr.error(traceback.format_exc())
                ret = False

        self.check_for_complete_tpv(name)

        return ret

    def check_for_complete_tpv(self, cmd):
        '''
        Assumptions:
         - 1 Hz
        '''
        found_it = False

        if self.realtime:
            if not self.msg_lock:
                longest_msg = max(self.msg_tdel, key=self.msg_tdel.get)
                if len(self.msg_tdel) < 2 \
                    or self.msg_tdel.get(longest_msg, 0) < 0.100:
                    pass
                elif longest_msg == cmd:
                    self.lgr.debug("Got msg_lock! First sentence: %s", cmd)
                    self.lgr.debug("Last sentence: %s", self.last_cmd)
                    self.msg_lock = True
                    found_it = True

                if not self.msg_lock:
                    self.lgr.debug("Not this one: %s", cmd)
                    self.last_cmd = cmd
            else:
                found_it = (cmd == self.last_cmd)

        if found_it:
            print(self.incoming_tpv)
            for sat in self.incoming_tpv.satellites.values():
                print(' - %s' % sat)
            self.incoming_tpv = TPV()

    def parse_RMC(self, message):
        # Assumptions:
        #  - Lat and Lon format: HHMM.MMM
        #  - Hours may not be 0 filled, 1-3 characters
        #  - Minutes are 0 filled. (Otherwise, wat?)
        #  - We're past Y2K
        inc = self.incoming_tpv

        cmd = message[0]

        time = message[1]
        if time != '':
            inc.hr = int(time[0:2])
            inc.min = int(time[2:4])
            inc.sec = int(time[4:6])

        inc.warn = message[2] != 'A'

        lat = message[3]
        ns = message[4]
        lon = message[5]
        ew = message[6]

        inc.vel_knots = flon(message[7])
        inc.vel_deg = flon(message[8])

        if lat != '' and lon != '':
            inc.lat_dec = nmea_coord_to_dec_deg(lat, ns)
            inc.lon_dec = nmea_coord_to_dec_deg(lon, ew)

        date = message[9]
        if date != '':
            inc.day = int(date[0:2])
            inc.mon = int(date[2:4])
            inc.yr = int(date[4:6]) + 2000

        # TODO: Mag Dev
        # message[10] = mag_dev degrees
        # message[11] = mag_dev E/W

        try:
            inc.faa = FAAMode(ion(message[12]))
        except ValueError:
            inc.faa = FAAMode.NOT_VALID

    def parse_GGA(self, message):
        # Assumpions:
        # - lat / lon / time the same as GPRMC
        # - num_sats is the same as GPGSV
        # - hdop is in GPGSA
        # - No one cares about DGPS
        # - Alt and Height are in M
        inc = self.incoming_tpv

        cmd = message[0]

        time = message[1]
        if time != '':
            inc.hr = int(time[0:2])
            inc.min = int(time[2:4])
            inc.sec = int(time[4:6])

        lat = message[2]
        ns = message[3]
        lon = message[4]
        ew = message[5]

        if lat != '' and lon != '':
            inc.lat_dec = nmea_coord_to_dec_deg(lat, ns)
            inc.lon_dec = nmea_coord_to_dec_deg(lon, ew)

        try:
            inc.fix_quality = FixQuality(ion(message[6]))
        except ValueError:
            inc.fix_quality = FixQuality.NOT_AVAIL

        inc.alt = flon(message[9])
        inc.height_wgs84 = flon(message[11])

    def parse_GSA(self, message):
        inc = self.incoming_tpv

        cmd = message[0]

        inc.forced = (message[1] == 'M')
        try:
            inc.fix_dim = FixDimension(ion(message[2]))
        except ValueError:
            inc.fix_dim = FixDimension.NONE

        for nmea_id in message[3:15]:
            try:
                nmea_id = int(nmea_id)
            except ValueError:
                continue

            sat = inc.get_satellite(nmea_id)
            sat.used = True

        (inc.pdop, inc.hdop, inc.vdop) = map(float, message[15:18])

    def parse_GSV(self, message):
        # Assumptions:
        # - No duplicate nmea_id's
        message = list(map(ion, message[1:]))
        (num_msgs, msg_idx, sat_count) = message[0:3]

        # Grab satellites in blocks of four
        for i in range(3, len(message), 4):
            (nmea_id, elevation, azimuth, snr) = message[i:i+4]
            if nmea_id is None or \
                elevation is None or \
                azimuth is None:
                continue

            sat = self.incoming_tpv.get_satellite(nmea_id)
            sat.elevation = elevation
            sat.azimuth = azimuth
            sat.snr = snr

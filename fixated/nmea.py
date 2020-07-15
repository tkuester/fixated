import traceback
import logging
from datetime import datetime

from .util import nmea_coord_to_dec_deg
from .datatypes import TPV, Satellite

class NmeaParser(object):
    def __init__(self, collect_errors=False):
        self.lgr = logging.getLogger('NmeaParser')

        self.collect_errors = collect_errors
        self.parsing_errors = []

        self.seen_cmds = set()

        self.satellites = {}
        self.last_satellites = datetime.fromtimestamp(0)
        self.incoming_gsvs = {}

        self.tpv_cmds = set()
        self.tpv_set_known = False
        self.this_tpv_set = set()

        self.last_valid_tpv = TPV()
        self.latest_tpv = TPV()
        self.incoming_tpv = TPV()

        self.tpvs = []

    def check_for_complete_tpv_set(self, cmd):
        complete_set = False
        self.this_tpv_set.add(cmd)

        if not self.tpv_set_known:
            if cmd in self.tpv_cmds:
                self.tpv_set_known = True
                complete_set = True
                self.lgr.info("Got complete TPV set: %s", str(self.tpv_cmds))
            else:
                self.tpv_cmds.add(cmd)
                return

        if self.this_tpv_set == self.tpv_cmds:
            self.latest_tpv = self.incoming_tpv
            self.tpvs.append(self.latest_tpv)

            self.this_tpv_set = set()
            self.incoming_tpv = TPV()
            self.lgr.info(str(self.latest_tpv))

    def parse(self, line):
        # Strip, and skip empty lines
        line = line.strip()
        if line == '':
            return

        # Skip messages that don't start with $
        if not line.startswith('$'):
            if self.collect_errors:
                self.parsing_errors.append((line, None, "Doesn't start with $"))
            return

        self.lgr.debug(line)

        # Even if we don't parse it, let's add the command
        name = line.strip().split(",")[0]
        self.seen_cmds.add(name)

        # Split into message and checksum
        _line = line.split('*')
        if len(_line) != 2:
            return
        (message, reported_csum) = _line
        
        # Convert the checksum from string to int
        try:
            reported_csum = int(reported_csum, 16)
        except ValueError as e:
            self.lgr.warn('Unable to parse checksum for line', line)
            if self.collect_errors:
                self.parsing_errors.append((line, e, traceback.format_exc()))
            return

        # Calculate the checksum (characters after $ sign)
        # Dump if the line doesn't match
        calced_csum = 0
        for char in message[1:]:
            calced_csum ^= ord(char)
        if calced_csum != reported_csum:
            msg = 'Checksum Mismatch / %s / expected %02x'
            msg = msg % (line, calced_csum)
            self.lgr.warn(msg)
            if self.collect_errors:
                self.parsing_errors.append((line, None, msg))
            return

        # Find appropriate parsing function (if it exists)
        func = getattr(self, 'parse_%s' % name[1:], None)
        if func is None:
            #if self.collect_errors:
            #    self.parsing_errors.append((line, None,
            #        "No handlers for %s" % name[1:]))
            return

        try:
            return func(message)
        except Exception as e:
            msg = '%s\n%s' % (line, e)
            self.lgr.error(msg)
            self.lgr.error(traceback.format_exc())
            if self.collect_errors:
                self.parsing_errors.append((line, e, traceback.format_exc()))

    def parse_GPRMC(self, message):
        # Assumptions:
        #  - Lat and Lon format: HHMM.MMM
        #  - Hours may not be 0 filled, 1-3 characters
        #  - Minutes are 0 filled. (Otherwise, wat?)
        #  - We're past Y2K
        message = message.split(',')
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

        try:
            inc.vel_knots = float(message[7])
        except ValueError:
            inc.vel_knots = None

        try:
            inc.vel_deg = float(message[8])
        except:
            inc.vel_deg = None

        if lat != '' and lon != '':
            inc.lat_dec = nmea_coord_to_dec_deg(lat, ns)
            inc.lon_dec = nmea_coord_to_dec_deg(lon, ew)

        date = message[9]
        if date != '':
            inc.day = int(date[0:2])
            inc.mon = int(date[2:4])
            inc.yr = int(date[4:6]) + 2000

        self.check_for_complete_tpv_set(cmd)

    def parse_GPGGA(self, message):
        # Assumpions:
        # - lat / lon / time the same as GPRMC
        # - num_sats is the same as GPGSV
        # - hdop is in GPGSA
        # - No one cares about DGPS
        # - Alt and Height are in M
        message = message.split(',')
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

        # fix_type 0 = None
        # fix_type 1 = GPS
        # fix_type 2 = DPGS
        inc.fix_type = int(message[6])

        if message[9] != '':
            inc.alt = float(message[9])
        if message[11] != '':
            inc.height_wgs84 = float(message[11])

        self.check_for_complete_tpv_set(cmd)

    def parse_GPGSA(self, message):
        message = message.split(',')
        inc = self.incoming_tpv

        cmd = message[0]

        inc.forced = (message[1] == 'M')

        # fix_dim:
        # 0 - None
        # 1 - 2d
        # 2 - 3d
        inc.fix_dim = int(message[2])

        for prn in message[3:15]:
            try:
                prn = int(prn)
            except ValueError:
                continue

            if prn in self.satellites:
                self.satellites[prn].used = True

        if message[15] != '':
            inc.pdop = float(message[15])
        if message[16] != '':
            inc.hdop = float(message[16])
        if message[17] != '':
            inc.vdop = float(message[17])

        self.check_for_complete_tpv_set(cmd)
        # TODO: Parse GPVTG
        # TODO: Skip empty lines

    def parse_GPGSV(self, message):
        # Assumptions:
        # - GSV starts at 1, and ends at N
        # - Other GSV messages can come out of order
        # - Satellite count will not change until all GSVs are reported
        # - No duplicate PRN's
        message = message.split(',')

        num_msgs = int(message[1])
        msg_idx = int(message[2])
        sat_count = int(message[3])

        # We'll reset our state on msg_idx == 1
        if msg_idx == 1:
            self.incoming_gsvs.clear()

        # Grab satellites in blocks of four
        for i in range(4, len(message), 4):
            sat = message[i:i+4]
            (prn, elevation, azimuth, snr) = sat

            if prn == '' or \
                elevation == '' or \
                azimuth == '':
                continue

            sat = Satellite(prn, elevation, azimuth, snr)
            self.incoming_gsvs[int(prn)] = sat

        # Stop if we're not on the last message
        if msg_idx != num_msgs:
            return

        if sat_count != len(self.incoming_gsvs):
            self.incoming_gsvs = {}
            self.lgr.debug("Didn't get expected number of satellites!")
            self.lgr.debug("Expected %d, got %d" % (sat_count, len(self.incoming_gsvs)))
        else:
            # Copy over 'used' attribute
            for (prn, sat) in self.satellites.items():
                if prn not in self.incoming_gsvs:
                    continue
                self.incoming_gsvs[prn].used = self.satellites[prn].used

            self.satellites = self.incoming_gsvs
            self.last_satellites = datetime.now()
            self.incoming_gsvs = {}

            for sat in self.satellites.values():
                self.lgr.debug('> %s' % sat)

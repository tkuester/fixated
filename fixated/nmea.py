import traceback
from datetime import datetime

class TPV(object):
    def __init__(self):
        self.lat_dec = None
        self.lon_dec = None
        self.alt = None
        self.height_wgs84 = None

        self.hdop = None
        self.vdop = None
        self.pdop = None

        self.fix_type = None
        self.fix_dim = None
        self.forced = None
        self.warn = None

        self.hr = None
        self.mn = None
        self.sec = None

        self.day = None
        self.mon = None
        self.yr = None

        self.ts = None

    def _finalize(self):
        self.ts = datetime(self.yr, self.mon, self.day, self.hr,
                self.mn, self.sec)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'TPV<ll=(%.6f, %.6f), fix_type=%s, fix_dim=%s, ts=%s>' % (
                self.lat_dec,
                self.lon_dec,
                self.fix_type,
                self.fix_dim,
                self.ts)

class Satellite(object):
    def __init__(self, prn, elevation, azimuth, snr):
        self.prn = prn
        self.elevation = int(elevation.strip())
        self.azimuth = int(azimuth.strip())

        try:
            self.snr = int(snr.strip())
            self.tracked = True
        except ValueError as e:
            if snr.strip() in ['', None]:
                self.tracked = False
                self.snr = None
            else:
                raise e

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'Satellite<prn=%s, elevation=%d, azimuth=%d, snr=%s>' % (
                self.prn,
                self.elevation,
                self.azimuth,
                self.snr)

class NmeaParser(object):
    def __init__(self, collect_errors=False):
        self.collect_errors = collect_errors
        self.parsing_errors = []
        self.seen_cmds = set()

        self.satellites = []
        self.last_satellites = datetime.fromtimestamp(0)
        self.incoming_gsvs = []

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
            else:
                self.tpv_cmds.add(cmd)
                return

        if self.this_tpv_set == self.tpv_cmds:
            self.incoming_tpv._finalize()
            self.latest_tpv = self.incoming_tpv
            self.tpvs.append(self.latest_tpv)

            self.this_tpv_set = set()
            self.incoming_tpv = TPV()

        # TODO: Last valid TPV

    def parse(self, line):
        # Strip, and skip empty lines
        line = line.strip()
        if line == '':
            return

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
        except ValueError:
            return

        # Skip messages that don't start with $
        if not message.startswith('$'):
            return

        # Calculate the checksum (characters after $ sign)
        # Dump if the line doesn't match
        calced_csum = 0
        for char in message[1:]:
            calced_csum ^= ord(char)
        if calced_csum != reported_csum:
            return

        # Find appropriate parsing function (if it exists)
        func = getattr(self, 'parse_%s' % name[1:], None)
        if func is None:
            return

        try:
            return func(message)
        except StandardError as e:
            if self.collect_errors:
                self.parsing_errors.append((line, e, traceback.format_exc()))


    def parse_GPRMC(self, message):
        # Assumptions:
        #  - Lat and Lon format: HHMM.MMM
        #  - Hours may not be 0 filled, 1-3 characters
        #  - Minutes are 0 filled. (Otherwise, wat?)
        #  - We're past Y2K
        message = message.split(',')
        i = self.incoming_tpv

        cmd = message[0]

        time = message[1]
        i.hr = int(time[0:2])
        i.mn = int(time[2:4])
        i.sec = int(time[4:6])

        i.warn = message[2] != 'A'

        lat = message[3]
        ns = message[4]
        dec_idx = lat.index('.') - 2
        lat_deg = int(lat[0:dec_idx])
        lat_min = float(lat[dec_idx:])
        i.lat_dec = (lat_deg + (lat_min / 60)) * (1 if ns == 'N' else -1)

        lon = message[5]
        ew = message[6]
        dec_idx = lon.index('.') - 2
        lon_deg = int(lon[0:dec_idx])
        lon_min = float(lon[dec_idx:])
        i.lon_dec = (lon_deg + (lon_min / 60)) * (1 if ew == 'E' else -1)

        date = message[9]
        i.day = int(date[0:2])
        i.mon = int(date[2:4])
        i.yr = int(date[4:6]) + 2000

        self.check_for_complete_tpv_set(cmd)

    def parse_GPGGA(self, message):
        # Assumpions:
        # - lat / lon / time the same as GPRMC
        # - num_sats is the same as GPGSV
        # - hdop is in GPGSA
        # - No one cares about DGPS
        # - Alt and Height are in M
        message = message.split(',')
        i = self.incoming_tpv

        cmd = message[0]

        # fix_type 0 = None
        # fix_type 1 = GPS
        # fix_type 2 = DPGS
        i.fix_type = int(message[6])
        i.alt = float(message[9])
        i.height_wgs84 = float(message[11])

        self.check_for_complete_tpv_set(cmd)

    def parse_GPGSA(self, message):
        message = message.split(',')
        i = self.incoming_tpv

        cmd = message[0]

        i.forced = (message[1] == 'M')

        # fix_dim:
        # 0 - None
        # 1 - 2d
        # 2 - 3d
        i.fix_dim = int(message[2])

        i.pdop = float(message[15])
        i.hdop = float(message[16])
        i.vdop = float(message[17])

        self.check_for_complete_tpv_set(cmd)

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
            self.incoming_gsvs = []

        # Grab satellites in blocks of four
        for i in range(4, len(message), 4):
            sat = message[i:i+4]
            (prn, elevation, azimuth, snr) = sat
            sat = Satellite(prn, elevation, azimuth, snr)
            self.incoming_gsvs.append(sat)

        if msg_idx != num_msgs:
            return

        if sat_count != len(self.incoming_gsvs):
            self.gsvs = []
            raise ValueError("Didn't get expected number of satellites!")
        else:
            self.satellites = self.incoming_gsvs
            self.last_satellites = datetime.now()
            self.gsvs = []

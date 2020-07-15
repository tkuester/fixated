from datetime import datetime

class TPV(object):
    def __init__(self):
        self.lat_dec = None
        self.lon_dec = None
        self.alt = None
        self.height_wgs84 = None

        self.vel_knots = None

        self.hdop = None
        self.vdop = None
        self.pdop = None

        self.fix_type = None
        self.fix_dim = None
        self.forced = None
        self.warn = None

        self.hr = None
        self.min = None
        self.sec = None

        self.day = None
        self.mon = None
        self.yr = None

        self._ts = None

    @property
    def ts(self):
        if self._ts is not None:
            return self._ts

        try:
            self._ts = datetime(self.yr, self.mon, self.day, self.hr,
                self.min, self.sec)
        except TypeError as e:
            self._ts = None

        return self._ts

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        if self.lat_dec is None or self.lon_dec is None:
            return 'TPV<ll=None, ts=%s>' % (self.ts)
        return 'TPV<ll=(%.6f, %.6f),\n' \
               '    ts=%s,\n'           \
               '    vel=%s, ang=%s,\n'  \
               '    hdop=%s, vdop=%s, pdop=%s,\n' \
               '    fix=%s,%s,%s,%s>' % (
                self.lat_dec, self.lon_dec,
                self.ts,
                self.vel_knots, self.vel_deg,
                self.hdop, self.vdop, self.pdop,
                self.fix_type, self.fix_dim, self.forced, self.warn)

class Satellite(object):
    def __init__(self, prn, elevation, azimuth, snr):
        self.prn = prn
        self.elevation = int(elevation.strip())
        self.azimuth = int(azimuth.strip())
        self.used = False

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
        return 'Satellite<prn=%s, elevation=%d, azimuth=%d, snr=%s, used=%s>' % (
                self.prn,
                self.elevation,
                self.azimuth,
                self.snr,
                self.used)

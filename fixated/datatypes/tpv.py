from datetime import datetime

from .satellite import Satellite

class TPV:
    def __init__(self):
        self.satellites = {}

        self.lat_dec = None
        self.lon_dec = None
        self.alt = None
        self.height_wgs84 = None

        self.vel_knots = None
        self.vel_deg = None

        self.hdop = None
        self.vdop = None
        self.pdop = None

        self.fix_quality = None
        self.fix_dim = None
        self.forced = None
        self.warn = None

        self.hr = None
        self.min = None
        self.sec = None

        self.day = None
        self.mon = None
        self.yr = None

        self.mag_dev = None

        self.faa = None

        self._ts = None

    def get_satellite(self, nmea_id):
        sat = self.satellites.get(nmea_id)
        if sat is None:
            sat = Satellite(nmea_id)
            self.satellites[nmea_id] = sat

        return sat

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
               '    alt=%sm, height_wgs84=%sm,\n' \
               '    vel=%s, ang=%s,\n'  \
               '    hdop=%s, vdop=%s, pdop=%s,\n' \
               '    fix_quality=%s,\n' \
               '    fix_dim=%s,\n' \
               '    faa=%s,forced=%s,warn=%s>' % (
                self.lat_dec, self.lon_dec,
                self.ts,
                self.alt, self.height_wgs84,
                self.vel_knots, self.vel_deg,
                self.hdop, self.vdop, self.pdop,
                self.fix_quality, self.fix_dim, self.faa, self.forced, self.warn)


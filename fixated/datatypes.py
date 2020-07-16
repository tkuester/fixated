import enum
from datetime import datetime

class FixDimension(enum.Enum):
    NONE    = 1
    TWO_D   = 2
    THREE_D = 3

class FixQuality(enum.Enum):
    NOT_AVAIL  = 0
    GPS_FIX    = 1
    DGPS_FIX   = 2
    PPS_FIX    = 3
    RTK        = 4
    RTK_FLOAT  = 5
    ESTIMATED  = 6
    MANUAL     = 7
    SIMULATION = 8

class FAAMode(enum.Enum):
    NOT_VALID    = 'N'
    SIMULATED    = 'S'
    MANUAL       = 'M'
    ESTIMATED    = 'E'
    AUTONOMOUS   = 'A'
    DIFFERENTIAL = 'D'
    RTK_INT      = 'R'
    RTK_FLOAT    = 'F'
    PRECISE      = 'P'

class TPV(object):
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

        alt = None
        height_wgs84 = None
        if self.alt:
            alt = '%.1f' % self.alt
        if self.height_wgs84:
            height_wgs84 = '%.1f' % self.height_wgs84

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
                alt, height_wgs84,
                self.vel_knots, self.vel_deg,
                self.hdop, self.vdop, self.pdop,
                self.fix_quality, self.fix_dim, self.faa, self.forced, self.warn)

class Satellite(object):
    __slots__ = ['nmea_id', 'elevation', 'azimuth', 'used', 'snr']

    def __init__(self, nmea_id, elevation=None, azimuth=None, snr=None):
        self.nmea_id = nmea_id
        self.elevation = elevation
        self.azimuth = azimuth
        self.snr = snr
        self.used = False

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'Satellite<nmea_id=%s, elevation=%s, azimuth=%s, snr=%s, used=%s>' % (
                self.nmea_id,
                self.elevation,
                self.azimuth,
                self.snr,
                self.used)

    def __eq__(self, other):
        if not isinstance(other, Satellite):
            return False

        return self.nmea_id == other.nmea_id

    def __hash__(self):
        return self.nmea_id

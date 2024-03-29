import time
from datetime import datetime as dt
from collections import OrderedDict

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
        self.epx = None
        self.epy = None
        self.epv = None

        self.fix_quality = None
        self.fix_dim = None
        self.forced = None
        self.warn = None

        self.dt = None

        self.mag_dev = None

        self.faa = None

        self._ts = None

    def get_satellite(self, nmea_id):
        sat = self.satellites.get(nmea_id)
        if sat is None:
            sat = Satellite(nmea_id)
            self.satellites[nmea_id] = sat

        return sat

    def gpsd_tpv(self, name):
        jsn = OrderedDict()
        jsn['class'] = 'TPV'
        jsn['device'] = name
        jsn['mode'] = int(self.fix_dim.value)
        if self.dt:
            jsn['time'] = self.dt.isoformat() + 'Z'
        #jsn['ept'] = 0.1
        if self.lat_dec:
            jsn['lat'] = float(self.lat_dec)
        if self.lon_dec:
            jsn['lon'] = float(self.lon_dec)
        if self.alt:
            jsn['alt'] = float(self.alt)
        if self.epx is not None:
            jsn['epx'] = float(self.epx)
        if self.epy is not None:
            jsn['epy'] = float(self.epy)
        if self.epv is not None:
            jsn['epv'] = float(self.epv)
        if self.vel_deg:
            jsn['track'] = float(self.vel_deg)
        if self.vel_knots:
            jsn['speed'] = float(self.vel_knots) # TODO: Convert to m/s
        if self.mag_dev is not None:
            jsn['magvar'] = self.mag_dev
        #jsn['climb'] = 0.0
        #jsn['eps'] = 0.5
        #jsn['epc'] = 0.6

        return jsn

    def gpsd_sky(self, name):
        sky = OrderedDict()
        sky['class'] = 'SKY'
        sky['device'] = name
        #sky['xdop'] = 0.1
        #sky['ydop'] = 0.2
        if self.vdop:
            sky['vdop'] = float(self.vdop)
        #sky['tdop'] = 0.4
        if self.hdop:
            sky['hdop'] = float(self.hdop)
        #sky['gdop'] = 0.6
        if self.pdop:
            sky['pdop'] = float(self.pdop)

        sats = []
        for sat in self.satellites.values():
            od = OrderedDict()
            od['PRN'] = sat.nmea_id
            od['el'] = sat.elevation
            od['az'] = sat.azimuth
            od['ss'] = sat.snr
            od['used'] = sat.used
            sats.append(od)

        sky['satellites'] = sats

        return sky

    @property
    def coords(self):
        return (self.lat_dec, self.lon_dec)

    @property
    def unix_ts(self):
        if self._ts:
            return self._ts

        if self.dt is None:
            return None

        self._ts = time.mktime(self.dt.utctimetuple())

        return self._ts

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        if self.dt is None:
            ret_dt = None
        else:
            ret_dt = self.dt.isoformat()

        if self.lat_dec is None or self.lon_dec is None:
            return 'TPV<ll=None, dt=%s>' % (ret_dt)

        return 'TPV<ll=(%.6f, %.6f),\n' \
               '    ts=%s,\n'           \
               '    alt=%sm, height_wgs84=%sm,\n' \
               '    vel=%s, ang=%s,\n'  \
               '    hdop=%s, vdop=%s, pdop=%s,\n' \
               '    epx=%s, epy=%s, epv=%s,\n' \
               '    mag_dev=%s,\n' \
               '    fix_quality=%s,\n' \
               '    fix_dim=%s,\n' \
               '    faa=%s,forced=%s,warn=%s>' % (
                self.lat_dec, self.lon_dec,
                ret_dt,
                self.alt, self.height_wgs84,
                self.vel_knots, self.vel_deg,
                self.hdop, self.vdop, self.pdop,
                self.epx, self.epy, self.epv,
                self.mag_dev,
                self.fix_quality, self.fix_dim, self.faa, self.forced, self.warn)


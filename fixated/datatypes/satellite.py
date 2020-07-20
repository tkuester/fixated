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

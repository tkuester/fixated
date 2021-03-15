from pkg_resources import get_distribution, DistributionNotFound

from . import nmea
from .datatypes import TPV
from .serial_parser import SerialNmeaParser
from .gpsd_sock import GpsdSocket

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    __version__ = "unknown"

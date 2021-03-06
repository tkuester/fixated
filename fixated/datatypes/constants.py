import enum

class FixDimension(enum.Enum):
    NONE    = '1'
    TWO_D   = '2'
    THREE_D = '3'

class FixQuality(enum.Enum):
    NOT_AVAIL  = '0'
    GPS_FIX    = '1'
    DGPS_FIX   = '2'
    PPS_FIX    = '3'
    RTK        = '4'
    RTK_FLOAT  = '5'
    ESTIMATED  = '6'
    MANUAL     = '7'
    SIMULATION = '8'

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


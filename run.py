#!/usr/bin/env python
import sys
import fixated
import serial
import logging
#import simplekml

def main():
    logging.basicConfig(level=logging.INFO)
    np = fixated.nmea.NmeaParser(True)

    ser = serial.Serial('/dev/ttyUSB0', 4800)
    line = ser.readline()

    try:
        while True:
            line = ser.readline()
            np.parse(line)
    except KeyboardInterrupt:
        pass

    '''
    fp = open(sys.argv[1])
    for line in fp.readlines():
        np.parse(line)

    fp.close()

    coords = []
    for tpv in np.tpvs:
        print tpv
        coords.append((tpv.lon_dec, tpv.lat_dec))

    kml = simplekml.Kml()
    kml.newlinestring(coords=coords)
    kml.save('out.kml')

    print np.seen_cmds
    print np.tpv_cmds

    print len(np.parsing_errors)

    for (line, err, tb) in np.parsing_errors:
        print err, '>', line
        print tb
        print '-' * 70
    '''

if __name__ == '__main__':
    main()

#!/usr/bin/env python
import sys
import fixated
import simplekml

def main():
    np = fixated.nmea.NmeaParser(True)

    fp = open(sys.argv[1])
    for line in fp.readlines():
        np.parse(line)

    fp.close()

    coords = []
    for tpv in np.tpvs:
        coords.append((tpv.lon_dec, tpv.lat_dec))
    kml = simplekml.Kml()
    kml.newlinestring(coords=coords)
    kml.save('out.kml')

    print np.seen_cmds
    print np.tpv_cmds

    print len(np.parsing_errors)

    if len(np.parsing_errors) > 0:
        print np.parsing_errors[0][0]
        print np.parsing_errors[0][1]
        print np.parsing_errors[0][2]

if __name__ == '__main__':
    main()

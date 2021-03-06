import sys
import logging

import fixated

def main():
    logging.basicConfig(level=logging.DEBUG)

    try:
        port = sys.argv[1]
        baud = int(sys.argv[2])
    except (IndexError, ValueError):
        print('Usage: %s port baud' % sys.argv[0])
        sys.exit(1)

    np = fixated.SerialNmeaParser(port, baud)
    try:
        while True:
            np.run()
    except KeyboardInterrupt:
        np.stop()

if __name__ == '__main__':
    main()

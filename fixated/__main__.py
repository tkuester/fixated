import sys
import time
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
    np.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        np.stop()

    np.join()

if __name__ == '__main__':
    main()

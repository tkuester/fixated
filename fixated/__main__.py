import sys
import time
import logging

import fixated

def main():
    logging.basicConfig(level=logging.INFO)

    try:
        port = sys.argv[1]
        baud = int(sys.argv[2])
    except (IndexError, ValueError):
        print 'Usage: %s port baud'
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

import sys
import logging
import time

import fixated

def main():
    logging.basicConfig(level=logging.DEBUG)

    try:
        port = sys.argv[1]
        baud = int(sys.argv[2])
    except (IndexError, ValueError):
        print('Usage: %s port baud' % sys.argv[0])
        sys.exit(1)

    try:
        np = fixated.SerialNmeaParser(port, baud)
    except OSError as exc:
        print("Unable to open %s", port, file=sys.stderr)
        sys.exit(1)

    np.start()
    try:
        while True:
            time.sleep(1000)
    except KeyboardInterrupt:
        pass

    np.stop()
    np.join()

if __name__ == '__main__':
    main()

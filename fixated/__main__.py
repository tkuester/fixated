import sys
import logging
import time
from collections import OrderedDict

import fixated
from fixated import TPV

def main():
    logging.basicConfig(level=logging.DEBUG)

    try:
        port = sys.argv[1]
        baud = int(sys.argv[2])
    except (IndexError, ValueError):
        print('Usage: %s port baud' % sys.argv[0])
        sys.exit(1)

    st = fixated.GpsdSocket()
    st.start()

    try:
        np = fixated.SerialNmeaParser(st.tpv_queue, port, baud)
    except OSError as exc:
        print("Unable to open %s", port, file=sys.stderr)
        sys.exit(1)

    np.start()
    try:
        while True:
            (sender, dat) = st.tpv_queue.get()
            if isinstance(dat, TPV):
                print(sender)
                print(dat)

                for client in st.clients.values():
                    if client.watch is True:
                        client.send(dat.gpsd_tpv(sender.name))
                        client.send(dat.gpsd_sky(sender.name))
            elif isinstance(dat, str):
                for client in st.clients.values():
                    if client.watch == 2:
                        client.send(dat)
    except KeyboardInterrupt:
        pass

    try:
        np.stop()
        np.join()

        st.stop()
        st.join()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()

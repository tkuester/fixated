import select

import serial

from .nmea import NmeaParser, NmeaError, ChecksumError

class SerialNmeaParser(NmeaParser):
    def __init__(self, tpv_queue, tty, baud=9600):
        super().__init__(tpv_queue, tty)

        self.baud = baud
        self.buff = b''

        self.lgr.info("Opening %s @ %s baud", self.name, self.baud)
        self.ser = serial.Serial(tty, self.baud)

    def run(self):
        while not self.stopped.is_set():
            (rd_fds, _, _) = select.select([self.ser], [], [], 1)
            if not rd_fds:
                continue

            # pyserial's readline consumes an absurd amount of CPU...
            self.buff += self.ser.read(self.ser.in_waiting)

            lines = self.buff.split(b'\n')
            for line in lines[:-1]:
                try:
                    self.parse(line.decode('ascii'))
                except (UnicodeDecodeError, ChecksumError):
                    # TODO: Alert on bad baud rate?
                    continue
                except NmeaError as exc:
                    self.lgr.warn("Bad NMEA sentence: %s", line, exc_info=exc)
                except Exception as exc:
                    self.lgr.error("Unhandled exception: %s", line, exc_info=exc)

            self.buff = lines[-1]

        self.lgr.info("Shutting down")

    def stop(self):
        super().stop()
        if self.ser:
            self.ser.close()

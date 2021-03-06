import select

import serial

from .nmea import NmeaParser

class SerialNmeaParser(NmeaParser):
    def __init__(self, tty, baud=9600):
        super().__init__()

        self.tty = tty
        self.fp = serial.Serial(tty, baud)
        self.buff = ''

    def run(self):
        while True:
            (rd_fds, _, _) = select.select([self.fp], [], [], 10)
            if not rd_fds:
                continue

            # pyserial's readline consumes an absurd amount of CPU...
            self.buff += self.fp.read(self.fp.in_waiting).decode('ascii')
            lines = self.buff.split('\n')
            for line in lines[:-1]:
                self.parse(line)

            self.buff = lines[-1]

    def stop(self):
        self.fp.close()

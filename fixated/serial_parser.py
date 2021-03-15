import select

import serial

from .nmea import NmeaParser

class SerialNmeaParser(NmeaParser):
    def __init__(self, tty, baud=9600):
        super().__init__()

        self.tty = tty
        self.baud = baud
        self.buff = ''

        self.lgr.info("Opening %s @ %s baud", self.tty, self.baud)
        self.ser = serial.Serial(self.tty, self.baud)

    def run(self):
        while not self.stopped.is_set():
            (rd_fds, _, _) = select.select([self.ser], [], [], 1)
            if not rd_fds:
                continue

            # pyserial's readline consumes an absurd amount of CPU...
            self.buff += self.ser.read(self.ser.in_waiting).decode('ascii')
            lines = self.buff.split('\n')
            for line in lines[:-1]:
                self.parse(line)

            self.buff = lines[-1]

        self.lgr.info("Shutting down")

    def stop(self):
        super().stop()
        if self.ser:
            self.ser.close()

import threading
from queue import Queue

import serial
from .nmea import NmeaParser

class SerialNmeaParser(threading.Thread):
    def __init__(self, tty, baud=9600):
        threading.Thread.__init__(self)
        self.tty = tty
        self.stopped = False
        self.fp = serial.Serial(tty, baud)
        self.nmea = NmeaParser()

    def run(self):
        while not self.stopped:
            line = self.fp.readline()
            self.nmea.parse(line)

        self.fp.close()

    def stop(self):
        self.stopped = True

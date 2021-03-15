import time
import logging
import socket
import threading
import select
import json
import queue

#from fixated import __version__

__version__ = '1.2.3'

class GpsdClient:
    def __init__(self, sock):
        self.lgr = logging.getLogger(self.__class__.__name__)
        self.sock = sock
        self.watch = False

        self.buff = ''
        self.out_buff = b''

        msg = {
            'class': 'VERSION',
            'release': __version__,
            'rev': __version__,
            'proto_major': 3,
            'proto_minor': 11
        }

        self.send(msg)

    def send(self, msg):
        if isinstance(msg, dict):
            self.out_buff += json.dumps(msg, separators=(',', ':')).encode()
            self.out_buff += b'\n'
        else:
            self.out_buff += msg.encode()
            if msg[-1] != '\n':
                self.out_buff += b'\n'

    def _send(self):
        sent = self.sock.send(self.out_buff[0:1024])
        self.out_buff = self.out_buff[sent:]

    @property
    def has_data(self):
        return len(self.out_buff) > 0

    def feed(self, data):
        self.buff += data
        lines = self.buff.split('\n')
        for line in lines[:-1]:
            self.parse(line)

        self.buff = lines[-1]

    def parse(self, line):
        self.lgr.info('%s', line)
        if line[0] != '?':
            return

        try:
            (cmd, args) = line.split('=', 1)
            args = json.loads(args.rstrip(';'))
        except Exception as exc:
            self.lgr.warn("Bad line", exc_info=exc)
            return

        if cmd == '?WATCH':
            self.lgr.info(args)
            self.watch = False
            if args.get('enable') is True:
                self.send('''{"class":"DEVICES","devices":[{"class":"DEVICE","path":"/dev/ttyS1","driver":"NMEA0183","activated":"2021-03-15T02:22:01.163Z","flags":1,"native":0,"bps":115200,"parity":"N","stopbits":1,"cycle":1.00}]}''')
                self.send('''{"class":"WATCH","enable":true,"json":true,"nmea":false,"raw":0,"scaled":false,"timing":false,"split24":false,"pps":false}''')
                self.watch = args.get('json') == True
                self.lgr.info("self.watch=%s", self.watch)
            elif args.get('raw') == 2:
                self.send('''{"class":"DEVICES","devices":[{"class":"DEVICE","path":"/dev/ttyS1","driver":"NMEA0183","activated":"2021-03-15T02:22:01.163Z","flags":1,"native":0,"bps":115200,"parity":"N","stopbits":1,"cycle":1.00}]}''')
                self.send('''{"class":"WATCH","enable":true,"json":true,"nmea":false,"raw":2,"scaled":false,"timing":false,"split24":false,"pps":true}''')
                self.watch = 2
                self.lgr.info("self.watch=%s", self.watch)


class GpsdSocket(threading.Thread):
    def __init__(self, bind='127.0.0.1', port=2947):
        super().__init__()

        self.lgr = logging.getLogger(self.__class__.__name__)
        self.stopped = threading.Event()
        self.tpv_queue = queue.Queue()

        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.lgr.info("Binding to %s:%s", bind, port)
        self.srv.bind((bind, port))

        self.clients = {}

    def client_disconnect(self, sock, reason):
        self.lgr.info("Client disconnect: %s (%s)", sock, reason)
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except:
            pass
        finally:
            sock.close()

        self.clients.pop(sock)

    def run(self):
        self.srv.listen()

        while not self.stopped.is_set():
            rd_sox = list(self.clients.keys())
            rd_sox.append(self.srv)

            wr_sox = [sock for (sock, client) in self.clients.items()
                      if client.has_data]

            (rd_sox, wr_sox, _) = select.select(rd_sox, wr_sox, [], 0.10)

            for sox in rd_sox:
                if sox is self.srv:
                    try:
                        (client, _) = self.srv.accept()
                    except OSError:
                        break

                    self.lgr.info("New client: %s", client)
                    self.clients[client] = GpsdClient(client)
                    continue

                data = sox.recv(4096).decode()
                if len(data) == 0:
                    self.client_disconnect(sox, "Client closed socket")
                    continue

                self.clients[client].feed(data)

            for sox in wr_sox:
                try:
                    self.clients[sox]._send()
                except socket.error:
                    sox.close()

        clients = list(self.clients.keys())
        for client in clients:
            self.client_disconnect(client, "Server shutting down")

    def stop(self):
        if self.srv:
            try:
                self.srv.shutdown(socket.SHUT_RDWR)
            except:
                pass

        self.stopped.set()

    def client_data(self):
        pass

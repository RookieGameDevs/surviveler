#!/usr/bin/env python

import click
import datetime
import msgpack
import socket
import socketserver
import struct
import time

HEADER_SIZE = 6


def tstamp(dt=None):
    dt = dt or datetime.datetime.utcnow()
    return int((dt - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)


class MockServer(socketserver.BaseRequestHandler):
    """Mocked server.
    """
    def read_header(self):
        try:
            data = self.request.recv(HEADER_SIZE)
            print('receiving header {}'.format(data))
            return struct.unpack('!HI', data)
        except socket.error:
            pass

    def read_data(self, size):
        try:
            data = self.request.recv(size)
            print('receiving data {}'.format(data))
            return msgpack.unpackb(data)
        except socket.error:
            pass

    def read(self):
        self.header = getattr(self, 'header', None)
        self.data = getattr(self, 'data', None)
        if self.header is None:
            self.header = self.read_header()
        if self.data is None and self.header is not None:
            self.data = self.read_data(self.header[1])

        if self.header is not None and self.data is not None:
            result = (self.header, self.data)
            self.header, self.data = None, None
            return result

    def handle(self):
        self.request.setblocking(False)
        try:
            while True:
                t0 = datetime.datetime.now()
                data = self.read()
                if data:
                    ((t, _), d) = data
                    if t == 0:
                        data = msgpack.packb({
                            'id': d[b'id'],
                            'tstamp': tstamp()
                        })
                        response = struct.pack('!HI', 1, len(data)) + data
                        print('sending response {}'.format(response))
                        self.request.sendall(response)

                dt = datetime.datetime.now() - t0
                if (dt.microseconds * 1000000 + dt.seconds) >= 1:
                    time.sleep(1 - (dt.seconds + dt.microseconds/1000000))
                self.request.sendall(
                    struct.pack('!HI', 2, 1) + msgpack.packb({}))
        except:
            self.request.close()
            raise


@click.command()
@click.argument(
    'host',
    required=True, type=click.STRING, default='localhost', metavar='HOST')
@click.argument(
    'port',
    required=True, type=click.INT, default=1234, metavar='PORT')
def main(host, port):
    server = socketserver.TCPServer((host, port), MockServer)
    print('listening on {} {}'.format(host, port))
    server.serve_forever()


if __name__ == '__main__':
    main()

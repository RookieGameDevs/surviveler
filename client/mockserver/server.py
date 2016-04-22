#!/usr/bin/env python

from time import sleep
import click
import socketserver


class MockServer(socketserver.BaseRequestHandler):
    """Mocked server.
    """
    def handle(self):
        while True:
            self.request.sendall(b'example message')
            sleep(1)


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

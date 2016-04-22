#!/usr/bin/env python

from IPy import IP
from client import Client
from client import sdl2context
from connection import Connection
import click


class IpAddress(click.ParamType):
    """Custom click type for ip addresses.
    """
    name = 'ip address'

    def convert(self, value, param, ctx):
        try:
            ip_address = IP(value)
        except ValueError:
            msg = "{} is not a valid ip address".format(value)
            self.fail(msg)
        return str(ip_address)

IP_ADDRESS = IpAddress()
DEFAULT_SERVER_IP_ADDRESS = IP('127.0.0.1')
DEFAULT_SERVER_PORT = 1234


@click.command()
@click.argument(
    'host',
    required=True, type=IP_ADDRESS, default=DEFAULT_SERVER_IP_ADDRESS,
    metavar='IP')
@click.argument(
    'port',
    required=True, type=click.INT, default=DEFAULT_SERVER_PORT, metavar='PORT')
@sdl2context()
def main(host, port):
    print('starting application with on {} {}'.format(host, port))
    conn = Connection(host, port)
    client = Client(1024, 768, conn)
    client.start()
    client.quit()


if __name__ == '__main__':
    main()

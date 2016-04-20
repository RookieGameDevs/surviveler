#!/usr/bin/env python

from IPy import IP
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
        return ip_address

IP_ADDRESS = IpAddress()
DEFAULT_SERVER_IP_ADDRESS = IP('127.0.0.1')
DEFAULT_SERVER_PORT = 1234


@click.command()
@click.argument(
    'server',
    required=True, type=IP_ADDRESS, default=DEFAULT_SERVER_IP_ADDRESS,
    metavar='IP')
@click.argument(
    'port',
    required=True, type=click.INT, default=DEFAULT_SERVER_PORT, metavar='PORT')
def main(server, port):
    click.echo('{}:{}'.format(server, port))


if __name__ == '__main__':
    main()

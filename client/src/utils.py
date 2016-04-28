from datetime import datetime


def as_ascii(b):
    """Transform a byte array into an ASCII string.

    :param b: byte sequence to convert to string
    :type b: bytes or bytearray
    """
    return b.decode('ascii')


def as_utf8(b):
    """Transform a byte array into an UTF-8 string.

    :param b: byte sequence to convert to string
    :type b: bytes or bytearray
    """
    return b.decode('utf8')


def tstamp(dt=None):
    """Returns the number of milliseconds since epoch

    :param dt: the compared datetime object
    :type dt: :class:`datetime.datetime` or None

    :return: number of milliseconds since epoch
    :rtype: int
    """
    dt = dt or datetime.utcnow()
    return int((dt - datetime(1970, 1, 1)).total_seconds() * 1000)

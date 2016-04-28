from datetime import datetime


def tstamp(dt=None):
    """Returns the number of milliseconds since epoch

    :param dt: the compared datetime object
    :type dt: :class:`datetime.datetime` or None

    :return: number of milliseconds since epoch
    :rtype: int
    """
    dt = dt or datetime.utcnow()
    return int((dt - datetime(1970, 1, 1)).total_seconds() * 1000)

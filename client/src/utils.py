from datetime import datetime


def tstamp(dt=None):
    dt = dt or datetime.utcnow()
    return int((dt - datetime(1970, 1, 1)).total_seconds() * 1000)

# mock_zoneinfo.py
import pytz

class ZoneInfo:
    def __init__(self, zone_name):
        self.zone = pytz.timezone(zone_name)

    def utcoffset(self, dt):
        return self.zone.utcoffset(dt)

    def dst(self, dt):
        return self.zone.dst(dt)

    def tzname(self, dt):
        return self.zone.tzname(dt)

class ZoneInfoNotFoundError(Exception):
    pass

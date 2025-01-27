# patch_tzlocal.py
import sys
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

# Patch the tzlocal utils module
def patch_tzlocal():
    import tzlocal.utils
    tzlocal.utils.zoneinfo = sys.modules[__name__]

patch_tzlocal()

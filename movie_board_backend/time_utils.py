from datetime import datetime

from zoneinfo import ZoneInfo

from .configs import TIME_ZONE


def get_now() -> datetime:
    return datetime.now(ZoneInfo(TIME_ZONE))

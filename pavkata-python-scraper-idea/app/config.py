import pytz
from datetime import datetime

CURRENT_USER = "gerryjekova"
CURRENT_TIME = "2025-02-17 06:00:52"


def get_current_time():
    return datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S")

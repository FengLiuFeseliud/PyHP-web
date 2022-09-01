import time
from typing import Union


def full_date(time_: Union[float, time.struct_time] = None) -> str:
    if time_ is None:
        timestamp = time.localtime()

    if type(time_) is float:
        timestamp = time.gmtime(time_)

    return time.strftime("%a, %d %b %Y %H:%M:%S %Z", timestamp)
import time
from traceback import extract_tb, format_list
from typing import Any, Union


def _traceback_to_html(traceback_):
    """错误回溯转 HTML 数据"""
    traceback_data = ""
    for format_ in format_list(extract_tb(traceback_)):
        for msg_ in format_.split("\n"):
            msg_ = msg_.replace(" ", "&nbsp;")
            traceback_data = f"{traceback_data}<p>{msg_}</p>\n"
    return traceback_data


def _get_response_header(
    header: dict[str, Any], 
    response: str, 
    body: Union[str, bytes], 
    encoding: str,
    cookies: str = None
) -> bytes:
    """设置请求头"""
    header["Date"] = full_date()
    if "charset" not in header["Content-Type"]:
        header["Content-Type"] += f";charset={encoding}"
    
    if header["Content-Length"] is None:
        header["Content-Length"] = len(body)
    
    header_str =f"{response}\n"
    for item in header.items():
        key, val = item
        header_str += f"{key}: {val}\n"

    if cookies:
        header_str += f"{cookies}\n"

    return header_str.encode(encoding)


def full_date(time_: Union[float, time.struct_time] = None) -> str:
    """请求头 Date"""
    if time_ is None:
        timestamp = time.localtime()

    if type(time_) is float:
        timestamp = time.gmtime(time_)

    return time.strftime("%a, %d %b %Y %H:%M:%S %Z", timestamp)


def html_encode(str_: str) -> str:
    """编码 html 输出时浏览器将不会识别为标签 (防止 xss)"""
    str_ = str_.replace("<", "&lt;")
    str_ = str_.replace(">", "&gt;")
    str_ = str_.replace(" ", "&nbsp;")
    str_ = str_.replace("'", "&#39;")
    str_ = str_.replace('"', "&quot;")
    return str_.replace("\n", "<br>")
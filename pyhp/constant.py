import regex as re
from typing import Any


# 版本号
__version__ = "1.0.0"


# 代码块正则匹配
Py_Code_Pattern = re.compile(r"<\?py[\w\W]+?\?>")


# 响应头
Http_Response_Header: dict[str, Any] = {
    "Connection": "keep-alive",
    "Content-Type": "text/html",
    "Content-Length": None,
    "Cache-Control": "no-store",
    "Date": None,
    "Server": f"pyhp {__version__}"
}


# 错误消息格式
Error_Response_Body: str = """<h2>{code} {msg}</h2>
<h3>{type_}: {value}</h3>
<div>{traceback_}</div>

<hr />
<h2 style="text-align: center">PyHP</h2>
"""


# 数据类型
Content_Type: dict[str, str] = {
    "txt": "text/plain",
    "html": "text/html",
    "css": "text/css",
    "pyhtml": "text/html",
    "py": "text/html",
    "bmp": "image/bmp",
    "png": "image/png",
    "jpg": "image/jpg",
    "gif": "image/gif",
    "ico": "image/ico",
    "json": "application/json",
    "xml": "text/xml",
    "mp3": "audio/mpeg",
    "mp4": "audio/mp4",
    "flv": "audio/mp4",
    "avi": "audio/mp4",
}
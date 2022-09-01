import asyncio
import logging
import os
import re
import sys
from pyhp.tools import full_date
import aiofiles
from traceback import extract_tb, format_list
from typing import Any, Union
from threading import Thread
from urllib import parse


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
    "mp3": "audio/mp4",
    "mp4": "audio/mp4",
    "flv": "audio/mp4",
    "avi": "audio/mp4",
}


def _get_response_header(
    header: dict[str, Any], 
    response: str, 
    html_code: Union[str, bytes], 
    encoding: str,
    cookies: str = None
) -> bytes:
    header["Date"] = full_date()
    if "charset" not in header["Content-Type"]:
        header["Content-Type"] += f";charset={encoding}"
    
    if header["Content-Length"] is None:
        header["Content-Length"] = len(html_code)
    
    header_str =f"{response}\n"
    for item in header.items():
        key, val = item
        header_str += f"{key}: {val}\n"

    if cookies:
        header_str += f"{cookies}\n"

    return header_str.encode(encoding)


class Py_Html:

    def __init__(
        self, 
        html_data: str, 
        encoding: str = "utf-8",
        vals: dict[str, Any] = {}
    ) -> None:
        self.__ehco_list: list[str] = []
        self.__html = html_data
        self.__encoding = encoding
        self.__set_cookies = ""
        self.__response: dict[str, Union[str, int]] = {
            "http_version": "1.1",
            "code": 200,
            "msg": "OK"
        }
        self.__header: dict[str, Any] = Http_Response_Header.copy()
        self._run_py_code_block(vals)

    @staticmethod
    def _get_py_code_block(html_code: str):
        """获取文件中的 python 代码块"""
        return Py_Code_Pattern.finditer(html_code)

    def _run_py_code_block(self, vals: dict[str, Any] = {}):
        """运行文件中的 python 代码"""
        py_code_block_list = self._get_py_code_block(self.__html)
        # 设置内置方法
        vals["html"] = self
        vals["print"] = self.print
        vals["set_cookies"] = self.set_cookies
        vals["__name__"] = __name__
        # 存储所有已经运行代码块的变量
        run_py_vals: dict[str, Any] = {}

        for py_code_block in py_code_block_list:
            def run_py_code(py_code_block):
                try:
                    py_code_block = py_code_block.group() \
                        .replace("<?py ", "", 1) \
                        .replace("<?py", "", 1) \
                        .lstrip("\n") \
                        .rstrip("\n") \
                        .rstrip("?>")
                    """
                    避免前面解析出的代码产生缩进错误
                    在解析出的代码前面加上一句需要缩进的语句, 可以解决任何格的缩进问题
                    """
                    if py_code_block[0] in [" ", " \n"]:
                        py_code_block = "if True:\n%s" % py_code_block
                    
                    exec(py_code_block, vals, run_py_vals)
                except Exception:
                    self.print(PyHP_Server._get_error_response_body("PyHtml", "Error"))

            thread = Thread(target=run_py_code, args=(py_code_block, ))
            thread.setDaemon(True)
            thread.start()
            thread.join()

            self.__html = Py_Code_Pattern.sub(
                "".join(self.__ehco_list), 
                self.__html, 
                count=1
            )
            self.__ehco_list = []
    
    def print(self, *args):
        """保存数据, 在代码块运行完成后替换为保存数据"""
        self.__ehco_list.append("\n".join(str(arg) for arg in args))

    def set_cookies(
        self, 
        cookies: dict[str, Any], 
        max_age: Union[str, int] = None, 
        expires: str = None, 
        path: str = "/"
    ):
        """设置 cookie"""
        if not cookies:
            return
        
        if max_age is None and expires is None:
            max_age = -1
        
        for key, val in cookies.items():
            cookie = f"{key}={val}; Path={path};"

            if not max_age is None:
                cookie = f"{cookie} Max-Age={max_age};"
            elif not expires is None:
                cookie = f"{cookie} Expires={expires};"

            self.__set_cookies = f"{self.__set_cookies}Set-Cookie: {cookie}\n"
        
        self.__set_cookies.rstrip("\n")

    @property
    def html(self) -> Union[str, bytes]:
        return self.__html.encode(self.__encoding)

    @property
    def header(self) -> bytes:
        return _get_response_header(
            header=self.__header,
            response=self.response,
            html_code=self.html,
            encoding=self.__encoding,
            cookies=self.__set_cookies
        )

    @header.setter
    def header(self, header: dict[str, Union[str, int]]):
        self.__header.update(header)

    @property
    def response(self):
        return "HTTP/%s %s %s" % (
            self.__response["http_version"],
            self.__response["code"],
            self.__response["msg"]
        )

    @response.setter
    def response(self, response: dict[str, Union[str, int]]):
        self.__response.update(response)

    def get_response(self):
        return self.__response

    def get_header(self):
        return self.__header

    def get_response_body(self):
        return b"%b\n%b" % (self.header, self.html)


class PyHP_Server:

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: Union[str, int] = 5000,
        web_path: str = "./",
        web_index: str = "index.pyhtml",
        encoding: str = "utf-8"
    ) -> None:
        self._server = None
        self._host = host
        self._port = port
        self._web_path = os.path.abspath(web_path)
        self._web_index = web_index
        self._encoding = encoding

    @staticmethod
    def _get_content_type(file_path: str):
        file_name_list = file_path.rsplit("/", maxsplit=1)[-1].rsplit(".", maxsplit=1)
        if len(file_name_list) < 2:
            return "text/html"
        
        file_type = file_name_list[-1]
        return Content_Type[file_type]

    @staticmethod
    def _get_response_body(
        body: bytes,
        code: Union[str, int] = 200,
        msg: str = "OK",
        type_: str = "text/html",
        encoding: str = "utf-8"
    ):
        """设置响应体"""
        response_header = Http_Response_Header.copy()
        response_header["Content-Type"] = type_
        response_header_data = _get_response_header(
            response_header, 
            f"HTTP/1.1 {code} {msg}",
            body,
            encoding
        )
        return b"%b\n%b" % (response_header_data, body)

    @staticmethod
    def _get_error_response_body(
        code: Union[str, int] = 500,
        msg: str = "Server Error",
        encoding: str = "utf-8"
    ):
        """设置错误样式 (没有自定义时使用)"""
        error, value, traceback_ = sys.exc_info()

        traceback_data = ""
        for format_ in format_list(extract_tb(traceback_)):
            format_list_ = format_.split("\n")
            for msg_ in format_list_:
                msg_ = msg_.replace("    ", "&nbsp;&nbsp;&nbsp;&nbsp;")
                traceback_data = f"{traceback_data}<p>{msg_}</p>\n"

        return PyHP_Server._get_response_body(
            body=Error_Response_Body.format(
                code = code,
                msg = msg,
                type_ = error.__name__,
                value = value,
                traceback_ = traceback_data
            ).encode(encoding),
            code=code,
            msg=msg,
            encoding=encoding
        )

    def _set_request(self, request_body: bytes):
        """解析客户端请求"""
        request_data = request_body.decode(self._encoding).replace("\r", "").rstrip("\n").split("\n")

        request: dict[str, Any] = {} 
        data: dict[str, dict[str, Any]] = {
            "GET": {},
            "POST": {}
        }

        request_path = request_data[0].split(" ")
        # 分解 get 数据
        url_data = request_path[1].rsplit("?", maxsplit=1)
        if len(url_data) == 2 and url_data[-1]:
            for data_item in url_data[-1].split("&"):
                item = parse.unquote(data_item).split("=")
                data["GET"][item[0]] = item[1]

        try:
            # 分解请求头数据
            for text in request_data[1:]:
                key = text.split(": ")
                request[key[0]] = key[1]

        except IndexError:
            # 分解 post 数据
            if request_data[-1] != "":
                for data_item in parse.unquote(request_data[-1].replace("+", " ")).split("&"):
                    item = data_item.split("=")
                    data["POST"][item[0]] = item[1]

        # if "multipart/form-data" in request["Content-Type"]:
        #     web_kit: str = request["Content-Type"].split("; boundary=", maxsplit=1)[-1]
        #     print(request_body.split())
        
        cookie = {}
        # 分解 cookie 数据
        if "Cookie" in request:
            for cookie_key in request["Cookie"].split("; "):
                cookie_key = cookie_key.split("=")
                cookie[cookie_key[0]] = cookie_key[1]

        return {
            "request_path": {
                "mode": request_path[0],
                "path": request_path[1],
                "http_version": request_path[2],
            },
            "request_header": request,
            "request_data": data,
            "cookie": cookie
        }
    
    async def _get_connected_body(self, request: dict[str, dict[str, Any]]):
        """获取响应该次客户端请求的数据, request 为 _set_request 返回值"""
        try:
            path = request["request_path"]["path"]
            request["request_path"]["path"] = path.rsplit("?", maxsplit=1)[0]
            
            file_path = self._web_path + request["request_path"]["path"]
            if request["request_path"]["path"] == "/":
                file_path += self._web_index
            
            # 解析文件
            body = b""
            async with aiofiles.open(file_path, "rb") as _file:
                content_type = self._get_content_type(file_path)
                body = await _file.read()
                
                if content_type == "text/html":
                    pyhtml = Py_Html(body.decode(self._encoding), self._encoding,{
                        "request": request,
                        "request_header": request["request_header"],
                        "request_path": request["request_path"],
                        "request_data": request["request_data"],
                        "url": f"'{path}'",
                        "post": request["request_data"]["POST"],
                        "get": request["request_data"]["GET"],
                        "cookie": request["cookie"]
                    })

                    body = pyhtml.get_response_body()
                    code = pyhtml.get_response()["code"]
                else:
                    body = self._get_response_body(
                        body, 
                        encoding=self._encoding, 
                        type_=content_type
                    )

        except FileNotFoundError:
            body = self._get_error_response_body(404, "Not Found", encoding=self._encoding)
            code = 404

        return code, body

    async def _client_connected(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter): 
        """处理请求"""
        try:
            request = self._set_request(await reader.read(2000))
            code, body = await self._get_connected_body(request)

            logging.debug(body)
            writer.write(body)
        except Exception:
            request = {}
            writer.write(self._get_error_response_body(encoding=self._encoding))
            code = 500
        
        await writer.drain()
        writer.close()

        if not request:
            return

        logging.info('- - %s - "%s %s" %s - %s' % (
            f"{self._host}:{self._port}",
            request["request_path"]["mode"],
            request["request_path"]["http_version"],
            code,
            request["request_path"]["path"],
        ))

    async def start(self):
        """启动服务器"""
        self._server = await asyncio.start_server(
            self._client_connected,
            host = self._host,
            port = self._port
        )

        addr = self._server.sockets[0].getsockname()
        file_name = sys.argv[0].rsplit("/", maxsplit=1)[-1]
        print(
            f"\n * Serving PyPH {__version__} Server '{file_name}' on ip: {addr[0]} port: {addr[1]}\n\n",
            f"* Website Root Directory '{self._web_path}'\n\n",
            f"* Web Index Page '{self._web_index}' Encoding {self._encoding}\n\n",
            "* Logging DEBUG %s \n\n" % (logging.DEBUG == logging.root.level),
            f'* Running on http://{addr[0]}:{addr[1]} (Press CTRL+C to quit)\n'
        )

        async with self._server:
            await self._server.serve_forever()
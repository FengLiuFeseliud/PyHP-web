import asyncio
import platform
import aiofiles
import logging
import os
import sys
from time import time
from typing import Any, Optional, Union
from threading import Thread
from pyhpweb.client import Request
from pyhpweb.constant import *
from pyhpweb.error import IncludeImportError
from pyhpweb.log import Server_Log
from pyhpweb.tools import full_date, _traceback_to_html, _get_response_header, _get_include_path


class Py_Html:
    """
    PyHP HTML 对象
    ----------------
    初始化时将动态生成页面

    html_data:
        HTML 数据 (str)
    html_path:
        HTML 文件路径 (用于处理代码块中的相对路径)
    encoding: 
        HTML 编码
    response:
        响应行
    vals:
        可在 HTML 中 Pythom 代码块使用的数据, 为一个字典\n
        key 为在代码块时的变量名, val 为变量数据
    include_run_py_vals:
        包含该 PyHP HTML 对象的页面的已经运行代码块的变量\n
        存在时在该页面可以获取包含该 PyHP HTML 对象的页面的变量
    """

    def __init__(
        self, 
        html_data: str, 
        html_path: str, 
        encoding: str = "utf-8",
        response: dict[str, Union[str, int]] = None,
        vals: dict[str, Any] = {},
        include_run_py_vals: dict[str, Any] = {},
    ) -> None:
        self.__response: dict[str, Union[str, int]] = {
            "http_version": "1.1",
            "code": 200,
            "msg": "OK"
        }

        if not response is None:
            self.__response.update(response)

        self.__ehco_list: list[str] = []
        self.__html_path = html_path
        self.__html = html_data
        self.__encoding = encoding
        self.__header: dict[str, Any] = Http_Response_Header.copy()
        self._vals: dict[str, Any] = vals
        self._include_run_py_vals: dict[str, Any] = include_run_py_vals
        # 存储所有已经运行代码块的变量
        self._run_py_vals: dict[str, Any] = {}
        self._set_cookies = ""
        
        self._run_py_code_block(self._vals)

    @staticmethod
    def _get_py_code_block(html_code: str):
        """获取文件中的代码块"""
        return Py_Code_Pattern.finditer(html_code)
    
    @staticmethod
    def _format_py_code_block(py_code_block: str):
        """格式化代码块为 exec 可运行代码"""
        py_code_lines = py_code_block.replace("<?py ", "", 1).replace("<?py", "", 1) \
            .rstrip("?>").strip("\n").splitlines(True)

        remove_indent = ""
        for str_ in py_code_lines[0]:
            if str_ != " ":
                break
            remove_indent = f"{remove_indent}{str_}"

        return "".join(
            py_code.replace(remove_indent, "", 1) for py_code in py_code_lines
        )

    def _run_py_code_block(self, vals: dict[str, Any] = {}):
        """运行文件中的代码块"""
        py_code_block_list = self._get_py_code_block(self.__html)
        # 设置内置方法
        self._vals["html"] = self
        self._vals["print"] = self.print
        self._vals["set_cookies"] = self.set_cookies
        self._vals["include"] = self.include
        self._vals["__name__"] = __name__
        self._vals.update(vals)

        for py_code_block in py_code_block_list:
            def run_py_code(py_code_block):
                try:
                    exec(
                        self._format_py_code_block(py_code_block.group()), 
                        self._vals, 
                        self._run_py_vals
                    )
                except Exception:
                    self.print(PyHP_Server._get_error_body(
                            sys.exc_info(), 
                            "PyHtml", 
                            "Error"
                        )
                    )

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
        max_age: Optional[int] = -1, 
        path: str = "/"
    ):
        """设置 cookie, max_age 如果为 None 于客户端被关闭时失效
        大部分浏览器被关闭时 max_age 为 None 的 cookie 才会失效"""
        if not cookies:
            return

        expires = ""
        if not max_age is None:
            if max_age > 0:
                expires = full_date(time() + max_age)

            cookie_ = "Set-Cookie: {key}={val}%s" % f"; Path={path}; Expires={expires}; Max-Age={max_age};\n"
        else:
            cookie_ = "Set-Cookie: {key}={val}%s" % f"; Path={path}; Expires={expires};\n"
        
        for key, val in cookies.items():
            self._set_cookies += cookie_.format(key=key, val=val)
        
        self._set_cookies.rstrip("\n")
    
    def include(self, pyhtm_path: str, update_header: bool = False):
        """包含页面"""
        try:
            # 处理页面
            include_file_path = _get_include_path(self.__html_path, pyhtm_path)
            with open(include_file_path, "r", encoding=self.__encoding) as _file:
                py_html = Py_Html(
                    _file.read(), include_file_path, self.__encoding, self.__response.copy(), self._vals.copy(), self._run_py_vals.copy()
                )

            # 更新包含它的页面数据
            if update_header:
                self.__response.update(py_html.response)
                self.__header.update(py_html.header)
            self._run_py_vals.update(py_html._run_py_vals)
            self._set_cookies = f"{self._set_cookies}\n{py_html._set_cookies}" if self._set_cookies else py_html._set_cookies
            self.print(f"{py_html.get_html()}\n")
        except Exception as err:
            raise IncludeImportError(str(err))

    @property
    def html(self) -> bytes:
        return self.__html.encode(self.__encoding)

    @property
    def header(self) -> dict[str, Union[str, int]]:
        return self.__header

    @header.setter
    def header(self, header: dict[str, Union[str, int]]):
        self.__header.update(header)

    @property
    def response(self) -> dict[str, Union[str, int]]:
        return self.__response

    @response.setter
    def response(self, response: dict[str, Union[str, int]]):
        self.__response.update(response)
    
    def get_html(self):
        return self.__html

    def get_response(self):
        return "HTTP/%s %s %s" % (
            self.__response["http_version"],
            self.__response["code"],
            self.__response["msg"]
        )

    def get_header(self) -> bytes:
        return _get_response_header(
            header=self.__header,
            response=self.get_response(),
            body=self.html,
            encoding=self.__encoding,
            cookies=self._set_cookies
        )

    def get_response_body(self) -> bytes:
        return b"%b\n%b" % (self.get_header(), self.html)


class PyHP_Server:
    """
    PyHP 轻量服务端
    --------------

    host: 
        服务 IP
    port: 
        服务端口
    web_path: 
        网站根目录, 默认启动服务端文件目录
    web_index:
        网站主页
    web_error_page:
        网站错误页, 默认 None 使用 PyHP 内置错误页
    encoding:
        网站编码
    debug:
        是否开启 debug 日志输出
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: Union[str, int] = 5000,
        web_path: str = "./",
        web_index: str = "index.pyh",
        web_error_page: Optional[str] = None,
        request_body_max_size: int = 20480,
        request_header_max_size: int = 2048,
        encoding: str = "utf-8",
        debug: bool = False
    ) -> None:
        # 如果可以使用 uvloop 则使用
        try:
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy()) 
            self.__use_uvloop_in = True
        except ModuleNotFoundError:
            self.__use_uvloop_in = False
            if platform.system().lower() == "linux":
                print("\n * Your system is for Linux It is recommended to install uvloop (pip install uvloop) for better performance")

        # 设置日志输出
        Server_Log(logging.INFO if not debug else logging.DEBUG)

        self._server = None
        self._host = host
        self._port = port
        self._web_path = os.path.abspath(web_path)
        self._web_index = web_index
        self._web_error_page = web_error_page
        self._request_body_max_size = request_body_max_size * 1024
        self._request_header_max_size = request_header_max_size * 1024
        self._encoding = encoding

    @staticmethod
    def _get_content_type(file_path: str):
        """获取数据类型"""
        file_name_list = file_path.rsplit("/", maxsplit=1)[-1].rsplit(".", maxsplit=1)
        file_type = file_name_list[-1]

        if len(file_name_list) < 2 or file_type not in Content_Type:
            return "text/html"
        
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
    def _get_error_body(
        exc_info: tuple,
        code: Union[str, int] = 500,
        msg: str = "Server Error"
    ):
        """设置错误样式 (没有自定义时使用)"""
        _, error_value, traceback_ = exc_info

        return Error_Response_Body.format(
            code = code,
            msg = msg,
            type_ = type(error_value).__name__,
            value = error_value,
            traceback_ = _traceback_to_html(traceback_)
        )
    
    def _run_html_py_code(
        self, 
        html: str, 
        path: str, 
        html_path: str,
        request: dict[str, Any], 
        response: dict[str, Any] = None,
        expand_vals: dict[str, Any] = None
    ) -> tuple[Union[str, int], bytes]:
        """动态生成页面"""
        if expand_vals is None:
            expand_vals = {}

        vals = {
            "request": request,
            "request_header": request["request_header"],
            "request_path": request["request_path"],
            "request_data": request["request_data"],
            "url": f"'{path}'",
            "get": request["request_data"]["GET"],
            "post": request["request_data"]["POST"],
            "files": request["request_data"]["Files"],
            "cookie": request["cookie"]
        }
        vals.update(expand_vals)
        pyhtml = Py_Html(html, html_path, self._encoding, response, vals)

        return pyhtml.response["code"], pyhtml.get_response_body()

    async def _get_error_response_body(
        self,
        request,
        code: Union[str, int] = 500,
        msg: str = "Internal Server Error",
    ):
        """设置错误响应"""
        error, error_value, traceback_ = sys.exc_info()
        try:
            if self._web_error_page is None:
                raise FileNotFoundError

            # 自定义错误页
            self._web_error_page_path = f"{self._web_path}/{self._web_error_page}"
            async with aiofiles.open(self._web_error_page_path, "r") as _file:
                html = await _file.read()

            return await asyncio.to_thread(self._run_html_py_code,
                html=html,
                path=f"/{self._web_error_page}",
                html_path=self._web_error_page,
                request=request,
                response={
                    "code": code,
                    "msg": msg
                },
                expand_vals={
                    "error": (error_value, _traceback_to_html(traceback_)),
                    "error_url": request["url"],
                }
            )
        except Exception:
            # 如果自定义错误页执行失败, 重新启用内置错误页
            body = PyHP_Server._get_error_body(
                (error, error_value, traceback_), code, msg
            ).encode(self._encoding)

        return code, PyHP_Server._get_response_body(
            body=body,
            code=code,
            msg=msg,
            encoding=self._encoding
        )
    
    async def _get_connected_body(self, request: dict[str, dict[str, Any]]):
        """获取响应该次客户端请求的数据, request 为 _set_request 返回值"""
        file_path = self._web_path + request["request_path"]["path"]
        if request["request_path"]["path"] == "/":
            file_path += self._web_index
        
        # 解析文件
        body = b""
        async with aiofiles.open(file_path, "rb") as _file:
            content_type = self._get_content_type(file_path)
            body = await _file.read()
            
            if content_type == "text/html":
                code, body = await asyncio.to_thread(self._run_html_py_code,
                    body.decode(self._encoding), str(request["url"]), file_path, request
                )
            else:
                body = self._get_response_body(
                    body, 
                    encoding=self._encoding, 
                    type_=content_type
                )
                code = 200

        return code, body

    async def _client_connected(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter): 
        """处理请求"""
        body = b""
        try:
            request = await Request(reader, self).request

            if type(request) == dict:
                code, body = await self._get_connected_body(request)
            elif type(request) == tuple:
                code, body, request = request

        except PermissionError:
            code, body = await self._get_error_response_body(request, 403, "Forbidden")
        except FileNotFoundError:
            code, body = await self._get_error_response_body(request, 404, "Not Found")
        except Exception:
            code, body = await self._get_error_response_body(request)
        finally:
            logging.debug(body)

            writer.write(body)
            await writer.drain()
            writer.close()

        try:
            if type(request) == dict:
                logging.info('- - %s - "%s %s" %s - %s' % (
                    f"{self._host}:{self._port}",
                    request["request_path"]["mode"],
                    request["request_path"]["http_version"],
                    code,
                    request["request_path"]["path"],
                ))
        except KeyError:
            pass

    def start(self):
        """启动服务器"""
        loop = asyncio.get_event_loop()
        try:
            self._server = loop.run_until_complete(asyncio.start_server(
                self._client_connected,
                host = self._host,
                port = self._port,
                loop=loop
            ))
        except Exception as err:
            print(f"* The Server Failed To Start: {err}")
            return

        from pyhpweb.constant import __version__

        addr = self._server.sockets[0].getsockname()
        file_name = sys.argv[0].rsplit("/", maxsplit=1)[-1]
        print(
            f"\n * Serving PyHP {__version__}, Server '{file_name}' on ip: {addr[0]} port: {addr[1]}\n\n",
            f"* Website Root Directory '{self._web_path}'\n\n",
            f"* Web Index Page '{self._web_index}', Web Error Page '{self._web_error_page}', Encoding {self._encoding}\n\n",
            "* DEBUG Mode %s, Used uvloop %s\n\n" % (logging.DEBUG == logging.root.level, self.__use_uvloop_in),
            f'* Running on http://{addr[0]}:{addr[1]} (Press CTRL+C to quit)\n'
        )
        del self.__use_uvloop_in

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            print("\n\n\r* PyHP Server Down")
        finally:
            self._server.close()
            loop.run_until_complete(self._server.wait_closed())
            loop.close()
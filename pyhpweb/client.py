import asyncio, aiofiles
import os
from typing import TYPE_CHECKING, Any, Union
from urllib import parse
from pyhpweb.constant import Header_Data_Pattern


if TYPE_CHECKING:
    from pyhpweb import PyHP_Server


class Request:
    """客户端请求\n
    使用 Request.request 获取本次请求体数据"""

    def __init__(
        self,
        reader: asyncio.StreamReader,
        server: "PyHP_Server",
    ) -> None:
        self._server = server
        self._reader = reader
        self._encoding = server._encoding
        self.__request_get_in = False
        self.__data: dict[str, Any] = {
            "GET": {},
            "POST": {},
            "Files": {}
        }
        self.__request: dict[str, Any] = {
            "request_data": self.__data,
            "cookie": {},
        }

    async def _get_request_line(self) -> dict[str, Any]:
        """解析客户端请求行"""
        data = await self._reader.readline()
        request_path = data.decode(self._encoding).rstrip("\r\n").split(" ")

        return {
            "request_path": {
                "mode": request_path[0],
                "path": request_path[1].rsplit("?", maxsplit=1)[0],
                "http_version": request_path[2],
            },
            "url": request_path[1]
        }

    async def _get_request_header(self) -> tuple[int, dict[str, Any]]:
        """解析客户端请求头"""
        all_data_size = 0
        request_header: dict[str, Any] = {}
        while True:
            data = await self._reader.readline()
            all_data_size += len(data)
            if data == b"\r\n" or all_data_size > self._server._request_header_max_size:
                return all_data_size, request_header

            key, val = data.decode(self._encoding).rstrip("\r\n").split(": ")
            request_header[key.lower()] = val
    
    async def _get_request_get_data(self):
        """分解 get 数据"""
        url_data =  self.__request["url"].rsplit("?", maxsplit=1)

        data = {}
        if len(url_data) == 2 and url_data[-1]:
            for data_item in url_data[-1].split("&"):
                item = parse.unquote(data_item).split("=")
                data[item[0]] = item[1]

        return data

    async def _get_form_urlencoded_data(self):
        """解析 application/x-www-form-urlencoded 表单请求格式的数据"""
        data = await self._reader.read(self._server._request_body_max_size)
        request_form_data = data.decode(self._encoding)

        form_data = {}
        for data_item in request_form_data.replace("+", " ").split("&"):
            item = data_item.split("=")
            form_data[item[0]] = parse.unquote(item[1])
        
        return form_data

    async def _get_form_multipart_data(self):
        """解析 multipart/form-data 表单请求格式的数据"""
        data = await self._reader.read(self._server._request_body_max_size)
        # multipart/form-data 表单数据分割符
        boundary = b"--%b\r\n" % Header_Data_Pattern["boundary"].search(
            self.__request["request_header"]["content-type"]
        ).group().encode(self._encoding)

        form_data, files = {}, []
        data_list = data.replace(boundary, b'').split(b'\r\n')
        for index, data_line in enumerate(data_list):
            if data_line == boundary or not data_line:
                continue
            try:
                form_data_head = data_line.decode(self._encoding)
            except UnicodeDecodeError:
                # 解码了文件数据直接跳过
                continue

            if "filename" in form_data_head:
                file_name = Header_Data_Pattern["filename"].search(form_data_head).group()
                file_data = data_list[index + 2]
                file_path = f"./web_upload_file/{file_name}"

                if not os.path.isdir("./web_upload_file"):
                    os.makedirs("./web_upload_file")

                async with aiofiles.open(file_path, "wb") as _file:
                    await _file.write(file_data)
                
                files.append({
                    "file_name": file_name,
                    "file_size": len(file_data),
                    "file_path": file_path
                })
            else:
                name = Header_Data_Pattern["name"].search(form_data_head)
                if name is None:
                    continue
                
                form_data[name.group()] = data_list[index + 2].decode(self._encoding)
        
        return form_data, files
    
    def _get_request_cookie(self):
        """解析请求头 cookie"""
        cookie = {}
        for cookie_key in self.__request["request_header"]["cookie"].split("; "):
            cookie_key = cookie_key.split("=")
            cookie[cookie_key[0]] = cookie_key[1]

        return cookie

    @property
    async def request(self) -> Union[dict[str, Any], tuple[Union[str, int], bytes, dict[str, Any]]]:
        """解析客户端请求\n
        解析错误将返回一个元组 tuple (http 状态码, 错误页数据, 未解析完的请求体)\n
        解析错误的元组 tuple 将可以返回给客户端输出错误页"""
        if self.__request_get_in:
            return self.__request
        
        try:
            self.__request.update(await self._get_request_line())
            request_header_size, request_header = await self._get_request_header()
            self.__request["request_header"] = request_header

            if "cookie" in request_header:
                self.__request["cookie"] = self._get_request_cookie()

            if request_header_size > self._server._request_header_max_size:
                code, body = await self._server._get_error_response_body(
                    self.__request, 431, "Request Header Fields Too Large"
                )
                return code, body, self.__request

            self.__data["GET"] = await self._get_request_get_data()
            if "content-type" not in request_header:
                self.__request["request_data"] = self.__data
                return self.__request

            if "content-length" not in request_header:
                code, body = await self._server._get_error_response_body(
                    self.__request, 411, "Length Required"
                )
                return code, body, self.__request

            if "application/x-www-form-urlencoded" in request_header["content-type"]:
                self.__data["POST"] = await self._get_form_urlencoded_data()
            
            if "multipart/form-data" in request_header["content-type"]:
                form_data, files = await self._get_form_multipart_data()
                self.__data["POST"] = form_data
                self.__data["Files"] = files
            
            self.__request["request_data"] = self.__data
            self.__request_get_in = True
        except Exception:
            # 无法解析请求头时 400
            code, body = await self._server._get_error_response_body(
                self.__request, 400, "Bad Request"
            )
            return code, body, self.__request
        return self.__request
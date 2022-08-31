from pyhp import PyHP_Server, Server_Log
import asyncio

"""
测试 server

运行后访问 127.0.0.1:5000/demo下的文件名
查看 demo
"""

Server_Log()

async def main():
    server = PyHP_Server(
        host="127.0.0.1",
        web_path="./demo"
    )
    await server.start()

asyncio.run(main())
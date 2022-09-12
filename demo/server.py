from pyhpweb import PyHP_Server

"""
测试 server

运行后访问 127.0.0.1:5000/demo下的文件名
查看 demo
"""

PyHP_Server(
    web_path="./demo"
).start()
# PyHP-web

一种 Python 异步 Web 服务端，在请求页面时后端执行 Html 文件中的 Python 代码动态生成页面

![](https://img.sakuratools.top/docs/pyhp/pyhp0.png@0x0x0.5x80)

## Demo

后端代码

```python
<?py 
    import time 

    time = time.asctime(time.localtime(time.time()))
?>
<div>
    <?py print(f"<h2>{time}</h2>") ?>
    <div>
        <h3> GET </h3>
        <form action="/test.pyhtml" method="GET">
        First name: <input type="text" name="firstName"><br>
        Last name: <input type="text" name="lastName"><br>
        <input type="submit" value="提交">
        </form>
    </div>
    <div>
        <h3> POST </h3>
        <form action="/test.pyhtml" method="POST">
        First name: <input type="text" name="firstName"><br>
        Last name: <input type="text" name="lastName"><br>
        <input type="submit" value="提交">
        </form>
    </div>
</div>

<?py
    from pyhp import __version__

    print(
        "<p>http_version: %s</p>" % request_path["http_version"],
        "<p>request_mode: %s</p>" % request_path["mode"],
        "<p>request_path: %s</p>" % request_path["path"],
        "<p>url: %s</p>" % url,
        f"<p>get: {get}</p>",
        f"<p>post: {post}</p>",
        f"<p>request_header: {request_header}</p>",
        f"<p>request_data: {request_data}</p>",
        f"<p>PyHP version {__version__}</p>"
    ) 
?>

```

客户端请求生成动态页面

![](https://img.sakuratools.top/docs/pyhp/pyhp1.png@0x0x0.8x80)

![](https://img.sakuratools.top/docs/pyhp/pyhp2.png@0x0x0.8x80)



## 快速入门

使用 PyHP 时需要先启动 PyHP 服务，如下创建一个最简单的服务器文件，运行后启动 PyHP 服务，默认网站根目录为服务器文件所在文件夹

```python
import asyncio
from pyhp import PyHP_Server, Server_Log

Server_Log()

async def main():
    server = PyHP_Server()
    await server.start()

asyncio.run(main())
```

默认启动后可以访问 http://127.0.0.1:5000/

### 主页

默认启动后主页为网站路径下的 `index.pyhtml` ，在没有主页时访问 http://127.0.0.1:5000/ 会发生 404

简单创建一个主页显示 PyHP 服务已经启动

```python
<?py
    from .pyhp import __version__
    
	# 这里的 print 将向页面输入
    print(f"<h2>PyHP v{__version__}</h2>")
?>

<h3>Run in Server</h3>
```

效果

![](https://img.sakuratools.top/docs/pyhp/pyhp3.png@0x0x0.8x80)

### 代码块

PyHP 在 html 页面中的任何地方都可以执行 Python 代码只需要使用 `<?py 你的代码 ?>` 说明

前面代码块中定义的变量，在后面的代码块都可以使用，但是前面代码块引用的模块，在后面的代码块不可以使用

代码块 `print` 会向页面输出，代码块 `print` 的数据将在这块代码块执行完后，替换这块代码块 （代码块在哪个元素中 `print` 的数据就会在哪个元素中）

```python
<!DOCTYPE html>
<html lang="zh-CN">
<meta charset="utf-8">
<head>
    <meta charset="utf-8">
    <title>测试代码块</title>
</head>

<!-- 标准代码块 -->
<?py
    p_style = "color:blue;text-align:center"
    p_text = "Hi PyHP!!!"
?>

<body>
    <!-- 行代码块 -->

    <!-- 变量输出 动态样式 动态內容 -->
    <p style="<?py print(p_style) ?>"><?py print(p_text) ?></p>

    <!-- 单行输出多个元素 -->
    <?py print(f'<p style="{p_style}">print ps {p_text}</p>\n'*10) ?>
    
    <hr>

    <!-- 元素中的代码块 -->

    <div>
        <!-- 向元素中输出多个元素 -->
        <?py
        for i in range(0, 10):
            print(f'<p style="{p_style}">for in {i} {p_text}</p>\n')
        ?>
    </div>
</body>

```

## 超级全局变量

超级全局变量为 PyHP 定义的变量，在代码块的所有作用域中都可用

这里列出常用的，详细查看文档

> **`html`**：当前代码块所在的 Py_Html 对象
>
> **`request_header`**：请求头
>
> **`request_path`**：请求才模式 / 请求路径  /  请求 HTTP 版本
>
> **`url`**：请求 URL
>
> **`post`**： POST 数据
>
> **`get`**： GET 数据

输出测试

```python
<?py
    html_text = str(html).strip("<").rstrip(">")

    print(
        f"<p>html: {html_text}</p>",
        f"<p>request_header: {request_header}</p>",
        f"<p>request_path: {request_path}</p>",
        f"<p>url: {url}</p>",
        f"<p>post: {post}</p>",
        f"<p>get: {get}</p>",
    ) 
?>
```


# PyHP-web

一种 Python 轻量异步 Web 服务端 (原生异步 socket 实现)，在请求页面时后端执行 Html 文件中的 Python 代码动态生成页面

可以在 Html 文件中使用各种 Python 库，非常适合不用处理大量请求的 web 线上工具

![img](https://img.sakuratools.top/docs/pyhp/pyhp0.png@0x0x0.5x80)

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
        <form action="" method="GET">
        First name: <input type="text" name="firstName"><br>
        Last name: <input type="text" name="lastName"><br>
        <input type="submit" value="提交">
        </form>
    </div>
    <div>
        <h3> POST </h3>
        <form action="" method="POST">
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
        f"<p>cookie: {cookie}</p>",
        f"<p>request_header: {request_header}</p>",
        f"<p>request_data: {request_data}</p>",
        f"<p>PyHP version {__version__}</p>"
    ) 
?>

```

客户端请求生成动态页面

![img](https://img.sakuratools.top/docs/pyhp/pyhp1.png@0x0x0.8x80)

![img](https://img.sakuratools.top/docs/pyhp/pyhp2.png@0x0x0.8x80)

## 快速入门

使用 PyHP 时需要先启动 PyHP 服务，如下创建一个最简单的服务器文件，运行后启动 PyHP 服务，默认网站根目录为服务器文件所在文件夹

```python
from pyhp import PyHP_Server

PyHP_Server().start()
```

默认启动后可以访问 [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

### 主页

默认启动后主页为网站路径下的 `index.pyhtml` ，在没有主页时访问 [http://127.0.0.1:5000/](http://127.0.0.1:5000/) 会发生 404

简单创建一个主页显示 PyHP 服务已经启动

```python
<?py
    from pyhp import __version__
    
    # 这里的 print 将向页面输入
    print(f"<h2>PyHP v{__version__}</h2>")
?>

<h3>Run in Server</h3>
```

效果

![img](https://img.sakuratools.top/docs/pyhp/pyhp3.png@0x0x0.8x80)

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

## 非阻塞生成页面

PyHP 如果一个页面生成在执行 io 操作不会影响其他页面

```python
<?py 
    """
    pyhp 在执行页面生成时不会阻塞其他页面

    注意 页面不要写永远阻塞的代码
    请求永远阻塞代码数量一多将会导致服务器卡死 (都去执行永远阻塞的代码了)
    """
    import time
    # 模拟 io 操作, 这时候可以去看看别的页面是否会被影响
    time.sleep(30)
    print("ok")
?>
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
>
> **`cookie`**: Cookie 数据

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
        f"<p>cookie: {cookie}</p>"
    ) 
?>
```

## 自定义错误页

想要自定义错误页, 首先需要指定错误页名称 `web_error_page` 参数, 错误页必须在网站根目录下

```python
from pyhp import PyHP_Server

PyHP_Server(
    web_error_page="error.pyhtml"
).start()
```

然后就可以自定义错误页为 `web_error_page` 参数, 错误页会额外获得错误数据

```python
<h1>自定义错误页</h1>

<?py 
    """
    错误页会额外提供 error, error_url 内置变量
    并且响应行也会被修改
    """
    print(
        f"<p>response: {html.response}</p>",
        f"<p>response_data: {html.get_response()}</p>",
        f"<p>error_url: {error_url}</p>",
        f"<p>error_class_name: {type(error[0]).__name__}</p>",
        "<p>error_msg: %s</p>" % error[0],
        f"<p>error: {error}</p>"
    )
?>
```

## 使用 Cookie

使用 set_cookie 设置 cookie, set_cookie max_age 默认 -1 立刻过期, max_age 为 None 时于客户端被关闭时失效

```python
<?py
    from pyhp.tools import full_date
    
    if not cookie:
        """
        当 get 数据有 nomaxage 项时 (cookie.pyhtml?nomaxage=)
        这个 Cookie 将在浏览器被关闭时失效
        """
        if not "nomaxage" in get:
            # max_age Cookie 有效时长 (秒)
            # max_age -1 或者 0 Cookie 立刻过期
            set_cookies({
                "text": "30秒后过期!!!",
                "set-time": full_date(),
            }, max_age=30)
            print("<h1>没有 Cookie 设置 Cookie</h1>")
        else:
            # max_age 为 None 时于客户端被关闭时失效
            set_cookies({
                "text": "浏览器被关闭时失效!!!",
                "set-time": full_date(),
            }, max_age=None)
            print("<h1>没有 Cookie 设置 Cookie, 这个 Cookie 将在浏览器被关闭时失效</h1>")

    elif "nocookie" in get:
        """
        当 get 数据有 nocookie 项时 (cookie.pyhtml?nocookie=)
        删除所有 cookie
        """ 
        # set_cookies max_age 默认 -1 立刻过期
        set_cookies(cookie)
        print("<h1>删除所有 cookie </h1>")

    else:
        print("<h1>cookie str: %s</h1>" % request_header["cookie"])
        print("<h1>cookie: %s</h1>" % cookie)
?>
```

## Json Api

```python
<?py
    from pyhp import Content_Type, __version__
    import json

    # 设置请求头 Content-Type 为 json
    html.header = {
        "Content-Type": Content_Type["json"],
    }

    data = {
        "code": 200, 
        "msg": "OK",
        "data": {   
            "request_path": request_path,
            "request_header": request_header,
            "url": url,
            "get": get,
            "post": post,
            "version": __version__
        }
    }

    # json.dumps json 序列化后输出至页面
    print(json.dumps(data))
?>
```

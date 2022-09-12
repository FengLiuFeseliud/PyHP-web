# PyHP-web

一种 Python 轻量异步 Web 服务端 (原生异步 socket 实现)，在请求页面时后端执行 Html 文件中的 Python 代码动态生成页面

可以在 Html 文件中使用各种 Python 库，非常适合不用处理大量请求的 web 线上工具

![img](https://img.sakuratools.top/docs/pyhp/pyhp0.png@0x0x0.5x80)

## 安装

pyhp 安装使用 pip

```bash
pip install pyhpweb
```

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
    from pyhpweb import __version__

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

使用 PyHP 时需要先启动 PyHP 服务，如下创建一个最简单的服务器文件，运行后启动 PyHP 服务，默认网站根目录为服务器文件所在文件夹，如果 Linux 下有安装 uvloop PyHP 将自动启用

```python
from pyhpweb import PyHP_Server

PyHP_Server().start()
```

默认启动后可以访问 [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

### 主页

使用 `.html` `.py` `.pyhtml` `.pyh` 的文件都会被 pyhp 解析，不过还是推荐使用 `.pyhtml` `.pyh`，PyHP 服务默认启动后主页为网站路径下的 `index.pyh` ，在没有主页时访问 [http://127.0.0.1:5000/](http://127.0.0.1:5000/) 会发生 404

简单创建一个主页显示 PyHP 服务已经启动

```python
<?py
    from pyhpweb import __version__
    
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

代码块 `print` 会向页面输出，代码块 `print` 的数据将在这块代码块执行完后，替换这块代码块 （代码块在哪个元素中 `print` 的数据就会在哪个元素中，如果需要直接输出请求数据使用 `html_encode` 可以防止 xss 攻击 ,`from pyhp.tools import html_encode` 引用 `html_encode`

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
> **`html.header`**：页面响应头, 设置响应头html.header = {"响应类型": 值}
>
> **`html.response`**：页面响应行, 设置响应行 html.response = {"响应类型": 值}, 响应类型: code: 响应码, msg: 响应内容, http_version: http 版本
>
> **`request_header`**：请求头
>
> **`request_path`**：请求模式 / 请求路径  /  请求 HTTP 版本
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
    from pyhpweb import __version__
    from pyhpweb.tools import html_encode

    print(
        html_encode(str(html)),
        "<hr>\n<p>请求参数</p>",
        "<p>request_path: %s</p>" % request_path,
        "<p>url: %s</p>" % url,
        f"<p>get: {get}</p>",
        f"<p>post: {post}</p>",
        f"<p>cookie: {cookie}</p>",
        "<hr>\n<p>请求头</p>",
        f"<p>request_header: {request_header}</p>",
        "<hr>\n<p>响应头</p>",
        f"<p>response: {html.response}</p>",
        f"<p>header: {html.header}</p>",
        "<hr>",
        f"<p>PyHP version {__version__}</p>"
    )
```

## include 包含文件

PyHP 中的 `include` 与 PHP 类似, 可以导入页面并执行里面的 Python 代码并把页面写入当前页面

被包含页面执行完后可以更新包含它的文件中的变量与设置的 Cookie, 被包含的页面也可以使用包含它的文件中的变量与响应头与响应行 , `include` `update_header` 为 `True` 时, 被包含可以允许更新包含它的文件的响应头与响应行

`include` 导入页面错误时不会影响后面代码执行

```python
<?py
    print("<h1>include cookie.pyhtml </h1>")

    # 相对路径引入
    include("cookie.pyhtml")

    print("<br><br><h1>include vals.pyhtml </h1>")

    # 相对路径引入 ./
    include("./vals.pyhtml")

    print("<br><br><h1>include json.pyhtml </h1>")

    # 相对路径引入 ../
    include("../demo/json.pyhtml")
    """
    将更新响应头为 Content-Type: application/json
    include("../demo/json.pyhtml", update_header=True)
    """

    print("<br><br><h1>include test.pyhtml </h1>")

    # 绝对路径引入
    include("/home/sakura/pyhp-web/demo/demo/test.pyhtml")
?>

<br><br><h1>include end ...</h1>
```

## 自定义错误页

想要自定义错误页, 首先需要指定错误页名称 `web_error_page` 参数, 错误页必须在网站根目录下

```python
from pyhpweb import PyHP_Server

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
    from pyhpweb.tools import full_date
    
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
    from pyhpweb import Content_Type, __version__
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

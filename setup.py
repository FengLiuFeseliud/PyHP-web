from setuptools import setup, find_packages

"""
打包指令: python3 setup.py sdist
python3 -m twine upload dist/*
"""

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pyhpweb",
    version="0.1.1",
    description="Web 服务端，在请求页面时后端执行 Html 文件中的 Python 代码生成动态网页 （类似 PHP）",
    keywords=[
        "web",
        "server",
        "html",
        "Hypertext-Preprocessor"
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    url="https://github.com/FengLiuFeseliud/PyHP-web",
    author="FengLiuFeseliud",
    author_email="17351198406@qq.com",

    packages=find_packages(),
    include_package_data=True,
    platforms="any",
    install_requires=[
        "aiofiles",
        "regex"
    ],
    python_requires='>=3.9'
)
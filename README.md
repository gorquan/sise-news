# sise-news
华软新闻网爬虫

##### 运行的平台

Linux(Ubuntu 18.04已通过)、Unix（未知）、Windows（不支持）

python3(3.5以上)、 python2.7(不支持)

##### 安装依赖

``` shell
pip3 install -r requirements.txt
```

##### 运行

``` shell
python3 main.py
```

##### 采用的技术

* aiohttp
* aiofiles
* asyncio
* threading

##### 功能

* 抓取网站上的网页
* 解析抓取网页（目前仅可以解析文章，图片、视频、以及主题页面暂不支持）
* 写入解析结果到目录下
* 自定义抓取速度（可在config.yaml中的sem下定义爬取速度)

##### TODO

* 支持其他各种页面解析
* 支持自定义路径保存路径
* 支持自定义日志保存路径
* 采用进程池改写解析部分

##### issue与pr

* 如果有更好的建议，或者有已实现的代码，欢迎提交pr
* 如果代码中出现问题，欢迎提交issue

##### 本项目仅为学习使用，请勿用于非法用途或商业用途


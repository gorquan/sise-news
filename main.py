# author: gorquan
# date: 2019.9.23

from buildHeaders import buildHeader
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from  multiprocessing import pool
import logging
import logging.config
import os
import yaml


# 定义日志
def setLog(baseDir, filename):
    logConfigPath = baseDir + '/' + filename
    try:
        if os.path.exists(logConfigPath):
            with open(logConfigPath, 'r') as f:
                logConfig = yaml.load(f.read())
                logging.config.dictConfig(logConfig)
                log = logging.getLogger('crawler')
                log.info("配置日志成功!")
        else:
            logging.basicConfig(level=logging.INFO)
            log = logging.getLogger('crawler')
            log.info("配置默认日志成功!")
        return log
    except IOError:
        exit(1)

# 读取配置文件
def setConfig(baseDir, filename, log):
    configPath = baseDir + '/' + filename
    try:
        if os.path.exists(configPath):
            with open(configPath, 'r') as f:
                config = yaml.load(f.read())
                log.debug('加载配置文件成功!')
            return config
        else:
            raise Exception('配置文件不存在!')
    except Exception as e:
        log.error("配置文件读取失败,原因{}" .format(e))


if __name__ == "__main__":
    baseDir = os.path.dirname(os.path.abspath(__file__))
    # 定义日志
    log = setLog(baseDir, 'logConfig.yaml')
    # 定义配置文件
    config = setConfig(baseDir, 'config.yaml', log)
    # 定义信号量
    sem = asyncio.Semaphore(config['semaphore']['num'])
    # 目录url字典
    toc = dict()
    #  文章url列表
    article = set()
    # 先遍历1-11, 取得html
    # 解析页面,然后将栏目和目录页数写入字典
    # 遍历字典, 取得html
    # 解析html, 然后将文章总数写入列表
    # 遍历列表,取得html
    # 解析html. 将文章内容写入文本
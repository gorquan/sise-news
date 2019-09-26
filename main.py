# author: gorquan
# date: 2019.9.23

from buildHeaders import buildHeader
import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
import logging
import logging.config
import os
import yaml
import threading

# 控制爬虫开关
productr_switch = False


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
        log.error("配置文件读取失败,原因{}".format(e))


async def client(session, headers, url, sem, log):
    async with sem:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status in [200, 201]:
                    data = await resp.text()
                    return {'status': True, 'data': data}
        except Exception as e:
            log.error('爬取网页失败!url为{},错误原因是{}'.format(url, e))
            return {'status': False, 'data': None}


async def productr(Headers, urls, sem, waitToAnalysis, log):
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                global productr_switch
                if (len(urls) != 0):
                    item = urls.popitem()
                    webType = item[1]
                    url = item[0]
                    headers = Headers.build()
                    result = await client(session, headers, url, sem, log)
                    if result['status']:
                        waitToAnalysis.append({
                            'data': result['data'],
                            'type': webType
                        })
                        log.debug('{}数据获取成功,已添加进队列待解析'.format(url))
                    else:
                        urls[url] = webType
                        log.error('url:{}抓取失败，返回队列等待重新抓取'.format(url))
                        continue
                # TODO: 处理任务结束
                elif productr_switch:
                    log.debug('任务结束,停止爬取!')
                    break
                else:
                    log.debug('url池为空，继续等待..')
                    await asyncio.sleep(2)
                    continue
            except Exception as e:
                log.error('爬取数据失败!url为{},原因是{}'.format(url, e))
                if (url != None and webType != None):
                    urls[url] = webType
                continue


async def analysisr(waitToAnalysis, waitToWrite, urls, host, log):
    while True:
        try:
            if (len(waitToAnalysis) != 0):
                itemData = waitToAnalysis.pop()
                source = BeautifulSoup(itemData['data'], 'lxml')
                if (itemData['type'] == 'article'):
                    # 处理文章页面
                    name = ((source.find(
                        'div', {'class': 'article-title'})).text).strip()
                    data = (source.find('div', {'class': 'article-body'})).text
                    fileType = 'article'
                    waitToWrite.append({
                        'name': name,
                        'data': data,
                        'type': fileType
                    })
                    log.debug('内容：{}解析成功！已添加到待写入队列'.format(name))
                    # TODO：处理视频页面
                    # TODO：处理图片页面
                    # TODO：处理校报页面
                    # TODO：处理专题页面
                else:
                    # TODO: 存在问题 126行
                    if (itemData['type'] == 'column'):
                        urlArray = ((source.find(
                            'a', {'class': 'end'}))['href']).split('/')
                        endNum = (urlArray[-1]).rstrip('.html')
                        pageNum = urlArray[-3]
                        for i in range(1, int(endNum) + 1):
                            url = 'http://' + host + '/cms/news/' + str(
                                pageNum) + '/p/' + str(i) + '.html'
                            urls[url] = 'tof'
                        log.debug('文章目录网址添加完成!')
                    elif (itemData['type'] == 'tof'):
                        aritcles = source.find_all(
                            'h3',
                            {'class': 'list-title text-overflow margin-top-none'})
                        for article in aritcles:
                            url = 'http://' + host + (article.a['href'])
                            urls[url] = 'article'
                        log.debug('文章网址添加完成!')
            else:
                log.debug('待解析队列为空，继续等待..')
                await asyncio.sleep(2)
                continue
        except Exception as e:
            log.error('数据解析过程中发生错误，原因是: {}, 异常行数{}'.format(e,e.__traceback__.tb_lineno))
            continue


async def writer(waitToWrite, log):
    while True:
        try:
            if (len(waitToWrite) != 0):
                # TODO: 处理重复和分类（文本（时间），图片， 视频）
                item = waitToWrite.pop()
                if (item['type'] == 'article'):
                    async with aiofiles.open(item['name'] + '.txt', 'w+') as f:
                        await f.writelines(item['data'])
                    log.debug('{}写入文件完成!'.format(item['name']))
                else:
                    # TODO： 爬取视频和图片
                    if (item['type'] == 'img'):
                        pass
                    elif (item['type'] == 'video'):
                        pass
            else:
                log.debug('待写入队列为空，继续等待..')
                await asyncio.sleep(2)
                continue
        except Exception as e:
            log.error('写入过程中报错,原因是{}'.format(e))
            # TODO: 添加到队列重新写入
            continue


# 定义每个线程中的协程
def main(loop):
    # print(func)
    asyncio.set_event_loop(loop)
    loop.run_forever()


if __name__ == "__main__":
    baseDir = os.path.dirname(os.path.abspath(__file__))
    # 定义日志
    log = setLog(baseDir, 'logConfig.yaml')
    # 定义配置文件
    config = setConfig(baseDir, 'config.yaml', log)
    # 定义信号量
    sem = asyncio.Semaphore(config['semaphore']['num'])
    # log.debug("加载信号量信息成功, 当前信号量为{}".format(config['semaphore']['num']))
    host = config['website']['host']
    # 初始化头部类
    Headers = buildHeader("http://" + host)
    # 未爬取url
    urls = dict()
    # 添加第一批url
    for i in range(1, 12):
        # 目前只爬取文章，不爬取视频和图片
        if (i in [[3,4,7,8]]):
            continue
        urls['http://news.sise.edu.cn/cms/news/{}.html'.format(
            str(i))] = 'column'
    # 创建一个协程
    product_loop = asyncio.new_event_loop()
    analysis_loop = asyncio.new_event_loop()
    write_loop = asyncio.new_event_loop()
    # 创建线程
    # 生产者线程
    tProducter = threading.Thread(target=main,
                                  name='product',
                                  args=(product_loop, ))
    # 解析消费者线程
    tAnalysisr = threading.Thread(target=main,
                                  name='analysis',
                                  args=(analysis_loop, ))
    # 写入消费者线程
    tWriter = threading.Thread(target=main, name='writer', args=(write_loop, ))
    tProducter.setDaemon = True
    tAnalysisr.setDaemon = True
    tWriter.setDaemon = True
    # 执行线程
    tProducter.start()
    tAnalysisr.start()
    tWriter.start()
    array1 = list()
    array2 = list()
    # 添加到协程
    asyncio.run_coroutine_threadsafe(productr(Headers, urls, sem, array1, log),
                                     product_loop)
    asyncio.run_coroutine_threadsafe(
        analysisr(array1, array2, urls, host, log), analysis_loop)
    asyncio.run_coroutine_threadsafe(writer(array2, log), write_loop)

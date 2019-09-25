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


async def client(session, url, sem, headers):
    # async with sem:
    try:
        async with session.get(url, headers=headers) as resp:
            if resp.status in [200, 201]:
                data = await resp.text()
                # log.debug("网页{}爬取成功!".format(url))
                return {'status': True, 'data': data}
    except Exception as e:
        # log.error('爬取网页失败!url为{},错误原因是{}'.format(url,e))
        return {'status': False, 'data': None}


async def productr(Headers, sem, urls, waitToAnalysis):
    async with aiohttp.ClientSession() as session:
        while True:
            # try:
            global productr_switch
            # urls存在url
            if (len(urls) != 0):
                item = urls.popitem()
                webType = item[1]
                url = item[0]
                headers = Headers.build()
                result = await client(session, url, sem, headers)
                # log.debug('{}'.format(result['data']))
                if result['status']:
                    waitToAnalysis.append({
                        'data': result['data'],
                        'type': webType
                    })
                    # log.debug('{}数据获取成功,已添加进Queue1!'.format(url))
                else:
                    urls[url] = webType
                    continue
            # 读写完最后一个文件时,开关为True
            elif productr_switch:
                # log.debug('任务结束,停止爬取!')
                break
            # urls不存在url
            else:
                print(len(urls))
                await asyncio.sleep(2)
                print('继续')
                continue
        # except Exception as e:
        # log.error('爬取数据失败!url为{},原因是{}'.format(url,e))
        # urls.append({'data':url,'type':webType})
        # print(e)
        # continue


async def analysisr(waitToAnalysis, waitToWrite, urls, host):
    while True:
        try:
            if (len(waitToAnalysis) != 0):
                itemData = waitToAnalysis.pop()
                # log.debug("内容{}提取成功,待处理..".format(itemData['data']))
                source = BeautifulSoup(itemData['data'])
                if (itemData['type'] == 'article'):
                    # TODO: 处理视频页面
                    # TODO: 处理图片页面
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
                else:
                    if (itemData['type'] == 'column'):
                        urlArray = ((source.find(
                            'a', {'class': 'end'}))['href']).split('/')
                        endNum = (urlArray[-1]).rstrip('.html')
                        pageNum = urlArray[-3]
                        for i in range(1, int(endNum) + 1):
                            url = 'http://' + host + '/cms/news/' + str(
                                pageNum) + '/p/' + str(i) + '.html'
                            urls[url] = 'tof'
                        # log.debug('网址添加完成!')
                    elif (itemData['type'] == 'tof'):
                        aritcles = source.find_all('h3', {
                            'class':
                            'list-title text-overflow margin-top-none'
                        })
                        for article in aritcles:
                            url = 'http://' + host + (article.a['href'])
                            urls[url] = 'article'
                        # log.debug('网址添加完成!')
            else:
                await asyncio.sleep(2)
                continue
        except Exception as e:
            # log.error('从队列获取数据失败,原因是{}'.format(e))
            continue


async def writer(waitToWrite, Headers):
    # async with aiohttp.ClientSession as session:
        while True:
            try:
                if (len(waitToWrite) != 0):
                    item = waitToWrite.pop()
                    print(item)
                    if (item['type'] == 'article'):
                        async with aiofiles.open(item['name'] + '.txt',
                                                 'w+') as f:
                            await f.writelines(item['data'])
                            # log.debug('{}写入文件完成!'.format(item['name']))
                    else:
                        headers = Headers.build()
                        if (item['type'] == 'img'):
                            pass
                        elif (item['type'] == 'video'):
                            pass
                else:
                    await asyncio.sleep(2)
                    print('write继续')
                    continue
            except Exception as e:
                # log.error('无法从队列获取数据,原因是{}'.format(e))
                continue


# 定义每个线程中的协程
# def main(func, loop, *args):
def main(loop):
    # print(func)
    asyncio.set_event_loop(loop)
    # asyncio.ensure_future(analysisr(loop, *args))
    loop.run_forever()


if __name__ == "__main__":
    baseDir = os.path.dirname(os.path.abspath(__file__))
    # 定义日志
    # log = setLog(baseDir, 'logConfig.yaml')
    # 定义配置文件
    # config = setConfig(baseDir, 'config.yaml', log)
    # 定义信号量
    # sem = asyncio.Semaphore(config['semaphore']['num'])
    sem = 100
    # log.debug("加载信号量信息成功, 当前信号量为{}".format(config['semaphore']['num']))
    # host = config['website']['host']
    host = 'news.sise.edu.cn'
    # 未爬取url
    urls = dict()
    # 添加第一批url
    # for i in range(1,12):
    for i in range(1, 12):
        # http://news.sise.edu.cn/cms/news/1.html
        urls['http://news.sise.edu.cn/cms/news/{}.html'.format(
            str(i))] = 'column'
    # 创建Queue

    # 创建header
    Headers = buildHeader("http://" + host)
    # 创建一个协程
    product_loop = asyncio.new_event_loop()
    analysis_loop = asyncio.new_event_loop()
    write_loop = asyncio.new_event_loop()
    # 创建线程
    # 生产者线程
    tProducter = threading.Thread(target=main,
                                  name='product',
                                  args=(product_loop, ))
    # tProducter = threading.Thread(target=main, name='product', args=(productr, thread_loop, Headers, sem, log, q1, url,))
    # 解析消费者线程
    tAnalysisr = threading.Thread(target=main,
                                  name='analysis',
                                  args=(analysis_loop, ))
    # tAnalysisr = threading.Thread(target=main, name='analysis', args=(analysisr, thread_loop, host, log, q1, q2, url,))
    # 写入消费者线程
    tWriter = threading.Thread(target=main, name='writer', args=(write_loop, ))
    # tWriter = threading.Thread(target=main, name='writer', args=(writer, thread_loop, Headers, log, q2,))
    tProducter.setDaemon = True
    tAnalysisr.setDaemon = True
    tWriter.setDaemon = True
    # 执行线程
    tProducter.start()
    # tProducter.join()
    tAnalysisr.start()
    tWriter.start()
    array1 = list()
    array2 = list()
    # urls, Headers, sem, log, waitToAnalysis
    asyncio.run_coroutine_threadsafe(productr(Headers, sem, urls, array1),
                                     product_loop)
    # urls, Headers, sem, waitToAnalysis
    # waitToAnalysis, log, waitToWrite, urls, host
    asyncio.run_coroutine_threadsafe(analysisr(array1, array2, urls, host),
                                     analysis_loop)
    # log, waitToWrite, Headerss
    asyncio.run_coroutine_threadsafe(writer(array2, Headers), write_loop)

import requests
from requests.utils import get_encoding_from_headers,get_encodings_from_content
from utils import retry,user_agent
import socket
import time
from urllib.parse import splittype
import tempfile
from urllib.error import ContentTooShortError
import contextlib
import traceback
import os
from urllib.request import (Request,urlopen,ProxyHandler,
                                    build_opener,install_opener)


__all__ = ['geturl','loadurl','set_now']


def geturl(url, m='get', headers={}, ip=None, retries=0, encoding=None, data=None, *args, **kwargs):
    """基于requests第三方库，对其进一步封装，返回response对象
            1.自动设定User-Agent
            2.自动判断html编码方式（url链接为文件的话无法自动判断）

        参数：
            url: 请求的网址 
            m：请求的方式，默认get
            headers: 设置头文件，默认添加User-Agent
            ip：代理,输入字符串格式 [ip:port]
            retries：请求错误之后的重试次数，显示错误信息
            encoding： 网页的编码格式，默认不编码
            data：向服务器发送的数据，注意修改方式
            其他：可以传入基于requests的其他参数
        返回值：
            requests的response对象
    """
    us = {'User-Agent':user_agent()}
    if headers.get('User-Agent') == None:
        headers.update(us)

    # 代理ip的处理  
    proxies = None
    if ip:
        proxies = {'http':ip,'https':ip,'socks5':ip}
    
    # 请求网页的主函数
    #    retry 请求响应错误时重试 
    @retry(retries=retries)
    def _response():
        request_method = getattr(requests, m)   # 字符串变成函数变量名
        rm = request_method(url,headers=headers,proxies=proxies,*args,**kwargs)
        return rm
    r = _response()

    # 重试失败的话返回错误信息
    if False in r:
        return r[1]

    # 优先采用encoding参数，如果不存在则自动判断 
    if encoding != None:
        r.encoding = encoding
    else:
        # 一般的下载文件都很大，判断编码方式过于占用时间
        # 故先判断url链接是否为文件，不是文件才分析编码      
        if "text/html" in r.headers['Content-Type']:
            encoding = get_encodings_from_content(r.text)
            if encoding:
                r.encoding = encoding[0]

    return r


def format_size(bytes):
    """字节bytes转化K/M/G

        参数：
            bytes：字节流
        返回值：
            转换后的字符串数据（关系为1024）
    """
    bytes = float(bytes)
    KB = bytes / 1024
    if KB >= 1024:
        M = KB / 1024
        if M >= 1024:
            G = M / 1024
            return "{:.3f}GB".format(G)
        else:
            return "{:.3f}MB".format(M)
    return "{:.3f}KB".format(KB)


def set_now():
    """获取当前时间

        返回值：
            特殊格式的字符串时间戳
    """
    DATE = time.strftime("%H:%M:%S", time.localtime())
    return DATE


def callbackfunc(downsize, totalsize, start_time):
    """下载文件时的回调函数

        参数：
            downsize: 已经下载的数据
            totalsize: 远程文件的总大小
            start_time： 用于统计网速的起始时间
        返回值：
            在控制台上打印出下载的进度条
    """
    # 产生网速数据，并将bytes数据转化成 K/M/G
    INTERVAL = time.time() - start_time  # 间隔时间过短时不允许为0
    if INTERVAL <= 0:
        INTERVAL = 0.00001

    # 产生剩余时间
    SPEED = downsize / INTERVAL
    REMIND_TIME_STR = "--"
    if SPEED != 0:
        remind_time = (totalsize - downsize) / SPEED
        REMIND_TIME_STR = "{:.2f}s".format(remind_time)

    # 产生进度条 
    percent = 100.0 * downsize / totalsize  # 计算百分比
    D = format_size(downsize)
    T = format_size(totalsize)
    if percent > 100: percent = 100
    elif percent == 0:
        print(set_now() + " Start download " + str(path) + ' (' + T + ')')

    # 计算进度条步伐，显示方式等 
    STEPS = 25 
    num_arrow = int(downsize/(totalsize/STEPS))    
    num_line = STEPS - num_arrow   
    DONE = "+" * num_arrow
    UNDONE = "-" * num_line

    # 拼接各个数据 
    SPEED_STR = "{}/s".format(format_size(SPEED))
    PERCENT_STR =  "{:.2f}%".format(percent)  
    P_STR = PERCENT_STR + ' [' + DONE + UNDONE + "] " + D + " " + SPEED_STR + " " + REMIND_TIME_STR    # 显示进度条和百分比
    SUS = set_now() + " Download success {}".format(str(path))
    R = '\r'
    N = '\n'
    P_BLANK = " " * 5       # 命令行一行输出会重叠，末尾用空格替代
    S_BLANK = " " * ( len(P_STR) - len(SUS) + 5 )

    # 显示进度条 
    if hook == True:
        print(P_STR + P_BLANK + R,end="")
    if percent == 100:
        print(SUS + S_BLANK + N,end="")   


def download_func(url, filename=None, ip=None, headers=None, reporthook=None, data=None):
    """参考于urllib.request.urlretrieve函数，进行了一定的改进
            1.可以添加ip代理与headers
            2.可以显示制定的进度条

        参数：
            url：下载文件的链接
            filename：下载文件路径名称
            ip：代理ip 格式为字符串 【ip：port】
            headers：添加头文件，默认为空
            reporthook：是否显示进度条  True False
            data：向服务器发送数据
        返回值：
            下载文件相关信息
    """
    url_type, path = splittype(url)
    req_obj = Request(url);

    # 添加headers 
    if headers:
        def addheaders(headers,req_obj):
            for key,value in headers.items():
                req_obj.add_header(key,value)     # 添加头文件
            return req_obj
        req = addheaders(headers,req_obj)

    # 添加ip代理
    if ip:
        proxies = {"http":ip,"https":ip,"socks":ip}
        proxy_support = ProxyHandler(proxies)
        opener = build_opener(proxy_support)
        install_opener(opener)

    # 利用urlopen进行下载  
    with contextlib.closing(urlopen(req,data)) as fp:
        headers = fp.info()

        # 判断传入的url是http网址还是本地文件地址 
        if url_type == "file" and not filename:
            return os.path.normpath(path), headers

        # 如果为本地地址则open创建新文件 
        #        否则创建临时文件 
        if filename:
            tfp = open(filename, 'wb')
        else:
            tfp = tempfile.NamedTemporaryFile(delete=False)
            filename = tfp.name
            url_tempfile.append(filename)
        with tfp:
            result = filename, headers
            bs = 1024 * 20     # 每块的大小
            size = -1       # 总大小
            downsize = 0        # 已下载的大小

            if "content-length" in headers:
                size = int(headers["Content-Length"])
            else:
                headers = {'Accept-Encoding':'None'} # 有的返回headers中不存在Conten-Length, 令其为none
                new_req = addheaders(headers,req_obj)
                size = int(urlopen(new_req,data).info()["Content-Length"])

            if reporthook:
                start_time = time.time()    # 网速的起始时间
                reporthook(downsize, size, start_time)

            # 下载文件循环，直到下载完成 
            while True:
                block = fp.read(bs)
                if not block:
                    break
                downsize += len(block)
                tfp.write(block)
                if reporthook:
                    reporthook(downsize, size,start_time)
    if size >= 0 and downsize < size:
        raise ContentTooShortError(
            "retrieval incomplete: got only %i out of %i bytes"
            % (downsize, size), result)

    return result



def loadurl(url, filename=None, ip=None,retries=0, headers={}, timeout=30, showhook=True):
    """下载远程文件，流程为： 主函数 --> 下载函数 --> 进度条函数
            1.下载失败的话自动删除下载文件（程序中断的情况无法删除）

        参数：
            url：下载文件的链接
            filename：文件的路径
            ip：代理ip，格式为 【ip：port】
            retries: 错误后重试次数，默认不重试
            headers：传入头文件，默认添加User-Agent
            timeout：设置超时时间，默认30s
            showhook：是否显示进度条
        返回值
            下载成功返回 True
            下载失败返回 False
    """
    global hook,path,url_tempfile
    hook = showhook
    if not isinstance(hook,bool):  raise TypeError(hook)
    path = filename   # 局部参数与global参数有冲突，重新赋值
    
    socket.setdefaulttimeout(timeout)
    url_tempfile = list()

    us = {'User-Agent':user_agent()}
    if headers.get('User-Agent') == None:
        headers.update(us)


    # 重试函数不允许重复嵌套，只能从这里下手 
    @retry(retries=retries)
    def _temp(*args,**kwargs):
        download_func(*args,**kwargs)
    r = _temp(url, filename=filename, ip=ip, headers=headers, reporthook=callbackfunc)

    # 重试也失败的话返回错误信息
    if not r == None:
        if False in r:
            return r[1]

    # 下载错误的话删除下载不完整的文件 
    #        注意：程序突然终止的话文件无法删除
    if r == False:
        if os.path.exists(filename):
            os.remove(filename)
        return False
    return True


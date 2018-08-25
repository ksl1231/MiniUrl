
'''
    转载于 https://github.com/phoemur/ipgetter
    做了一些删减改造

    Reprinted in https://github.com/phoemur/ipgetter
    I just made some modifications


'''

import re
import random
import ssl
import urllib.request as urllib
import http.cookiejar as cjar
from ..get import user_agent



server_list = ['http://ip.dnsexit.com',
                'http://ifconfig.me/ip',
                'http://ipecho.net/plain',
                'http://checkip.dyndns.org/plain',
                'http://websiteipaddress.com/WhatIsMyIp',
                'http://getmyipaddress.org/',
                'http://www.my-ip-address.net/',
                'http://myexternalip.com/raw',
                'http://www.canyouseeme.org/',
                'http://www.trackip.net/',
                'http://icanhazip.com/',
                'http://www.iplocation.net/',
                'http://www.ipchicken.com/',
                'http://whatsmyip.net/',
                'http://www.ip-adress.com/',
                'http://checkmyip.com/',
                'http://www.tracemyip.org/',
                'http://www.lawrencegoetz.com/programs/ipinfo/',
                'http://www.findmyip.co/',
                'http://ip-lookup.net/',
                'http://www.mon-ip.com/en/my-ip/',
                'http://ipgoat.com/',
                'http://www.myipnumber.com/my-ip-address.asp',
                'http://formyip.com/',
                'https://check.torproject.org/',
                'http://www.displaymyip.com/',
                'http://www.bobborst.com/tools/whatsmyip/',
                'http://www.geoiptool.com/',
                'https://www.whatsmydns.net/whats-my-ip-address.html',
                'https://www.privateinternetaccess.com/pages/whats-my-ip/',
                'http://checkip.dyndns.com/',
                'http://www.ip-adress.eu/',
                'http://www.infosniper.net/',
                'https://wtfismyip.com/text',
                'http://ipinfo.io/',
                'http://httpbin.org/ip',
                'https://diagnostic.opendns.com/myip',
                'http://checkip.amazonaws.com',
                'https://api.ipify.org',
                'https://v4.ident.me',
                'http://2018.ip138.com/ic.asp']

def get_externalip():
    '''
        随机获取ip的网站

    '''

    myip = str()
    for i in range(7):
        myip = fetch(random.choice(server_list))
        if myip:
            return myip
        else:
            continue
    return None

def fetch(server):
    '''
        获取具体网站的ip

    '''
    url = None
    cj = cjar.CookieJar()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    opener = urllib.build_opener(urllib.HTTPCookieProcessor(cj), urllib.HTTPSHandler(context=ctx))
    opener.addheaders = [('User-agent', user_agent()),
                         ('Accept', "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                         ('Accept-Language', "en-US,en;q=0.5")]

    try:
        url = opener.open(server, timeout=1)
        content = url.read()

        import chardet   #  需要导入这个模块，检测编码格式
        encode_type = chardet.detect(content)  
        content = content.decode(encode_type['encoding']) # 进行相应解码，赋给原标识符（变量）

        m = re.search(
            '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)',
            content)
        myip = m.group(0)
        return myip if len(myip) > 0 else None
    except Exception:
        return None
    finally:
        if url:
            url.close()



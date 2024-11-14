# -*- coding:utf-8 -*-
import requests
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter

from factory import LoggerFactory
from config import constraints

logger = LoggerFactory.getLogger(__name__)

proxy_url = "http://%s:%d/" % (constraints.proxy_host, constraints.proxy_port)


def get_proxy():
    # 5000：settings中设置的监听端口，不是Redis服务的端口
    return requests.get("%sget/" % proxy_url).json()


def delete_proxy(proxy):
    requests.get("%sdelete/?proxy=%s" % (proxy_url, proxy))


def request(url, timeout=None, stream=None, max_retries=None):
    ua = UserAgent()
    headers = {"User-Agent": ua.random}
    if constraints.switch_on_proxy:
        # 请求头

        # proxy = net_util.get_proxy().get("proxy")
        # proxies = {"http": "http://{}".format(proxy)}

        s = requests.Session()
        max_retries = 3 if max_retries is None else max_retries
        s.mount('http://', HTTPAdapter(max_retries=max_retries))
        s.mount('https://', HTTPAdapter(max_retries=max_retries))
        # s.config['keep_alive'] = False
        s.keep_alive = False
        # logger.debug("headers =  %s", headers)
        # logger.debug("proxies =  %s", proxies)
        # logger.info('request data in : %s ...' % url)
        return s.get(url, headers=headers, proxies=constraints.proxies, timeout=timeout, stream=stream)
    else:
        return requests.get(url, headers=headers, timeout=timeout)


def down4img(url, output_name, type):
    """
    下载指定url的一张图片，支持所有格式:jpg\png\gif .etc
    """
    response = request(url, stream=True)
    with open('.'.join((output_name, type)), 'wb') as output_img:
        for chunk in response:
            output_img.write(chunk)
        output_img.close()
        logger.debug(f"下载成功，图片名称：{'.'.join((output_name, type))}")

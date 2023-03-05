# -*- coding:utf-8 -*-
import requests
from fake_useragent import UserAgent

from factory import LoggerFactory
from util import net_util

logger = LoggerFactory.getLogger(__name__)


def request(url):
    # 请求头
    ua = UserAgent()
    headers = {"User-Agent": ua.random}

    proxy = net_util.get_proxy().get("proxy")
    proxies = {"http": "http://{}".format(proxy)}

    logger.debug("headers =  %s", headers)
    logger.debug("proxies =  %s", proxies)
    logger.info('request data in : %s ...' % url)
    return requests.get(url, headers=headers, proxies=proxies)

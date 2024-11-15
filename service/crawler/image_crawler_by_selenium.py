# -*- coding:utf-8 -*-
import os

from lxml import etree
from selenium import webdriver

from factory import LoggerFactory, DriverFactory
from config import constraints

logger = LoggerFactory.getLogger(__name__)


# 爬取图片
def crawl_pics_by_selenium(url, bg_num, pic_num, retry):
    logger.debug('Retrying crawling at %d/3 times : %s' % (retry, url))
    # timeout = constraints.base_second_in_crawl_image + constraints.single_image_second_in_crawl_image * pic_num * retry
    timeout = constraints.base_second_in_crawl_image * (0.5 + retry * 0.5)
    logger.debug('url %s has %d bg_pic, %d pics ,timeout = %d' % (url, bg_num, pic_num, timeout))
    edge = DriverFactory.getEdgeDriver(timeout)
    imgs = []
    bg_img = []
    try:
        edge.get(url)
        html = etree.HTML(edge.page_source)
        imgs = html.xpath('//blockquote[1]/following-sibling::p[following-sibling::blockquote[1]]/img/@src')
        if bg_num > 0:
            bg_img_element = html.xpath('//div[@class="blog-background"]/@style')
            if len(bg_img_element) and len(bg_img_element[0]):
                a = bg_img_element[0].split('url("')
                if len(a) > 1:
                    b = a[1].split('");')
                    if len(b) > 1:
                        bg_img_base64 = b[0]
                        bg_img.append(bg_img_base64)

    except Exception as e:
        logger.error(e)
        logger.debug("Get page '%s' timeout" % url)
        logger.debug("closing page '%s'..." % url)
        # 执行js脚本
        edge.execute_script("window.stop()")
        edge.quit()
        edge = None

    if len(imgs) < pic_num:
        if retry == 3:
            return bg_img, imgs
        return crawl_pics_by_selenium(url, bg_num, pic_num, retry + 1)
    return bg_img, imgs


def getChromeDriver(timeout):
    chrome = webdriver.Chrome()
    if constraints.switch_on_proxy:
        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.add_argument("--proxy-server=%s" % constraints.chrome_proxy)
        chrome = webdriver.Chrome(chrome_options=chromeOptions)

    chrome.set_window_size(100, 50)
    chrome.minimize_window()
    # chrome.implicitly_wait(timeout)
    chrome.set_page_load_timeout(timeout)
    chrome.set_script_timeout(timeout)
    return chrome

# -*- coding:utf-8 -*-
# self is a sample Python script.
import json
import re

import requests
from lxml import etree
from selenium import webdriver
from selenium.webdriver.edge.service import Service
import LoggerFactory
import constraints
# 获取logger实例，如果参数为空则返回root logger
from code_enum import AttributeCode
from util import common_util, net_util

logger = LoggerFactory.getLogger(__name__)


def crawl_infos_by_selenium(page):
    status_code = 404

    try:
        url = common_util.get_page_url(page)
        logger.info("Crawling page: '%s'..." % url)
        info = {AttributeCode.URL: url, AttributeCode.STATUS_CODE: None, AttributeCode.TITLE: None,
                AttributeCode.DATE: None, AttributeCode.LINKS: None, AttributeCode.CONTENT: None,
                AttributeCode.VIDEO_URLS: None, AttributeCode.IMAGE_URLS: None}

        edge = getDriver(20)
        try:
            edge.get(url)
        except Exception as e:
            logger.error(e)
            logger.info("Get page '%s' timeout" % url)
            logger.info("closing page '%s'..." % url)
            # 执行js脚本
            edge.execute_script("window.stop()")
        # status_code = resp.status_code

        logger.info("Status code of page:%s is '%s'..." % (url, status_code))

        html = etree.HTML(edge.page_source)
        status_code = crawl_404(html)
        info[AttributeCode.STATUS_CODE] = status_code
        if status_code == 404:
            logger.info("Page 404: '%s'..." % url)
            constraints.img_num_in_page[page] = {'code': status_code, 'cpt_num': 0, 'folder_path': ''}
            return info
        if status_code == 200:
            # title
            logger.info('Crawling title in %s' % url)
            info[AttributeCode.TITLE] = crawl_title(html)

            # date
            logger.info('Crawling date in %s' % url)
            info[AttributeCode.DATE] = crawl_date(html)

            # content
            logger.info('Crawling content in %s' % url)
            info[AttributeCode.CONTENT] = crawl_content(html)

            # images
            logger.info('Crawling images in %s' % url)
            info[AttributeCode.IMAGE_URLS] = crawl_imgs(html)

            # videos
            logger.info('Crawling videos in %s' % url)
            info[AttributeCode.VIDEO_URLS] = crawl_videos(html)
            return info

    except requests.exceptions.ConnectionError as rec:
        logger.error(rec)
        constraints.img_num_in_page[page] = {'code': status_code, 'cpt_num': 0, 'folder_path': ''}
        return info
    except Exception as e:
        logger.error(e)
        logger.info("Request page error: '%s'." % url)
        constraints.img_num_in_page[page] = {'code': status_code, 'cpt_num': 0, 'folder_path': ''}
        return info


# 爬取h3
def crawl_404(html):
    content404_elements = html.xpath('//div[@class="content404-wrapper"]')
    logger.debug('content404_elements %s', content404_elements)
    if len(content404_elements) > 0:
        return 404
    return 200


# 爬取date
def crawl_date(html):
    date = None
    time_elements = html.xpath('//time')
    logger.debug('timeobj %s', time_elements)
    if len(time_elements) > 0:
        date = time_elements[0].text.replace('年', '.').replace('月', '.').replace('日', '').replace(' ', '')
        # if len(date) == 5:
        #     date = '%s%s%s' % (constraints.year, '.', date)
        #     if '年' in date:
        #         date = date.replace(' ', '').replace('年', '.').replace('月', '.').replace('日', '')
        logger.debug('date: %s', date)
    return date


# 爬取title
def crawl_title(html):
    title = None
    title_elements = html.xpath('//span[@class="anti-theft-decode"]')
    if len(title_elements) > 0:
        title = title_elements[0].text.strip()
        rstr = r"[\/\\\:\*\?\"\\|]"  # '/ \ : * ? " < > |'
        new_title = re.sub(rstr, "_", title)
        if new_title == '.':
            new_title = '_'
        while new_title.endswith('.'):
            new_title = new_title[:-1]

        return new_title
    return title


# 爬取links
def crawl_links(page_source):
    links = {}
    # h1_elements = html.xpath(
    #     '//article[starts-with(@class, "joe_detail__article")]//a[re:match(@href,"/\d+")]')
    a_tags = page_source.xpath(
        '//article[starts-with(@class, "joe_detail__article")]//a[not(contains(@href,".")) and starts-with(@href,"/")]')
    if len(a_tags) > 0:
        for a in a_tags:
            links[a.text] = '%s%s' % (constraints.domain, a.get('href'))
    return links


# 爬取content
def crawl_content(html):
    # content
    text = ''
    try:
        # <div class="post-content" itemprop="articleBody">
        content_strong_list = html.xpath('//div[@class="post-content"]//p//strong')
        for strong in content_strong_list:
            text += strong.text + '\n'
        content_p_list = html.xpath('//div[@class="post-content"]//p')
        for p in content_p_list:
            if p.text is not None:
                text += p.text + '\n'
        return text
    except Exception as e:
        logger.error(e)
        return text


def crawl_videos(html):
    urls = []
    content_tabs = html.xpath('//div[@class="post-content"]//div[@class="content-tabs"]')
    for content in content_tabs:
        data_config_1 = content.xpath('//div[@data-tab-index="1"]//div/@data-config')
        url1_error = False
        if len(data_config_1):
            url1 = json.loads(data_config_1[0])['video']['url']
            try:
                if net_util.request(url1).status_code == 200:
                    urls.append(url1)
            except Exception as e:
                url1_error = True
                logger.info("url1 is 404: %", url1)
        if url1_error:
            data_config_2 = content.xpath('//div[@data-tab-index="2"]//div/@data-config')
            if len(data_config_2):
                url2 = json.loads(data_config_2[0])['video']['url']
                if net_util.request(url2).status_code == 200:
                    urls.append(url2)
                else:
                    urls.append(url1)
                    urls.append(url2)
    urls = list(set(urls))
    return urls


def crawl_tab_1(iframe_url):
    resp = net_util.request(iframe_url)
    m3u8_list = []
    if resp.status_code == 200:
        page_source = etree.HTML(resp.text)
        scripts = page_source.xpath('//script[contains(text(),"new DPlayer")]/text()')
        for text in scripts:
            try:
                m3u8 = text.replace(' ', '').replace('\n', '').split("url:'", 1)[1].split("',", 1)[0]
                m3u8_list.append(m3u8)
            except Exception as e:
                logger.error('parsing error %s', text)

        return m3u8_list


def crawl_iframe_m3u8_url(iframe_url):
    resp = net_util.request(iframe_url)
    m3u8_list = []
    if resp.status_code == 200:
        page_source = etree.HTML(resp.text)
        scripts = page_source.xpath('//script[contains(text(),"new DPlayer")]/text()')
        for text in scripts:
            try:
                m3u8 = text.replace(' ', '').replace('\n', '').split("url:'", 1)[1].split("',", 1)[0]
                m3u8_list.append(m3u8)
            except Exception as e:
                logger.error('parsing error %s', text)

        return m3u8_list


def crawl_imgs(html):
    img_src_data_list = html.xpath('//div[@class="post-content"]//p//img/@src')
    return img_src_data_list


def getDriver(timeout):
    s = Service(constraints.webbrowser_driver_path)
    edge = webdriver.Edge(service=s)
    edge.set_window_size(100, 50)
    edge.minimize_window()
    edge.set_page_load_timeout(timeout)
    edge.set_script_timeout(timeout)
    return edge

# -*- coding:utf-8 -*-
# self is a sample Python script.
import re

import requests
from lxml import etree

from factory import LoggerFactory
from config import constraints
# 获取logger实例，如果参数为空则返回root logger
from config.code_enum import AttributeCode
from util import common_util, net_util

logger = LoggerFactory.getLogger(__name__)


def crawl_by_page(page):
    status_code = 404
    try:
        url = common_util.get_page_url(page)
        logger.info("Crawling page: '%s'..." % url)
        info = {AttributeCode.URL: url, AttributeCode.STATUS_CODE: None, AttributeCode.TITLE: None,
                AttributeCode.DATE: None, AttributeCode.LINKS: None, AttributeCode.CONTENT: None,
                AttributeCode.VIDEO_URLS: None, AttributeCode.IMAGE_URLS: None}

        resp = net_util.request(url, 20)
        status_code = resp.status_code
        info[AttributeCode.STATUS_CODE] = status_code
        logger.info("Status code of page:%s is '%s'..." % (url, status_code))
        if status_code == 404:
            logger.info("Page 404: '%s'..." % url)
            constraints.img_num_in_page[page] = {'code': status_code, 'cpt_num': 0, 'folder_path': ''}
            return info
        if status_code == 200:
            # 使用xpath
            page_source = etree.HTML(resp.text)

            # date
            logger.info('Crawling date in %s' % url)
            info[AttributeCode.DATE] = crawl_date(page_source)
            # title
            logger.info('Crawling title in %s' % url)
            info[AttributeCode.TITLE] = crawl_title(page_source)
            # links
            logger.info('Crawling links in %s' % url)
            info[AttributeCode.LINKS] = crawl_links(page_source)
            # content
            logger.info('Crawling content in %s' % url)
            info[AttributeCode.CONTENT] = crawl_content(page_source)
            # videos
            logger.info('Crawling videos in %s' % url)
            info[AttributeCode.VIDEO_URLS] = crawl_videos(page_source)
            # images
            logger.info('Crawling images in %s' % url)
            info[AttributeCode.IMAGE_URLS] = crawl_imgs(page_source)
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


# 爬取date
def crawl_date(page_source):
    date = None
    time_elements = page_source.xpath('//meta[starts-with(@itemprop, "datePublished")]/@content')
    logger.debug('timeobj %s', time_elements)
    if len(time_elements) > 0:
        date = time_elements[0].split('T')[0].replace('-','.')
        # if len(date) == 5:
        #     date = '%s%s%s' % (constraints.year, '.', date)
        #     if '年' in date:
        #         date = date.replace(' ', '').replace('年', '.').replace('月', '.').replace('日', '')
        logger.debug('date: %s', date)
    return date


# 爬取title
def crawl_title(page_source):
    title = None
    h1_elements = page_source.xpath('//h1[starts-with(@class, "joe_detail__title")]')
    if len(h1_elements) > 0:
        title = h1_elements[0].text.strip()
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
def crawl_content(page_source):
    # content
    text = ''
    try:
        h2_list = page_source.xpath('//h2')
        for h2 in h2_list:
            text += h2.text + '\n'
        return text
    except Exception as e:
        logger.error(e)
        return text


def crawl_videos(paeg_source):
    m3u8List = paeg_source.xpath('//joe-dplayer/@src')
    if not len(m3u8List):
        m3u8List = paeg_source.xpath('//div[@class="box"]/div[starts-with(@class,"item")]/@data-src')

    videoList = []
    m3u8List = list(set(m3u8List))
    for m3u8Obj in m3u8List:
        m3u8Obj = m3u8Obj.replace('<br>', '')
        try:
            if net_util.request(m3u8Obj).status_code == 200:
                videoList.append(m3u8Obj)
        except Exception as e:
            logger.error(e)
    if len(videoList) == 0:
        player_list = paeg_source.xpath('//joe-dplayer/@player')
        src_list = paeg_source.xpath('//joe-dplayer/@src')
        if len(player_list) * len(src_list):
            for i in range(len(src_list)):
                try:
                    iframe_url = '%s%s%s' % (constraints.domain, player_list[i], src_list[i].replace('<br>', ''))
                    scripts_urls = crawl_iframe_m3u8_url(iframe_url)
                    videoList.extend(scripts_urls)
                except Exception as e:
                    logger.error(e)
    return videoList


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


def crawl_imgs(page_source):
    img_urls = []
    imgs = page_source.xpath('//article[@class="joe_detail__article"]//img/@src')
    for i in imgs:
        img_urls.append(i if 'http' in i else constraints.domain + i)
    return img_urls

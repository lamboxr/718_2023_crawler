# -*- coding:utf-8 -*-
# self is a sample Python script.
import json
import re

import requests
from lxml import etree

from config.constraints import line_types
from factory import LoggerFactory
from config import constraints
# 获取logger实例，如果参数为空则返回root logger
from config.code_enum import AttributeCode
from service.saver import single_page_saver
from util import common_util, net_util

logger = LoggerFactory.getLogger(__name__)


def crawl_by_page(page):
    status_code = 404
    try:
        url = common_util.get_page_url(page)
        logger.info("Crawling page: '%s'..." % url)
        info = {AttributeCode.URL.value: url, AttributeCode.STATUS_CODE.value: None, AttributeCode.TITLE.value: None,
                AttributeCode.DATE.value: None, AttributeCode.LINKS.value: None, AttributeCode.CONTENT.value: None,
                AttributeCode.VIDEO_URLS.value: None, AttributeCode.IMAGE_URLS.value: None,
                AttributeCode.IMAGE_URLS.value: None,
                AttributeCode.IMAGE_B64S.value: None, AttributeCode.IMAGE_BG_B64.value: None}

        resp = net_util.request(url, 20)
        status_code = resp.status_code
        info[AttributeCode.STATUS_CODE.value] = status_code
        logger.debug("Status code of page:%s is '%s'..." % (url, status_code))
        if status_code == 404:
            logger.debug("Page 404: '%s'..." % url)
            constraints.img_num_in_page[page] = {'code': status_code, 'cpt_num': 0, 'folder_path': ''}
            return info
        if status_code == 200:
            # 使用xpath
            page_source = etree.HTML(resp.text)

            # date
            logger.debug('Crawling date in %s' % url)
            info[AttributeCode.DATE.value] = crawl_date(page_source)
            # title
            logger.debug('Crawling title in %s' % url)
            info[AttributeCode.TITLE.value] = crawl_title(page_source)
            # links
            logger.debug('Crawling links in %s' % url)
            info[AttributeCode.LINKS.value] = crawl_links(page_source)
            # content
            logger.debug('Crawling content in %s' % url)
            info[AttributeCode.CONTENT.value] = crawl_content(page_source)
            # videos
            logger.debug('Crawling videos in %s' % url)
            info[AttributeCode.VIDEO_URLS.value] = crawl_videos(page_source)
            # image_num
            logger.debug('Crawling images in %s' % url)
            info[AttributeCode.IMAGE_NUM.value] = crawl_img_num(page_source)
            # image_bg_num
            logger.debug('Crawling images in %s' % url)
            info[AttributeCode.IMAGE_BG_NUM.value] = crawl_bg_img_num(page_source)

            constraints.img_num_in_page[page] = {AttributeCode.STATUS_CODE.value: status_code,
                                                 AttributeCode.TITLE.value: info[AttributeCode.TITLE.value],
                                                 AttributeCode.IMAGE_NUM.value: info[AttributeCode.IMAGE_NUM.value],
                                                 AttributeCode.IMAGE_BG_NUM.value: info[AttributeCode.IMAGE_BG_NUM.value],
                                                 AttributeCode.FOLDER_PATH.value: single_page_saver.generate_single_page_folder_path(
                                                     page,
                                                     info)}
            return info

    except requests.exceptions.ConnectionError as rec:
        logger.error(rec)
        constraints.img_num_in_page[page] = {'code': status_code, 'cpt_num': 0, 'folder_path': ''}
        return info
    except Exception as e:
        logger.error(e)
        logger.debug("Request page error: '%s'." % url)
        constraints.img_num_in_page[page] = {'code': status_code, 'cpt_num': 0, 'folder_path': ''}
        return info


# 爬取date
def crawl_date(page_source):
    date = None
    time_elements = page_source.xpath('//meta[starts-with(@itemprop, "datePublished")]/@content')
    logger.debug('timeobj %s', time_elements)
    if len(time_elements) > 0:
        date = time_elements[0].split('T')[0].replace('-', '.')
        # if len(date) == 5:
        #     date = '%s%s%s' % (constraints.year, '.', date)
        #     if '年' in date:
        #         date = date.replace(' ', '').replace('年', '.').replace('月', '.').replace('日', '')
        logger.debug('date: %s', date)
    return date


# 爬取title
def crawl_title(page_source):
    title = None
    title_list = page_source.xpath('//h1[starts-with(@class, "post-title")]/text()')
    if title_list and len(title_list) > 0:
        title = title_list[0].strip()
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
        h2_list = page_source.xpath(
            '///blockquote[1]/following-sibling::p[string-length(normalize-space()) > 0 and following-sibling::blockquote]/text()')
        return '\n'.join(h2_list)
    except Exception as e:
        logger.error(e)
        return text


def crawl_videos(paeg_source):
    m3u8_dict = {}
    for line_type in line_types:
        m3u8_dict[line_type] = []

        data_configs = paeg_source.xpath(
            '//blockquote[1]/following-sibling::div[@class="content-tabs" and .//div/div[normalize-space(text())="%s"] and following-sibling::blockquote]/div[2]//div/div/@data-config' % line_type)
        for dc in data_configs:
            if len(dc):
                url = json.loads(dc)['video']['url']
                try:
                    if net_util.request(url).status_code == 200:
                        m3u8_dict[line_type].append(url)
                except Exception as e:
                    logger.debug("url1 is 404: %", url)
    return m3u8_dict


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
    img_urls = page_source.xpath('//blockquote[1]/following-sibling::p[following-sibling::blockquote[1]]//img/@src')
    return img_urls


def crawl_img_num(page_source):
    img_urls = page_source.xpath('//blockquote[1]/following-sibling::p[following-sibling::blockquote[1]]//img/@src')
    return len(img_urls)


def crawl_bg_img_num(page_source):
    bg_img = page_source.xpath('//h1[@class="blog-title"]')
    return len(bg_img)

# -*- coding:utf-8 -*-
# self is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import datetime
import json
import os
import pathlib
import random
from concurrent.futures import wait, ALL_COMPLETED

import LoggerFactory
import constraints
import image_downloader
import m3u8_downloader
import seven18_crawler
from code_enum import AttributeCode, DownloadCode
from t.BoundedThreadPoolExecutor import BoundedThreadPoolExecutor
from util import common_util, file_util, net_util

logger = LoggerFactory.getLogger(__name__)

pathlib.Path(constraints.out_put).mkdir(parents=True, exist_ok=True)


def save_by_page(page, info):
    url = common_util.get_page_url(page)
    if info is None:
        info = {AttributeCode.URL: url}
        createSingleFile(page, info)
        return
    elif info[AttributeCode.STATUS_CODE] is None:
        return
    elif info[AttributeCode.STATUS_CODE] == 404:
        logger.info("Page '%s' is 404, continue..." % url)
        createSingleFile(page, info)
        return
    elif (info[AttributeCode.VIDEO_URLS] is None or len(info[AttributeCode.VIDEO_URLS]) == 0) and (
            info[AttributeCode.IMAGE_URLS] is None or len(info[AttributeCode.IMAGE_URLS]) == 0):
        # 图片 视频均不存在
        logger.info('Page "%s" has no media, continue...' % url)
        createSingleFile(page, info)
        return
    else:
        saveData(page, info)


def createSingleFile(page, info):
    txt_dir = os.path.join(constraints.out_put, 'txt')
    pathlib.Path(txt_dir).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(txt_dir, '%05d' % page)  # output/idx
    txt = ''
    date_in_path = ''
    title_in_path = ''
    url = info[AttributeCode.URL]
    if len(info) == 1 or info[AttributeCode.STATUS_CODE] == 404:
        txt = url
        file_path += '.txt'
    elif info[AttributeCode.STATUS_CODE] == 200:
        txt += '%s\n\n' % info[AttributeCode.URL]
        if info[AttributeCode.DATE] is not None:  # 日期不为空
            date_in_path = '%s%s' % ('_', info[AttributeCode.DATE])  # output/idx_date
            txt += '%s%s' % (info[AttributeCode.TITLE], '\n')

        title = info[AttributeCode.TITLE]
        if title is not None:  # 如果标题不为空  # output/idx_date_title
            title_in_path = '%s%s' % ('_', title)  # output/idx_date_title
            txt += '%s%s' % (title, '\n')

        links = info[AttributeCode.LINKS]
        if links is not None:
            for p_title, link in links.items():
                txt += '%s\n%s\n\n' % (p_title, link)

        if info[AttributeCode.CONTENT] is not None:  # 如果content不为空
            txt += info[AttributeCode.CONTENT]

        file_path = '%s%s%s%s' % (file_path, date_in_path, title_in_path, '.txt')
    if os.path.exists(file_path):
        logger.info("Skip creating single file %s..." % file_path)
    else:
        logger.info("Creating single file '%s'..." % file_path)
        with open(file_path, 'w', encoding='utf8') as text_file:
            text_file.write(txt)
            text_file.flush()
            text_file.close()


def saveData(page_idx, info):
    single_page_folder_path = generate_single_page_folder_path(page_idx, info)
    pathlib.Path(single_page_folder_path).mkdir(parents=True, exist_ok=True)
    saveContent(info, single_page_folder_path)
    # # imgs
    if constraints.switch_on_save_image:
        saveImgs(info, single_page_folder_path)
    # video
    if constraints.switch_on_save_video:
        saveVideos(info, single_page_folder_path, page_idx)

    return single_page_folder_path


def generate_single_page_folder_path(page_idx, info):
    return os.path.join(constraints.out_put,
                        '%s%s%s%s%s' % (
                            '%05d' % page_idx, '_', info[AttributeCode.DATE], '_', info[AttributeCode.TITLE]))


def saveContent(info, single_page_folder_path):
    if info[AttributeCode.STATUS_CODE] == 404:
        return
    links = info[AttributeCode.LINKS]
    link_txt = ''
    if links is not None:
        for p_title, link in links.items():
            link_txt += '%s\n%s\n\n' % (p_title, link)
    m3u8_list = info[AttributeCode.VIDEO_URLS]
    img_list = info[AttributeCode.IMAGE_URLS]
    m3u8s_url = '视频链接(%d):\n' % len(info[AttributeCode.VIDEO_URLS])
    imgs_url = '图片链接(%d):\n' % len(info[AttributeCode.IMAGE_URLS])
    if m3u8_list is not None and len(m3u8_list) > 0:
        for i in m3u8_list:
            m3u8s_url += i + '\n'
    if img_list is not None and len(img_list) > 0:
        img_idx_pattern = '%0' + str(len(str(len(img_list)))) + 'd'
        idx = 1
        for i in img_list:
            imgs_url += '%s: %s%s' % (img_idx_pattern % idx, i, '\n')
            idx += 1

    txt_file_path = os.path.join(single_page_folder_path, '%s%s' % (info[AttributeCode.TITLE], '.txt'))

    if os.path.exists(txt_file_path):
        # logger.info('Skip saving existing content file: %s ' % filePath)
        logger.info('Deleting existing content file: %s ' % txt_file_path)
        os.remove(txt_file_path)

    logger.info('Saving content file: %s ... ' % txt_file_path)
    with open(txt_file_path, 'w', encoding='utf-8') as file_object:
        file_object.write(
            '%s\n\n%s\n%s\n%s\n%s\n%s\n' % (
                info[AttributeCode.URL], info[AttributeCode.TITLE], info[AttributeCode.CONTENT], link_txt, m3u8s_url,
                imgs_url))
        file_object.close()


def saveVideos(info, single_page_folder_path, page):
    m3u8_list = info[AttributeCode.VIDEO_URLS]
    if m3u8_list is not None:

        suffix = ''
        video_idx_pattern = '_video_%0' + str(len(str(len(m3u8_list)))) + 'd' if len(m3u8_list) > 1 else ''
        fragments_folder_suffix_patter = '_%0' + str(len(str(len(m3u8_list)))) + 'd' if len(m3u8_list) > 1 else ''
        for i in range(len(m3u8_list)):
            if len(m3u8_list) > 1:
                suffix = video_idx_pattern % (i + 1)
            output_video_path = os.path.join(single_page_folder_path,
                                             '%s%s%s' % (info[AttributeCode.TITLE], suffix, '.mp4'))
            if os.path.exists(output_video_path):
                logger.info('Skip saving existing video: %s ' % output_video_path)
            else:
                logger.info('Downloading fragments of video: "%s"...' % output_video_path)
                fragments_folder_name = '%d%s' % (
                    page, fragments_folder_suffix_patter % (i + 1) if len(m3u8_list) > 1 else '')
                fragments_cache_dir, fragments_folder_name = init_fragments_cache_dir(fragments_folder_name)
                constraints.download_video_count += 1
                download_code, cachePath, = m3u8_downloader.download(m3u8_list[i], fragments_cache_dir)
                if download_code is DownloadCode._200:
                    if cachePath is None:
                        logger.info('Cache video failed: %s - %s' % (output_video_path, m3u8_list[i]))

                        insert_into_error_log(page, i, m3u8_list[i], output_video_path, download_code) // TODO
                        continue
                    logger.info('cachePath: %s , savePath: %s' % (cachePath, output_video_path))
                    logger.info('Saving video "%s"...' % output_video_path)
                    os.rename(cachePath, output_video_path)
                else:
                    insert_into_error_log(page, i, m3u8_list[i], output_video_path, download_code)
    else:
        logger.info('There is not video to save.')


def saveImgs(info, single_page_folder_path):
    images_info = generate_images_info(info, single_page_folder_path)
    if len(images_info) > 0:
        if is_images_saved(images_info=images_info, single_page_folder_path=single_page_folder_path):
            logger.info('Skipping to save %d images in page %s' % (len(images_info), info[AttributeCode.URL]))
            return
        else:
            logger.info('Saving %d images in page %s' % (len(images_info), info[AttributeCode.URL]))
            if constraints.switch_on_img_thread:
                with BoundedThreadPoolExecutor(max_workers=constraints.max_image_size_in_threadpool) as t:
                    all_tasks = [t.submit(lambda p: image_downloader.save(*p),
                                          [images_url, image_path]) for image_path, images_url in
                                 images_info.items()]
                    wait(all_tasks, return_when=ALL_COMPLETED)
            else:
                for image_path, images_url in images_info.items():
                    image_downloader.save(images_url, image_path)


def is_images_saved(images_info, single_page_folder_path):
    return len([img for img in os.listdir(single_page_folder_path) if
                (not img.endswith('.mp4')) and (not img.endswith('.txt'))]) == len(images_info)


def generate_images_info(info, single_page_folder_path):
    images_info = {}
    img_idx_pattern = ''
    title = info[AttributeCode.TITLE]
    img_urls = info[AttributeCode.IMAGE_URLS]
    if len(img_urls) > 1:
        img_idx_pattern = '%0' + str(len(str(len(img_urls)))) + 'd'
    idx = 1
    for img_url in img_urls:
        prefix = img_url.split(';')[0].split('/')[1]
        if prefix == 'jpeg':
            prefix = 'jpg'
        images_info[os.path.join(single_page_folder_path, '%s_%s.%s' % (
            title, img_idx_pattern % idx if len(img_urls) > 1 else '', prefix))] = img_url
        idx += 1
    return images_info


def download_single_image(image_url, image_path):
    net_util.down4img(
        url=image_url,
        output_name=image_path,
        type=image_url.rsplit('.', 1)[1])


def insert_into_error_log(page, i, m3u8_url, output_video_path, download_code):
    _dict = file_util.read_file_as_json(seven18_crawler.error_video_page_path)  # dict

    # j_dict = json.dumps(j, indent=4, ensure_ascii=False)  # dict
    code_group = {}  # dict
    if download_code.value in _dict:
        code_group = _dict[download_code.value]
    else:
        _dict[download_code.value] = code_group

    page_data = {}  # dict
    page_str = str(page)
    if page_str in code_group:
        page_data = code_group[page_str]
    else:
        code_group[page_str] = page_data

    page_data[i + 1] = {"output_video_path": output_video_path, "m3u8_url": m3u8_url}
    # keys = sorted(j, key=cmp_to_key(lambda x, y: int(x) - int(y)))
    # _j = {}
    # for key in keys:
    #     _j[key] = j[key]
    with open(seven18_crawler.error_video_page_path, 'w', encoding='utf8') as file_object:
        file_object.write(json.dumps(_dict, indent=4, ensure_ascii=False))
        file_object.close()


def init_fragments_cache_dir(fragments_folder_name):
    # 指定存储目录
    fragments_cache_root = constraints.cache_root
    pathlib.Path(fragments_cache_root).mkdir(parents=True, exist_ok=True)
    fragments_folder_name = '%s_%d' % (datetime.datetime.now().strftime('%H%M'), '%03d' % random.randint(0,
                                                                                                         1000)) if fragments_folder_name is None else fragments_folder_name
    # 新建日期文件夹
    fragments_cache_dir = os.path.join(fragments_cache_root, fragments_folder_name)
    file_util.resetDir(fragments_cache_dir)
    return fragments_cache_dir, fragments_folder_name

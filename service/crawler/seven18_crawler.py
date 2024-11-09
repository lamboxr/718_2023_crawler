# -*- coding:utf-8 -*-
# self is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import json
import os.path
import pathlib
import time
from concurrent.futures import FIRST_COMPLETED, wait, ALL_COMPLETED

from tqdm import tqdm

from config import page_config, constraints
from config.constraints import pre_collect_on
from factory import LoggerFactory
from service.crawler import single_page_crawler_by_selenium, _200_collector
from service.saver import single_page_saver
from t.BoundedThreadPoolExecutor import BoundedThreadPoolExecutor

logger = LoggerFactory.getLogger(__name__)

time_stamp = time.strftime('%Y-%m-%d %H%M%S', time.localtime())
error_log_folder = os.path.join(os.getcwd(), 'error_log')
pathlib.Path(error_log_folder).mkdir(parents=True, exist_ok=True)

too_long_urls_dir = os.path.join(os.getcwd(), 'too_long_urls')
pathlib.Path(too_long_urls_dir).mkdir(parents=True, exist_ok=True)

error_video_page_path = os.path.join(error_log_folder, 'error_video_page_%s.txt' % time_stamp)
error_img_page_path = os.path.join(error_log_folder, 'error_img_page_%s.txt' % time_stamp)
too_long_urls_file_path = os.path.join(too_long_urls_dir, 'too_long_urls_%s.txt' % time_stamp)


def crawl(self):
    start_page = page_config.start_page
    end_page = page_config.end_page
    if start_page > end_page:
        _ = start_page
        start_page = end_page
        end_page = _

    loop_size = 20
    loop_count = (end_page - start_page) // loop_size + 1

    for i in range(loop_count):
        first_in_loop = end_page - loop_size * i
        last_in_loop = start_page - 1 if i == loop_count - 1 else end_page - loop_size * (i + 1)
        logger.info('%s', range(first_in_loop, last_in_loop, -1))

        if constraints.switch_on_main_thread:
            with BoundedThreadPoolExecutor(max_workers=constraints.max_size_in_main_threadpool) as t:
                all_tasks = [t.submit(self.handle_single_page, page) for page in
                             range(first_in_loop, last_in_loop, -1)]
                wait(all_tasks, return_when=FIRST_COMPLETED)

        else:
            for page in range(first_in_loop, last_in_loop, -1):
                self.handle_single_page(page)
    write_too_long_command_2_file()


def crawl1():
    start_page = page_config.start_page
    end_page = page_config.end_page
    if start_page > end_page:
        _ = start_page
        start_page = end_page
        end_page = _
    """
    #old逻辑
    if constraints.switch_on_main_thread:
        with BoundedThreadPoolExecutor(max_workers=constraints.max_size_in_main_threadpool) as t:
            all_tasks = [t.submit(self.handle_single_page, page) for page in
                         range(end_page, start_page - 1, -1)]
            wait(all_tasks, return_when=ALL_COMPLETED)

    else:
        for page in range(end_page, start_page - 1, -1):
            self.handle_single_page(page)
    """
    # with BoundedThreadPoolExecutor(max_workers=constraints.check_200_thread_num) as t:
    #     all_tasks = [t.submit(_200_collector.collect_200_by_page, page) for page in
    #                  range(end_page, start_page - 1, -1)]
    #     wait(all_tasks, return_when=ALL_COMPLETED)

    if pre_collect_on:
        _200_collector.collect_200(start_page, end_page)

        constraints.list_200.sort()
        constraints.list_404.sort()
        constraints.list_others.sort()
        logger.info('200 pages: %s' % constraints.list_200)
        logger.info('404 pages: %s' % constraints.list_404)
        for page in tqdm(constraints.list_200):
            handle_single_page(page)
        for page in tqdm(constraints.list_404):
            single_page_saver.createSingleFile(page, None)
    else:
        for page in range(end_page, start_page - 1, -1):
            handle_single_page(page)


def handle_single_page(page):
    info = single_page_crawler_by_selenium.crawl_infos_by_selenium(page)
    if info:
        single_page_saver.save_by_page(page, info)


def write_too_long_command_2_file():
    urls = constraints.command_too_long_urls
    if len(urls) > 0:
        with open(too_long_urls_file_path, 'w', encoding='utf8') as f:
            f.write(json.dumps(urls, indent=4, ensure_ascii=False))
            f.flush()
            f.close()

def launch():
    start = time.time()
    logger.info('========== Main thread : %s ==========' % (
        'on ,thread num: %d' % constraints.max_size_in_main_threadpool if constraints.switch_on_main_thread else 'off'))
    logger.info('========== Proxy : %s ==========' % ('on' if constraints.switch_on_proxy else 'off'))
    try:
        crawl1()
    finally:
        end = time.time()
        logger.info('200 pages: %s' % constraints.list_200)
        logger.info('others pages: %s' % constraints.list_others)
        logger.info('Timeout pages: %s' % constraints.list_timeout)
        logger.info('                  Execute Result                   ')
        logger.info('---------------------------------------------------')
        logger.info('     act\t\tbg_images\t  images\t  videos')
        logger.info('---------------------------------------------------')
        logger.info('  download\t\t\t%d\t\t\t%d\t\t\t %d' % (
            constraints.download_bg_image_count, constraints.download_image_count, constraints.download_video_count))
        logger.info('    skip\t\t\t%d\t\t\t%d\t\t\t %d' % (
            constraints.skip_download_bg_image_count, constraints.skip_download_image_count,
            constraints.skip_download_video_count))
        logger.info('download images pages are %s' % constraints.pages_of_download_images)
        logger.info('download videos pages are %s' % constraints.pages_of_download_videos)

        logger.info('too long urls num is %d' % len(constraints.command_too_long_urls))
        logger.info('Cost time %f seconds.' % (end - start))

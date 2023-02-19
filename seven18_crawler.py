# -*- coding:utf-8 -*-
# self is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import os.path
import pathlib
import time
from concurrent.futures import FIRST_COMPLETED, wait, ALL_COMPLETED

import LoggerFactory
import constraints
import page_config
import single_page_crawler_by_selenium
import single_page_saver
from t.BoundedThreadPoolExecutor import BoundedThreadPoolExecutor
from util import common_util

logger = LoggerFactory.getLogger(__name__)

time_stamp = time.strftime('%Y-%m-%d %H%M%S', time.localtime())
error_log_folder = os.path.join(os.getcwd(), 'error_log')
pathlib.Path(error_log_folder).mkdir(parents=True, exist_ok=True)

error_video_page_path = os.path.join(error_log_folder, 'error_video_page_%s.txt' % time_stamp)

error_img_page_path = os.path.join(error_log_folder, 'error_img_page_%s.txt' % time_stamp)


class Seven18Crawler_multithread():

    def crawl(self):

        start_page = page_config.start_page
        end_page = page_config.end_page
        if start_page > end_page:
            _ = start_page
            start_page = end_page
            end_page = _

        loop_size = 100
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

    def crawl1(self):

        start_page = page_config.start_page
        end_page = page_config.end_page
        if start_page > end_page:
            _ = start_page
            start_page = end_page
            end_page = _

        if constraints.switch_on_main_thread:
            with BoundedThreadPoolExecutor(max_workers=constraints.max_size_in_main_threadpool) as t:
                all_tasks = [t.submit(self.handle_single_page, page) for page in
                             range(end_page, start_page - 1, -1)]
                wait(all_tasks, return_when=ALL_COMPLETED)

        else:
            for page in range(end_page, start_page - 1, -1):
                self.handle_single_page(page)

    def handle_single_page(self, page):
        # url = common_util.get_page_url(page)
        info = single_page_crawler_by_selenium.crawl_infos_by_selenium(page)
        single_page_saver.save_by_page(page, info)


if __name__ == '__main__':
    start = time.time()
    logger.info('App launched...')
    try:
        Seven18Crawler_multithread().crawl1()
    finally:
        end = time.time()
        logger.info('Download videos times: %d' % constraints.download_video_count)
        logger.info('Download images times: %d' % constraints.download_image_count)
        logger.info('Cost time %f seconds.' % (end - start))
        logger.info('Closing app...')

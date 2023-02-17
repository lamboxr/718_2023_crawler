# -*- coding:utf-8 -*-
import os
import pathlib
import shutil
from concurrent.futures import wait, ALL_COMPLETED
from time import sleep

import requests
from Crypto.Cipher import AES

import LoggerFactory
# 获取logger实例，如果参数为空则返回root logger
import constraints
from code_enum import DownloadCode
from exception.M3U8Exception import NotM3U8Exception, M3U8MergeException, M3U8ParseException, M3U8DownloadException
from t.BoundedThreadPoolExecutor import BoundedThreadPoolExecutor
from util import net_util

logger = LoggerFactory.getLogger(__name__)


def download(m3u8_url, fragments_cache_dir):
    try:
        # fragments_cache_dir, fragments_folder_name = init_cache_dir(fragments_folder_name)
        pathlib.Path(fragments_cache_dir).mkdir(parents=True, exist_ok=True)
        logger.info('Downloading cache files to folder "%s"...' % fragments_cache_dir)

        # 获取第一层M3U8文件内容
        resp = net_util.request(m3u8_url)
        if resp.status_code == 200:
            all_content = resp.text
            if "#EXTM3U" not in all_content:
                raise NotM3U8Exception("Url '%s' is not right M3U8 format." % m3u8_url)
            # 第一层
            file_lines, m3u8_url = handle_level_1(all_content, m3u8_url)

            # 第二层
            total_count = calc_fragments_num(file_lines, m3u8_url)
            # 碎片索引号pattern
            idxWidth = len(str(total_count))
            fragment_name_pattern = '%0' + str(idxWidth) + 'd'

            unknow, key, fragments_info = parse_all_fragments(m3u8_url, file_lines, fragment_name_pattern)
            if unknow:
                raise M3U8DownloadException("Can not parse and download the specific m3u8 url: %s" % m3u8_url)
            else:
                if constraints.switch_on_video_thread:
                    logger.info("Downloading fragments of %s with multithread..." % m3u8_url)
                    with BoundedThreadPoolExecutor(max_workers=constraints.max_fragment_size_in_threadpool) as t:
                        all_tasks = [t.submit(lambda p: download_fragment_ts(*p),
                                              [fragments_cache_dir, key, fragment_url, fragment_file_name,
                                               total_count]) for fragment_file_name, fragment_url in
                                     fragments_info.items()]
                        wait(all_tasks, return_when=ALL_COMPLETED)
                else:
                    logger.info("Downloading fragments of %s with single thread..." % m3u8_url)
                    for fragment_file_name, fragment_url in fragments_info.items():
                        download_fragment_ts(fragments_cache_dir, key, fragment_url, fragment_file_name, total_count)
                logger.info("Download completely: %s" % m3u8_url)

            output_file = merge_file(fragments_cache_dir, total_count)
            delete_ts(fragments_cache_dir)
            if not os.path.exists(output_file):
                raise M3U8MergeException("Merge error: '%s' to '%s'." % (m3u8_url, fragments_cache_dir))
            return DownloadCode._200, output_file
        else:
            return DownloadCode._404, None
    except NotM3U8Exception as e:
        logger.error(e)
        # logger.error("Exception: Download error: '%s' to '%s'." % (m3u8_url, fragments_folder_path))
        return DownloadCode._NOT_M3U8, None
    except M3U8ParseException as e:
        logger.error(e)
        return DownloadCode._PARSE_ERROR, None
        # logger.error("Exception: Download error: '%s' to '%s'." % (m3u8_url, fragments_folder_path))
    except M3U8DownloadException as e:
        logger.error(e)
        return DownloadCode._DOWNLOAD_ERROR, None
        # logger.error("Exception: Download error: '%s' to '%s'." % (m3u8_url, fragments_folder_path))
    except M3U8MergeException as e:
        logger.error(e)
        return DownloadCode._MERGE_ERROR, None
    except BaseException as e:
        logger.error(e)
        # logger.error("Exception: Download error: '%s' to '%s'." % (m3u8_url, fragments_folder_path))
        return DownloadCode._UNKNOWN, None


def calc_fragments_num(file_lines, m3u8_url):
    total_count = 0
    for line_idx, line in enumerate(file_lines):
        if "EXTINF" in line:
            total_count += 1
    logger.info('Page has %s fragments videos total: %d' % (m3u8_url, total_count))
    return total_count


def parse_all_fragments(m3u8_url, file_lines, name_pattern):
    logger.info('Parsing fragments in %s ' % m3u8_url)
    unknow = True
    key = ''
    fragments_info = {}
    fragment_idx = 0
    for line_idx, line in enumerate(file_lines):
        key = parse_key(key, line, m3u8_url)
        if "EXTINF" in line:
            unknow = False
            # 拼出ts片段的URL
            next_line = file_lines[line_idx + 1]
            fragment_url = next_line if next_line.startswith('http:') or next_line.startswith('https:') else \
                m3u8_url.rsplit("/", 1)[0] + "/" + next_line
            fragment_file_name = str(fragment_idx)
            fragments_info[fragment_file_name] = fragment_url
            fragment_idx += 1
    return unknow, key, fragments_info


def download_fragment_ts(fragments_folder_path, key, fragment_url, fragment_file_name, total_count):
    logger.info("Downloading %d/%d file into dir %s: '%s ..." % (
        (int(fragment_file_name) + 1), total_count, fragments_folder_path, fragment_url))
    resp = net_util.request(fragment_url)
    if resp.status_code == 200:
        # AES 解密
        if len(key):

            cryptor = AES.new(key, AES.MODE_CBC, key)
            fragments_file = os.path.join(fragments_folder_path, fragment_file_name)
            with open(fragments_file, 'ab') as f:
                f.write(cryptor.decrypt(resp.content))
                f.flush()
                f.close()
        else:
            fragments_file = os.path.join(fragments_folder_path, fragment_file_name)
            with open(fragments_file, 'ab') as f:
                f.write(resp.content)
                f.flush()
                f.close()
        logger.info("Download completely: %d/%d file into dir %s: '%s ..." % (
            (int(fragment_file_name) + 1), total_count, fragments_folder_path, fragment_url))
    else:
        raise M3U8DownloadException("Download error: '%s' to '%s'." % (fragment_url, fragments_folder_path))


def parse_key(key, line, m3u8_url):
    if "#EXT-X-KEY" in line:
        logger.info('parsing key in %s' % m3u8_url)
        method_pos = line.find("METHOD")
        comma_pos = line.find(",")
        method = line[method_pos:comma_pos].split('=')[1]
        logger.debug("Decode Method：%s", method)

        uri_pos = line.find("URI")
        quotation_mark_pos = line.rfind('"')
        key_path = line[uri_pos:quotation_mark_pos].split('"')[1]

        # 拼出key解密密钥URL
        key_url = m3u8_url.rsplit("/", 1)[0] + "/" + key_path
        res = requests.get(key_url)
        if res.status_code == 200:
            key = res.content
            logger.debug("key：%s", key)
        else:
            if (not m3u8_url.endswith('m3u8')) and 'v=' in m3u8_url:
                key_url = m3u8_url.split('//', 1)[0] + '//' + m3u8_url.split('//', 1)[1].split('/', 1)[
                    0] + '/' + key_path
                res = requests.get(key_url)
                if res.status_code == 200:
                    key = res.content
                logger.debug("key：%s", key)
    return key


def handle_level_1(all_content, m3u8_url):
    # 第一层
    if "EXT-X-STREAM-INF" in all_content:
        file_lines = all_content.split("\n")
        for line in file_lines:
            if '.m3u8' in line:
                # 拼出第二层m3u8的URL
                m3u8_url = m3u8_url.rsplit("/", 1)[0] + "/" + line
                all_content = requests.get(m3u8_url).text
    file_lines = all_content.split("\n")
    return file_lines, m3u8_url


def merge_file(fragments_folder_path, total_count):
    fragments_list = os.listdir(fragments_folder_path)
    if len(fragments_list) < total_count:
        return None

    fragments_num_list = []
    for filename in os.listdir(fragments_folder_path):
        fragments_num_list.append(int(filename))
    fragments_num_list.sort()
    fragments_list = [str(num) for num in fragments_num_list]
    input_file = '|'.join(fragments_list)
    output_file = fragments_folder_path + '.mp4'
    if os.path.exists(output_file):
        os.remove(output_file)
    command = 'cd {} && ffmpeg -i "concat:{}" -acodec copy -vcodec copy -absf aac_adtstoasc {}'.format(
        fragments_folder_path, input_file, output_file)
    logger.info('executing command to merge video %s: %s' % (output_file, command))
    os.system(command)
    logger.info('Finish merging fragments to file: %s' % output_file)
    return output_file


def delete_ts(path):
    try:
        logger.info('Deleting ts files in %s ...' % path)
        shutil.rmtree(path)
        logger.info('ts files are deleted: %s' % path)
    except:
        logger.error('ts文件删除失败, dir: %s' % path)
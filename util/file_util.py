# -*- coding: utf-8 -*-
import json
import os.path
import pathlib
import shutil

from factory import LoggerFactory

logger = LoggerFactory.getLogger(__name__)


def readLines(path):
    if not os.path.isfile(path):
        return []
    file = open(path, "r", encoding="UTF-8")
    lines = file.readlines()
    newList = []
    for line in lines:
        newList.append(line.rstrip("\n"))
    file.close()
    return newList


# 删除文件夹下面的所有文件(只删除文件,不删除文件夹)
# python删除文件的方法 os.remove(path)path指的是文件的绝对路径,如：
def setDir(filepath):
    '''
    param filepath:需要创建的文件夹路径
    '''
    if os.path.isfile(filepath):
        return
    pathlib.Path(filepath).mkdir(parents=True, exist_ok=True)
    for i in os.listdir(filepath):
        f = os.path.join(filepath, i)
        if os.path.isfile(f):
            os.remove(f)
        else:
            shutil.rmtree(f)


# 删除文件夹下面的所有文件(只删除文件,不删除文件夹)
# python删除文件的方法 os.remove(path)path指的是文件的绝对路径,如：
def resetDir(dir_path):
    '''
    param filepath:需要创建的文件夹路径
    '''
    if os.path.isfile(dir_path):
        return
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.mkdir(dir_path)


def read_file(path):
    if not os.path.exists(path) or os.path.isdir(path):
        return {}
    file = open(path, mode='r', encoding='utf-8')
    try:
        return file.read().rstrip()
    except Exception as e:
        logger.error(e)
        return {}
    finally:
        file.close()


def read_file_as_json(path):
    try:
        return json.loads(read_file(path))
    except Exception as e:
        logger.error(e)
        return json.loads("{}")

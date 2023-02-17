# -*- coding:utf-8 -*-
import os
import pathlib

import LoggerFactory
import constraints

output = constraints.out_put

logger = LoggerFactory.getLogger(__name__)


def clear_single_file():
    for i in [i for i in os.listdir(output) if i.endswith('.txt') and (i.startswith('0') or i.startswith('1'))]:
        page = i[0:5]
        for j in [j for j in os.listdir(output) if j.startswith(page) and os.path.isdir(os.path.join(output, j))]:
            f = os.path.join(output, j)
            if len([k for k in os.listdir(f) if
                    k.endswith('.mp4') or k.endswith('.jpg') or k.endswith('.png') or k.endswith('.gif')]):
                logger.info('Removing file %s: ' % i)
                os.remove(os.path.join(output, i))


def find_duplicate():
    for i in range(13293):
        if len([f for f in os.listdir(output) if f.endswith('.txt') and f.startswith('%05d' % i)]) > 1:
            logger.info('Page %05d has duplicate files.' % i)


def find_no_media_and_move():
    for f in [f for f in os.listdir(output) if
              os.path.isdir(os.path.join(output, f)) and (f.startswith('0') or f.startswith('1'))]:
        list = os.listdir(os.path.join(output, f))
        if len(list) == 1 and list[0].endswith('.txt'):
            src = os.path.join(output, f, list[0])
            tgt = os.path.join(output, f + '.txt')
            logger.info('moving %s to %s ' % (src, tgt))
            os.rename(src, tgt)
            os.removedirs(os.path.join(output, f))


def move_txt():
    txt_dir = os.path.join(output, 'txt')
    pathlib.Path(txt_dir).mkdir(parents=True, exist_ok=True)
    for i in [i for i in os.listdir(output) if i.endswith('.txt')]:
        src = os.path.join(output, i)
        tgt = os.path.join(txt_dir, i)
        logger.info('moving %s to %s ' % (src, tgt))
        os.rename(src, tgt)


def findsubdir():
    for f in [f for f in os.listdir(output) if not f.endswith('.txt')]:
        if len([j for j in os.listdir(os.path.join(output, f)) if os.path.isdir(os.path.join(output, f, j))]) > 0:
            logger.info('Folder %s has subdir' % f)


def findempty():
    for f in [f for f in os.listdir(output) if
              not f.endswith('.txt') and len(
                  [j for j in os.listdir(os.path.join(output, f)) if j.endswith('.jpg') or j.endswith('.mp4')]) == 0]:
        logger.info('Folder %s is empty' % f)


def move_pic():
    pic_dir = os.path.join(output, 'pic')
    pathlib.Path(pic_dir).mkdir(parents=True, exist_ok=True)
    for f in [f for f in os.listdir(output) if
              not (f == 'pic') and os.path.isdir(os.path.join(output, f)) and len(
                  [j for j in os.listdir(os.path.join(output, f)) if
                   not (j.endswith('.txt') or j.endswith('.mp4'))]) > 0
              and len(
                  [j for j in os.listdir(os.path.join(output, f)) if j.endswith('.mp4')]) == 0]:
        logger.info('Moving %s to %s' % (os.path.join(output, f), os.path.join(pic_dir, f)))
        os.rename(os.path.join(output, f), os.path.join(pic_dir, f))


def handle_idx():
    for f in [f for f in os.listdir(constraints.out_put) if not f == 'txt']:
        jpgs = [j for j in os.listdir(os.path.join(constraints.out_put, f)) if
                os.path.isdir(os.path.join(constraints.out_put, f)) and (j.endswith('.jpg') or j.endswith('.png'))]
        if len(jpgs) > 1:
            for j in jpgs:
                if not j[-4 - int(len(str(len(jpgs)))) - 1] == '_':
                    l = list(j)
                    l.insert(-4 - int(len(str(len(jpgs)))), '_')
                    new_j = ''.join(l)
                    os.rename(os.path.join(constraints.out_put, f, j), os.path.join(constraints.out_put, f, new_j))
                    logger.info('rename %s to %s ' % (j, new_j))


def move_single_file():
    txt = os.path.join(output, 'txt')
    pathlib.Path(os.path.join(output, '1')).mkdir(parents=True, exist_ok=True)
    for i in [i for i in os.listdir(txt) if '_' in i]:
        logger.info("Moving %s to %s" % (os.path.join(txt, i), os.path.join(output, '1', i)))
        os.renames(os.path.join(txt, i), os.path.join(output, '1', i))


def find2video():
    for i in [i for i in os.listdir(output) if os.path.isdir(os.path.join(output, i)) and len(
            [j for j in os.listdir(os.path.join(output, i)) if '2.mp4' in j]) > 0]:
        print(i)


def checksingle():
    idx = 0
    for i in [i.replace('.txt', '') for i in os.listdir(os.path.join(output, '1'))]:
        if os.path.exists(os.path.join(output, i)) and os.path.isdir(os.path.join(output, i)):

            if len([j for j in os.listdir(os.path.join(output, i)) if j.endswith('.mp4')]):
                idx += 1
                logger.info("%03d: Delete %s" % (idx, os.path.join(output, '1', i + '.txt')))
                os.remove(os.path.join(output, '1', i + '.txt'))


if __name__ == '__main__':
    clear_single_file()
    find_no_media_and_move()
    move_txt()
    move_pic()

    # find2video()
    # checksingle()
    pass

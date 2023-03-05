# -*- coding:utf-8 -*-
from config import constraints


def get_page_url(page):
    return constraints.base_url_pattern % page

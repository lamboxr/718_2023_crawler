# -*- coding:utf-8 -*-
import constraints


def get_page_url(page):
    return constraints.base_url_pattern % page

import time

from config import constraints
from factory import LoggerFactory
from util import common_util, net_util

logger = LoggerFactory.getLogger(__name__)


def collect_200(start_page, end_page):
    for page in range(start_page, end_page + 1):
        collect_200_by_page(page)


def collect_200_by_page(page):
    # time.sleep(1)
    url = common_util.get_page_url(page)
    resp = net_util.request(url)
    status_code = resp.status_code

    if status_code == 200:
        if constraints.no_content_str in str(resp.content) or constraints.no_content_str_eng in str(resp.content):
            constraints.list_404.append(page)
        else:
            logger.info("Checking %s: %s ..." % (str(status_code), url))
            constraints.list_200.append(page)
    elif status_code == 404:
        constraints.list_404.append(page)
    else:
        constraints.list_others.append(page) 

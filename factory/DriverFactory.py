from factory import LoggerFactory
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service

from config import constraints

logger = LoggerFactory.getLogger(__name__)


def getEdgeDriver(timeout):
    s = Service(constraints.edge_driver_path)
    edge_options = Options()
    edge_options.add_argument(f'user-agent={UserAgent().random}')
    # logger.info('Edge user-agent: %s' % edge_options)
    edge = webdriver.Edge(service=s, options=edge_options)
    edge.set_window_size(100, 50)
    edge.minimize_window()
    edge.set_page_load_timeout(timeout)
    edge.set_script_timeout(timeout)
    logger.info("navigator.userAgent: %s" % edge.execute_script("return navigator.userAgent"))
    return edge

from service.crawler import seven18_crawler
from factory import LoggerFactory

logger = LoggerFactory.getLogger(__name__)

if __name__ == '__main__':
    logger.info('App launched...')
    seven18_crawler.launch()
    logger.info('App closed...')

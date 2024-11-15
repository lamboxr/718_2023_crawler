from enum import Enum


class DownloadCode(Enum):
    _200 = "200"
    _404 = "404"
    _NOT_M3U8 = "3"
    _PARSE_ERROR = "4"
    _DOWNLOAD_ERROR = "5"
    _MERGE_ERROR = "6"
    _UNKNOWN = "7"
    _COMMAND_TOO_LONG = "8"


class AttributeCode(Enum):
    PAGE = 'PAGE'
    URL = 'URL'
    STATUS_CODE = 'STATUS_CODE'
    TITLE = 'TITLE'
    DATE = 'DATE'
    LINKS = 'LINKS'
    CONTENT = 'CONTENT'
    VIDEO_URLS = 'VIDEO_URLS'
    IMAGE_URLS = 'IMAGE_URLS'
    IMAGE_B64S = 'IMAGE_B64S'
    IMAGE_BACKGROUND_B64 = 'IMAGE_BACKGROUND_B64'

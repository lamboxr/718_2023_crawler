# -*- coding:utf-8 -*-
download_video_count = 0
download_image_count = 0
download_bg_image_count = 0
skip_download_video_count = 0
skip_download_image_count = 0
skip_download_bg_image_count = 0
pages_of_download_images = []
pages_of_download_videos = []

cmd_max_char_num = 8191
command_too_long_urls = {}

switch_on_proxy = False

pre_collect_on = False

no_content_str = "\\xe6\\xb2\\xa1\\xe6\\x9c\\x89\\xe6\\x89\\xbe\\xe5\\x88\\xb0\\xe5\\x86\\x85\\xe5\\xae\\xb9"
no_content_str_eng = "No Content Here"

proxies = {
    'http': "http://127.0.0.1:7890",
    'https': "http://127.0.0.1:7890"
}
# proxy_host = "127.0.0.1"
proxy_host = "47.97.1.34"
proxy_port = 5010
edge_driver_path = '../drivers/edgedriver_win64/116.0.1938.54/msedgedriver.exe'
# driver download url
# https://www.selenium.dev/zh-cn/documentation/webdriver/getting_started/install_drivers/


domain = 'https://www.ac38yule.com/'
# base_url_pattern = "https://www.u718.sx/archives/%d"
base_url_pattern = domain+"%d"

# domain = 'https://zztt46.com'
# base_url_pattern = "https://zztt46.com/archives/%d.html"

year = 2023

timeout = 60
out_put = 'D:\\output\\718\\decrypted'
cache_root = 'D:\\_'

list_200 = []
list_404 = []
list_others = []
list_timeout = []
list_200_all = {}
list_400_all = {}
list_others_all = {}

img_num_in_page = {}
error_video_page = {}
# {
#     "1": {
#         'code': 404,
#         'cpt_num': 123,
#         'folder_path': ''}
# }

switch_on_save_video = True
switch_on_save_image = True

clean_image_then_save = True
# clean_video_then_save = True

check_200_thread_num = 1
loop_size = 20

switch_on_main_thread = False
# switch_on_main_thread = True
max_size_in_main_threadpool = 5

switch_on_video_thread = True
max_fragment_size_in_threadpool = 16

switch_on_img_thread = True
max_image_size_in_threadpool = 8



# -*- coding:utf-8 -*-
download_video_count = 0
switch_on_proxy = False

proxies ={
    'http': "http://127.0.0.1:7890",
    'https': "http://127.0.0.1:7890"
}
# proxy_host = "127.0.0.1"
proxy_host = "47.97.1.34"
proxy_port = 5010
webbrowser_driver_path = 'drivers/edgedriver_win64/103.0.1264.71/msedgedriver.exe'
# driver download url
# https://www.selenium.dev/zh-cn/documentation/webdriver/getting_started/install_drivers/
domain = 'https://www.u718.sx'
base_url_pattern = "https://www.u718.sx/archives/%d"
year = 2023

timeout = 30
out_put = 'D:\\output\\718\\xxx'
cache_root = 'D:\\_'

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

switch_on_main_thread = False
# switch_on_main_thread = True
max_size_in_main_threadpool = 4

switch_on_video_thread = True
max_fragment_size_in_threadpool = 8

switch_on_img_thread = True
max_image_size_in_threadpool = 8

# start_page = 6253
# end_page = 6378
start_page = 4960
end_page = 4960


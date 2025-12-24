# pip install selenium -i https://mirrors.aliyun.com
# 下载驱动：
# Chrome浏览器驱动地址：https://googlechromelabs.github.io/chrome-for-testing/
# 注意区分系统的版本以及浏览器版本：chromedriver.exe

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
# executable_path指定Driver驱动所在的地址
# ChromeService(executable_path='../../driver/chromedriver.exe') # win
my_chrome_service = ChromeService(executable_path='../../driver/chromedriver') # mac
# 进行配置
options = webdriver.ChromeOptions()
options.add_experimental_option('detach', True) # 请求完后不自动关闭浏览器
# driver是整个浏览器的agent
driver = webdriver.Chrome(service=my_chrome_service,options=options)
# 请求一个页面，不用接收，代码执行后会打开浏览器并请求该地址
driver.get("https://www.baidu.com") # 默认浏览器请求完成后会自动关闭
# 定位元素
search_input_text = driver.find_element(By.ID, 'chat-textarea') # 定位搜索框
search_input_text.send_keys("今日热点新闻") # 输入文字
# 找到搜索按钮
search_button = driver.find_element(By.ID, 'chat-submit-button')
search_button.click() # 点击按钮

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By

my_chrome_service = ChromeService(executable_path='../../driver/chromedriver')
options = webdriver.ChromeOptions()
options.add_experimental_option('detach', True)
driver = webdriver.Chrome(service=my_chrome_service,options=options)

driver.get("https://101.qq.com/#/hero")
# time.sleep(5) # 等待页面渲染完成，不管1s就渲染完了，还是4s就渲染完成，都要强制等5s，会影响性能
# 在规定时间内等待某个特定的元素出现，如果超时了则会出现异常
try:
    # 只要在10s内的任意时刻页面渲染完成，则可以继续执行后续代码，性能会更优
    ul = WebDriverWait(driver, 10).until(lambda d: d.find_element(By.XPATH, "//ul[@class='hero-list']"))
    for p in ul.find_elements(By.XPATH, ".//p[@class='hero-name']"):
        print(p.text)
except Exception as e:
    print(e)

# 手动退出
# driver.quit()
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import ddddocr

class WuhuBiddingPDFDownloader:
    def __init__(self, download_dir=None):
        """
        初始化下载器
        :param download_dir: PDF下载目录，默认当前目录下的downloads文件夹
        """
        self.download_dir = download_dir or os.path.join(os.getcwd(), "downloads")
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        # 初始化Chrome选项
        self.chrome_options = Options()
        self.chrome_options.add_experimental_option('detach', True)
        # self.chrome_options.add_argument('--headless')  # 无头模式
        # self.chrome_options.add_argument('--no-sandbox')
        # self.chrome_options.add_argument('--disable-dev-shm-usage')
        # self.chrome_options.add_argument('--disable-gpu')

        # 设置下载路径
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "safebrowsing.enabled": True
        }
        self.chrome_options.add_experimental_option("prefs", prefs)

        # 初始化验证码识别器
        self.ocr = ddddocr.DdddOcr(show_ad=False)

        # 目标URL
        self.target_url = "https://whsggzy.wuhu.gov.cn/whggzyjy/005/005001/005001001/20240906/e5bfcdcc-aff8-47f9-b331-df8641b6ca40.html"

    def setup_driver(self):
        """设置并返回WebDriver"""
        try:
            service = ChromeService(executable_path='../driver/chromedriver')
            driver = webdriver.Chrome(service=service, options=self.chrome_options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            print(f"初始化WebDriver失败: {e}")
            return None

    def find_and_click_pdf_link(self, driver):
        """
        查找并点击PDF链接
        :param driver: WebDriver实例
        :return: 是否成功找到并点击链接
        """
        try:
            # 等待页面加载完成
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//body"))
            )

            print("正在查找PDF链接...")

            # 使用提供的XPath查找链接
            pdf_link = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@title='招标文件正文.pdf']"))
            )

            # 获取链接的原始url（用于调试）
            pdf_url = pdf_link.get_attribute("url")
            print(f"找到PDF链接: {pdf_url}")

            # 点击链接（会触发验证码弹窗）
            pdf_link.click()
            print("已点击PDF链接，等待验证码弹窗...")

            return True

        except Exception as e:
            print(f"查找或点击PDF链接失败: {e}")
            # 尝试备用方法：查找包含"招标文件正文.pdf"文本的链接
            try:
                pdf_link = driver.find_element(By.PARTIAL_LINK_TEXT, "招标文件正文.pdf")
                pdf_link.click()
                print("使用备用方法找到并点击了PDF链接")
                return True
            except:
                print("备用方法也失败")
                return False

    def handle_verification_popup(self, driver):
        """
        处理验证码弹窗
        :param driver: WebDriver实例
        :return: 是否成功处理验证码
        """
        try:
            # 等待弹窗出现（可能需要切换窗口或iframe）
            time.sleep(2)  # 等待弹窗加载

            print("正在处理iframe内的验证码...")

            # 等待iframe出现
            print("等待iframe加载...")
            iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "layui-layer-iframe100001"))
            )

            # 切换到iframe
            driver.switch_to.frame(iframe)
            print("已切换到iframe内部")

            # 等待验证码图片加载
            print("等待验证码图片加载...")
            captcha_img = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "imgVerify"))
            )

            # 获取验证码图片
            captcha_src = captcha_img.get_attribute("src")
            print(f"验证码图片地址: {captcha_src}")

            # 保存验证码图片到本地（用于调试）
            captcha_path = os.path.join(self.download_dir, "captcha.png")

            # 方法1：如果验证码是base64编码
            if captcha_src.startswith("data:image"):
                import base64
                # 提取base64数据
                base64_data = captcha_src.split(",")[1]
                img_data = base64.b64decode(base64_data)
                with open(captcha_path, "wb") as f:
                    f.write(img_data)
            else:
                # 方法2：如果是URL，下载图片
                response = requests.get(captcha_src, stream=True)
                with open(captcha_path, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)

            print(f"验证码图片已保存到: {captcha_path}")

            # 使用ddddocr识别验证码
            with open(captcha_path, "rb") as f:
                image_bytes = f.read()

            captcha_text = self.ocr.classification(image_bytes)
            print(f"识别到的验证码: {captcha_text}")

            # 查找验证码输入框
            captcha_input = driver.find_element(By.ID, 'yzm')

            if not captcha_input:
                print("未找到验证码输入框")
                return False

            # 输入验证码
            captcha_input.clear()
            captcha_input.send_keys(captcha_text)
            print("已输入验证码")

            # 先切回默认的页面，相当于从iframe跳出来
            driver.switch_to.default_content()
            # 查找确认按钮
            confirm_button = driver.find_element(By.XPATH, "//a[@class='layui-layer-btn0']")

            if not confirm_button:
                print("未找到确认按钮")
                return False

            # 点击确认按钮
            confirm_button.click()
            print("已点击确认按钮，开始下载...")

            # 等待下载开始
            time.sleep(5)

            return True

        except Exception as e:
            print(f"处理验证码弹窗时出错: {e}")
            # 保存当前页面截图以便调试
            driver.save_screenshot(os.path.join(self.download_dir, "error_screenshot.png"))
            return False

    def download_pdf(self):
        """
        主下载函数
        :return: 下载的PDF文件路径列表
        """
        driver = None
        try:
            print("正在启动浏览器...")
            driver = self.setup_driver()
            if not driver:
                return []

            print(f"正在访问目标页面: {self.target_url}")
            driver.get(self.target_url)

            # 查找并点击PDF链接
            if not self.find_and_click_pdf_link(driver):
                print("无法找到或点击PDF链接")
                return []

            # 处理验证码弹窗
            if not self.handle_verification_popup(driver):
                print("验证码处理失败")
                return []

            # 等待下载完成（根据文件大小调整等待时间）
            print("等待文件下载...")
            time.sleep(10)

            # 检查下载目录中的PDF文件
            pdf_files = []
            for file in os.listdir(self.download_dir):
                if file.endswith(".pdf"):
                    pdf_files.append(os.path.join(self.download_dir, file))

            if pdf_files:
                print(f"下载完成！找到 {len(pdf_files)} 个PDF文件:")
                for pdf in pdf_files:
                    print(f"  - {pdf}")
            else:
                print("未找到下载的PDF文件")

                # 检查是否有临时文件
                temp_files = [f for f in os.listdir(self.download_dir) if f.endswith(".crdownload")]
                if temp_files:
                    print(f"发现 {len(temp_files)} 个正在下载的临时文件，请稍等...")

            return pdf_files

        except Exception as e:
            print(f"下载过程中出错: {e}")
            return []
        finally:
            if driver:
                print("关闭浏览器...")
                # driver.quit()

    def check_downloaded_files(self):
        """检查已下载的文件"""
        pdf_files = []
        for file in os.listdir(self.download_dir):
            if file.endswith(".pdf"):
                file_path = os.path.join(self.download_dir, file)
                file_size = os.path.getsize(file_path)
                pdf_files.append({
                    "name": file,
                    "path": file_path,
                    "size": file_size
                })

        return pdf_files


def main():
    """主函数"""
    print("芜湖公共资源交易中心PDF下载程序")
    print("=" * 50)

    # 创建下载器实例
    downloader = WuhuBiddingPDFDownloader()

    print(f"下载目录: {downloader.download_dir}")
    print(f"目标URL: {downloader.target_url}")
    print("-" * 50)

    # 开始下载
    downloaded_files = downloader.download_pdf()

    print("-" * 50)
    if downloaded_files:
        print("下载任务完成！")
    else:
        print("下载未完成，可能需要手动处理或调整代码。")

        # 提供调试建议
        print("\n调试建议:")
        print("1. 暂时禁用无头模式以便观察:")
        print("   chrome_options.add_argument('--headless')  # 注释掉这行")
        print("2. 增加等待时间")
        print("3. 检查验证码弹窗的实际HTML结构")
        print("4. 手动访问页面，查看网络请求和元素结构")


if __name__ == "__main__":
    main()
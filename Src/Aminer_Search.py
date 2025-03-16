from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import time

class LoginManager:
    def __init__(self, driver):
        self.driver = driver
        self.cookies_file = "config/aminer_cookies.json"
        
    def manual_login(self):
        """处理扫码登录流程"""
        print("请打开浏览器扫码登录，登录完成后返回控制台按回车继续...")
        self.driver.get("https://www.aminer.cn/login")
        input("登录完成后按回车键继续执行爬取...")
        self._save_cookies()

    def check_login(self):
        """检查是否已登录"""
        try:
            # 等待页面完全加载
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # 查找退出登录按钮
            logout_elements = self.driver.find_elements(By.XPATH, "//span[contains(text(), '退出登录')]")
            return len(logout_elements) > 0
        except:
            return False

    def _save_cookies(self):
        """保存登录cookies"""
        cookies = self.driver.get_cookies()
        with open(self.cookies_file, 'w') as f:
            json.dump(cookies, f)

with open('config/org_mapping.json', 'r', encoding='utf-8') as f:
    ORG_MAPPING = json.load(f)

def supplement_data(teacher_name, teacher_org):
    driver = webdriver.Chrome()
    
    try:
        # 先访问网站
        driver.get("https://www.aminer.cn")
        
        # 尝试加载已保存的cookies
        try:
            with open("config/aminer_cookies.json", "r") as f:
                cookies = json.load(f)
                for cookie in cookies:
                    driver.add_cookie(cookie)
            # 刷新页面使cookies生效
            driver.refresh()
        except:
            print("未找到cookies或cookies加载失败")
        
        # 创建登录管理器并检查登录状态
        login_manager = LoginManager(driver)
        if not login_manager.check_login():
            print("未登录状态，需要手动登录")
            login_manager.manual_login()
        else:
            print("已检测到登录状态，无需重新登录")
            
        print(f"开始搜索 {teacher_name}...")
        driver.get(f"https://www.aminer.cn/search/person?q={teacher_name}")
        
        # 等待页面加载完成
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("页面加载完成")
        
        # 等待搜索结果出现
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".a-aminer-components-expert-c-person-item-personItem"))
            )
            print("搜索结果已加载")
        except TimeoutException:
            print("未找到搜索结果")
            return {}
        
        current_page = 1
        
        # 尝试获取实际的最大页码
        try:
            pagination_items = driver.find_elements(By.CSS_SELECTOR, ".ant-pagination-item")
            if pagination_items:
                max_pages = max([int(item.text) for item in pagination_items if item.text.isdigit()])
                print(f"检测到总共有 {max_pages} 页结果")
        except:
            print(f"无法确定总页数，将检查默认的 {max_pages} 页")
        
        first_result = None  # 保存第一个结果作为备选
        
        # 遍历所有页面
        while current_page <= max_pages:
            print(f"正在检查第 {current_page} 页")
            
            # 获取当前页的所有搜索结果项
            items = driver.find_elements(By.CSS_SELECTOR, ".a-aminer-components-expert-c-person-item-personItem")
            print(f"当前页找到 {len(items)} 个搜索结果")
            
            # 如果是第一页且有结果，保存第一个结果作为备选
            if current_page == 1 and items and first_result is None:
                try:
                    first_item = items[0]
                    name_elem = first_item.find_element(By.CSS_SELECTOR, ".profileName .name")
                    name = name_elem.text
                    link = first_item.find_element(By.CSS_SELECTOR, ".person_name a")
                    profile_url = link.get_attribute("href")
                    first_result = {
                        'name': name,
                        'url': profile_url
                    }
                except:
                    pass
            
            # 尝试查找匹配机构的结果
            for item in items:
                try:
                    # 获取姓名
                    name_elem = item.find_element(By.CSS_SELECTOR, ".profileName .name")
                    name = name_elem.text
                    
                    # 获取机构信息
                    org_elems = item.find_elements(By.CSS_SELECTOR, ".person_info_item")
                    for org_elem in org_elems:
                        if "lacale" in org_elem.get_attribute("innerHTML"):  # 检查是否是机构信息
                            org_text = org_elem.text
                            print(f"检查: {name}, 机构: {org_text}")
                            
                            # 检查是否匹配目标机构
                            for alias in ORG_MAPPING.get(teacher_org, []):
                                if alias in org_text:
                                    # 找到匹配的结果，获取链接
                                    link = item.find_element(By.CSS_SELECTOR, ".person_name a")
                                    profile_url = link.get_attribute("href")
                                    print(f"找到匹配的教师和机构: {name}, {alias}")
                                    return {
                                        'aminer_url': profile_url,
                                    }
                except Exception as e:
                    continue
            
            # 检查是否有下一页
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, ".ant-pagination-next:not(.ant-pagination-disabled)")
                current_page += 1
                
                # 点击下一页
                next_button.click()
                print("点击下一页按钮")
                
                # 等待页面加载
                time.sleep(2)  # 简单等待页面更新
                
                # 等待新页面的搜索结果加载
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".a-aminer-components-expert-c-person-item-personItem"))
                )
            except NoSuchElementException:
                print("没有更多页面")
                break
            except TimeoutException:
                print("下一页加载超时")
                break
        
        # 如果没有找到匹配机构的结果，返回第一个结果
        if first_result:
            print(f"未找到匹配机构的结果，返回第一个结果: {first_result['name']}")
            return {
                'aminer_url': first_result['url'],
            }
                
        return {}
    finally:
        driver.quit()

if __name__ == "__main__":
    teacher_name = input("请输入教师姓名（默认：陈海山）: ") or "陈海山"
    teacher_org = input("请输入教师单位（默认：南京信息工程大学）: ") or "南京信息工程大学"
    data = supplement_data(teacher_name, teacher_org)
    print(data)

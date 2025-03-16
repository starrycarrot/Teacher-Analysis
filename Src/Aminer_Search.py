from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json

with open('config/org_mapping.json', 'r', encoding='utf-8') as f:
    ORG_MAPPING = json.load(f)

def supplement_data(teacher_name = "陈海山", teacher_org = "南京信息工程大学"):
    driver = webdriver.Chrome()
    try:
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
        
        # 获取所有搜索结果项
        items = driver.find_elements(By.CSS_SELECTOR, ".a-aminer-components-expert-c-person-item-personItem")
        print(f"找到 {len(items)} 个搜索结果")
        
        # 首先尝试查找同时匹配姓名和机构的结果
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
        
        # 如果没有找到匹配机构的结果，返回第一个结果
        if items:
            try:
                first_item = items[0]
                name_elem = first_item.find_element(By.CSS_SELECTOR, ".profileName .name")
                name = name_elem.text
                link = first_item.find_element(By.CSS_SELECTOR, ".person_name a")
                profile_url = link.get_attribute("href")
                print(f"未找到匹配机构的结果，返回第一个结果: {name}")
                return {
                    'aminer_url': profile_url,
                }
            except:
                pass
                
        return {}
    finally:
        driver.quit()

if __name__ == "__main__":
    teacher_name = input("请输入教师姓名（默认：陈海山）: ") or "陈海山"
    teacher_org = input("请输入教师单位（默认：南京信息工程大学）: ") or "南京信息工程大学"
    data = supplement_data(teacher_name, teacher_org)
    print(data)

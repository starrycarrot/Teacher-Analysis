#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import time
import certifi
import logging
from playwright.sync_api import sync_playwright

# 配置证书环境变量
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

class LoginManager:
    """
    Aminer登录管理器
    功能：
    1. 处理扫码登录流程
    2. 检查是否已登录
    3. 保存登录cookies
    """
    def __init__(self, page, cookies_path="config/aminer_cookies.json"):
        self.page = page
        self.cookies_file = cookies_path
        os.makedirs(os.path.dirname(cookies_path), exist_ok=True)
        
    def manual_login(self):
        """处理扫码登录流程"""
        logging.info("请打开浏览器扫码登录，登录完成后返回控制台按回车继续...")
        self.page.goto("https://www.aminer.cn/login", wait_until="domcontentloaded")
        input("登录完成后按回车键继续执行爬取...")
        
        # 等待页面加载
        self.page.wait_for_load_state("domcontentloaded", timeout=10000)
        time.sleep(1)  # 减少等待时间
        
        # 保存登录状态
        if self.check_login():
            logging.info("登录成功，保存cookies...")
        else:
            logging.warning("未检测到成功登录，但仍保存当前状态")
        self._save_cookies()

    def check_login(self):
        """检查是否已登录"""
        try:
            # 使用更快的选择器
            logout_elements = self.page.locator("text=退出登录").count()
            return logout_elements > 0
        except Exception as e:
            logging.error(f"检查登录状态时出错: {e}")
            return False

    def _save_cookies(self):
        """保存登录cookies和浏览器状态"""
        try:
            self.page.context.storage_state(path=self.cookies_file)
            logging.info(f"已保存浏览器状态: {self.cookies_file}")
        except Exception as e:
            logging.error(f"保存cookies时出错: {e}")


def search_teacher(teacher_name, teacher_org, headless=False):
    """
    搜索教师信息的核心函数
    
    参数:
        teacher_name: 教师姓名
        teacher_org: 教师所属机构
        headless: 是否使用无头模式
        
    返回:
        str: 教师在Aminer的个人主页完整URL
    """
    cookies_path = "config/aminer_cookies.json"
    org_mapping_path = "config/org_mapping.json"
    
    # 加载机构映射
    try:
        with open(org_mapping_path, 'r', encoding='utf-8') as f:
            org_mapping = json.load(f)
    except Exception as e:
        logging.error(f"加载机构映射文件失败: {e}")
        org_mapping = {teacher_org: [teacher_org]}
    
    with sync_playwright() as playwright:
        browser = None
        context = None
        login_manager = None
        
        try:
            cookies_exists = os.path.exists(cookies_path) and os.path.getsize(cookies_path) > 0
            
            # 启动浏览器，优化启动参数
            browser = playwright.chromium.launch(
                headless=headless,
                slow_mo=50 if not headless else 0,  # 无头模式下不需要减速
                env={
                    "SSL_CERT_FILE": certifi.where(),
                    "REQUESTS_CA_BUNDLE": certifi.where()
                },
                ignore_default_args=["--disable-extensions"]
            )
            
            # 创建浏览器上下文，如果cookies存在则加载
            browser_context_params = {
                # 禁用图片加载，可显著提高页面加载速度
                "viewport": {"width": 1280, "height": 720},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            if cookies_exists:
                try:
                    browser_context_params["storage_state"] = cookies_path
                    context = browser.new_context(**browser_context_params)
                    logging.info("已加载登录状态")
                except Exception:
                    context = browser.new_context(**browser_context_params)
            else:
                context = browser.new_context(**browser_context_params)
            
            # 配置更快的导航设置
            context.set_default_navigation_timeout(20000)
            context.set_default_timeout(15000)
            
            # 禁用CSS，提高页面加载速度(仅在无头模式时)
            if headless:
                context.route("**/*.{png,jpg,jpeg,gif,webp}", lambda route: route.abort())
                context.route("**/*.css", lambda route: route.abort())
            
            page = context.new_page()
            max_pages = 5
            
            # 创建登录管理器
            login_manager = LoginManager(page, cookies_path)
            
            # 访问网站主页
            page.goto("https://www.aminer.cn", wait_until="domcontentloaded")
            
            # 检查登录状态
            if not login_manager.check_login():
                logging.info("需要手动登录...")
                login_manager.manual_login()
            else:
                logging.info("已成功登录")
                
            logging.info(f"开始搜索 {teacher_name}...")
            page.goto(f"https://www.aminer.cn/search/person?q={teacher_name}", 
                     wait_until="domcontentloaded", timeout=20000)
            
            # 使用更高效的方法等待搜索结果
            result_selector = ".a-aminer-components-expert-c-person-item-personItem"
            
            # 检查搜索结果是否存在
            if not page.wait_for_selector(result_selector, state="attached", timeout=15000):
                logging.warning("未找到搜索结果")
                return ""
            
            # 使用更高效的方式获取最大页码
            max_pages_text = page.evaluate("""
                () => {
                    const items = document.querySelectorAll('.ant-pagination-item');
                    if (!items.length) return 5; // 默认5页
                    let maxPage = 0;
                    items.forEach(item => {
                        const num = parseInt(item.textContent);
                        if (!isNaN(num) && num > maxPage) maxPage = num;
                    });
                    return maxPage;
                }
            """)
            
            max_pages = max_pages_text if isinstance(max_pages_text, int) else 5
            
            current_page = 1
            
            # 遍历所有页面 - 使用更高效的方法
            while current_page <= max_pages:
                logging.info(f"检查第 {current_page} 页")
                
                # 使用JavaScript直接在页面中查找匹配结果，提高效率
                found = page.evaluate("""
                    (params) => {
                        const teacherOrg = params.teacherOrg;
                        const orgAliases = params.orgAliases;
                        const items = document.querySelectorAll('.a-aminer-components-expert-c-person-item-personItem');
                        let foundLink = null;
                        
                        for (const item of items) {
                            try {
                                const nameElem = item.querySelector('.profileName .name');
                                if (!nameElem) continue;
                                
                                const name = nameElem.textContent.trim();
                                const orgElems = item.querySelectorAll('.person_info_item');
                                
                                for (const orgElem of orgElems) {
                                    if (orgElem.innerHTML.includes('lacale')) {
                                        const orgText = orgElem.textContent.toLowerCase();
                                        
                                        for (const alias of orgAliases) {
                                            if (orgText.includes(alias.toLowerCase())) {
                                                const link = item.querySelector('.person_name a');
                                                if (link) {
                                                    console.log(`找到匹配: ${name}, ${orgText}`);
                                                    foundLink = link.getAttribute('href');
                                                    return { name, foundLink };
                                                }
                                            }
                                        }
                                    }
                                }
                            } catch (e) {
                                continue;
                            }
                        }
                        return null;
                    }
                """, {"teacherOrg": teacher_org, "orgAliases": org_mapping.get(teacher_org, [teacher_org])})
                
                if found and found.get('foundLink'):
                    profile_url = found.get('foundLink')
                    
                    # 确保URL是完整的
                    if not profile_url.startswith("http"):
                        profile_url = "https://www.aminer.cn" + profile_url
                    
                    logging.info(f"找到匹配: {found.get('name', '未知')}")
                    return profile_url
                
                # 检查是否有下一页
                next_button = page.query_selector(".ant-pagination-next:not(.ant-pagination-disabled)")
                if next_button:
                    current_page += 1
                    next_button.click()
                    page.wait_for_load_state("domcontentloaded", timeout=8000)
                    
                    # 更高效地等待搜索结果
                    try:
                        page.wait_for_selector(result_selector, timeout=8000)
                    except Exception:
                        pass
                else:
                    break
            
            logging.warning("未找到匹配的教师")
            return ""
        except Exception as e:
            logging.error(f"搜索过程中发生错误: {e}")
            return ""
        finally:
            # 关闭资源
            if browser is not None:
                browser.close()

if __name__ == "__main__":  
    # （建议一定要运行一次保存一下cookies）
    # 测试搜索；以我们的陈海山校长为例
    profile_url = search_teacher("陈海山", "南京信息工程大学", headless=False)
    print(f"找到的URL: {profile_url}")

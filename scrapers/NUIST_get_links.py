import requests
from bs4 import BeautifulSoup
import time
import os
import certifi
import logging
from typing import List, Dict, Tuple

class NUISTScraper:
    def __init__(self, school_name: str):
        """初始化爬虫"""
        self.school_name = school_name
        # 设置证书路径
        self.cert_path = certifi.where()
        # 添加请求头模拟浏览器
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def get_all_teacher_links(self) -> List[Dict]:
        """获取门户网页上所有教师的链接和姓名
        
        返回:
            List[Dict]: 包含教师链接和姓名的列表，每个字典包含:
                - url: 教师个人主页链接
                - name: 教师姓名
        """
        teacher_info_list = []
        
        # 根据学校名称获取对应的门户网站
        if self.school_name == "南京信息工程大学":
            # 南信大教师列表页面
            base_url = "https://faculty.nuist.edu.cn"
            
            # 获取总页数 - 根据网页底部信息可知共15页
            total_pages = 15
            
            # 循环遍历所有页面
            for page in range(1, total_pages + 1):
                # 根据页码构建URL - 使用正确的分页参数格式
                list_url = f"https://faculty.nuist.edu.cn/dwlistjs.jsp?totalpage={total_pages}&PAGENUM={page}&urltype=tsites.CollegeTeacherList&wbtreeid=1021&st=0&id=1103&lang=zh_CN"
                logging.info(f"正在爬取第{page}页教师列表...")
                
                try:
                    # 获取页面内容，使用证书路径和请求头
                    response = requests.get(list_url, verify=self.cert_path, headers=self.headers, timeout=30)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 南信大的HTML结构是独特的，我们需要直接查找包含教师信息的<li>元素
                    teacher_elements = soup.select("ul.clearfix > li")
                    
                    page_teacher_count = 0
                    for element in teacher_elements:
                        # 只处理包含<a>标签且href属性包含/zh_CN/index.htm的元素
                        link_element = element.select_one("a[href*='/zh_CN/index.htm']")
                        if link_element and link_element.has_attr('href'):
                            link = link_element['href']
                            # 确保链接是完整的URL
                            if not link.startswith('http'):
                                link = base_url + link
                            
                            # 教师姓名在<div class="text">中
                            name_element = element.select_one('div.text')
                            name = name_element.text.strip() if name_element else "未知"
                            
                            # 添加教师信息到列表
                            teacher_info = {
                                "url": link,
                                "name": name
                            }
                            teacher_info_list.append(teacher_info)
                            page_teacher_count += 1
                    
                    logging.info(f"第{page}页找到{page_teacher_count}位教师")
                    
                    # 添加延迟，避免请求过快
                    time.sleep(1)
                    
                except Exception as e:
                    logging.error(f"爬取第{page}页教师列表出错: {str(e)}")
                    continue
        
        logging.info(f"总共找到{len(teacher_info_list)}位教师")
        return teacher_info_list
    
if __name__ == "__main__":
    # 设置日志格式
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    scraper = NUISTScraper("南京信息工程大学")
    teacher_info = scraper.get_all_teacher_links()
    
    # 打印结果用于调试
    print(f"共找到 {len(teacher_info)} 位教师")
    for i, info in enumerate(teacher_info[:20]):  # 只打印前5个进行验证
        print(f"教师{i+1}: {info['name']} - {info['url']}")
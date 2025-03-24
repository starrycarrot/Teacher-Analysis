import requests
from bs4 import BeautifulSoup
import time
import os

class SchoolScraper:
    def __init__(self, school_name: str):
        """初始化爬虫"""
        self.school_name = school_name
        # 清除可能导致问题的环境变量
        if "SSL_CERT_FILE" in os.environ:
            del os.environ["SSL_CERT_FILE"]
    
    def get_all_teacher_links(self):
        """获取门户网页上所有教师的链接"""
        teacher_links = []
        
        # 根据学校名称获取对应的门户网站
        if self.school_name == "南京信息工程大学":
            list_url_template = f"https://faculty.nuist.edu.cn/dwlistjs.jsp?urltype=tsites.CollegeTeacherList&wbtreeid=1021&st=0&id=1103&lang=zh_CN#collegeteacher"
            base_url="https://faculty.nuist.edu.cn"
        
        # 获取总页数 - 实际项目中应该动态获取
        total_pages = 2  # 默认值，可以通过页面内容动态获取
        
        # 循环遍历所有页面
        for page in range(1, total_pages + 1):
            list_url = list_url_template.format(page)
            print(f"正在爬取第{page}页教师列表...")
            
            try:
                # 获取页面内容
                response = requests.get(list_url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找所有教师链接 - 选择器需要根据实际网页结构调整
                teacher_elements = soup.select("a[href*='/zh_CN/index.htm']")
                
                for element in teacher_elements:
                    link = element.get('href')
                    if link:
                        # 确保链接是完整的URL
                        if not link.startswith('http'):
                            link = base_url + link
                        teacher_links.append(link)
                
                # 添加延迟，避免请求过快
                time.sleep(1)
                
            except Exception as e:
                print(f"爬取第{page}页教师列表出错: {str(e)}")
                continue
        
        print(f"共找到{len(teacher_links)}位教师")
        return teacher_links
    
if __name__ == "__main__":
    scraper = SchoolScraper("南京信息工程大学")
    teacher_links = scraper.get_all_teacher_links()
    print(teacher_links)

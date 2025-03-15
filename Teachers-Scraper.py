from scrapegraphai.graphs import SmartScraperGraph
import json  # 用于保存结构化数据
import os  # 用于创建文件夹
import requests  # 用于获取网页
from bs4 import BeautifulSoup  # 用于解析网页
import time  # 用于添加延迟，避免请求过快

# 正确的配置参数结构
graph_config = {
    "llm": {
        "api_key": "sk-60a2221879044d9482635aca04389f90",
        "model": "deepseek-chat",
    },
    "headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    },
    "verbose": True
}

# 强化版提示词（结构化数据提取）
scrape_prompt = """
请严格按照JSON格式提取结构化以下信息，缺失字段请填"无"：

{
    "basic_info": {
        "name": "教师全名",
        "title": ["学术职称（教授/副教授/研究员/讲师）"],
        "admin_role": "行政职务（院长/系主任等，无则填'无'）",
        "mentor_qualification": ["导师资格（博导/硕导）"],
        "honors": ["荣誉头衔（院士/杰青等）"]
    },
    "bio_details": {
        "birth_year": "出生年份（直接提取即可）",
        "education": {
            "undergrad": "本科（格式：1995-1999 学校全称 所学专业）",
            "master": "硕士（同上）",
            "phd": "博士（同上）" 
        }
    },
    "likes": （点赞数）
    "academic": {
        "research_fields": ["研究领域1", "研究领域2", ……],
        "publications": [
            {
                "title_cn": "论文标题（必译中文）",
                "title_en": "原标题（英文论文保留）",
                "year": 发表年份,
                "journal": "期刊/出版社"
            }
        ]
    },
}

数据处理需遵循的规则：
1. 如果实在找不到出生年份，我们可以用时间推断：
   - 出生年推算：本科入学年-18（需加*标注）例如：2000年本科入学 → 推算1982年出生

2. 格式要求
   - 学校全称不需要学院信息（比如就是 南京大学 气象学）

3. 格式校验：
   - 教育经历时间格式：YYYY-YYYY
   - 出生年份：纯数字（推断值需加*）
   - 点赞数：仅数字或"无"

4. 学术经历：
   - 研究领域：从论文、著作、或着直接信息里综合分析得到
   - 论文：只需选择最具代表性的即可（比如一作、二作的、或着有影响力的），宁缺毋滥

5. 冲突解决：
   - 时间冲突取页面最显眼位置信息
   - 中英文论文标题同时保留

请严格验证数据逻辑：
- 教育时间顺序：本科<硕士<博士
- 职称与导师资格匹配（博导须有高级职称）

最终输出必须是完整且语法正确的JSON对象！
"""

def get_all_teacher_links(base_url="https://faculty.nuist.edu.cn"):
    """获取所有教师的链接"""
    teacher_links = []
    
    # 基础URL
    list_url_template = "https://faculty.nuist.edu.cn/dwlistjs.jsp?urltype=tsites.CollegeTeacherList&wbtreeid=1021&st=0&id=1103&lang=zh_CN&PAGENUM={}"
    
    # 总页数
    total_pages = 15  # 根据搜索结果中看到的"共172条 1/15"信息
    
    # 循环遍历所有页面
    for page in range(1, total_pages + 1):
        list_url = list_url_template.format(page)
        print(f"正在爬取第{page}页教师列表...")
        
        # 获取页面内容
        response = requests.get(list_url, headers=graph_config["headers"])
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找所有教师链接
        # 注意：这里的选择器需要根据实际网页结构调整
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
    
    print(f"共找到{len(teacher_links)}位教师")
    return teacher_links

def scrape_teacher_data(teacher_url):
    """使用SmartScraperGraph爬取单个教师的数据"""
    try:
        # 创建智能爬虫实例
        smart_scraper = SmartScraperGraph(
            prompt=scrape_prompt,
            source=teacher_url,
            config=graph_config,
            schema=None
        )
        
        # 执行爬取
        result = smart_scraper.run()
        return result
    except Exception as e:
        print(f"爬取 {teacher_url} 时出错: {str(e)}")
        return None

def main():
    # 创建保存数据的文件夹
    output_dir = "NUIST"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 获取所有教师链接
    teacher_links = get_all_teacher_links()
    
    # 存储所有教师数据的列表
    all_teachers_data = []
    
    # 循环爬取每位教师的信息
    for i, link in enumerate(teacher_links):
        print(f"正在爬取第 {i+1}/{len(teacher_links)} 位教师: {link}")
        
        # 爬取教师数据
        teacher_data = scrape_teacher_data(link)
        
        if teacher_data:
            # 将教师数据添加到列表中
            all_teachers_data.append(teacher_data)
            
            # 从正确的路径获取教师姓名
            teacher_name = teacher_data.get("content", {}).get("basic_info", {}).get("name", f"教师_{i+1}")
            file_name = f"{teacher_name}.json"
            with open(os.path.join(output_dir, file_name), "w", encoding="utf-8") as f:
                json.dump(teacher_data, f, ensure_ascii=False, indent=2)
            
            print(f"成功保存 {teacher_name} 的数据")
        
        # 添加延迟，避免请求过快
        time.sleep(3)
    
    # 保存所有教师数据的汇总文件
    with open(os.path.join(output_dir, "所有教师数据.json"), "w", encoding="utf-8") as f:
        json.dump(all_teachers_data, f, ensure_ascii=False, indent=2)
    
    print(f"爬取完成！共爬取了 {len(all_teachers_data)} 位教师的信息")
    print(f"数据已保存至 {output_dir} 文件夹")

if __name__ == "__main__":
    main()

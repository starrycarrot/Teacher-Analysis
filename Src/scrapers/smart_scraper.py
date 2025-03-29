from scrapegraphai.graphs import SmartScraperGraph
import os
import certifi


# 环境变量设置
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

def scrape_profile(profile_url):
    """使用SmartScraperGraph爬取Aminer个人主页的详细信息"""
    # 使用智能爬虫爬取
    try:
        print(f"开始使用SmartScraperGraph爬取个人主页: {profile_url}")
        
        # 创建智能爬虫实例
        smart_scraper = SmartScraperGraph(
            prompt=scrape_prompt,
            source=profile_url,
            config=graph_config
        )
        
        # 执行爬取
        print("执行SmartScraperGraph.run()...")
        result = smart_scraper.run()
        
        # 检查结果
        if result is None:
            print("爬取结果为None")
            return {}
            
        print(f"爬取成功，获取到数据: {type(result)}")
        return result
    except Exception as e:
        import traceback
        print(f"爬取个人主页 {profile_url} 失败:")
        raise e

# 爬虫的图配置
graph_config = {
    "llm": {
        "model": "deepseek/deepseek-chat",
        "api_key": "sk-73062d5391b94e2e8465019ef399a35f",
    },
    "headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    },
    "storage_state": "Src/config/aminer_cookies.json",
    "verbose": True,
    "headless": False
}

# 智能爬虫的提示词（结构化数据提取）
scrape_prompt = """
请严格按照JSON格式提取结构化以下信息，缺失字段为空字符串：

{
    "basic_info": {
        "name": "教师全名",
        "title": ["学术职称（教授/副教授/研究员/讲师）"],
        "admin_role": ["行政职务（院长/系主任等）"],
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
    "likes": （点赞数，int数字）
    "academic": {
        "research_fields": ["研究领域1", "研究领域2", ……],
        "publications": [
            {
                "title_cn": "论文标题（必译中文）",
                "title_en": "原标题（英文论文保留）",
                "year": 发表年份,
                "journal": "期刊/出版社",
                "DOI": "DOI号"
            }
        ]
    },
}

数据处理需遵循的规则：
1. 如果实在找不到出生年份，我们可以用时间推断：
   - 出生年推算：本科入学年-18（需加*标注）例如：2000年本科入学 → 推算1982年出生

2. 格式要求
   - 学校全称，不需要学院信息（比如就是 南京大学 气象学）

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
- 讲师直接填讲师，不需要加（高校）
- 硕士生导师、博士生导师直接转为硕导、博导

最终输出必须是完整且语法正确的JSON对象！
"""

# 单独测试智能爬虫
if __name__ == "__main__":
    test_url = "https://www.aminer.cn/profile/haishan-chen/54491420dabfae1e04143cba"
    result = scrape_profile(test_url)
    print(result)

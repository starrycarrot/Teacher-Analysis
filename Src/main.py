#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
教师信息分析系统主程序

该模块是系统的入口点，负责从学校教师门户获取所有教师信息，并转换为结构化JSON文件。
"""
import json
from typing import Dict, List, Tuple, Optional


# 导入爬虫模块
from Src.scrapers.shool_get_links import SchoolScraper
from Src.scrapers.smart_scraper import scrape_profile
from Src.scrapers.aminer_search import search_teacher

# 导入工具模块
from Src.utils import check_data_quality
from Src.utils.merge_data import merge_data

def process_single_teacher(teacher_url: str, school_name: str) -> Optional[Dict]:
    """
    处理单个教师信息的完整流程
    
    输入：
    teacher_url: 教师学校网页URL
    school_name: 教师所属学校名称
    
    流程：
    1. 学校个人网页数据采集
    2. 数据质量评估（若合格，跳过3、4、5步骤）
    3. 在Aminer搜索教师
    4. 爬取Aminer个人主页
    5. 合并数据
    6. 存储最终数据

    输出：
    教师数据json字典
    """
    
    # 1. 学校数据采集
    school_data = scrape_profile(teacher_url)
    # 把字典从爬虫原始输出的content里提取出来,得到真正的字典
    school_data = school_data["content"]
    
    # 提取教师基本信息
    teacher_name = school_data["basic_info"]["name"]


    # 2. 数据质量评估
    is_qualified = check_data_quality.check_data(school_data)
    if is_qualified:
        # 6. 如果数据合格，直接返回学校数据，跳过3、4、5步骤
        return school_data
    
    else:
        # 3. 先进行搜索得到教师的AMiner主页
        aminer_url = search_teacher(teacher_name, school_name)

        # 4. 爬取Aminer个人主页
        aminer_data = scrape_profile(aminer_url)
        # 把字典从爬虫原始输出的content里提取出来,得到真正的字典
        aminer_data = aminer_data["content"]
        
        # 5. 合并数据
        merged_data = merge_data.merge_data(school_data, aminer_data)
        
        # 6. 返回合并数据
        return merged_data
    

def process_all_teachers(school_name: str, output_dir: str) -> None:
    """
    处理所有教师信息的完整流程
    
    输入：
    school_name: 学校名称
    output_dir: json数据输出目录

    流程：
    1. 获取所有教师链接
    2. 处理每个教师信息
    3. 存储最终数据

    输出：
    所有教师数据json字典
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出目录: {output_dir}")

    # 1. 获取所有教师链接
    print("使用BeautifulSoup爬虫获取教师链接...")
    teacher_urls = SchoolScraper(school_name).get_all_teacher_links()

    # 2. 处理每个教师信息
    for teacher_url in teacher_urls:
        teacher_data = process_single_teacher(teacher_url, school_name)
        # 存储单个教师数据为json文件
        json.dump(teacher_data, open(f"{output_dir}/{teacher_url}.json", "w", encoding="utf-8"))


if __name__ == "__main__":
    school_name = "南京信息工程大学"
    output_dir = "NUIST_teacher_data"
    process_all_teachers(school_name, output_dir)


    
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
教师信息分析系统主程序

该模块是系统的入口点，负责从学校教师门户获取所有教师信息，并转换为结构化JSON文件。
"""
import json
from typing import Dict, List, Tuple, Optional
import os
import time
import certifi

# 环境变量设置
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

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
    print(f"正在处理教师网页: {teacher_url}")
    
    # 1. 学校数据采集
    school_data = scrape_profile(teacher_url)
    # 把字典从爬虫原始输出的content里提取出来,得到真正的字典
    school_data = school_data["content"]
    
    # 提取教师基本信息
    teacher_name = school_data["basic_info"]["name"]
    print(f"已获取 {teacher_name} 的学校网页数据")

    # 2. 数据质量评估
    print("评估数据质量...")
    is_qualified = check_data_quality.check_data(school_data)
    if is_qualified:
        # 6. 如果数据合格，直接返回学校数据，跳过3、4、5步骤
        print(f"{teacher_name} 的学校数据质量合格，无需补充")
        return school_data
    
    else:
        print(f"{teacher_name} 的学校数据不完整，尝试从AMiner获取补充数据")
        # 3. 先进行搜索得到教师的AMiner主页
        print(f"在AMiner搜索 {teacher_name}...")
        aminer_url = search_teacher(teacher_name, school_name)
        
        if not aminer_url:
            print(f"未找到 {teacher_name} 的AMiner主页，返回原始数据")
            return school_data

        # 4. 爬取Aminer个人主页
        print(f"爬取 {teacher_name} 的AMiner主页数据...")
        aminer_data = scrape_profile(aminer_url)
        # 把字典从爬虫原始输出的content里提取出来,得到真正的字典
        aminer_data = aminer_data["content"]
        
        # 5. 合并数据
        print("合并学校数据和AMiner数据...")
        merged_data = merge_data(school_data, aminer_data)
        
        # 6. 返回合并数据
        print(f"{teacher_name} 的数据处理完成")
        return merged_data
    

def process_all_teachers(school_name: str, output_dir: str, test_mode: bool = False, test_limit: int = 3) -> None:
    """
    处理所有教师信息的完整流程
    
    输入：
    school_name: 学校名称
    output_dir: json数据输出目录
    test_mode: 是否为测试模式，默认为False
    test_limit: 测试模式下处理的教师数量，默认为3

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
    print(f"开始从 {school_name} 获取教师链接...")
    start_time = time.time()
    teacher_urls = SchoolScraper(school_name).get_all_teacher_links()
    end_time = time.time()
    print(f"获取到 {len(teacher_urls)} 个教师链接，耗时 {end_time - start_time:.2f} 秒")

    # 测试模式下，只处理前几个教师
    if test_mode:
        print(f"⚠️ 测试模式已启用，仅处理前 {test_limit} 位教师")
        teacher_urls = teacher_urls[:test_limit]

    # 2. 处理每个教师信息
    print(f"开始处理教师信息...")
    processed_count = 0
    for i, teacher_url in enumerate(teacher_urls):
        print(f"处理第 {i+1}/{len(teacher_urls)} 位教师...")
        start_time = time.time()
        teacher_data = process_single_teacher(teacher_url, school_name)
        end_time = time.time()
        
        # 提取教师姓名用于文件命名
        teacher_name = teacher_data["basic_info"]["name"]
        # 存储单个教师数据为json文件
        output_path = f"{output_dir}/{teacher_name}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(teacher_data, f, ensure_ascii=False, indent=2)
        
        processed_count += 1
        print(f"已保存 {teacher_name} 的数据到 {output_path}，耗时 {end_time - start_time:.2f} 秒")
    
    print(f"✅ 所有任务完成！共处理 {processed_count} 位教师数据")

if __name__ == "__main__":
    school_name = "南京信息工程大学"
    output_dir = "NUIST_teacher_data"
    
    # 运行模式选择
    test_mode = True  # 设置为True启用测试模式，仅处理少量教师
    test_limit = 3    # 测试模式下处理的教师数量
    
    if test_mode:
        process_all_teachers(school_name, output_dir, test_mode=True, test_limit=test_limit)
    else:
        process_all_teachers(school_name, output_dir)

    
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
import logging

# 环境变量设置
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# 导入爬虫模块
from scrapers.shool_get_links import SchoolScraper
from scrapers.smart_scraper import scrape_profile
from scrapers.aminer_search import search_teacher

# 导入工具模块
from utils import check_data_quality
from utils.merge_data import merge_data

class SimpleFormatter(logging.Formatter):
    """自定义格式化器，只在WARNING和ERROR级别显示级别前缀"""
    
    def format(self, record):
        # 保存原始消息
        original_msg = record.msg
        
        # 只有WARNING和ERROR级别显示前缀
        if record.levelno >= logging.WARNING:
            record.msg = f"{record.levelname} - {record.msg}"
        
        # 格式化记录
        result = super().format(record)
        
        # 恢复原始消息，避免影响其他处理器
        record.msg = original_msg
        
        return result

def setup_logging(output_dir: str) -> None:
    """设置日志配置"""
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 日志文件直接放在输出目录下
    log_file = os.path.join(output_dir, 'teacher_analysis.log')
    
    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 清除现有的handlers
    logger.handlers = []
    
    # 创建简单格式化器
    formatter = SimpleFormatter('%(message)s')
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='w')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def process_single_teacher(teacher_info: Dict, force_aminer: bool = False) -> Optional[Dict]:
    """
    处理单个教师信息的完整流程
    
    输入：
    teacher_info: 包含教师基本信息的字典，包括url和name
    force_aminer: 是否强制使用AMiner搜索，默认为False
    
    流程：
    1. 学校个人网页数据采集
    2. 数据质量评估（若合格且不强制使用AMiner，跳过3、4、5步骤）
    3. 在Aminer搜索教师
    4. 爬取Aminer个人主页
    5. 合并数据
    6. 存储最终数据

    输出：
    教师数据json字典
    """
    teacher_url = teacher_info["url"]
    teacher_name = teacher_info["name"]
    school_name = "南京信息工程大学"  # 在这个例子中是硬编码的
    
    logging.info(f"【信息】正在处理教师: {teacher_name}")
    logging.info(f"【信息】网页URL: {teacher_url}")
    
    # 1. 学校数据采集
    logging.info(f"【步骤1】开始爬取学校个人网页...")
    school_data = scrape_profile(teacher_url)
    # 把字典从爬虫原始输出的content里提取出来,得到真正的字典
    school_data = school_data["content"]
    
    # 确保基本信息中包含从列表页获取的姓名信息
    if "basic_info" not in school_data:
        school_data["basic_info"] = {}
    
    # 使用从列表页获取的姓名信息填充或更新基本信息
    school_data["basic_info"]["name"] = teacher_name
    
    # 添加数据来源信息
    school_data["data_sources"] = {
        "school_url": teacher_url
    }
    
    logging.info(f"【步骤1完成】已获取 {teacher_name} 的学校网页数据")

    # 2. 数据质量评估
    logging.info(f"【步骤2】评估数据质量...")
    is_qualified = check_data_quality.check_data(school_data)
    if is_qualified and not force_aminer:  # 增加force_aminer的判断
        # 6. 如果数据合格且不强制使用AMiner，直接返回学校数据
        logging.info(f"【步骤2完成】{teacher_name} 的学校数据质量合格，无需补充")
        return school_data
    
    else:
        reason = "数据不完整" if not is_qualified else "强制使用AMiner"
        logging.info(f"【步骤2完成】{teacher_name} 的学校数据{reason}，尝试从AMiner获取补充数据")
        # 3. 先进行搜索得到教师的AMiner主页
        logging.info(f"【步骤3】在AMiner搜索 {teacher_name}...")
        aminer_url = search_teacher(teacher_name, school_name)
        
        if not aminer_url:
            logging.warning(f"【步骤3失败】未找到 {teacher_name} 的AMiner主页，返回原始数据")
            return school_data

        # 4. 爬取Aminer个人主页
        logging.info(f"【步骤4】爬取 {teacher_name} 的AMiner主页数据...")
        aminer_data = scrape_profile(aminer_url)
        # 把字典从爬虫原始输出的content里提取出来,得到真正的字典
        aminer_data = aminer_data["content"]
        
        # 添加AMiner数据来源
        aminer_data["data_sources"] = {
            "aminer_url": aminer_url
        }
        logging.info(f"【步骤4完成】已获取AMiner数据")
        
        # 5. 合并数据
        logging.info(f"【步骤5】合并学校数据和AMiner数据...")
        merged_data = merge_data(school_data, aminer_data)
        
        # 确保合并后的数据包含所有数据来源
        merged_data["data_sources"] = {
            "school_url": teacher_url,
            "aminer_url": aminer_url
        }
        
        # 6. 返回合并数据
        logging.info(f"【步骤6完成】{teacher_name} 的数据处理完成")
        return merged_data
    

def process_all_teachers(school_name: str, output_dir: str, test_mode: bool = False, test_limit: int = 3, force_aminer: bool = False) -> None:
    """
    处理所有教师信息的完整流程
    
    输入：
    school_name: 学校名称
    output_dir: json数据输出目录
    test_mode: 是否为测试模式，默认为False
    test_limit: 测试模式下处理的教师数量，默认为3
    force_aminer: 是否强制使用AMiner搜索，默认为False

    流程：
    1. 获取所有教师链接
    2. 处理每个教师信息
    3. 存储最终数据

    输出：
    所有教师数据json字典
    """
    # 设置日志
    setup_logging(output_dir)
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logging.info(f"创建输出目录: {output_dir}")

    # 获取已处理的教师列表（从现有JSON文件中提取）
    existing_teachers = []
    if os.path.exists(output_dir):
        for filename in os.listdir(output_dir):
            if filename.endswith('.json'):
                teacher_name = os.path.splitext(filename)[0]
                existing_teachers.append(teacher_name)
        logging.info(f"===============================================")
        logging.info(f"发现已有 {len(existing_teachers)} 位教师的数据文件")
        logging.info(f"===============================================")

    # 1. 获取所有教师链接和基本信息
    logging.info(f"")
    logging.info(f"【阶段1：获取教师列表】")
    logging.info(f"开始从 {school_name} 获取教师信息...")
    start_time = time.time()
    teacher_info_list = SchoolScraper(school_name).get_all_teacher_links()
    end_time = time.time()
    logging.info(f"获取到 {len(teacher_info_list)} 个教师信息，耗时 {end_time - start_time:.2f} 秒")
    logging.info(f"【阶段1完成】")
    logging.info(f"")

    # 测试模式下，只处理前几个教师
    if test_mode:
        logging.warning(f"⚠️ 测试模式已启用，仅处理前 {test_limit} 位教师")
        teacher_info_list = teacher_info_list[:test_limit]

    # 2. 处理每个教师信息
    logging.info(f"【阶段2：处理教师信息】")
    logging.info(f"开始处理教师信息... {'(强制使用AMiner)' if force_aminer else ''}")
    processed_count = 0
    skipped_count = 0
    
    for i, teacher_info in enumerate(teacher_info_list):
        logging.info(f"")
        logging.info(f"------ 处理第 {i+1}/{len(teacher_info_list)} 位教师 ------")
        
        # 获取教师姓名
        teacher_name = teacher_info["name"]
        
        # 检查是否已存在该教师的数据
        if teacher_name in existing_teachers:
            logging.info(f"跳过 {teacher_name} - 数据已存在")
            skipped_count += 1
            continue
        
        try:
            # 完整处理教师信息
            start_time = time.time()
            teacher_data = process_single_teacher(teacher_info, force_aminer)
            end_time = time.time()
            
            if not teacher_data:
                logging.error(f"处理 {teacher_name} 的数据失败，跳过")
                continue
            
            # 存储单个教师数据为json文件
            output_path = f"{output_dir}/{teacher_name}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(teacher_data, f, ensure_ascii=False, indent=2)
            
            processed_count += 1
            logging.info(f"已保存 {teacher_name} 的数据到 {output_path}，耗时 {end_time - start_time:.2f} 秒")
        
        except Exception as e:
            logging.error(f"处理教师 {teacher_name} 数据时出错: {str(e)}")
            continue
    
    logging.info(f"")
    logging.info(f"===============================================")
    logging.info(f"✅ 所有任务完成！共处理 {processed_count} 位教师数据，跳过 {skipped_count} 位已有数据的教师")
    logging.info(f"===============================================")

if __name__ == "__main__":
    school_name = "南京信息工程大学"
    output_dir = "NUIST_teacher_data"
    
    # 运行模式选择
    test_mode = True  # 设置为True启用测试模式，仅处理少量教师
    test_limit = 3    # 测试模式下处理的教师数量
    force_aminer = False  # 设置是否强制使用AMiner搜索
    
    if test_mode:
        process_all_teachers(school_name, output_dir, test_mode=True, test_limit=test_limit, force_aminer=force_aminer)
    else:
        process_all_teachers(school_name, output_dir, force_aminer=force_aminer)

    
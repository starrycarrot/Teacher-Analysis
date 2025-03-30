#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
教师数据质量检查模块

该模块负责检查爬取的教师数据是否完整，确保基本信息和教育经历是完整的。
"""
from typing import Dict, List, Any, Tuple
import logging


def check_data(data: Dict) -> bool:
    """
    检查教师数据是否完整
    
    参数:
        data: 教师数据字典
    
    返回:
        bool: 数据质量是否合格 (True为合格，False为不合格)
    """
    all_passed = True
    
    # 检查基本信息字段
    basic_info_result = check_basic_info(data.get('basic_info', {}))
    if not basic_info_result[0]:
        logging.warning(f"数据质量检查问题：基本信息 - {basic_info_result[1]}")
        all_passed = False
    
    # 检查个人信息字段
    bio_details_result = check_bio_details(data.get('bio_details', {}))
    if not bio_details_result[0]:
        logging.warning(f"数据质量检查问题：个人信息 - {bio_details_result[1]}")
        all_passed = False
    
    # 检查工作经历字段
    work_experience_result = check_work_experience(data.get('work_experience', []))
    if not work_experience_result[0]:
        logging.warning(f"数据质量检查问题：工作经历 - {work_experience_result[1]}")
        all_passed = False
    
    if all_passed:
        logging.info("数据质量检查通过")
    else:
        logging.warning("数据质量检查未通过")
        
    return all_passed


def check_basic_info(basic_info: Dict) -> Tuple[bool, str]:
    """检查基本信息字段是否完整"""
    missing_fields = []
    
    # 检查姓名
    if not basic_info.get('name') or basic_info.get('name') == "":
        missing_fields.append("姓名")
    
    # 检查职称
    if not basic_info.get('title') or len(basic_info.get('title', [])) == 0:
        missing_fields.append("职称")
    
    # 检查导师资格
    if not basic_info.get('mentor_qualification') or len(basic_info.get('mentor_qualification', [])) == 0:
        missing_fields.append("导师资格")
    
    # 检查荣誉头衔
    if not basic_info.get('honors') or len(basic_info.get('honors', [])) == 0:
        missing_fields.append("荣誉头衔")
    
    if missing_fields:
        return False, f"缺失字段: {', '.join(missing_fields)}"
    return True, ""


def check_bio_details(bio_details: Dict) -> Tuple[bool, str]:
    """检查生物信息字段是否完整"""
    missing_fields = []
    
    # 检查出生年份
    if 'birth_year' not in bio_details or bio_details.get('birth_year') == "":
        missing_fields.append("出生年份")
    
    # 获取教育信息
    education = bio_details.get('education', {})
    
    # 检查本科信息
    if 'undergrad' not in education or education.get('undergrad') == "":
        missing_fields.append("本科教育信息")
    
    # 检查硕士信息
    if 'master' not in education or education.get('master') == "":
        missing_fields.append("硕士教育信息")
    
    # 检查博士信息
    if 'phd' not in education or education.get('phd') == "":
        missing_fields.append("博士教育信息")
    
    if missing_fields:
        return False, f"缺失字段: {', '.join(missing_fields)}"
    return True, ""


def check_work_experience(work_experience: List[Dict]) -> Tuple[bool, str]:
    """检查工作经历字段是否存在"""
    # 仅检查工作经历是否为空
    if not work_experience or len(work_experience) == 0:
        return False, "缺少工作经历信息"
    
    return True, ""


# 测试
if __name__ == "__main__":
    test_data = {
        'basic_info': {
            'name': '赵坤', 
            'title': ['教授'], 
            'admin_role': ['院长'], 
            'mentor_qualification': ['博导'], 
            'honors': ['国家自然科学基金杰出青年基金', '国家自然科学基金优秀青年基金', 
                      '教育部新世纪人才计划', '江苏省"333高层次人才培养工程"中青年科技领军人才']
        },
        'bio_details': {
            'birth_year': '', 
            'education': {
                'undergrad': '', 
                'master': '', 
                'phd': ''
            }
        }, 
        'work_experience': [
            {
                'period': '2015-2020',
                'institution': '南京大学',
                'position': '副教授'
            }
        ],
        'likes': '无', 
        'academic': {
            'research_fields': ['灾害性天气雷达反演', '同化预报', '形成机理研究'], 
            'publications': [
                {
                    'title_cn': '三维风场和X波段相控阵天气雷达双极化信号在对流风暴中垂直运动和云电化的诊断应用', 
                    'title_en': 'Application of Three-Dimensional Wind Fields and Dual-Polarization Signals of an X-band Phased Array Weather Radar in Diagnosing Vertical Motion and Cloud Electrification in Convective Storms', 
                    'year': 2025, 
                    'journal': 'Advances in Atmospheric Sciences'
                }
            ]
        }
    }
    print(check_data(test_data))

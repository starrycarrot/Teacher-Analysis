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
    # 检查基本信息字段
    basic_info_result = check_basic_info(data.get('basic_info', {}))
    if not basic_info_result[0]:
        logging.warning(f"数据质量检查失败：基本信息 - {basic_info_result[1]}")
        return False
    
    # 检查个人信息字段
    bio_details_result = check_bio_details(data.get('bio_details', {}))
    if not bio_details_result[0]:
        logging.warning(f"数据质量检查失败：个人信息 - {bio_details_result[1]}")
        return False
    
    # 所有检查都通过，返回True
    logging.info("数据质量检查通过")
    return True


def check_basic_info(basic_info: Dict) -> Tuple[bool, str]:
    """检查基本信息字段是否完整"""
    # 检查姓名
    if not basic_info.get('name') or basic_info.get('name') == "":
        return False, "姓名缺失"
    
    # 检查职称
    if not basic_info.get('title') or len(basic_info.get('title', [])) == 0:
        return False, "职称缺失"
    
    # 检查导师资格
    if not basic_info.get('mentor_qualification') or len(basic_info.get('mentor_qualification', [])) == 0:
        return False, "导师资格缺失"
    
    # 检查荣誉头衔
    if not basic_info.get('honors') or len(basic_info.get('honors', [])) == 0:
        return False, "荣誉头衔缺失"
    
    return True, ""


def check_bio_details(bio_details: Dict) -> Tuple[bool, str]:
    """检查生物信息字段是否完整"""
    # 检查出生年份
    if 'birth_year' not in bio_details or bio_details.get('birth_year') == "":
        return False, "出生年份缺失"
    
    # 获取教育信息
    education = bio_details.get('education', {})
    
    # 检查本科信息
    if 'undergrad' not in education or education.get('undergrad') == "":
        return False, "本科教育信息缺失"
    
    # 检查硕士信息
    if 'master' not in education or education.get('master') == "":
        return False, "硕士教育信息缺失"
    
    # 检查博士信息
    if 'phd' not in education or education.get('phd') == "":
        return False, "博士教育信息缺失"
    
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
        'likes': '无', 
        'academic': {
            'research_fields': ['灾害性天气雷达反演', '同化预报', '形成机理研究'], 
            'publications': [
                {
                    'title_cn': '三维风场和X波段相控阵天气雷达双极化信号在对流风暴中垂直运动和云电化的诊断应用', 
                    'title_en': 'Application of Three-Dimensional Wind Fields and Dual-Polarization Signals of an X-band Phased Array Weather Radar in Diagnosing Vertical Motion and Cloud Electrification in Convective Storms', 
                    'year': 2025, 
                    'journal': 'Advances in Atmospheric Sciences'
                }, 
                {
                    'title_cn': '华北弱对流系统中云和降水微物理的机载研究', 
                    'title_en': 'Airborne Investigation of Riming: Cloud and Precipitation Microphysics Within a Weak Convective System in North China', 
                    'year': 2025, 
                    'journal': 'Advances in Atmospheric Sciences'
                }, 
                {
                    'title_cn': '利用X波段相控阵雷达数据同化EnKF观测和模拟微爆的演变', 
                    'title_en': 'The Observed and Simulated Evolution of a Microburst Using X-Band Phased-Array Radar Data Assimilation with EnKF', 
                    'year': 2025, 
                    'journal': 'JOURNAL OF GEOPHYSICAL RESEARCH-ATMOSPHERES'
                }
            ]
        }
    }
    print(check_data(test_data))

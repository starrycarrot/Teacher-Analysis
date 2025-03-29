#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
教师数据合并模块

该模块负责合并从不同来源（如学校网站和AMiner）获取的教师数据，
处理可能的数据冲突，确保最终结果的准确性和完整性。
"""
from typing import Dict, List, Any
import logging


def merge_data(school_data: Dict, aminer_data: Dict) -> Dict:
    """
    合并来自学校网站和AMiner的教师数据
    
    参数:
        school_data: 从学校网站获取的教师数据
        aminer_data: 从AMiner获取的教师数据
    
    返回:
        Dict: 合并后的教师数据
    """
    # 创建一个新的结果字典，以学校数据为基础
    merged_data = school_data.copy()
    
    # 合并基本信息 (basic_info)
    merged_data['basic_info'] = merge_basic_info(
        school_data.get('basic_info', {}), 
        aminer_data.get('basic_info', {})
    )
    
    # 合并生物信息 (bio_details)
    merged_data['bio_details'] = merge_bio_details(
        school_data.get('bio_details', {}),
        aminer_data.get('bio_details', {})
    )
    
    # 合并点赞数信息
    merged_data['likes'] = merge_likes(
        school_data.get('likes', ''),
        aminer_data.get('likes', '')
    )
    
    # 合并学术信息 (academic)
    merged_data['academic'] = merge_academic(
        school_data.get('academic', {}),
        aminer_data.get('academic', {})
    )
    
    return merged_data


def merge_basic_info(school_basic: Dict, aminer_basic: Dict) -> Dict:
    """合并基本信息"""
    merged_basic = school_basic.copy()
    
    # 如果学校数据中没有姓名，则使用AMiner的
    if not merged_basic.get('name'):
        merged_basic['name'] = aminer_basic.get('name', '')
    
    # 合并职称信息（去重）
    school_titles = set(merged_basic.get('title', []))
    aminer_titles = set(aminer_basic.get('title', []))
    merged_basic['title'] = list(school_titles.union(aminer_titles))
    
    # 合并行政职务
    if not merged_basic.get('admin_role'):
        merged_basic['admin_role'] = aminer_basic.get('admin_role', '')
    
    # 合并导师资格信息（去重）
    school_qualifications = set(merged_basic.get('mentor_qualification', []))
    aminer_qualifications = set(aminer_basic.get('mentor_qualification', []))
    merged_basic['mentor_qualification'] = list(school_qualifications.union(aminer_qualifications))
    
    # 合并荣誉头衔（去重）
    school_honors = set(merged_basic.get('honors', []))
    aminer_honors = set(aminer_basic.get('honors', []))
    merged_basic['honors'] = list(school_honors.union(aminer_honors))
    
    return merged_basic


def merge_bio_details(school_bio: Dict, aminer_bio: Dict) -> Dict:
    """合并生物信息"""
    merged_bio = school_bio.copy()
    
    # 合并出生年份
    if not merged_bio.get('birth_year') or merged_bio.get('birth_year') == '':
        merged_bio['birth_year'] = aminer_bio.get('birth_year', '')
    
    # 获取教育信息
    school_education = merged_bio.get('education', {})
    aminer_education = aminer_bio.get('education', {})
    
    # 初始化合并后的教育信息
    if 'education' not in merged_bio:
        merged_bio['education'] = {}
    
    # 合并本科信息
    if not school_education.get('undergrad') or school_education.get('undergrad') == '':
        merged_bio['education']['undergrad'] = aminer_education.get('undergrad', '')
    else:
        merged_bio['education']['undergrad'] = school_education.get('undergrad', '')
    
    # 合并硕士信息
    if not school_education.get('master') or school_education.get('master') == '':
        merged_bio['education']['master'] = aminer_education.get('master', '')
    else:
        merged_bio['education']['master'] = school_education.get('master', '')
    
    # 合并博士信息
    if not school_education.get('phd') or school_education.get('phd') == '':
        merged_bio['education']['phd'] = aminer_education.get('phd', '')
    else:
        merged_bio['education']['phd'] = school_education.get('phd', '')
    
    return merged_bio


def merge_likes(school_likes: str, aminer_likes: str) -> str:
    """合并点赞数信息"""
    # 如果学校数据的点赞数为空，则使用AMiner的
    if not school_likes or school_likes == '':
        return aminer_likes
    return school_likes


def merge_academic(school_academic: Dict, aminer_academic: Dict) -> Dict:
    """合并学术信息,替换学校网页数据使用Aminer的数据"""
    merged_academic = aminer_academic.copy()
    
    # 研究领域：合并去重，保留所有研究方向
    school_fields = set(school_academic.get('research_fields', []))
    aminer_fields = set(aminer_academic.get('research_fields', []))
    merged_academic['research_fields'] = list(school_fields.union(aminer_fields))
    
    # 根据DOI去重，合并两个来源的数据
    school_pubs = school_academic.get('publications', [])
    aminer_pubs = aminer_academic.get('publications', [])
    
    # 初始化合并后的出版物列表
    merged_pubs = []
    
    # 创建DOI集合用于去重
    processed_dois = set()
    
    # 优先处理AMiner的出版物（因为通常AMiner的数据更全面）
    for pub in aminer_pubs:
        doi = pub.get('DOI', '')
        if doi and doi not in processed_dois:
            merged_pubs.append(pub)
            processed_dois.add(doi)
    
    # 添加学校数据中AMiner没有的出版物
    for pub in school_pubs:
        doi = pub.get('DOI', '')
        if doi and doi not in processed_dois:
            merged_pubs.append(pub)
            processed_dois.add(doi)
    
    # 更新合并后的出版物列表
    merged_academic['publications'] = merged_pubs
    
    return merged_academic


# 单元测试代码
if __name__ == "__main__":
    # 学校数据示例
    school_data = {
        "basic_info": {
            "name": "张三",
            "title": ["副教授"],
            "admin_role": "系主任",
            "mentor_qualification": ["硕导"],
            "honors": ["优秀教师"]
        },
        "bio_details": {
            "birth_year": "",
            "education": {
                "undergrad": "1995-1999 北京大学 计算机科学",
                "master": "",
                "phd": ""
            }
        },
        "likes": "",
        "academic": {
            "research_fields": ["人工智能", "机器学习"],
            "publications": [
                {
                    "title_cn": "深度学习研究",
                    "title_en": "Research on Deep Learning",
                    "year": 2020,
                    "journal": "计算机研究",
                    "DOI": "10.1234/dl2020"
                },
                {
                    "title_cn": "机器学习应用",
                    "title_en": "Machine Learning Applications",
                    "year": 2019,
                    "journal": "计算机科学",
                    "DOI": "10.1234/ml2019"
                },
                {
                    "title_cn": "无DOI论文",
                    "title_en": "Paper Without DOI",
                    "year": 2018,
                    "journal": "信息系统",
                    "DOI": ""
                }
            ]
        }
    }
    
    # AMiner数据示例
    aminer_data = {
        "basic_info": {
            "name": "张三",
            "title": ["副教授", "研究员"],
            "admin_role": "",
            "mentor_qualification": ["硕导", "博导"],
            "honors": ["优秀教师", "杰出人才"]
        },
        "bio_details": {
            "birth_year": "1975",
            "education": {
                "undergrad": "1995-1999 北京大学 计算机科学",
                "master": "1999-2002 清华大学 人工智能",
                "phd": "2002-2005 中国科学院 计算机应用"
            }
        },
        "likes": "56",
        "academic": {
            "research_fields": ["人工智能", "深度学习", "计算机视觉"],
            "publications": [
                {
                    "title_cn": "深度学习研究（修订版）",
                    "title_en": "Research on Deep Learning (Revised)",
                    "year": 2020,
                    "journal": "计算机研究与发展",
                    "DOI": "10.1234/dl2020"
                },
                {
                    "title_cn": "计算机视觉新方法",
                    "title_en": "New Method for Computer Vision",
                    "year": 2021,
                    "journal": "人工智能学报",
                    "DOI": "10.1234/cv2021"
                },
                {
                    "title_cn": "自然语言处理进展",
                    "title_en": "Progress in Natural Language Processing",
                    "year": 2022,
                    "journal": "计算机学报",
                    "DOI": "10.1234/nlp2022"
                },
                {
                    "title_cn": "另一篇无DOI论文",
                    "title_en": "Another Paper Without DOI",
                    "year": 2021,
                    "journal": "软件学报",
                    "DOI": ""
                }
            ]
        }
    }
    
    # 测试合并
    merged_result = merge_data(school_data, aminer_data)
    
    # 打印结果
    import json
    print(json.dumps(merged_result, ensure_ascii=False, indent=2)) 
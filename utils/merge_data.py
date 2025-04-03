#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
教师数据合并模块

该模块负责合并从不同来源（如学校网站和AMiner）获取的教师数据，
处理可能的数据冲突，确保最终结果的准确性和完整性。
"""
from typing import Dict, List, Any
import logging
import re # 导入正则表达式模块

# --- 辅助合并函数 ---

def _get_value(data_dict: Dict, key: str, default: Any = None) -> Any:
    """安全地从字典获取值，处理 None 的情况"""
    return data_dict.get(key, default) if data_dict else default

def _merge_single_field(school_val: Any, aminer_val: Any, default: Any = '') -> Any:
    """合并单个字段，优先使用学校数据，为空时用AMiner补充"""
    # 认为 None 或 空字符串 为空
    if school_val is not None and school_val != '':
        return school_val
    elif aminer_val is not None and aminer_val != '':
        return aminer_val
    else:
        return default

def _merge_list_field(school_list: List, aminer_list: List) -> List:
    """合并列表字段，去重并过滤空字符串"""
    # 确保输入是列表，处理 None 的情况
    s_list = school_list if isinstance(school_list, list) else []
    a_list = aminer_list if isinstance(aminer_list, list) else []

    # 合并并去重，同时过滤掉空字符串
    merged_set = set(item for item in s_list if item)
    merged_set.update(item for item in a_list if item)

    return sorted(list(merged_set)) # 返回排序后的列表

# --- 主要合并逻辑 ---

def merge_data(school_data: Dict, aminer_data: Dict) -> Dict:
    """
    合并来自学校网站和AMiner的教师数据 (优化版)

    参数:
        school_data: 从学校网站获取的教师数据 (可能为 None)
        aminer_data: 从AMiner获取的教师数据 (可能为 None)

    返回:
        Dict: 合并后的教师数据
    """
    # 处理输入可能为 None 的情况
    sd = school_data or {}
    ad = aminer_data or {}

    merged_data = {}

    # 合并基本信息
    merged_data['basic_info'] = merge_basic_info(sd.get('basic_info'), ad.get('basic_info'))

    # 合并生物信息
    merged_data['bio_details'] = merge_bio_details(sd.get('bio_details'), ad.get('bio_details'))

    # 仅使用学校数据，因为只有学校网页有
    merged_data['likes'] = sd.get('likes', 0)  # 默认给 0
    # 合并学术信息
    merged_data['academic'] = merge_academic(sd.get('academic'), ad.get('academic'))

    # 合并数据来源 (总是包含两者，如果存在的话)
    merged_data['data_sources'] = {}
    if sd.get('data_sources'):
        merged_data['data_sources'].update(sd['data_sources'])
    if ad.get('data_sources'):
        merged_data['data_sources'].update(ad['data_sources'])

    return merged_data


def merge_basic_info(school_basic: Dict, aminer_basic: Dict) -> Dict:
    """合并基本信息 (优化版)"""
    sb = school_basic or {}
    ab = aminer_basic or {}
    merged_basic = {}

    # 使用辅助函数合并单个字段
    merged_basic['name'] = _merge_single_field(sb.get('name'), ab.get('name'))
    merged_basic['admin_role'] = _merge_single_field(sb.get('admin_role'), ab.get('admin_role'))

    # 使用辅助函数合并列表字段
    merged_basic['title'] = _merge_list_field(sb.get('title'), ab.get('title'))
    merged_basic['mentor_qualification'] = _merge_list_field(sb.get('mentor_qualification'), ab.get('mentor_qualification'))
    merged_basic['honors'] = _merge_list_field(sb.get('honors'), ab.get('honors'))

    return merged_basic


def merge_bio_details(school_bio: Dict, aminer_bio: Dict) -> Dict:
    """合并生物信息 (优化版)"""
    sb = school_bio or {}
    ab = aminer_bio or {}
    merged_bio = {}

    merged_bio['birth_year'] = _merge_single_field(sb.get('birth_year'), ab.get('birth_year'))

    # 合并教育经历 (保持逐字段补充逻辑)
    merged_bio['education'] = merge_education(sb.get('education'), ab.get('education'))

    # 合并工作经历
    merged_bio['work_experience'] = merge_work_experience(
        sb.get('work_experience'),
        ab.get('work_experience')
    )

    return merged_bio

def merge_education(school_edu: Dict, aminer_edu: Dict) -> Dict:
    """合并教育经历，优先学校，为空时补充"""
    se = school_edu or {}
    ae = aminer_edu or {}
    merged_edu = {}

    merged_edu['undergrad'] = _merge_single_field(se.get('undergrad'), ae.get('undergrad'))
    merged_edu['master'] = _merge_single_field(se.get('master'), ae.get('master'))
    merged_edu['phd'] = _merge_single_field(se.get('phd'), ae.get('phd'))

    # 如果所有字段都为空，则返回空字典，否则返回合并结果
    return merged_edu if any(merged_edu.values()) else {}


def _extract_year(experience_str: str) -> int:
    """从工作经历字符串中提取起始年份用于排序"""
    if not isinstance(experience_str, str):
        return 9999 # 非字符串排最后
    # 匹配 YYYY 或 YYYY年
    match = re.search(r'^(\d{4})', experience_str)
    if match:
        return int(match.group(1))
    # 匹配 YYYY.MM
    match = re.search(r'^(\d{4})\.', experience_str)
    if match:
        return int(match.group(1))
    return 9999 # 无法解析年份的排在后面

def merge_work_experience(school_experience: List, aminer_experience: List) -> List:
    """合并工作经历信息 (优化版)"""
    # 使用辅助函数合并列表并去重过滤空值
    merged_list = _merge_list_field(school_experience, aminer_experience)

    # 按提取的年份排序
    try:
        # 对于无法解析年份的条目，让它们保持原有相对顺序或排在最后
        merged_list.sort(key=_extract_year)
    except Exception as e:
        logging.warning(f"工作经历排序时出现错误: {e}. 列表可能未完全排序.")

    return merged_list


def merge_academic(school_academic: Dict, aminer_academic: Dict) -> Dict:
    """合并学术信息, AMiner数据优先 (优化版)"""
    sa = school_academic or {}
    aa = aminer_academic or {}
    merged_academic = {}

    # 研究领域：合并去重
    merged_academic['research_fields'] = _merge_list_field(
        sa.get('research_fields'),
        aa.get('research_fields')
    )

    # 出版物：优先AMiner，基于DOI或标题+年份去重
    merged_academic['publications'] = merge_publications(
        sa.get('publications'),
        aa.get('publications')
    )

    return merged_academic

def merge_publications(school_pubs: List, aminer_pubs: List) -> List:
    """合并出版物列表，优先AMiner，基于DOI或标题+年份去重 (优化版)"""
    sp = school_pubs if isinstance(school_pubs, list) else []
    ap = aminer_pubs if isinstance(aminer_pubs, list) else []

    merged_pubs_dict = {}

    # 优先处理AMiner的出版物
    for pub in ap:
        if not isinstance(pub, dict):
            logging.debug(f"跳过格式错误的AMiner出版物条目: {type(pub)} - {pub}")
            continue
        # 使用 DOI 或 标题+年份 作为键
        key = pub.get('DOI') or f"{pub.get('title_en', pub.get('title_cn', 'NoTitle'))}_{pub.get('year', 'NoYear')}"
        # 简单的规范化键，去除空白符
        key = "".join(str(key).split()).lower()
        if key not in merged_pubs_dict:
             # 检查数据有效性
             if pub.get('title_en') or pub.get('title_cn') or pub.get('DOI'):
                 merged_pubs_dict[key] = pub

    # 添加学校数据中AMiner没有的出版物
    for pub in sp:
        if not isinstance(pub, dict):
            logging.debug(f"跳过格式错误的学校出版物条目: {type(pub)} - {pub}")
            continue
        key = pub.get('DOI') or f"{pub.get('title_en', pub.get('title_cn', 'NoTitle'))}_{pub.get('year', 'NoYear')}"
        key = "".join(str(key).split()).lower()
        if key not in merged_pubs_dict:
             if pub.get('title_en') or pub.get('title_cn') or pub.get('DOI'):
                 merged_pubs_dict[key] = pub

    # 转为列表并按年份降序排序
    final_pubs = list(merged_pubs_dict.values())
    try:
        # 提取年份进行排序，处理非数字年份
        def get_pub_year(p):
            year = p.get('year')
            if isinstance(year, (int, float)):
                return int(year)
            if isinstance(year, str) and year.isdigit():
                return int(year)
            return 0 # 无法解析年份的排在前面（降序）

        final_pubs.sort(key=get_pub_year, reverse=True)
    except Exception as e:
        logging.warning(f"出版物按年份排序时出现错误: {e}. 列表可能未完全排序.")

    return final_pubs


# --- 测试代码保持不变 (移除之前的函数) ---

# 单元测试代码
if __name__ == "__main__":
    # 学校数据示例
    school_data = {
        "basic_info": {
            "name": "张三",
            "title": [""],
            "admin_role": "",
            "mentor_qualification": ["硕导"],
            "honors": ["优秀教师", ""]
        },
        "bio_details": {
            "birth_year": "",
            "education": {
                "undergrad": "1995-1999 北京大学 计算机科学",
                "master": "",
                "phd": ""
            },
            "work_experience": [
                "2005-2010 浙江大学 讲师",
                "2000-2005 清华大学 助教"
            ]
        },
        "likes": None,
        "academic": {
            "research_fields": ["人工智能", "机器学习", ""],
            "publications": [
                {
                    "title_cn": "深度学习研究",
                    "title_en": "Research on Deep Learning",
                    "year": 2020,
                    "journal": "计算机研究",
                    "DOI": "10.1234/dl2020"
                },
                 {
                    "title_cn": "重复条目",
                    "title_en": "Duplicate Entry",
                    "year": 2021,
                    "journal": "测试期刊",
                    "DOI": "10.dup/test"
                }
            ]
        },
        "data_sources": {"school_url": "http://school.edu/zhangsan"}
    }

    # AMiner数据示例
    aminer_data = {
        "basic_info": {
            "name": "Zhang San", # 不同的名字
            "title": ["副教授"], # 有新增
            "admin_role": "副院长", # 有补充
            "mentor_qualification": ["博导"],
            "honors": ["杰出青年", "优秀教师"] # 有新增和重复
        },
        "bio_details": {
            "birth_year": "1975*", # 有补充
            "education": {
                "undergrad": "", # 学校有，这里没有
                "master": "2000-2003 清华大学 计算机科学", # 有补充
                "phd": "2003-2007 麻省理工学院 AI" # 有补充
            },
            "work_experience": [
                "2010-至今 XX大学 教授", # 新增
                "2005-2010 浙江大学 讲师", # 重复
                None # 无效条目
            ]
        },
        "likes": 100,
        "academic": {
            "research_fields": ["人工智能", "自然语言处理"], # 有新增和重复
            "publications": [
                {
                    "title_cn": "自然语言处理进展",
                    "title_en": "NLP Advances",
                    "year": "2022", # 字符串年份
                    "journal": "AI期刊",
                    "DOI": "10.5678/nlp2022"
                },
                {
                    "title_cn": "深度学习研究",
                    "title_en": "Research on Deep Learning", # 无DOI，但标题年份与学校重复
                    "year": 2020,
                    "journal": "IEEE TPAMI"
                },
                 {
                    "title_cn": "重复条目",
                    "title_en": "Duplicate Entry", # DOI与学校重复
                    "year": 2021,
                    "journal": "AMiner期刊",
                    "DOI": "10.dup/test"
                },
                "Invalid Pub Entry" # 无效条目
            ]
        },
        "data_sources": {"aminer_url": "http://aminer.org/zhangsan"}
    }

    merged_result = merge_data(school_data, aminer_data)
    import json
    print(json.dumps(merged_result, ensure_ascii=False, indent=2))

    print("\n--- 测试 None 输入 ---")
    merged_none_school = merge_data(None, aminer_data)
    print(json.dumps(merged_none_school, ensure_ascii=False, indent=2))

    merged_none_aminer = merge_data(school_data, None)
    print(json.dumps(merged_none_aminer, ensure_ascii=False, indent=2))

    merged_both_none = merge_data(None, None)
    print(json.dumps(merged_both_none, ensure_ascii=False, indent=2))

    print("\n--- 测试空字典输入 ---")
    merged_empty_dicts = merge_data({}, {})
    print(json.dumps(merged_empty_dicts, ensure_ascii=False, indent=2))
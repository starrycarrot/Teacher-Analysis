import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import certifi

class NJUScraper:
    def __init__(self, school_name: str):
        """初始化爬虫"""
        self.school_name = school_name
        # 设置证书路径
        self.cert_path = certifi.where()
        # 添加请求头模拟浏览器
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
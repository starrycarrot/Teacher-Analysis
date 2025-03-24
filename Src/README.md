# 教师信息分析系统

## 项目简介
教师信息分析系统是一个用于从高校教师门户网站和学术平台（如AMiner）收集、整合和分析教师信息的工具。该系统通过爬虫技术获取教师的基本信息、研究成果和学术影响力等数据，并将其结构化为统一的JSON格式。

## 系统架构

### 目录结构
```
Src/
├── main.py             # 主程序入口
├── config/             # 配置文件目录
├── scrapers/           # 爬虫模块
│   ├── shool_get_links.py  # 学校教师列表爬虫
│   ├── smart_scraper.py    # 通用智能爬虫
│   └── aminer_search.py    # AMiner搜索和爬虫
└── utils/              # 工具函数
    ├── check_data_quality.py  # 数据质量检查
    └── merge_data.py          # 数据合并工具
```

## 模块功能

### 1. 主模块 (main.py)
- 系统的入口点，负责协调各个模块的工作流程
- 包含两个主要函数：
  - `process_single_teacher`: 处理单个教师的信息采集、质量评估和数据合并
  - `process_all_teachers`: 处理整个学校的所有教师数据

### 2. 爬虫模块 (scrapers/)

#### 2.1 学校教师列表爬虫 (shool_get_links.py)
- `SchoolScraper` 类：负责从学校教师门户网站获取所有教师的个人主页链接
- 使用BeautifulSoup和requests库处理HTML内容
- 自动处理分页，支持不同学校门户网站的配置
- 适用于静态网页或结构简单的网站
- 低资源消耗，适合批量快速爬取

#### 2.2 通用智能爬虫 (smart_scraper.py)
- `scrape_profile` 函数：使用SmartScraperGraph爬取教师个人主页的详细信息
- 采用AI驱动的爬虫技术，能够适应不同结构的网页
- 使用统一的cookie存储路径 (aminer_cookies.json) 保持会话状态

#### 2.3 AMiner搜索和爬虫 (aminer_search.py)
- `LoginManager` 类：处理AMiner的登录流程，包括扫码登录、cookie管理等
- `search_teacher` 函数：在AMiner平台搜索教师，并返回其个人主页URL
- 特性：
  - 高效的页面加载策略：使用 "domcontentloaded" 事件而非 "networkidle"，避免页面加载超时
  - 智能 cookie 管理：自动保存和加载登录状态，减少重复登录
  - 性能优化：
    - 使用 JavaScript 执行部分搜索逻辑，提高匹配效率
    - 支持无头模式运行，显著提高爬取速度
    - 可选的资源优化（禁用图片和CSS加载）
  - 灵活的机构匹配：支持通过机构映射配置文件处理不同表达方式的机构名称
  - 返回完整URL：确保返回可直接访问的完整AMiner个人主页URL

### 3. 工具模块 (utils/)

#### 3.1 数据质量检查 (check_data_quality.py)
- `check_data` 函数：评估从学校网站获取的数据质量是否满足要求
- 通过检查关键字段的完整性，决定是否需要从AMiner平台获取补充数据
- 具体检查以下字段是否存在且非空：
  - 基本信息：姓名、职称、导师资格、荣誉头衔
  - 生物信息：出生年份、教育背景（本科、硕士、博士）
  - 其他信息：点赞数

#### 3.2 数据合并 (merge_data.py)
- `merge_data` 函数：合并从学校网站和AMiner获取的数据
- 处理数据冲突，确保最终结果的准确性和完整性
- 具体合并策略包括：
  - 基本信息合并：保留学校数据，补充缺失字段
  - 学术职称和资格：两个来源的数据合并去重
  - 教育经历：优先使用学校数据，缺失时补充AMiner数据
  - 研究领域：合并去重，保留所有研究方向
  - 论文出版物：仅使用DOI去重，优先保留AMiner数据，不处理无DOI的论文
  - 点赞数：学校数据为空时使用AMiner数据

## 程序流程

1. **初始阶段**：
   - 系统从指定的学校教师门户网站开始，获取所有教师的个人主页链接

2. **数据采集阶段**：
   - 对每个教师的个人主页进行爬取，获取基本信息（姓名、职称、研究方向等）
   - 使用智能爬虫技术适应不同结构的网页

3. **数据质量评估**：
   - 评估学校网站获取的数据质量是否满足要求
   - 若数据质量合格，则直接使用学校数据
   - 若数据质量不合格，则进入补充数据阶段

4. **补充数据阶段**：
   - 在AMiner学术平台搜索教师
   - 爬取AMiner上的教师个人主页，获取更多学术信息
   - 合并学校数据和AMiner数据，得到完整信息

5. **数据存储阶段**：
   - 将最终处理的数据存储为JSON格式文件

## 使用方法

1. 设置学校网站URL和学校名称：
```python
school_name = "南京信息工程大学"
output_dir = "NUIST_teacher_data"
```

2. 运行主程序：
```python
python -m Src.main
```

3. 数据将保存在指定的输出目录中，每个教师对应一个JSON文件

4. 单独使用AMiner搜索模块：
```python
from Src.scrapers.aminer_search import search_teacher

# 默认有头模式，方便调试
profile_url = search_teacher("教师姓名", "学校名称", headless=False)
print(f"找到的URL: {profile_url}")

# 使用无头模式提高速度
profile_url = search_teacher("教师姓名", "学校名称", headless=True)
```

## 数据格式

系统生成的JSON数据包含以下主要字段：
- `basic_info`: 教师基本信息（姓名、职称、学历等）
- `research`: 研究方向和领域
- `publications`: 发表的论文和著作

## 配置文件

### org_mapping.json
机构名称映射配置，用于处理同一机构的不同表达方式：
```json
{
  "南京信息工程大学": ["南京信息工程大学", "NUIST", "Nanjing University of Information Science and Technology"]
}
```

### aminer_cookies.json
AMiner平台的cookies文件，用于保持登录状态，避免重复登录。系统会自动管理此文件：
- 首次运行时需要手动扫码登录
- 后续运行时自动复用已有cookies
- cookies失效时会提示重新登录

## 依赖库
- playwright: 用于浏览器自动化和网页交互（AMiner搜索模块）
- scrapegraphai: 用于智能爬虫
- requests: 用于HTTP请求
- beautifulsoup4: 用于HTML解析
- certifi: 用于SSL证书验证

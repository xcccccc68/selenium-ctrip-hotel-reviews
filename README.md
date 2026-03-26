# 携程酒店爬虫项目

## 项目介绍

本项目是一个用于爬取携程酒店信息和评论的爬虫系统，支持：
- 爬取指定城市、酒店类型和星级的酒店列表
- 爬取酒店的详细评论信息
- 自动处理登录、滚动加载和翻页
- 生成结构化的CSV数据文件

## 项目结构

```
携程/
├── config.py          # 配置文件
├── get_hotels.py      # 酒店列表爬虫
├── get_comments.py    # 酒店评论爬虫
├── hotel_lists/       # 酒店列表存储目录
├── hotel_comments/    # 评论数据存储目录
└── README.md          # 项目说明文档
```

## 环境要求

- Python 3.6+
- Chrome 浏览器
- ChromeDriver（与Chrome版本匹配）

## 依赖安装

```bash
# 安装所需依赖
pip install selenium beautifulsoup4 pandas fake_useragent lxml
```

## 配置说明

### ChromeDriver配置

1. 下载与您的Chrome浏览器版本匹配的ChromeDriver
2. 在 `config.py` 文件中修改 `CHROME_DRIVER_PATH` 为您的ChromeDriver路径：

```python
CHROME_DRIVER_PATH = r"C:\Users\Surface\Desktop\chromedriver-win64\chromedriver.exe"
```

### 城市配置

在 `config.py` 文件的 `CITIES` 字典中添加或修改城市信息：

```python
CITIES = {
    "上海": {
        "cityId": 2,
        "provinceId": 2,
        "cityName": "上海",
        "destName": "上海"
    },
    "北京": {
        "cityId": 1,
        "provinceId": 1,
        "cityName": "北京",
        "destName": "北京"
    },
    # 可添加其他城市
}
```

### 城市英文名映射

在 `config.py` 文件的 `city_en_name_map` 字典中添加或修改城市英文名：

```python
city_en_name_map = {
    "上海": "Shanghai",
    "北京": "Beijing",
    "天津": "Tianjin",
    "重庆": "Chongqing"
    # 可添加其他城市
}
```

### 爬虫配置

在 `config.py` 文件的 `CRAWLER_CONFIG` 字典中修改爬虫配置：

```python
CRAWLER_CONFIG = {
    "max_scrolls": 10,  # 最大滚动次数
    "max_pages": 20,  # 最大翻页次数
    "headless": False,  # 是否无头模式运行
    "input_file": "hotels_list.csv",  # 默认输入文件名
    "output_file": "hotel_comments.csv",  # 默认输出文件名
    "hotels_output_file": "hotels_list.csv"  # 酒店列表输出文件名
}
```

### 反爬策略配置

在 `config.py` 文件的 `ANTI_CRAWL_CONFIG` 字典中修改反爬策略：

```python
ANTI_CRAWL_CONFIG = {
    "page_load_wait": (2, 5),  # 页面加载后等待时间范围(秒)
    "scroll_wait": (2, 4),  # 滚动后等待时间范围(秒)
    "click_wait": (2, 4),  # 点击后等待时间范围(秒)
    "page_wait": (2, 4),  # 页面处理等待时间范围(秒)
    "next_page_wait": (1, 5),  # 翻页后等待时间范围(秒)
    "hotel_wait": (5, 10),  # 处理完酒店后等待时间范围(秒)
    "error_wait": (3, 6),  # 出错后等待时间范围(秒)
    "scroll_distance": (800, 1200),  # 随机滚动距离范围
    "scroll_pause": 8  # 滚动后暂停时间(秒)
}
```

## 使用方法

### 1. 爬取酒店列表

1. 打开 `get_hotels.py` 文件，修改使用示例中的配置参数：

```python
# 配置参数
city_name = "天津"
hotel_type = "酒店"
star_rating = "五星级"
```

2. 运行 `get_hotels.py`：

```bash
python get_hotels.py
```

3. 在弹出的浏览器中完成登录操作，然后在终端中按下回车键继续。

4. 爬虫会自动滚动页面，获取酒店列表信息，并将数据保存到 `hotel_lists/` 目录下，文件名为 `{城市}_{酒店类型}{星级}.csv`，例如 `tianjin_jiudian_5.csv`。

### 2. 爬取酒店评论

1. 打开 `get_comments.py` 文件，修改使用示例中的配置参数（与上面保持一致）：

```python
# 配置参数
city_name = "天津"
hotel_type = "酒店"
star_rating = "五星级"
```

2. 运行 `get_comments.py`：

```bash
python get_comments.py
```

3. 爬虫会自动读取 `hotel_lists/` 目录下的酒店列表文件，然后逐个访问酒店详情页，获取评论信息，并将数据保存到 `hotel_comments/` 目录下，文件名为 `{城市}_{酒店类型}{星级}_comments.csv`，例如 `tianjin_jiudian_5_comments.csv`。

## 输出文件说明

### 酒店列表文件（hotel_lists/）

包含以下字段：
- hotel_id: 酒店ID
- hotel_name: 酒店名称
- price: 价格
- rating: 评分
- comment_count: 评论数量
- address: 地址
- hotel_url: 酒店链接
- crawl_time: 爬取时间

### 评论文件（hotel_comments/）

包含以下字段：
- hotel_id: 酒店ID
- hotel_name: 酒店名称
- content: 评论内容
- rating: 评分
- date: 评论日期
- user: 用户信息
- crawl_time: 爬取时间

## 注意事项

1. **登录要求**：爬取酒店列表时需要登录携程账号，请确保您有可用的携程账号。
2. **反爬措施**：本爬虫已实现基本的反爬措施，包括随机等待时间、滚动操作等，但请合理控制爬取频率，避免被封禁。
3. **ChromeDriver版本**：请确保ChromeDriver版本与您的Chrome浏览器版本匹配，否则可能会出现兼容性问题。
4. **城市ID**：添加新城市时，需要正确填写城市的 `cityId` 和 `provinceId`，这些ID可以从携程网站的URL中获取。
5. **文件路径**：请确保 `hotel_lists/` 和 `hotel_comments/` 目录存在，爬虫会自动在这些目录中生成文件。

## 常见问题

### 1. 登录失败
- 确保您的携程账号可以正常登录
- 确保网络连接正常
- 尝试手动登录后再运行爬虫

### 2. 酒店信息提取失败
- 可能是页面结构发生了变化，请检查 `_extract_hotel_info` 方法中的选择器是否正确
- 可能是反爬机制导致页面加载失败，请尝试增加等待时间

### 3. 评论提取失败
- 可能是页面结构发生了变化，请检查 `_extract_comments` 方法中的选择器是否正确
- 可能是评论页面需要登录，请确保您已登录携程账号

### 4. 被反爬机制封禁
- 减少爬取频率
- 增加等待时间
- 更换IP地址
- 更换用户代理

## 许可证

本项目仅供学习和研究使用，请勿用于商业用途。

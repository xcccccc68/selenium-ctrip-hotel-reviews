# 爬虫配置文件

# ChromeDriver路径
CHROME_DRIVER_PATH = r"C:\Users\Surface\Desktop\chromedriver-win64\chromedriver.exe"

# 城市配置
CITIES = {
    "上海": {
        "cityId": 2,
        "cityName": "上海",
        "destName": "上海"
    },
    "北京": {
        "cityId": 1,
        "cityName": "北京",
        "destName": "北京"
    },
    "天津": {
        "cityId": 3,
        "cityName": "天津",
        "destName": "天津"
    },
    "重庆": {
        "cityId": 4,
        "cityName": "重庆",
        "destName": "重庆"
    },
    "南京": {
        "cityId": 12,
        "cityName": "南京",
        "destName": "南京"
    }
}

# 酒店类型到英文代码的映射
HOTEL_TYPE_CODE_MAP = {
    "酒店": "jiudian",
    "民宿": "minsu"
}

# 城市名称到英文代码的映射（用于文件名）
CITY_CODE_MAP = {
    "上海": "shanghai",
    "北京": "beijing",
    "天津": "tianjin",
    "重庆": "chongqing",
    "南京": "nanjing"
}

# 基础URL
BASE_URL = "https://hotels.ctrip.com"

# 详情页URL模板
DETAIL_URL_TEMPLATE = "{base_url}/hotels/detail/?cityEnName={cityEnName}&cityId={cityId}&hotelId={hotelId}&checkIn={checkin}&checkOut={checkout}&adult=1&children=0&crn=1&ages=&curr=CNY&barcurr=CNY&masterhotelid_tracelogid=100053755-0a714631-492776-78276&detailFilters=30%7C{hotelType}~30~{hotelType}*17%7C1~17~1*80%7C2~80~2*29%7C1~29~1%7C1&hotelType=normal&display=incavg&subStamp=507&isCT=true&isFlexible=F&isFirstEnterDetail=T"

# 日期配置
CHECKIN_DATE = "2026-03-20"
CHECKOUT_DATE = "2026-03-21"

# 爬虫配置
CRAWLER_CONFIG = {
    "max_scrolls": 3,  # 最大滚动次数 ，获取酒店列表时，页面采用无限滚动加载的方式
    "max_pages": 5,  # 最大翻页次数
    "headless": False  # 是否无头模式运行
}

# 反爬策略配置
ANTI_CRAWL_CONFIG = {
    "page_load_wait": (1, 3),  # 页面加载后等待时间范围(秒)
    "scroll_wait": (1, 2),  # 滚动后等待时间范围(秒)
    "click_wait": (1, 2),  # 点击后等待时间范围(秒)
    "page_wait": (1, 2),  # 页面处理等待时间范围(秒)
    "next_page_wait": (1, 3),  # 翻页后等待时间范围(秒)
    "hotel_wait": (2, 5),  # 处理完酒店后等待时间范围(秒)
    "error_wait": (1, 3),  # 出错后等待时间范围(秒)
    "scroll_distance": (800, 1200),  # 随机滚动距离范围
    "scroll_pause": 4  # 滚动后暂停时间(秒)
}

# 浏览器配置
BROWSER_CONFIG = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 构建详情页URL的函数
def build_detail_url(hotel_id, city_name, hotel_type):
    """
    构建详情页URL
    Args:
        hotel_id: 酒店ID
        city_name: 城市名称
        hotel_type: 酒店类型（酒店/民宿）
    Returns:
        完整的详情页URL
    """
    city_info = CITIES.get(city_name, CITIES["上海"])
    
    # 城市英文名映射
    city_en_name_map = {
        "上海": "Shanghai",
        "北京": "Beijing",
        "天津": "Tianjin",
        "重庆": "Chongqing",
        "南京": "Nanjing"
    }
    city_en_name = city_en_name_map.get(city_name, "Shanghai")
    
    # 构建URL
    url = DETAIL_URL_TEMPLATE.format(
        base_url=BASE_URL,
        cityEnName=city_en_name,
        cityId=city_info["cityId"],
        hotelId=hotel_id,
        checkin=CHECKIN_DATE,
        checkout=CHECKOUT_DATE,
        hotelType=hotel_type
    )
    
    return url

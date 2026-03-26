import time
import random
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import logging
import config


class HotelListCrawler:
    """酒店列表爬虫，用于获取酒店基本信息"""

    def __init__(self, headless=None, output_file=None, city_name="上海", hotel_type="酒店", star_rating=None):
        """
        初始化爬虫
        Args:
            headless: 是否无头模式运行（默认使用配置文件中的设置）
            output_file: 输出CSV文件名（默认使用配置文件中的设置）
            city_name: 城市名称
            hotel_type: 酒店类型
            star_rating: 星级
        """
        self.ua = UserAgent()
        self.headless = headless if headless is not None else config.CRAWLER_CONFIG["headless"]
        
        # 根据城市、酒店类型和星级生成输出文件名
        if output_file:
            self.output_file = output_file
        else:
            # 生成文件名
            # 使用config.py中的映射关系
            city_code = config.CITY_CODE_MAP.get(city_name, city_name.lower())
            hotel_type_code = config.HOTEL_TYPE_CODE_MAP.get(hotel_type, hotel_type.lower())
            # 处理星级数字
            star_code = ""
            if star_rating:
                # 直接使用星级数字
                star_code = f"_{star_rating}"
            filename = f"{city_code}_{hotel_type_code}{star_code}.csv"
            self.output_file = f"./携程/hotel_lists/{filename}"
        
        self.driver = self._init_driver(self.headless)
        self.hotel_data = []  # 存储所有酒店数据
        self.wait_time = config.ANTI_CRAWL_CONFIG["page_load_wait"]  # 随机等待时间范围(秒)

    def _init_driver(self, headless):
        """初始化浏览器驱动"""
        options = webdriver.ChromeOptions()

        # 反检测配置
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        if headless:
            options.add_argument('--headless')

        # 使用固定的PC端User-Agent
        pc_user_agent = config.BROWSER_CONFIG["user_agent"]
        options.add_argument(f'user-agent={pc_user_agent}')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        service = Service(config.CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)

        # 执行反检测脚本
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })

        return driver

    def _random_wait(self):
        """随机等待，模拟人类行为"""
        wait_time = random.uniform(*self.wait_time)
        time.sleep(wait_time)

    def _extract_hotel_info(self, card):
        """
        从酒店卡片中提取基本信息
        Args:
            card: 酒店卡片元素
        Returns:
            hotel_info: 酒店信息字典
        """
        try:
            # 提取酒店ID
            hotel_id = card.get('id', '')

            # 提取酒店名称
            hotel_name = ""
            name_elem = card.find('span', class_='hotelName')
            if not name_elem:
                name_elem = card.find('h3', class_=lambda x: x and 'name' in x.lower())
            if name_elem:
                hotel_name = name_elem.get_text(strip=True)

            # 提取评分
            rating = None
            rating_elem = card.find('span', class_='score')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                try:
                    rating = float(rating_text)
                except ValueError:
                    pass

            # 提取评论数
            comment_count = None
            comment_elem = card.find('span', class_='comment-num')
            if comment_elem:
                comment_text = comment_elem.get_text(strip=True)
                match = re.search(r'(\d+)', comment_text)
                if match:
                    comment_count = int(match.group(1))

            # 提取价格
            price = None
            price_elem = card.find('span', class_='price')
            if not price_elem:
                price_elem = card.find('span', class_=lambda x: x and 'price' in x.lower())
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                match = re.search(r'¥?\s*(\d+)', price_text)
                if match:
                    price = int(match.group(1))

            # 提取地址
            address = None
            address_elem = card.find('span', class_='position-desc')
            if address_elem:
                address = address_elem.get_text(strip=True)

            # 提取酒店链接
            hotel_url = ""
            links = card.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if '/hotel/' in href:
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            href = 'https://hotels.ctrip.com' + href
                        else:
                            href = 'https://hotels.ctrip.com/' + href
                    hotel_url = href
                    break

            hotel_info = {
                'hotel_id': hotel_id,
                'hotel_name': hotel_name,
                'rating': rating,
                'comment_count': comment_count,
                'price': price,
                'address': address,
                'hotel_url': hotel_url,
                'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            return hotel_info

        except Exception as e:
            logging.error(f"提取酒店信息失败: {e}")
            return None

    def crawl_hotels(self, city_name, hotel_type, star_rating, max_scrolls=None):
        """
        爬取酒店列表
        Args:
            city_name: 城市名称
            hotel_type: 酒店类型
            star_rating: 星级
            max_scrolls: 最大滚动次数（默认使用配置文件中的设置）
        """
        logging.info(f"开始爬取酒店列表...")

        # 打开基础URL
        base_url = "https://hotels.ctrip.com/"
        logging.info(f"打开基础URL: {base_url}")
        self.driver.get(base_url)
        self._random_wait()

        # 等待用户登录
        logging.info("请在浏览器中完成登录操作...")
        logging.info("登录完成后，请在终端中按下回车键继续...")
        input("按下回车键继续...")

        # 等待页面加载完成
        time.sleep(5)

        # 点击目的地输入框
        try:
            logging.info("点击目的地输入框...")
            destination_input = self.driver.find_element(By.ID, "destinationInput")
            destination_input.click()
            self._random_wait()
        except Exception as e:
            logging.error(f"点击目的地输入框失败: {e}")
            return

        # 输入城市名称
        try:
            logging.info(f"输入城市: {city_name}")
            destination_input = self.driver.find_element(By.ID, "destinationInput")
            destination_input.clear()
            destination_input.send_keys(city_name)
            self._random_wait()
        except Exception as e:
            logging.error(f"输入城市失败: {e}")
            return

        # 点击第二个输入框（位置/品牌/酒店）
        try:
            logging.info("点击位置/品牌/酒店输入框...")
            # 找到第二个输入框，使用class选择器
            second_input = self.driver.find_element(By.CLASS_NAME, "keyword-inputBox_input__o9j9q")
            second_input.click()
            self._random_wait()
        except Exception as e:
            logging.error(f"点击第二个输入框失败: {e}")
            return

        # 在第二个输入框中输入酒店类型
        try:
            logging.info(f"输入酒店类型: {hotel_type}")
            second_input = self.driver.find_element(By.CLASS_NAME, "keyword-inputBox_input__o9j9q")
            second_input.clear()
            second_input.send_keys(hotel_type)
            self._random_wait()
        except Exception as e:
            logging.error(f"输入酒店类型失败: {e}")
            return

        # 点击搜索按钮
        try:
            logging.info("点击搜索按钮...")
            search_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'tripui-online-btn') and contains(@class, 'tripui-online-btn-solid-primary')]")
            search_button.click()
            logging.info("点击了搜索按钮")
            self._random_wait()
        except Exception as e:
            logging.error(f"点击搜索按钮失败: {e}")
            return

        # 等待搜索结果页面加载
        time.sleep(5)

        # 选择星级
        try:
            logging.info(f"选择星级: {star_rating}星")
            # 根据星级选择对应的元素
            star_mapping = {
                "2": "2钻/星及以下|经济",
                "3": "3钻/星|舒适",
                "4": "4钻/星|高档",
                "5": "5钻/星|豪华"
            }
            star_text = star_mapping.get(star_rating, "3钻/星|舒适")
            star_element = self.driver.find_element(By.XPATH, f"//label[contains(text(), '{star_text}')]/parent::div")
            star_element.click()
            logging.info(f"选择了 {star_text}")
            self._random_wait()
        except Exception as e:
            logging.error(f"选择星级失败: {e}")
            return

        # 等待筛选结果加载
        time.sleep(3)

        # 存储已处理的酒店ID，避免重复
        processed_ids = set()

        # 使用配置文件中的最大滚动次数
        actual_max_scrolls = max_scrolls if max_scrolls is not None else config.CRAWLER_CONFIG["max_scrolls"]

        # 执行无限滚动
        for scroll_count in range(actual_max_scrolls):
            try:
                logging.info(f"第 {scroll_count + 1} 次滚动...")
                
                # 记录当前页面高度
                initial_height = self.driver.execute_script("return document.body.scrollHeight")
                logging.info(f"当前页面高度: {initial_height}")

                # 滚动页面到底部
                logging.info("滚动到页面底部...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(config.ANTI_CRAWL_CONFIG["scroll_pause"])  # 等待加载

                # 检查页面高度是否变化
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                logging.info(f"滚动后页面高度: {new_height}")

                # 获取当前页面内容
                soup = BeautifulSoup(self.driver.page_source, 'lxml')

                # 输出页面标题和部分内容，确认页面结构
                title = soup.find('title')
                if title:
                    logging.info(f"页面标题: {title.get_text(strip=True)}")

                # 查找酒店卡片元素
                hotel_cards = soup.find_all('div', class_='hotel-card')
                logging.info(f"找到 {len(hotel_cards)} 个酒店卡片")

                # 处理每个酒店卡片
                for card in hotel_cards:
                    try:
                        # 提取酒店信息
                        hotel_info = self._extract_hotel_info(card)

                        if hotel_info and hotel_info['hotel_id'] not in processed_ids:
                            # 标记为已处理
                            processed_ids.add(hotel_info['hotel_id'])
                            
                            # 添加到数据列表
                            self.hotel_data.append(hotel_info)
                            logging.info(f"成功采集: {hotel_info.get('hotel_name')} - ID: {hotel_info.get('hotel_id')}")

                    except Exception as e:
                        logging.error(f"处理酒店卡片失败: {e}")
                        continue

                # 每处理完一次滚动，保存一次数据
                if (scroll_count + 1) % 3 == 0:
                    self.save_to_csv()
                    logging.info(f"已处理 {scroll_count + 1} 次滚动，当前共采集 {len(self.hotel_data)} 家酒店")

                # 休息一下，避免被封
                wait_time = random.uniform(*config.ANTI_CRAWL_CONFIG["hotel_wait"])
                logging.info(f"滚动后等待 {wait_time:.2f} 秒...")
                time.sleep(wait_time)

            except Exception as e:
                logging.error(f"滚动失败: {e}")
                # 出错后等待
                wait_time = random.uniform(*config.ANTI_CRAWL_CONFIG["error_wait"])
                logging.info(f"出错后等待 {wait_time:.2f} 秒...")
                time.sleep(wait_time)
                continue

        # 最终保存
        self.save_to_csv()
        logging.info(f"酒店列表爬取完成！共采集 {len(self.hotel_data)} 家酒店")

    def save_to_csv(self):
        """保存数据到CSV文件"""
        try:
            if not self.hotel_data:
                logging.warning("没有数据需要保存")
                return

            # 创建DataFrame
            df = pd.DataFrame(self.hotel_data)

            # 重新排列列顺序
            columns = [
                'hotel_id', 'hotel_name', 'price', 'rating', 'comment_count',
                'address', 'hotel_url', 'crawl_time'
            ]
            # 确保所有列都存在
            for col in columns:
                if col not in df.columns:
                    df[col] = None
            df = df[columns]

            # 保存到CSV
            df.to_csv(self.output_file, index=False, encoding='utf-8-sig')

            logging.info(f"数据已保存到 {self.output_file}")

            # 打印统计信息
            logging.info(f"CSV文件统计:")
            logging.info(f"- 总酒店数: {len(df)}")
            logging.info(f"- 有价格信息: {df['price'].notna().sum()} 家")
            logging.info(f"- 有评分信息: {df['rating'].notna().sum()} 家")
            if df['price'].notna().sum() > 0:
                logging.info(f"- 平均价格: ¥{df['price'].mean():.2f}")

        except Exception as e:
            logging.error(f"保存CSV失败: {e}")

    def close(self):
        """关闭爬虫，释放资源"""
        if self.driver:
            self.driver.quit()


# 使用示例
if __name__ == '__main__':
    # 配置参数（只使用中文）
    city_name = "天津"  # 城市中文名称
    hotel_type = "民宿"  # 酒店类型中文名称
    star_rating = "4"  # 星级数字
    
    # 创建爬虫实例（传递参数以生成正确的文件名）
    crawler = HotelListCrawler(
        city_name=city_name,
        hotel_type=hotel_type,
        star_rating=star_rating
    )

    try:
        logging.info(f"输出文件: {crawler.output_file}")

        crawler.crawl_hotels(
            city_name=city_name,
            hotel_type=hotel_type,
            star_rating=star_rating
        )
    finally:
        crawler.close()
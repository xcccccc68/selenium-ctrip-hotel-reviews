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


class HotelCommentCrawler:
    """酒店评论爬虫，用于获取酒店评论信息"""

    def __init__(self, headless=None, input_file=None, output_file=None, city_name="上海", hotel_type="酒店", star_rating=None):
        """
        初始化爬虫
        Args:
            headless: 是否无头模式运行（默认使用配置文件中的设置）
            input_file: 输入CSV文件名（默认使用配置文件中的设置）
            output_file: 输出CSV文件名（默认使用配置文件中的设置）
            city_name: 城市名称
            hotel_type: 酒店类型
            star_rating: 星级
        """
        self.ua = UserAgent()
        self.headless = headless if headless is not None else config.CRAWLER_CONFIG["headless"]
        self.input_file = input_file if input_file else config.CRAWLER_CONFIG["input_file"]
        
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
            filename = f"{city_code}_{hotel_type_code}{star_code}_comments.csv"
            self.output_file = f"./hotel_comments/{filename}"
        
        self.driver = self._init_driver(self.headless)
        self.comment_data = []  # 存储所有评论数据
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

    def _extract_comments(self, soup, hotel_id, hotel_name):
        """
        提取酒店评论
        Args:
            soup: BeautifulSoup对象
            hotel_id: 酒店ID
            hotel_name: 酒店名称
        Returns:
            comments: 评论列表
        """
        comments = []
        try:
            # 查找评论容器（根据实际HTML结构）
            comment_elements = soup.find_all('div', class_='yRvZgc0SICPUbmdb2L2a')
            logging.info(f"找到 {len(comment_elements)} 个评论容器")
            
            for comment_elem in comment_elements:
                # 提取评论内容
                content_elem = comment_elem.find('div', class_='tpHRPkB7n9UV_c7A5t6h')
                if not content_elem:
                    continue
                
                content = content_elem.get_text(strip=True)
                if not content:
                    continue
                
                # 提取评分
                rating = None
                rating_elem = comment_elem.find('strong', class_='xt_R_A70sdDRsOgExJWw')
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    try:
                        rating = float(rating_text)
                    except ValueError:
                        pass
                
                # 提取日期
                date = None
                date_elem = comment_elem.find('div', class_=lambda x: x and 'LPPTO8g2RH0Fk19jYMOQ' in x)
                if date_elem:
                    date = date_elem.get_text(strip=True)
                
                # 提取用户信息
                user = None
                user_elem = comment_elem.find('div', class_='yCIHzFRsP6Tzk7Kia6Qo')
                if user_elem:
                    user = user_elem.get_text(strip=True)
                
                comment = {
                    'hotel_id': hotel_id,
                    'hotel_name': hotel_name,
                    'content': content,
                    'rating': rating,
                    'date': date,
                    'user': user,
                    'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                comments.append(comment)
                logging.info(f"提取评论: {content[:50]}...")
                
                # 不限制评论数量，采集所有可用评论
            
            # 如果没找到，尝试其他可能的评论容器
            if not comments:
                logging.info("尝试其他评论容器...")
                other_comment_elements = soup.find_all('div', class_=lambda x: x and ('comment' in x.lower() or '点评' in x))
                logging.info(f"找到 {len(other_comment_elements)} 个其他评论容器")
                
                for comment_elem in other_comment_elements:
                    # 提取评论内容
                    content_elem = comment_elem.find('div', class_=lambda x: x and ('content' in x.lower() or 'text' in x.lower()))
                    if not content_elem:
                        continue
                    
                    content = content_elem.get_text(strip=True)
                    if not content:
                        continue
                    
                    # 提取评分
                    rating = None
                    rating_elem = comment_elem.find('span', class_=lambda x: x and ('score' in x.lower() or 'rating' in x.lower()))
                    if not rating_elem:
                        rating_elem = comment_elem.find('div', class_=lambda x: x and ('score' in x.lower() or 'rating' in x.lower()))
                    if rating_elem:
                        rating_text = rating_elem.get_text(strip=True)
                        try:
                            rating = float(rating_text)
                        except ValueError:
                            pass
                    
                    # 提取日期
                    date = None
                    date_elem = comment_elem.find('span', class_=lambda x: x and ('date' in x.lower() or 'time' in x.lower()))
                    if date_elem:
                        date = date_elem.get_text(strip=True)
                    
                    # 提取用户信息
                    user = None
                    user_elem = comment_elem.find('span', class_=lambda x: x and ('user' in x.lower() or 'name' in x.lower()))
                    if not user_elem:
                        user_elem = comment_elem.find('div', class_=lambda x: x and ('user' in x.lower() or 'name' in x.lower()))
                    if user_elem:
                        user = user_elem.get_text(strip=True)
                    
                    comment = {
                        'hotel_id': hotel_id,
                        'hotel_name': hotel_name,
                        'content': content,
                        'rating': rating,
                        'date': date,
                        'user': user,
                        'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    comments.append(comment)
                    logging.info(f"提取评论: {content[:50]}...")
                    
                    # 不限制评论数量，采集所有可用评论
                    
        except Exception as e:
            logging.error(f"提取评论失败: {e}")
            import traceback
            logging.error(f"详细错误信息: {traceback.format_exc()}")
        
        return comments

    def _construct_hotel_url(self, hotel_id, city_name="上海", hotel_type="民宿"):
        """
        根据酒店ID构造详情页URL
        Args:
            hotel_id: 酒店ID
            city_name: 城市名称
            hotel_type: 酒店类型
        Returns:
            url: 酒店详情页URL
        """
        # 使用配置文件中的URL构建函数
        url = config.build_detail_url(
            hotel_id=hotel_id,
            city_name=city_name,
            hotel_type=hotel_type
        )
        return url

    def crawl_comments(self):
        """
        爬取酒店评论
        """
        logging.info(f"开始爬取酒店评论...")

        # 读取酒店列表
        try:
            df = pd.read_csv(self.input_file)
            logging.info(f"成功读取酒店列表，共 {len(df)} 家酒店")
        except Exception as e:
            logging.error(f"读取酒店列表失败: {e}")
            return

        if len(df) == 0:
            logging.warning("酒店列表为空")
            return

        # 遍历所有酒店
        for index, row in df.iterrows():
            try:
                hotel_id = row.get('hotel_id', '')
                hotel_name = row.get('hotel_name', '')
                hotel_url = row.get('hotel_url', '')

                if not hotel_id:
                    logging.warning(f"第 {index + 1} 行没有酒店ID，跳过")
                    continue

                logging.info(f"处理第 {index + 1} 家酒店: {hotel_name} - ID: {hotel_id}")

                # 构造酒店详情页URL
                if not isinstance(hotel_url, str) or not hotel_url:
                    hotel_url = self._construct_hotel_url(hotel_id)
                    logging.info(f"构造URL: {hotel_url}")
                else:
                    logging.info(f"使用CSV中的URL: {hotel_url[:50]}...")

                # 访问酒店详情页
                logging.info(f"访问酒店详情页: {hotel_url[:50]}...")
                self.driver.get(hotel_url)
                logging.info("页面加载完成")
                # 随机等待
                wait_time = random.uniform(*config.ANTI_CRAWL_CONFIG["page_load_wait"])
                logging.info(f"页面加载后等待 {wait_time:.2f} 秒...")
                time.sleep(wait_time)

                # 等待页面加载完成
                logging.info("等待页面加载...")
                wait_time = random.uniform(*config.ANTI_CRAWL_CONFIG["page_load_wait"])
                time.sleep(wait_time)

                # 滚动页面，确保所有内容加载（随机滚动距离）
                logging.info("滚动页面...")
                scroll_distance = random.randint(*config.ANTI_CRAWL_CONFIG["scroll_distance"])
                self.driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
                wait_time = random.uniform(*config.ANTI_CRAWL_CONFIG["scroll_wait"])
                logging.info(f"滚动后等待 {wait_time:.2f} 秒...")
                time.sleep(wait_time)

                # 查找并点击"展开更多"按钮
                try:
                    logging.info("查找'展开更多'按钮...")
                    more_buttons = self.driver.find_elements(By.XPATH, "//span[contains(text(), '展开更多')]")
                    logging.info(f"找到 {len(more_buttons)} 个'展开更多'按钮")
                    if more_buttons:
                        more_button = more_buttons[0]
                        logging.info("点击'展开更多'按钮...")
                        self.driver.execute_script("arguments[0].click();", more_button)
                        logging.info("点击了'展开更多'按钮")
                        wait_time = random.uniform(*config.ANTI_CRAWL_CONFIG["click_wait"])
                        logging.info(f"点击后等待 {wait_time:.2f} 秒...")
                        time.sleep(wait_time)
                except Exception as e:
                    logging.warning(f"点击展开更多按钮失败: {e}")
                
                # 点击"差评"评论按钮
                try:
                    logging.info("查找'差评'按钮...")
                    # 查找所有包含"差评"文本的按钮
                    bad_comment_buttons = []
                    
                    # 方法1: 使用XPath查找包含"差评"文本的按钮
                    xpath_buttons = self.driver.find_elements(By.XPATH, "//button[contains(span/text(), '差评')]")
                    bad_comment_buttons.extend(xpath_buttons)
                    logging.info(f"使用XPath找到 {len(xpath_buttons)} 个'差评'按钮")
                    
                    # 方法2: 使用CSS选择器查找按钮，然后过滤出包含"差评"文本的
                    css_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.Y6jbaTqhIt3qdU3xFKfj")
                    for button in css_buttons:
                        try:
                            span = button.find_element(By.TAG_NAME, "span")
                            if "差评" in span.text:
                                bad_comment_buttons.append(button)
                        except:
                            pass
                    logging.info(f"使用CSS选择器并过滤后找到 {len(bad_comment_buttons)} 个'差评'按钮")
                    
                    # 去重
                    unique_buttons = []
                    seen_ids = set()
                    for button in bad_comment_buttons:
                        try:
                            button_id = button.get_attribute('id') or button.location
                            if button_id not in seen_ids:
                                seen_ids.add(button_id)
                                unique_buttons.append(button)
                        except:
                            unique_buttons.append(button)
                    bad_comment_buttons = unique_buttons
                    logging.info(f"去重后找到 {len(bad_comment_buttons)} 个'差评'按钮")
                    
                    if not bad_comment_buttons:
                        logging.warning("没有找到差评按钮，跳过当前酒店")
                        continue
                    
                    # 选择最后一个差评按钮
                    bad_comment_button = bad_comment_buttons[-1]
                    # 确认按钮文本确实包含"差评"
                    try:
                        button_text = bad_comment_button.text
                        if "差评" in button_text:
                            logging.info(f"确认找到差评按钮: {button_text}")
                            logging.info("点击最后一个'差评'按钮...")
                            self.driver.execute_script("arguments[0].click();", bad_comment_button)
                            logging.info("点击了'差评'按钮")
                            wait_time = random.uniform(*config.ANTI_CRAWL_CONFIG["click_wait"])
                            logging.info(f"点击后等待 {wait_time:.2f} 秒...")
                            time.sleep(wait_time)
                        else:
                            logging.warning(f"按钮文本不包含'差评': {button_text}")
                            logging.warning("跳过当前酒店")
                            continue
                    except Exception as e:
                        logging.warning(f"获取按钮文本失败: {e}")
                        # 即使获取文本失败，也尝试点击
                        logging.info("尝试点击最后一个按钮...")
                        self.driver.execute_script("arguments[0].click();", bad_comment_button)
                        logging.info("点击了按钮")
                        wait_time = random.uniform(*config.ANTI_CRAWL_CONFIG["click_wait"])
                        logging.info(f"点击后等待 {wait_time:.2f} 秒...")
                        time.sleep(wait_time)
                except Exception as e:
                    logging.warning(f"点击差评按钮失败: {e}")
                    logging.warning("跳过当前酒店")
                    continue

                # 处理评论翻页
                all_comments = []
                max_pages = config.CRAWLER_CONFIG["max_pages"]  # 最多翻页次数（从配置文件读取）
                seen_comments = set()  # 用于存储已见过的评论内容，检测重复
                
                for page in range(max_pages):
                    # 等待页面加载
                    logging.info(f"处理第 {page+1} 页评论...")
                    wait_time = random.uniform(*config.ANTI_CRAWL_CONFIG["page_wait"])
                    time.sleep(wait_time)
                    
                    # 提取当前页评论
                    logging.info("提取当前页评论...")
                    soup = BeautifulSoup(self.driver.page_source, 'lxml')
                    page_comments = self._extract_comments(soup, hotel_id, hotel_name)
                    
                    # 检测重复评论
                    current_comments = []
                    duplicate_count = 0
                    for comment in page_comments:
                        comment_content = comment['content']
                        if comment_content in seen_comments:
                            duplicate_count += 1
                        else:
                            seen_comments.add(comment_content)
                            current_comments.append(comment)
                    
                    # 如果当前页所有评论都是重复的，结束翻页
                    if duplicate_count == len(page_comments) and page_comments:
                        logging.info(f"当前页所有 {len(page_comments)} 条评论都是重复的，结束翻页")
                        break
                    
                    all_comments.extend(current_comments)
                    logging.info(f"当前页提取 {len(current_comments)} 条新评论，重复 {duplicate_count} 条")
                    
                    # 每处理完一页评论就保存一次数据
                    if current_comments:
                        self.comment_data.extend(current_comments)
                        self.save_to_csv()
                        logging.info(f"已保存第 {page+1} 页评论，当前共采集 {len(self.comment_data)} 条评论")
                    
                    # 查找下一页按钮
                    try:
                        logging.info("查找下一页按钮...")
                        # 使用用户提供的翻页按钮元素
                        next_buttons = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'nF6SWkdU6FLIzjoCbLMF')]//a[contains(@class, 'pQoxbX5l0DdjPttuVUQx')]")
                        logging.info(f"找到 {len(next_buttons)} 个下一页按钮")
                        
                        # 如果没找到，尝试其他可能的翻页按钮
                        if not next_buttons:
                            next_buttons = self.driver.find_elements(By.XPATH, "//a[contains(text(), '>')]")
                            logging.info(f"找到 {len(next_buttons)} 个其他下一页按钮")
                        
                        if next_buttons:
                            next_button = next_buttons[0]
                            # 检查按钮是否可点击
                            if next_button.is_displayed() and next_button.is_enabled():
                                logging.info("点击下一页按钮...")
                                self.driver.execute_script("arguments[0].click();", next_button)
                                logging.info(f"点击了第 {page+1} 页的下一页按钮")
                                # 每翻一页，停留随机时间
                                wait_time = random.uniform(*config.ANTI_CRAWL_CONFIG["next_page_wait"])
                                logging.info(f"翻页后等待 {wait_time:.2f} 秒...")
                                time.sleep(wait_time)
                            else:
                                logging.info("下一页按钮不可点击，结束翻页")
                                break
                        else:
                            logging.info("没有找到下一页按钮，结束翻页")
                            break
                    except Exception as e:
                        logging.warning(f"点击下一页失败: {e}")
                        break

                # 评论已经在每页处理时保存，这里只记录总数量
                if all_comments:
                    logging.info(f"成功采集 {len(all_comments)} 条评论")
                else:
                    logging.warning(f"没有找到评论")

                # 每处理完一个酒店，停留随机时间
                wait_time = random.uniform(*config.ANTI_CRAWL_CONFIG["hotel_wait"])
                logging.info(f"处理完酒店后等待 {wait_time:.2f} 秒...")
                time.sleep(wait_time)

            except Exception as e:
                logging.error(f"处理酒店 {hotel_name} 失败: {e}")
                import traceback
                logging.error(f"详细错误信息: {traceback.format_exc()}")
                # 即使出错，也要等待一段时间再处理下一个酒店
                wait_time = random.uniform(*config.ANTI_CRAWL_CONFIG["error_wait"])
                logging.info(f"处理出错后等待 {wait_time:.2f} 秒...")
                time.sleep(wait_time)
                continue

        # 最终保存
        self.save_to_csv()
        logging.info(f"酒店评论爬取完成！共采集 {len(self.comment_data)} 条评论")

    def save_to_csv(self):
        """保存评论数据到CSV文件"""
        try:
            if not self.comment_data:
                logging.warning("没有评论数据需要保存")
                return

            # 创建DataFrame
            df = pd.DataFrame(self.comment_data)

            # 重新排列列顺序
            columns = [
                'hotel_id', 'hotel_name', 'content', 'rating', 'date',
                'user', 'crawl_time'
            ]
            # 确保所有列都存在
            for col in columns:
                if col not in df.columns:
                    df[col] = None
            df = df[columns]

            # 保存到CSV
            df.to_csv(self.output_file, index=False, encoding='utf-8-sig')

            logging.info(f"评论数据已保存到 {self.output_file}")

            # 打印统计信息
            logging.info(f"CSV文件统计:")
            logging.info(f"- 总评论数: {len(df)}")
            logging.info(f"- 涉及酒店数: {df['hotel_id'].nunique()} 家")
            if df['rating'].notna().sum() > 0:
                logging.info(f"- 平均评分: {df['rating'].mean():.2f}")

        except Exception as e:
            logging.error(f"保存CSV失败: {e}")

    def close(self):
        """关闭爬虫，释放资源"""
        if self.driver:
            self.driver.quit()


# 使用示例
if __name__ == '__main__':
    # 配置参数（只使用中文）
    city_name = "南京"  # 城市中文名称
    hotel_type = "酒店"  # 酒店类型中文名称
    star_rating = "2"  # 星级数字 
    
    # 生成输入文件名（使用config.py中的映射关系）
    city_code = config.CITY_CODE_MAP.get(city_name, city_name.lower())
    hotel_type_code = config.HOTEL_TYPE_CODE_MAP.get(hotel_type, hotel_type.lower())
    star_code = f"_{star_rating}" if star_rating else ""
    input_filename = f"{city_code}_{hotel_type_code}{star_code}.csv"
    input_file = f"./携程/hotel_lists/{input_filename}"
    
    # 创建爬虫实例（传递参数以生成正确的文件名）
    crawler = HotelCommentCrawler(
        input_file=input_file,
        city_name=city_name,  # 传递中文城市名称用于构建URL
        hotel_type=hotel_type,  # 传递中文酒店类型用于构建URL
        star_rating=star_rating  # 传递星级数字
    )

    try:
        logging.info(f"输入文件: {crawler.input_file}")
        logging.info(f"输出文件: {crawler.output_file}")
        crawler.crawl_comments()
    finally:
        crawler.close()

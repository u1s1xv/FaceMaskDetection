#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
口罩图片爬虫脚本
用于爬取戴口罩、未戴口罩和不规范戴口罩的图片
"""

import os
import sys
import requests
import time
import random
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import json
from pathlib import Path
import hashlib

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

# 导入项目路径配置
from yoloserver.utils.paths import CRAWLED_IMAGES_DIR, CRAWLED_ORIGINAL_ANNOTATIONS_DIR

class MaskImageCrawler:
    def __init__(self, base_dir=None):
        """
        初始化爬虫
        :param base_dir: 图片保存的基础目录，如果为None则使用paths.py中定义的路径
        """
        # 使用paths.py中定义的路径
        if base_dir is None:
            self.base_dir = CRAWLED_IMAGES_DIR
        else:
            self.base_dir = Path(base_dir)

        self.annotations_dir = CRAWLED_ORIGINAL_ANNOTATIONS_DIR
        self.session = requests.Session()

        # 设置请求头，模拟浏览器
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        self.setup_directories()
        
    def setup_directories(self):
        """创建目录结构"""
        # 创建主目录和original_annotations目录
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.annotations_dir.mkdir(parents=True, exist_ok=True)

        # 添加.keep文件用于git版本控制
        for directory in [self.base_dir, self.annotations_dir]:
            keep_file = directory / '.keep'
            if not keep_file.exists():
                keep_file.touch()

        print(f"目录结构已创建在: {self.base_dir}")
        print(f"标注文件目录: {self.annotations_dir}")
        
    def get_image_hash(self, image_data):
        """计算图片的MD5哈希值，用于去重"""
        return hashlib.md5(image_data).hexdigest()
        
    def download_image(self, url, category, filename=None):
        """
        下载单张图片
        :param url: 图片URL
        :param category: 图片分类（用于文件名前缀）
        :param filename: 自定义文件名
        :return: 是否下载成功
        """
        try:
            response = self.session.get(url, timeout=10, stream=True)
            response.raise_for_status()

            # 检查是否为图片
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                print(f"跳过非图片文件: {url}")
                return False

            # 读取图片数据
            image_data = response.content

            # 检查图片大小（跳过过小的图片）
            if len(image_data) < 1024:  # 小于1KB
                print(f"跳过过小的图片: {url}")
                return False

            # 生成文件名
            if not filename:
                image_hash = self.get_image_hash(image_data)
                ext = self.get_file_extension(url, content_type)
                filename = f"{category}_{image_hash}{ext}"

            # 保存路径（直接保存到images目录）
            save_path = self.base_dir / filename

            # 检查文件是否已存在（去重）
            if save_path.exists():
                print(f"图片已存在，跳过: {filename}")
                return False

            # 保存图片
            with open(save_path, 'wb') as f:
                f.write(image_data)

            print(f"下载成功: {filename}")
            return True

        except Exception as e:
            print(f"下载失败 {url}: {str(e)}")
            return False
            
    def get_file_extension(self, url, content_type):
        """根据URL和content-type获取文件扩展名"""
        # 从URL获取扩展名
        parsed_url = urlparse(url)
        path = parsed_url.path
        if '.' in path:
            ext = os.path.splitext(path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                return ext
                
        # 从content-type获取扩展名
        if 'jpeg' in content_type:
            return '.jpg'
        elif 'png' in content_type:
            return '.png'
        elif 'gif' in content_type:
            return '.gif'
        elif 'webp' in content_type:
            return '.webp'
        else:
            return '.jpg'  # 默认
            
    def search_bing_images(self, query, category, max_images=50):
        """
        使用Bing搜索图片
        :param query: 搜索关键词
        :param category: 图片分类
        :param max_images: 最大下载数量
        """
        print(f"开始搜索: {query}")
        
        # Bing图片搜索URL
        search_url = "https://www.bing.com/images/search"
        params = {
            'q': query,
            'form': 'HDRSC2',
            'first': 1,
            'count': 35
        }
        
        downloaded = 0
        page = 0
        
        while downloaded < max_images:
            try:
                params['first'] = page * 35 + 1
                response = self.session.get(search_url, params=params, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找图片链接
                img_elements = soup.find_all('a', {'class': 'iusc'})
                
                if not img_elements:
                    print("未找到更多图片，搜索结束")
                    break
                    
                for img_element in img_elements:
                    if downloaded >= max_images:
                        break
                        
                    try:
                        # 解析图片信息
                        m_attr = img_element.get('m')
                        if m_attr:
                            img_info = json.loads(m_attr)
                            img_url = img_info.get('murl')
                            
                            if img_url:
                                if self.download_image(img_url, category):
                                    downloaded += 1
                                    
                                # 添加延时，避免请求过快
                                time.sleep(random.uniform(0.5, 1.5))
                                
                    except Exception as e:
                        print(f"解析图片信息失败: {str(e)}")
                        continue
                        
                page += 1
                print(f"已下载 {downloaded}/{max_images} 张图片")
                
                # 页面间延时
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"搜索页面失败: {str(e)}")
                break
                
        print(f"搜索完成: {query}, 共下载 {downloaded} 张图片")
        
    def crawl_all_categories(self, images_per_category=50):
        """爬取所有分类的图片"""
        search_queries = {
            'with_mask': [
                '戴口罩的人',
                '正确佩戴口罩',
                '医护人员口罩',
                'properly wearing surgical mask',
                'wearing N95 mask',
                '戴好医用口罩的人'
            ],
            'without_mask': [
                'bare-faced portrait',
                'smiling outdoors',
                '商场购物的人',
                '面部无遮挡的人像',
                '摘下口罩的人'
            ],
            'mask_weared_incorrect': [
                'wearing medical mask incorrectly',
                'medical mask below nose',
                'improper medical mask wearing',
                '错误佩戴口罩',
                'medical mask not covering nose',
                'mask under chin'
            ]
        }

        # 分类描述
        categories_desc = {
            'with_mask': '戴口罩',
            'without_mask': '未戴口罩',
            'mask_weared_incorrect': '不规范戴口罩'
        }

        for category, queries in search_queries.items():
            print(f"\n开始爬取分类: {categories_desc[category]}")

            images_per_query = images_per_category // len(queries)

            for query in queries:
                self.search_bing_images(query, category, images_per_query)

                # 查询间延时
                time.sleep(random.uniform(3, 6))

        print("\n所有分类爬取完成！")
        self.print_summary()
        
    def print_summary(self):
        """打印爬取结果摘要"""
        print("\n=== 爬取结果摘要 ===")

        # 统计各类图片数量
        categories = {
            'with_mask': '戴口罩',
            'without_mask': '未戴口罩',
            'mask_weared_incorrect': '不规范戴口罩'
        }

        total_images = 0
        for category, description in categories.items():
            image_files = [f for f in self.base_dir.iterdir()
                          if f.is_file() and f.name.startswith(category) and
                          f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']]
            count = len(image_files)
            total_images += count
            print(f"{description}: {count} 张图片")

        print(f"总计: {total_images} 张图片")
        print(f"保存位置: {self.base_dir}")

def main():
    """主函数"""
    print("口罩图片爬虫启动...")
    
    image_num = 100
    # 创建爬虫实例
    crawler = MaskImageCrawler()
    
    # 开始爬取，每个分类爬取image_num张图片
    crawler.crawl_all_categories(images_per_category=image_num)

if __name__ == "__main__":
    main()

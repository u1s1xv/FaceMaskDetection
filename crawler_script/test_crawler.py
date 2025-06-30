#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试爬虫脚本 - 只下载少量图片进行测试
"""

from mask_image_crawler import MaskImageCrawler

def test_crawler():
    """测试爬虫功能"""
    print("开始测试口罩图片爬虫...")
    
    # 创建爬虫实例
    crawler = MaskImageCrawler()
    
    # 测试搜索一个关键词，每个分类只下载2张图片
    test_queries = {
        'with_mask': ['people wearing face mask'],
        'without_mask': ['people without mask'],
        'incorrect_mask': ['wearing mask incorrectly']
    }
    
    for category, queries in test_queries.items():
        print(f"\n测试分类: {category}")
        for query in queries:
            print(f"搜索关键词: {query}")
            crawler.search_bing_images(query, category, max_images=2)
    
    # 打印结果
    crawler.print_summary()
    print("\n测试完成！")

if __name__ == "__main__":
    test_crawler()

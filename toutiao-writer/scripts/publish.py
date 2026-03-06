#!/usr/bin/env python3
"""
今日头条文章发布脚本
用法：python publish.py --title "标题" --content "内容"
"""

import argparse
import requests
import os
import json

# 配置
API_BASE = "https://open.toutiao.com/api"
APP_KEY = os.getenv('TOUTIAO_APP_KEY', '')
APP_SECRET = os.getenv('TOUTIAO_APP_SECRET', '')
ACCESS_TOKEN = os.getenv('TOUTIAO_ACCESS_TOKEN', '')


def get_access_token():
    """获取访问 Token"""
    if ACCESS_TOKEN:
        return ACCESS_TOKEN
    
    url = f"{API_BASE}/oauth/client_token/"
    params = {
        'client_key': APP_KEY,
        'client_secret': APP_SECRET,
        'grant_type': 'client_cred'
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if 'access_token' in data:
        return data['access_token']
    else:
        raise Exception(f"获取 Token 失败：{data}")


def upload_image(image_path):
    """上传图片素材"""
    token = get_access_token()
    
    url = f"{API_BASE}/media/upload/"
    files = {'file': open(image_path, 'rb')}
    params = {'access_token': token}
    
    response = requests.post(url, params=params, files=files)
    data = response.json()
    
    return data.get('image_id')


def publish_article(title, content, image_ids=None):
    """发布文章"""
    token = get_access_token()
    
    url = f"{API_BASE}/article/create/"
    data = {
        'access_token': token,
        'title': title,
        'content': content,
        'media_type': 1,  # 1=图文
    }
    
    if image_ids:
        data['image_ids'] = ','.join(image_ids)
    
    response = requests.post(url, json=data)
    result = response.json()
    
    return result


def main():
    parser = argparse.ArgumentParser(description='发布文章到今日头条')
    parser.add_argument('--title', required=True, help='文章标题')
    parser.add_argument('--content', required=True, help='文章内容')
    parser.add_argument('--image', help='封面图片路径')
    
    args = parser.parse_args()
    
    print(f"📰 发布文章：{args.title}")
    
    # 上传图片（如果有）
    image_ids = []
    if args.image and os.path.exists(args.image):
        print("📷 上传图片...")
        image_id = upload_image(args.image)
        if image_id:
            image_ids.append(image_id)
            print(f"✅ 图片上传成功：{image_id}")
    
    # 发布文章
    print("🚀 发布文章...")
    result = publish_article(args.title, args.content, image_ids if image_ids else None)
    
    if result.get('status') == 'success' or 'article_id' in result:
        article_id = result.get('article_id', 'unknown')
        print(f"✅ 发布成功！")
        print(f"🔗 文章 ID: {article_id}")
        print(f"🌐 链接：https://www.toutiao.com/article/{article_id}/")
    else:
        print(f"❌ 发布失败：{result}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Hexo 博客写作技能 - 自动化博客文章创建、编辑和发布
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

# 配置
HEXO_BLOG_PATH = os.getenv('HEXO_BLOG_PATH', '/home/admin/.openclaw/workspace/github-site/hexo-blog')
GITHUB_PAGES_PATH = os.getenv('GITHUB_PAGES_PATH', '/home/admin/.openclaw/workspace/github-site')
HEXO_CMD = os.path.expanduser('~/.npm-global/bin/hexo')


def run_command(cmd, cwd=None):
    """执行 shell 命令"""
    print(f"执行：{cmd}")
    result = subprocess.run(
        cmd, 
        shell=True, 
        cwd=cwd, 
        capture_output=True, 
        text=True
    )
    if result.returncode != 0:
        print(f"❌ 命令失败：{result.stderr}")
        return False, result.stderr
    print(f"✅ 成功：{result.stdout[:200]}")
    return True, result.stdout


def create_post(title, content=None, tags=None, categories=None):
    """创建新文章"""
    print(f"📝 创建文章：{title}")
    
    # 生成文件名
    filename = title.lower().replace(' ', '-').replace(':', '')
    filename = ''.join(c for c in filename if c.isalnum() or c in '-_')
    
    # 创建文章
    cmd = f"{HEXO_CMD} new post \"{title}\""
    success, output = run_command(cmd, cwd=HEXO_BLOG_PATH)
    
    if not success:
        return False, f"创建文章失败：{output}"
    
    # 找到生成的文件
    posts_dir = os.path.join(HEXO_BLOG_PATH, 'source', '_posts')
    post_file = None
    for f in os.listdir(posts_dir):
        if f.endswith('.md') and title.split()[0] in f:
            post_file = os.path.join(posts_dir, f)
            break
    
    if not post_file:
        return False, "找不到生成的文章文件"
    
    # 更新 Front-matter 和内容
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    front_matter = f"""---
title: {title}
date: {now}
"""
    
    if tags:
        front_matter += f"tags: [{', '.join(tags)}]\n"
    
    if categories:
        front_matter += f"categories: [{', '.join(categories)}]\n"
    
    front_matter += "---\n\n"
    
    # 写入内容
    with open(post_file, 'w', encoding='utf-8') as f:
        f.write(front_matter)
        if content:
            f.write(content)
    
    return True, f"文章已创建：{post_file}"


def generate():
    """生成静态文件"""
    print("🔨 生成静态文件...")
    cmd = f"{HEXO_CMD} generate"
    success, output = run_command(cmd, cwd=HEXO_BLOG_PATH)
    return success, output


def deploy():
    """部署到 GitHub Pages"""
    print("🚀 部署到 GitHub Pages...")
    
    # 清理旧的生成文件
    print("🧹 清理旧文件...")
    dirs_to_remove = ['2022', '2026', 'archives', 'categories', 'tags', 'css', 'js', 'fancybox', 'images']
    for dir_name in dirs_to_remove:
        dir_path = os.path.join(GITHUB_PAGES_PATH, dir_name)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            shutil.rmtree(dir_path)
            print(f"  删除：{dir_name}")
    
    # 复制新生成的文件
    public_dir = os.path.join(HEXO_BLOG_PATH, 'public')
    if not os.path.exists(public_dir):
        return False, "public 目录不存在，请先生成"
    
    print("📦 复制文件...")
    for item in os.listdir(public_dir):
        if item in ['.git', '.gitignore']:
            continue
        src = os.path.join(public_dir, item)
        dst = os.path.join(GITHUB_PAGES_PATH, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        print(f"  复制：{item}")
    
    # Git 提交
    print("💾 提交到 Git...")
    cmd = "git add ."
    success, output = run_command(cmd, cwd=GITHUB_PAGES_PATH)
    
    if not success:
        return False, f"git add 失败：{output}"
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    cmd = f"git commit -m \"feat: 更新博客文章 {now}\""
    success, output = run_command(cmd, cwd=GITHUB_PAGES_PATH)
    
    if not success:
        # 如果没有变化，跳过推送
        if "nothing to commit" in output:
            return True, "没有变化，跳过推送"
        return False, f"git commit 失败：{output}"
    
    # 推送
    print("📤 推送到 GitHub...")
    cmd = "git push origin master"
    success, output = run_command(cmd, cwd=GITHUB_PAGES_PATH)
    
    if not success:
        return False, f"git push 失败：{output}"
    
    return True, "部署成功！"


def list_posts():
    """列出所有文章"""
    posts_dir = os.path.join(HEXO_BLOG_PATH, 'source', '_posts')
    posts = []
    
    for f in os.listdir(posts_dir):
        if f.endswith('.md'):
            filepath = os.path.join(posts_dir, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                # 读取 Front-matter
                content = file.read()
                if content.startswith('---'):
                    lines = content.split('\n')
                    title = None
                    date = None
                    tags = []
                    for line in lines[1:]:
                        if line.startswith('title:'):
                            title = line.split(':', 1)[1].strip()
                        elif line.startswith('date:'):
                            date = line.split(':', 1)[1].strip()
                        elif line.startswith('tags:'):
                            tags_str = line.split(':', 1)[1].strip()
                            tags = [t.strip() for t in tags_str.strip('[]').split(',')]
                        if line == '---':
                            break
                    
                    if title:
                        posts.append({
                            'file': f,
                            'title': title,
                            'date': date,
                            'tags': tags
                        })
    
    return posts


def delete_post(title):
    """删除文章"""
    posts_dir = os.path.join(HEXO_BLOG_PATH, 'source', '_posts')
    
    for f in os.listdir(posts_dir):
        if f.endswith('.md') and title in f:
            filepath = os.path.join(posts_dir, f)
            os.remove(filepath)
            return True, f"文章已删除：{f}"
    
    return False, "未找到文章"


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法：python blog_writer.py <command> [args]")
        print("命令:")
        print("  create <title> [content]  - 创建文章")
        print("  generate                  - 生成静态文件")
        print("  deploy                    - 部署到 GitHub")
        print("  list                      - 列出文章")
        print("  delete <title>            - 删除文章")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'create':
        if len(sys.argv) < 3:
            print("❌ 请提供文章标题")
            sys.exit(1)
        title = sys.argv[2]
        content = sys.argv[3] if len(sys.argv) > 3 else None
        success, msg = create_post(title, content)
        print(msg)
        sys.exit(0 if success else 1)
    
    elif command == 'generate':
        success, msg = generate()
        print(msg)
        sys.exit(0 if success else 1)
    
    elif command == 'deploy':
        success, msg = deploy()
        print(msg)
        sys.exit(0 if success else 1)
    
    elif command == 'list':
        posts = list_posts()
        if posts:
            print(f"📝 共有 {len(posts)} 篇文章:\n")
            for i, post in enumerate(posts, 1):
                tags_str = ', '.join(post['tags']) if post['tags'] else '无标签'
                print(f"{i}. {post['title']} ({post['date']}) - {tags_str}")
        else:
            print("📭 暂无文章")
        sys.exit(0)
    
    elif command == 'delete':
        if len(sys.argv) < 3:
            print("❌ 请提供文章标题")
            sys.exit(1)
        title = sys.argv[2]
        success, msg = delete_post(title)
        print(msg)
        sys.exit(0 if success else 1)
    
    else:
        print(f"❌ 未知命令：{command}")
        sys.exit(1)


if __name__ == '__main__':
    main()

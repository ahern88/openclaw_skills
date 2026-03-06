#!/bin/bash
# 部署博客到 GitHub Pages 脚本
# 用法：bash deploy.sh

HEXO_PATH="${HEXO_BLOG_PATH:-/home/admin/.openclaw/workspace/ahern88_github_io/blog}"

echo "🚀 部署到 GitHub Pages..."

cd "$HEXO_PATH"

# 配置 Git
git config user.name "ahern88"
git config user.email "ahern88@163.com"

# 提交源文件
echo "💾 提交源文件..."
git add .
git commit -m "feat: 更新博客文章 $(date +%Y-%m-%d)"
git push origin main

if [ $? -ne 0 ]; then
    echo "⚠️  源文件提交失败，但继续部署..."
fi

# 部署到 Pages
echo "📤 部署到 GitHub Pages..."
hexo deploy

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 部署成功！"
    echo ""
    echo "🌐 访问地址："
    echo "https://ahern88.github.io/"
    echo ""
    echo "⏳ 等待 GitHub Pages 构建完成（约 1-2 分钟）"
else
    echo "❌ 部署失败"
    exit 1
fi

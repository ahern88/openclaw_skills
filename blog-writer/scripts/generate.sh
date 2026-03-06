#!/bin/bash
# 生成博客静态文件脚本
# 用法：bash generate.sh

HEXO_PATH="${HEXO_BLOG_PATH:-/home/admin/.openclaw/workspace/ahern88_github_io/blog}"

echo "🔨 生成静态文件..."

cd "$HEXO_PATH"

# 清理缓存
echo "🧹 清理缓存..."
hexo clean

# 生成
echo "📦 生成 HTML..."
hexo generate

if [ $? -eq 0 ]; then
    echo "✅ 生成成功"
    echo ""
    echo "接下来："
    echo "1. 提交源文件：git add . && git commit -m \"更新文章\""
    echo "2. 部署：bash scripts/deploy.sh"
else
    echo "❌ 生成失败"
    exit 1
fi

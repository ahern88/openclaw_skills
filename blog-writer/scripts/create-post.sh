#!/bin/bash
# 创建博客文章脚本
# 用法：bash create-post.sh "文章标题"

TITLE=$1
HEXO_PATH="${HEXO_BLOG_PATH:-/home/admin/.openclaw/workspace/ahern88_github_io/blog}"

if [ -z "$TITLE" ]; then
    echo "❌ 请提供文章标题"
    echo "用法：$0 \"文章标题\""
    exit 1
fi

echo "📝 创建文章：$TITLE"

# 创建文章
cd "$HEXO_PATH"
hexo new post "$TITLE"

if [ $? -eq 0 ]; then
    echo "✅ 文章已创建"
    echo "📁 位置：$HEXO_PATH/source/_posts/$TITLE.md"
    echo ""
    echo "接下来："
    echo "1. 编辑文章：vim source/_posts/$TITLE.md"
    echo "2. 生成 HTML: bash scripts/generate.sh"
    echo "3. 部署：bash scripts/deploy.sh"
else
    echo "❌ 创建失败"
    exit 1
fi

#!/bin/bash
# 验证博客部署状态脚本
# 用法：bash verify-deploy.sh

HEXO_PATH="${HEXO_BLOG_PATH:-/home/admin/.openclaw/workspace/ahern88_github_io/blog}"
PAGES_PATH="${GITHUB_PAGES_PATH:-/home/admin/.openclaw/workspace/ahern88.github.io}"

echo "🔍 验证博客部署状态"
echo "===================="
echo ""

# 1. 检查源文件
echo "1️⃣ 源文件状态"
cd "$HEXO_PATH"
echo "   📁 最新文章："
ls -lt source/_posts/*.md 2>/dev/null | head -3 | awk '{print "      " $9}'
echo ""

# 2. 检查 .deploy_git
echo "2️⃣ 部署仓库状态"
cd "$HEXO_PATH/.deploy_git"
echo "   📌 最新提交："
git log --oneline -3 | sed 's/^/      /'
echo ""

# 3. 检查 Pages 仓库
echo "3️⃣ Pages 仓库状态"
if [ -d "$PAGES_PATH" ]; then
    cd "$PAGES_PATH"
    echo "   📌 最新提交："
    git log --oneline -3 | sed 's/^/      /'
    echo ""
    echo "   📁 最新文章目录："
    ls -lt 2026/*/ 2>/dev/null | head -3 | awk '{print "      " $9}'
else
    echo "   ⚠️  Pages 仓库目录不存在"
fi
echo ""

# 4. 在线验证
echo "4️⃣ 在线验证"
echo "   🌐 检查首页..."
RESPONSE=$(curl -sL -o /dev/null -w "%{http_code}" "https://ahern88.github.io/" --max-time 10)
if [ "$RESPONSE" = "200" ]; then
    echo "   ✅ 首页可访问 (HTTP $RESPONSE)"
else
    echo "   ❌ 首页访问失败 (HTTP $RESPONSE)"
fi

echo ""
echo "   🌐 检查最新文章..."
# 尝试获取最新文章链接
ARTICLE_COUNT=$(curl -sL "https://ahern88.github.io/" 2>/dev/null | grep -c "href=\"/2026/")
echo "   📊 找到 $ARTICLE_COUNT 篇 2026 年的文章链接"

echo ""
echo "===================="
echo "✅ 验证完成"
echo ""
echo "💡 如果部署有问题，运行："
echo "   cd $HEXO_PATH"
echo "   hexo clean && hexo generate && hexo deploy"

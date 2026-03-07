#!/bin/bash
# 部署博客到 GitHub Pages 脚本（增强版）
# 用法：bash deploy.sh
# 
# 完整流程：
# 1. hexo clean - 清理缓存
# 2. hexo generate - 生成静态文件
# 3. hexo deploy - 部署到 GitHub Pages
# 4. 同步 ahern88.github.io 仓库

HEXO_PATH="${HEXO_BLOG_PATH:-/home/admin/.openclaw/workspace/ahern88_github_io/blog}"
PAGES_PATH="${GITHUB_PAGES_PATH:-/home/admin/.openclaw/workspace/ahern88.github.io}"

echo "🚀 部署到 GitHub Pages..."
echo ""

cd "$HEXO_PATH"

# 配置 Git
git config user.name "ahern88"
git config user.email "ahern88@163.com"

# 步骤 1: 清理缓存
echo "🧹 清理 Hexo 缓存..."
hexo clean
if [ $? -ne 0 ]; then
    echo "⚠️  清理缓存失败，继续执行..."
fi

# 步骤 2: 生成静态文件
echo "📝 生成静态文件..."
hexo generate
if [ $? -ne 0 ]; then
    echo "❌ 生成静态文件失败"
    exit 1
fi

# 步骤 3: 提交源文件
echo "💾 提交源文件..."
git add .
git diff --cached --quiet
if [ $? -ne 0 ]; then
    git commit -m "feat: 更新博客文章 $(date +%Y-%m-%d)"
    git push origin main
    if [ $? -ne 0 ]; then
        echo "⚠️  源文件提交失败，但继续部署..."
    fi
else
    echo "ℹ️  源文件无变化，跳过提交"
fi

# 步骤 4: 部署到 Pages
echo "📤 部署到 GitHub Pages..."
hexo deploy

if [ $? -ne 0 ]; then
    echo "❌ 部署失败"
    exit 1
fi

# 步骤 5: 同步 Pages 仓库（如果存在）
if [ -d "$PAGES_PATH" ]; then
    echo ""
    echo "🔄 同步 Pages 仓库..."
    cd "$PAGES_PATH"
    git fetch origin
    git reset --hard origin/master
    echo "✅ Pages 仓库已同步"
fi

# 步骤 6: 验证部署
echo ""
echo "🔍 验证部署..."
cd "$HEXO_PATH/.deploy_git"
LATEST_COMMIT=$(git log --oneline -1)
echo "📌 最新部署提交：$LATEST_COMMIT"

echo ""
echo "✅ 部署成功！"
echo ""
echo "🌐 访问地址："
echo "https://ahern88.github.io/"
echo ""
echo "📝 文章目录："
ls -la "$PAGES_PATH/2026/03/" 2>/dev/null || echo "（自动检测文章目录）"
echo ""
echo "⏳ 等待 GitHub Pages 构建完成（约 1-2 分钟）"
echo ""
echo "💡 如果浏览器看不到新文章："
echo "   1. 强制刷新：Ctrl+F5 (Windows) 或 Cmd+Shift+R (Mac)"
echo "   2. 检查：curl -sL https://ahern88.github.io/ | grep '文章标题'"

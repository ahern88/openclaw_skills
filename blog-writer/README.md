# Blog Writer Skill - 博客写作助手

📝 自动化 Hexo 博客文章写作和发布

---

## 🚀 快速开始

### 方式一：使用 OpenClaw 对话

直接对 AI 说：

```
帮我写一篇博客文章，介绍 Python 入门教程
```

AI 会自动完成所有步骤！

### 方式二：命令行

```bash
# 1. 创建文章
bash scripts/create-post.sh "文章标题"

# 2. 生成 HTML
bash scripts/generate.sh

# 3. 部署
bash scripts/deploy.sh
```

---

## 📝 完整流程示例

### 示例 1：创建技术文章

**你说**:
```
帮我写一篇博客，介绍如何学习 Kubernetes
```

**AI 执行**:
1. ✅ 创建 `source/_posts/kubernetes-learning-guide.md`
2. ✅ 生成完整的 K8s 学习教程
3. ✅ 执行 `hexo generate`
4. ✅ Git commit & push
5. ✅ 执行 `hexo deploy`
6. ✅ 返回文章链接

**AI 回复**:
```
✅ 文章已发布！

📝 Kubernetes 学习指南
🔗 https://ahern88.github.io/2026/03/06/kubernetes-learning-guide/

文章已推送到 GitHub Pages，预计 1 分钟后可以访问。
```

---

## 🔧 命令参考

| 命令 | 说明 | 示例 |
|------|------|------|
| `create` | 创建新文章 | `create "文章标题" "内容"` |
| `generate` | 生成静态文件 | `generate` |
| `deploy` | 部署到 GitHub | `deploy` |
| `list` | 列出所有文章 | `list` |
| `delete` | 删除文章 | `delete "文章标题"` |

---

## 📁 文件位置

- **Skill 目录**: `/home/admin/.openclaw/workspace/openclaw_skills/blog-writer/`
- **Hexo 源文件**: `/home/admin/.openclaw/workspace/ahern88_github_io/blog/`
- **GitHub Pages**: `/home/admin/.openclaw/workspace/ahern88.github.io/`
- **文章 Markdown**: `blog/source/_posts/`

---

## ⚙️ 配置

### 环境变量（可选）

```bash
export HEXO_BLOG_PATH=/home/admin/.openclaw/workspace/ahern88_github_io/blog
export GITHUB_PAGES_PATH=/home/admin/.openclaw/workspace/ahern88.github.io
```

### Git 配置

```bash
git config --global user.name "ahern88"
git config --global user.email "ahern88@163.com"
```

---

## 🎨 文章格式

Markdown 文件包含 Front-matter：

```yaml
---
title: 文章标题
date: 2026-03-06 00:00:00
tags: [标签 1, 标签 2]
categories: [分类]
---

# 文章标题

## 简介

这里是简介...

## 正文

这里是正文...

## 总结

这里是总结...
```

---

## 💡 提示

1. **文章标题** - 尽量简洁明确
2. **标签** - 3-5 个为宜
3. **分类** - 1-2 个即可
4. **内容** - 结构清晰，分段明确
5. **发布频率** - 建议每周 1-2 篇

---

## 🆘 常见问题

### Q: Hexo 命令找不到？

```bash
# 安装 Hexo
cd /home/admin/.openclaw/workspace/ahern88_github_io/blog
npm install
```

### Q: Git 推送失败？

```bash
# 检查 SSH key
ssh -T git@github.com

# 配置 Git
git config --global user.name "ahern88"
git config --global user.email "ahern88@163.com"
```

### Q: 文章不显示？

1. 检查 Markdown 是否在 `source/_posts/`
2. 执行 `hexo clean && hexo generate`
3. 执行 `hexo deploy`
4. 等待 GitHub Pages 构建完成（1-2 分钟）

---

## 📚 下一步

- ✅ 技能已创建完成
- ✅ 已提交到 GitHub
- 📝 开始写你的第一篇文章吧！

---

_🦞 Created by 小艾的龙虾_

# Blog Writer Skill - 博客写作助手

🦞 小艾的龙虾为你打造的博客自动化写作技能！

---

## 📋 功能

- ✅ **自动创建文章** - 生成 Markdown 模板
- ✅ **AI 辅助写作** - 自动生成文章内容
- ✅ **一键发布** - 自动推送到 GitHub Pages
- ✅ **文章管理** - 查看、修改、删除文章

---

## 🚀 快速开始

### 方式一：使用命令行

```bash
# 创建新文章
python /home/admin/.openclaw/workspace/skills/blog-writer/blog_writer.py create "文章标题" "文章内容"

# 生成静态文件
python /home/admin/.openclaw/workspace/skills/blog-writer/blog_writer.py generate

# 部署到 GitHub
python /home/admin/.openclaw/workspace/skills/blog-writer/blog_writer.py deploy

# 列出所有文章
python /home/admin/.openclaw/workspace/skills/blog-writer/blog_writer.py list

# 删除文章
python /home/admin/.openclaw/workspace/skills/blog-writer/blog_writer.py delete "文章标题"
```

### 方式二：使用 OpenClaw 对话

直接对 AI 说：

```
帮我写一篇博客文章，介绍如何学习 Python
```

AI 会自动：
1. 创建 Markdown 文件
2. 生成文章内容
3. 执行 hexo generate
4. 推送到 GitHub Pages
5. 返回文章链接

---

## 📁 目录结构

```
skills/blog-writer/
├── SKILL.md           # 技能配置
├── blog_writer.py     # 主程序
├── README.md          # 使用说明
└── templates/         # 文章模板（可选）
    └── post.md
```

---

## 🔧 配置

### 环境变量

```bash
export HEXO_BLOG_PATH=/home/admin/.openclaw/workspace/github-site/hexo-blog
export GITHUB_PAGES_PATH=/home/admin/.openclaw/workspace/github-site
```

### Git 配置

确保已配置 Git：

```bash
git config --global user.name "ahern88"
git config --global user.email "ahern88@163.com"
```

### SSH Key

确保已配置 GitHub SSH Key：

```bash
# 检查 SSH Key
ls -la ~/.ssh/github_key

# 如果没有，生成新的
ssh-keygen -t ed25519 -C "ahern88@163.com"
# 然后添加到 GitHub: https://github.com/settings/keys
```

---

## 💡 使用场景

### 场景 1：技术教程

```
帮我写一篇博客，介绍 Docker 的安装和使用
```

### 场景 2：学习笔记

```
写一篇学习笔记，记录 K8s 的核心概念
```

### 场景 3：项目总结

```
帮我写一个项目总结，关于物流分单 Agent 的开发经验
```

### 场景 4：修改文章

```
帮我修改"TiDB 架构"那篇文章，添加性能测试数据
```

---

## 📊 工作流程

```
用户请求
    ↓
AI 理解需求
    ↓
调用 blog_writer.py create
    ↓
生成 Markdown 文件
    ↓
调用 blog_writer.py generate
    ↓
Hexo 生成 HTML
    ↓
调用 blog_writer.py deploy
    ↓
复制到 Pages 目录 → Git commit → Git push
    ↓
GitHub Pages 自动部署
    ↓
返回文章链接 ✅
```

---

## 🎨 文章模板

默认模板包含：

```yaml
---
title: 文章标题
date: 2026-03-06 00:00:00
tags: [标签 1, 标签 2]
categories: [分类]
---

# 文章标题

## 简介

这里是文章简介...

## 正文

这里是正文内容...

## 总结

这里是总结...
```

---

## ⚠️ 注意事项

1. **Hexo 源文件** 在 `hexo-blog/` 目录
2. **GitHub Pages** 发布在根目录
3. **每次发布** 会自动清理旧的生成文件
4. **Git 推送** 使用 SSH key 认证

---

## 🔐 安全

- ✅ 不存储密码
- ✅ 使用 SSH key 认证
- ✅ 所有操作有 Git 历史记录
- ✅ 可追溯、可回滚

---

## 📖 示例输出

### 创建文章

```
📝 创建文章：Docker 入门教程
执行：~/.npm-global/bin/hexo new post "Docker 入门教程"
✅ 成功：Created: /path/to/hexo-blog/source/_posts/Docker 入门教程.md
文章已创建：/path/to/hexo-blog/source/_posts/Docker 入门教程.md
```

### 部署

```
🚀 部署到 GitHub Pages...
🧹 清理旧文件...
  删除：2026
  删除：archives
📦 复制文件...
  复制：2026
  复制：index.html
💾 提交到 Git...
📤 推送到 GitHub...
部署成功！
```

---

## 🆘 故障排除

### 问题 1：Hexo 命令找不到

```bash
# 检查 Hexo 安装
~/.npm-global/bin/hexo version

# 如果没安装
npm install -g hexo-cli --prefix ~/.npm-global
```

### 问题 2：Git 推送失败

```bash
# 检查 SSH key
ssh -T git@github.com

# 检查 Git 配置
git config --global user.name
git config --global user.email
```

### 问题 3：文章不显示

1. 检查 Markdown 文件是否在 `source/_posts/`
2. 执行 `hexo clean && hexo generate`
3. 检查 GitHub Pages 是否构建成功

---

## 📚 参考资料

- [Hexo 官方文档](https://hexo.io/zh-cn/)
- [GitHub Pages 文档](https://docs.github.com/en/pages)
- [OpenClaw 文档](https://docs.openclaw.ai)

---

_🦞 Made with ❤️ by 小艾的龙虾_

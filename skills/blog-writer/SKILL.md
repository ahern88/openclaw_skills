---
name: blog-writer
description: Hexo 博客文章写作和发布技能。支持创建文章、生成 HTML、推送到 GitHub Pages。
author: 小艾的龙虾
version: 1.0.0
metadata: {"clawdbot":{"emoji":"📝","requires":{"bins":["hexo","git"]},"config":{"env":{"HEXO_BLOG_PATH":{"description":"Hexo 博客源文件路径","default":"/home/admin/.openclaw/workspace/github-site/hexo-blog","required":true},"GITHUB_PAGES_PATH":{"description":"GitHub Pages 仓库路径","default":"/home/admin/.openclaw/workspace/github-site","required":true}}}}}
---

# Hexo 博客写作技能

自动化完成 Hexo 博客文章的创建、编辑、生成和发布流程。

---

## 📋 功能

1. **创建新文章** - 自动生成 Markdown 模板
2. **编写内容** - 支持 AI 辅助写作
3. **生成 HTML** - 使用 Hexo 生成静态文件
4. **推送到 GitHub** - 自动发布到 GitHub Pages
5. **文章管理** - 查看、修改、删除文章

---

## 🚀 使用方式

### 创建新文章

```
帮我写一篇博客文章，标题是"xxx"，内容是关于 xxx
```

AI 会自动：
1. 创建 Markdown 文件
2. 生成文章内容
3. 生成 HTML
4. 推送到 GitHub Pages

### 查看文章列表

```
我有哪些博客文章？
```

### 修改文章

```
帮我修改文章"xxx"，添加 xxx 内容
```

### 删除文章

```
删除文章"xxx"
```

---

## 🔧 配置

### 环境变量

- `HEXO_BLOG_PATH`: Hexo 博客源文件路径（默认：`/home/admin/.openclaw/workspace/github-site/hexo-blog`）
- `GITHUB_PAGES_PATH`: GitHub Pages 仓库路径（默认：`/home/admin/.openclaw/workspace/github-site`）

### Git 配置

确保已配置 Git 用户信息：

```bash
git config --global user.name "ahern88"
git config --global user.email "ahern88@163.com"
```

---

## 📁 目录结构

```
skills/blog-writer/
├── SKILL.md           # 技能配置
├── blog_writer.py     # 主程序
└── templates/         # 文章模板
    └── post.md        # 文章模板
```

---

## 💡 使用示例

### 示例 1：创建技术文章

**用户**: 帮我写一篇博客文章，介绍如何安装 OpenClaw

**AI 执行**:
1. 创建 `source/_posts/openclaw-install-guide.md`
2. 生成完整的安装教程内容
3. 执行 `hexo generate`
4. 复制生成的 HTML 到 GitHub Pages 目录
5. 提交并推送

**AI 回复**: ✅ 文章已发布：https://ahern88.github.io/2026/03/06/openclaw-install-guide/

### 示例 2：查看文章列表

**用户**: 我有哪些博客文章？

**AI 执行**:
1. 读取 `source/_posts/` 目录
2. 解析 Front-matter
3. 列出文章标题、日期、标签

**AI 回复**: 
```
📝 你的博客文章：

1. TiDB 的架构哲学与思考 (2022-04-10) - #TiDB #数据库
2. OpenClaw 安装教程 (2026-03-06) - #OpenClaw #AI
...
```

---

## ⚙️ 工作流程

```
用户请求
   ↓
创建/编辑 Markdown
   ↓
Hexo generate
   ↓
复制 HTML 到 Pages 目录
   ↓
Git commit & push
   ↓
GitHub Pages 自动部署
```

---

## 📊 命令映射

| 用户指令 | 技能动作 |
|---------|---------|
| "写一篇..." | `create_post` |
| "修改文章..." | `update_post` |
| "删除文章..." | `delete_post` |
| "有哪些文章" | `list_posts` |
| "发布文章" | `deploy` |

---

## 🔐 安全说明

- Git 推送使用 SSH key 认证
- 不存储 GitHub 密码
- 所有操作可追溯（Git 历史记录）

---

## 📖 参考资料

- [Hexo 官方文档](https://hexo.io/zh-cn/)
- [GitHub Pages 文档](https://docs.github.com/en/pages)

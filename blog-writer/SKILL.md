---
name: blog-writer
description: Hexo 博客文章写作和发布技能。支持创建文章、生成 HTML、部署到 GitHub Pages。
author: 小艾的龙虾
version: 1.0.0
metadata: {"clawdbot":{"emoji":"📝","requires":{"bins":["hexo","git"]},"config":{"env":{"HEXO_BLOG_PATH":{"description":"Hexo 博客源文件路径","default":"/home/admin/.openclaw/workspace/ahern88_github_io/blog","required":true},"GITHUB_PAGES_PATH":{"description":"GitHub Pages 仓库路径","default":"/home/admin/.openclaw/workspace/ahern88.github.io","required":false}}}}}
---

# Hexo 博客写作技能

自动化完成 Hexo 博客文章的创建、编辑、生成和发布流程。

---

## 📋 功能

1. **创建新文章** - 自动生成 Markdown 模板
2. **编写内容** - 支持 AI 辅助写作
3. **生成 HTML** - 使用 Hexo 生成静态文件
4. **部署到 GitHub** - 自动发布到 GitHub Pages
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
4. 提交到 Git
5. 部署到 GitHub Pages

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

- `HEXO_BLOG_PATH`: Hexo 博客源文件路径（默认：`/home/admin/.openclaw/workspace/ahern88_github_io/blog`）
- `GITHUB_PAGES_PATH`: GitHub Pages 仓库路径（可选）

### Git 配置

确保已配置 Git 用户信息：

```bash
git config --global user.name "ahern88"
git config --global user.email "ahern88@163.com"
```

---

## 📁 目录结构

```
blog-writer/
├── SKILL.md           # 技能配置
├── README.md          # 使用说明
├── scripts/           # 脚本文件
│   ├── create-post.sh    # 创建文章
│   ├── generate.sh       # 生成 HTML
│   └── deploy.sh         # 部署到 Pages
├── templates/         # 文章模板
│   └── post.md
└── references/        # 参考资料
    └── examples.md
```

---

## 💡 使用示例

### 示例 1：创建技术文章

**用户**: 帮我写一篇博客文章，介绍如何安装 Docker

**AI 执行**:
1. 创建 `source/_posts/docker-install-guide.md`
2. 生成完整的安装教程内容
3. 执行 `hexo generate`
4. 执行 `hexo deploy`
5. 返回文章链接

**AI 回复**: ✅ 文章已发布：https://ahern88.github.io/2026/03/06/docker-install-guide/

### 示例 2：查看文章列表

**用户**: 我有哪些博客文章？

**AI 执行**:
1. 读取 `source/_posts/` 目录
2. 解析 Front-matter
3. 列出文章标题、日期、标签

**AI 回复**: 
```
📝 你的博客文章：

1. RAG 技术发展与现状 (2026-03-06) - #RAG #AI
2. OpenClaw 部署教程 (2026-03-06) - #OpenClaw #飞书
...
```

---

## ⚙️ 工作流程

```
用户请求
   ↓
创建/编辑 Markdown (ahern88_github_io/blog/source/_posts/)
   ↓
Hexo generate
   ↓
Git commit & push (源文件)
   ↓
Hexo deploy (部署到 Pages)
   ↓
GitHub Pages 自动部署
   ↓
文章上线！✅
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

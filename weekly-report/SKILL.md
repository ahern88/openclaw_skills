---
name: weekly-report
description: 自动周报生成技能。每周五自动收集工作数据，生成结构化周报并推送到飞书。
author: 小艾的龙虾
version: 1.0.0
metadata: {"clawdbot":{"emoji":"📝","requires":{"bins":["python3","bash"]},"config":{"env":{"WORKSPACE_PATH":{"description":"OpenClaw 工作区路径","default":"/home/admin/.openclaw/workspace","required":true}}}}}
---

# 周报生成技能

自动收集工作数据，生成结构化周报。

---

## 📋 功能

1. **自动收集** - 从 memory 文件和 git 历史收集工作记录
2. **智能分析** - 分类整理完成的工作、进行中的任务
3. **周报生成** - 生成标准格式的周报文档
4. **飞书推送** - 自动创建飞书文档并发送通知

---

## ⏰ 定时任务

- **执行时间**: 每周五下午 2:00
- **Cron 表达式**: `0 14 * * 5`
- **时区**: Asia/Shanghai

---

## 🔧 使用方法

### 手动生成周报

```bash
cd /home/admin/.openclaw/workspace/openclaw_skills/weekly-report

# 1. 收集数据
bash scripts/weekly-collect.sh /tmp/weekly-data.json

# 2. 生成周报
python3 scripts/weekly-generate.py /tmp/weekly-data.json /tmp/weekly-report.md

# 3. 查看结果
cat /tmp/weekly-report.md
```

### 自动执行

定时任务会在每周五下午 2:00 自动触发。

---

## 📁 目录结构

```
weekly-report/
├── SKILL.md                 # 技能定义
├── README.md                # 使用说明
├── scripts/
│   ├── weekly-collect.sh    # 数据收集脚本
│   └── weekly-generate.py   # 周报生成脚本
└── references/
    ├── weekly-config.md     # 配置文件
    ├── template.md          # 周报模板
    └── examples.md          # 示例周报
```

---

## 📊 数据来源

1. **Memory 文件** - `/home/admin/.openclaw/workspace/memory/*.md`
2. **Git 提交历史** - OpenClaw 工作区的 git 记录
3. **日历事件** - （可选）飞书日历

---

## 📝 周报格式

```markdown
# 周报 - YYYY-MM-DD

## 本周概述
简要总结本周工作重点

## 完成工作
- [项目/任务 1] 具体完成内容
- [项目/任务 2] 具体完成内容

## 进行中工作
- [任务 1] 当前进度
- [任务 2] 当前进度

## 问题与思考
遇到的问题和解决方案

## 下周计划
- [计划 1]
- [计划 2]
```

---

## ⚙️ 配置

编辑 `references/weekly-config.md` 可以自定义：
- 周报模板
- 数据收集范围
- 关键词分类规则

---

## 🆘 故障排除

### Q: 找不到 memory 文件？
检查 `/home/admin/.openclaw/workspace/memory/` 目录是否存在

### Q: Git 提交历史为空？
确认工作区是 git 仓库且有提交记录

### Q: 周报内容为空？
检查 memory 文件中是否有工作记录

---

## 📖 示例

查看 `references/examples.md` 了解周报示例。

---

_🦞 Created by 小艾的龙虾_

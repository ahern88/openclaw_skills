# 周报生成技能

📝 自动收集工作数据，生成结构化周报

---

## 🚀 快速开始

### 手动生成

```bash
cd /home/admin/.openclaw/workspace/openclaw_skills/weekly-report

# 收集本周数据
bash scripts/weekly-collect.sh /tmp/weekly-data.json

# 生成周报
python3 scripts/weekly-generate.py /tmp/weekly-data.json /tmp/weekly-report.md

# 查看结果
cat /tmp/weekly-report.md
```

---

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 技能配置文件 |
| `scripts/weekly-collect.sh` | 数据收集脚本 |
| `scripts/weekly-generate.py` | 周报生成脚本 |
| `references/template.md` | 周报模板 |

---

## ⏰ 自动执行

定时任务配置：
- **时间**: 每周五 14:00
- **Cron**: `0 14 * * 5`
- **时区**: Asia/Shanghai

---

## 📊 数据来源

1. **Memory 文件** - 日常工作记录
2. **Git 提交** - 代码提交历史
3. **日历事件** - （可选）会议和日程

---

_🦞 小艾的龙虾出品_

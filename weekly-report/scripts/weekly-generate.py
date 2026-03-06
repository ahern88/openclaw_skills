#!/usr/bin/env python3
"""
周报生成脚本
用法：python3 weekly-generate.py <数据文件> <输出文件>
"""

import sys
import json
from datetime import datetime

def generate_report(data_file, output_file):
    """生成周报"""
    
    # 读取数据
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 生成周报内容
    report = f"""# 周报 - {data.get('date', 'N/A')}

**周期**: {data.get('week', 'N/A')}  
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 📋 本周概述

本周主要完成了以下工作：

"""
    
    # 分析 Memory 记录
    memory_records = data.get('memory_records', [])
    if memory_records:
        report += "### 工作记录\n\n"
        for record in memory_records[:5]:  # 最多显示 5 条
            filename = record.get('file', '')
            content = record.get('content', '')[:200]  # 限制长度
            report += f"- **{filename}**: {content}...\n"
        report += "\n"
    
    # Git 提交
    git_commits = data.get('git_commits', [])
    if git_commits:
        report += "### 代码提交\n\n"
        for commit in git_commits[:10]:  # 最多显示 10 条
            report += f"- {commit}\n"
        report += "\n"
    
    # 标准模板
    report += """
## ✅ 完成工作

- [ ] 任务 1：具体描述
- [ ] 任务 2：具体描述

## 🔄 进行中工作

- [ ] 任务 1：当前进度 XX%
- [ ] 任务 2：等待 XXX

## 💡 问题与思考

### 遇到的问题
1. 问题描述
   - 原因分析
   - 解决方案

### 技术思考
- 对某技术的理解
- 改进建议

## 📅 下周计划

- [ ] 计划 1
- [ ] 计划 2
- [ ] 计划 3

---

*🦞 由小艾的龙虾自动生成*
"""
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 周报生成成功：{output_file}")
    print(f"📊 包含 {len(memory_records)} 条工作记录，{len(git_commits)} 次代码提交")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("用法：python3 weekly-generate.py <数据 JSON 文件> <输出 MD 文件>")
        sys.exit(1)
    
    generate_report(sys.argv[1], sys.argv[2])

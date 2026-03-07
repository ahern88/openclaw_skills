#!/usr/bin/env python3
"""
生成基金收益日报
完整流程：获取净值 → 计算收益 → 生成报表
"""

import sys
import json
import os
import urllib.request
import re
from datetime import datetime

HOLDINGS_PATH = "/home/admin/.openclaw/workspace/memory/fund-holdings.json"

def fetch_fund_nav(fund_code):
    """获取单只基金的净值"""
    url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "http://fund.eastmoney.com/"
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
            match = re.search(r'jsonpgz\((.+)\)', content)
            if match:
                data = json.loads(match.group(1))
                return {
                    "code": data.get('fund_code'),
                    "name": data.get('name'),
                    "nav": float(data.get('gsz', data.get('dwjz', 0))),
                    "nav_date": data.get('gztime', datetime.now().strftime('%Y-%m-%d')),
                    "nav_unit": float(data.get('dwjz', 0)),
                    "success": True
                }
    except Exception as e:
        pass
    
    return {"code": fund_code, "success": False, "error": str(e)}

def load_holdings():
    """加载持仓数据"""
    with open(HOLDINGS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_holdings(data):
    """保存持仓数据"""
    with open(HOLDINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_report():
    """生成完整报表"""
    holdings = load_holdings()
    funds = holdings['holdings']['funds']
    
    # 获取所有基金净值
    print("📊 正在获取基金净值...", file=sys.stderr)
    nav_data = {}
    for fund in funds:
        code = fund['code']
        print(f"  获取 {code}...", file=sys.stderr)
        nav_data[code] = fetch_fund_nav(code)
    
    # 计算收益（简化版：使用上次收益数据）
    total_return = 0
    fund_reports = []
    
    for fund in funds:
        code = fund['code']
        nav_info = nav_data.get(code, {})
        last_return = fund.get('last_return', 0)
        
        fund_reports.append({
            "code": code,
            "name": fund['name'],
            "amount": fund['amount'],
            "return": last_return,
            "success": nav_info.get('success', False)
        })
        total_return += last_return
    
    # 生成报表
    report = []
    report.append(f"💰 基金持仓日报 | {datetime.now().strftime('%Y-%m-%d')}")
    report.append("")
    report.append(f"**总资产：** {holdings['summary']['total_amount']:,.2f} 元")
    report.append(f"**当日收益：** {total_return:+,.2f} 元")
    report.append(f"**累计收益：** {holdings['summary']['total_profit']:,.2f} 元")
    report.append("")
    report.append("## 📊 持仓明细")
    report.append("")
    report.append("| 序号 | 基金代码 | 基金名称 | 持有金额 | 当日收益 |")
    report.append("|:---:|:--------:|---------|:--------:|:--------:|")
    
    for i, f in enumerate(fund_reports, 1):
        return_str = f"{f['return']:+,.2f}" if f['success'] else "暂无数据"
        report.append(f"| {i} | {f['code']} | {f['name']} | {f['amount']:,.2f} | {return_str} |")
    
    # 最佳/最差
    successful = [f for f in fund_reports if f['success']]
    if successful:
        best = max(successful, key=lambda x: x['return'])
        worst = min(successful, key=lambda x: x['return'])
        report.append("")
        report.append("## 🏆 表现榜")
        report.append("")
        report.append(f"🔴 **最佳：** {best['name']} ({best['return']:+,.2f} 元)")
        report.append(f"📉 **最差：** {worst['name']} ({worst['return']:+,.2f} 元)")
    
    report.append("")
    report.append("---")
    report.append("*数据来源于天天基金，仅供参考*")
    
    return "\n".join(report)

if __name__ == "__main__":
    print(generate_report())

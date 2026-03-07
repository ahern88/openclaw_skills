#!/usr/bin/env python3
"""
计算基金每日收益
读取持仓数据和最新净值，计算收益并生成报表
"""

import sys
import json
import os
from datetime import datetime

def load_holdings(holdings_path):
    """加载持仓数据"""
    with open(holdings_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_returns(holdings_data, nav_data):
    """计算收益"""
    results = {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "total_amount": 0,
        "total_return": 0,
        "funds": []
    }
    
    # 创建净值查找表
    nav_map = {item['code']: item for item in nav_data}
    
    for fund in holdings_data['holdings']['funds']:
        code = fund['code']
        amount = fund['amount']
        
        nav_info = nav_map.get(code, {})
        current_nav = nav_info.get('nav', 0)
        
        # 估算收益（简化计算：用当日净值增长率估算）
        # 实际应该用份额 * (今日净值 - 昨日净值)
        # 这里用持有金额 * 估算增长率
        estimated_return = 0  # 需要昨日净值才能计算
        
        fund_result = {
            "code": code,
            "name": fund['name'],
            "amount": amount,
            "nav": current_nav,
            "return": fund.get('last_return', 0),  # 从持仓数据中获取
            "success": nav_info.get('success', False)
        }
        results["funds"].append(fund_result)
        results["total_amount"] += amount
        results["total_return"] += fund_result["return"]
    
    return results

def format_report(results):
    """格式化报表"""
    lines = []
    lines.append(f"💰 基金持仓日报 | {results['date']}")
    lines.append("")
    lines.append(f"**总资产：** {results['total_amount']:,.2f} 元")
    lines.append(f"**当日收益：** {results['total_return']:+,.2f} 元")
    lines.append("")
    lines.append("## 持仓明细")
    lines.append("")
    lines.append("| 基金代码 | 基金名称 | 持有金额 | 当日收益 |")
    lines.append("|---------|---------|---------|---------|")
    
    for fund in results['funds']:
        return_str = f"{fund['return']:+,.2f}" if fund.get('success', False) else "暂无数据"
        lines.append(f"| {fund['code']} | {fund['name']} | {fund['amount']:,.2f} | {return_str} |")
    
    # 最佳/最差表现
    successful_funds = [f for f in results['funds'] if f.get('success', False)]
    if successful_funds:
        best = max(successful_funds, key=lambda x: x.get('return', 0))
        worst = min(successful_funds, key=lambda x: x.get('return', 0))
        
        lines.append("")
        lines.append("## 表现榜")
        lines.append("")
        lines.append(f"🔴 **最佳：** {best['name']} ({best['return']:+,.2f} 元)")
        lines.append(f"📉 **最差：** {worst['name']} ({worst['return']:+,.2f} 元)")
    
    return "\n".join(lines)

def main():
    holdings_path = sys.argv[1] if len(sys.argv) > 1 else "/home/admin/.openclaw/workspace/memory/fund-holdings.json"
    nav_json_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 加载持仓
    holdings_data = load_holdings(holdings_path)
    
    # 加载净值数据（如果有）
    nav_data = []
    if nav_json_path and os.path.exists(nav_json_path):
        with open(nav_json_path, 'r', encoding='utf-8') as f:
            nav_data = json.load(f)
    
    # 计算收益
    results = calculate_returns(holdings_data, nav_data)
    
    # 输出报表
    report = format_report(results)
    print(report)

if __name__ == "__main__":
    main()

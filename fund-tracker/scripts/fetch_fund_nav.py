#!/usr/bin/env python3
"""
获取基金净值数据
通过天天基金 API 获取基金净值
"""

import sys
import json
import urllib.request
import re
from datetime import datetime

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
            
            # 解析 jsonpgz 格式：jsonpgz({"fund_code":"002943","name":"广发多因子混合",...})
            match = re.search(r'jsonpgz\((.+)\)', content)
            if match:
                data = json.loads(match.group(1))
                return {
                    "code": data.get('fund_code'),
                    "name": data.get('name'),
                    "nav": float(data.get('gsz', data.get('dwjz', 0))),  # 估算净值或单位净值
                    "nav_date": data.get('gztime', datetime.now().strftime('%Y-%m-%d')),
                    "nav_unit": float(data.get('dwjz', 0)),  # 单位净值
                    "nav_accum": float(data.get('ljjz', 0)),  # 累计净值
                    "success": True
                }
    except Exception as e:
        print(f"Error fetching {fund_code}: {e}", file=sys.stderr)
    
    return {
        "code": fund_code,
        "success": False,
        "error": str(e) if 'e' in locals() else "Unknown error"
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_fund_nav.py <fund_code> [fund_code2 ...]")
        sys.exit(1)
    
    fund_codes = sys.argv[1:]
    results = []
    
    for code in fund_codes:
        print(f"Fetching {code}...", file=sys.stderr)
        data = fetch_fund_nav(code)
        results.append(data)
    
    # 输出 JSON 格式
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

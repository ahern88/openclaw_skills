#!/usr/bin/env python3
"""
基金组合回测工具 - 天天基金网实时数据版
"""

import argparse
import json
import os
import sys
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


class TiantianFundBacktester:
    def __init__(self, fund_codes, weights, start_date="2019-01-01", end_date=None,
                 rebalance_month=1, initial_capital=1000000,
                 cache_dir="~/.openclaw/workspace/skills/fund-optimizer/cache"):
        self.fund_codes = fund_codes
        self.weights = np.array(weights)
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        self.rebalance_month = rebalance_month
        self.initial_capital = initial_capital
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.nav_data = None
        self.portfolio_nav = None
        self.rebalance_dates = []
    
    def fetch_fund_nav(self, fund_code):
        """使用天天基金 pingzhongdata JS 接口获取历史净值"""
        cache_file = self.cache_dir / f"{fund_code}_nav.csv"
        
        # 检查缓存
        if cache_file.exists():
            cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - cache_time < timedelta(days=7):
                try:
                    df = pd.read_csv(cache_file, parse_dates=['净值日期'])
                    df = df[(df['净值日期'] >= self.start_date) & (df['净值日期'] <= self.end_date)]
                    if len(df) > 0:
                        print("  ✓ 缓存：{} 条".format(len(df)))
                        return df
                except:
                    pass
        
        print("  📡 获取...", end=" ", flush=True)
        
        url = "http://fund.eastmoney.com/pingzhongdata/{}.js".format(fund_code)
        headers = [
            '-H', 'Referer: http://fund.eastmoney.com/',
            '-H', 'User-Agent: Mozilla/5.0',
        ]
        
        result = subprocess.run(
            ['curl', '-s', url] + headers,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, timeout=30
        )
        
        if result.returncode != 0 or not result.stdout.strip():
            print("❌ 请求失败")
            return pd.DataFrame()
        
        # 解析 JS 中的 Data_netWorthTrend
        content = result.stdout
        try:
            # 提取 Data_netWorthTrend 数组
            import re
            match = re.search(r'Data_netWorthTrend\s*=\s*(\[.*?\]);', content, re.DOTALL)
            if not match:
                print("❌ 未找到数据")
                return pd.DataFrame()
            
            data_str = match.group(1)
            data = json.loads(data_str)
            
            if not data:
                print("❌ 空数据")
                return pd.DataFrame()
            
            # 转换为 DataFrame
            df = pd.DataFrame(data)
            # x 是毫秒时间戳，y 是净值
            df['净值日期'] = pd.to_datetime(df['x'], unit='ms')
            df['单位净值'] = df['y']
            df = df[['净值日期', '单位净值']].copy()
            df = df.dropna()
            
            # 过滤日期
            df = df[(df['净值日期'] >= self.start_date) & (df['净值日期'] <= self.end_date)]
            
            df.to_csv(cache_file, index=False)
            print("✓ {} 条".format(len(df)))
            return df
            
        except Exception as e:
            print("❌ 解析失败：{}".format(e))
            return pd.DataFrame()
    
    def load_all_funds_data(self):
        if self.nav_data is not None:
            return self.nav_data
        
        all_nav = {}
        for code in self.fund_codes:
            print("\n基金 {}:".format(code))
            df = self.fetch_fund_nav(code)
            if df.empty:
                print("⚠️  跳过")
                continue
            df = df.set_index('净值日期')['单位净值']
            df = df.rename(code)
            all_nav[code] = df
        
        if not all_nav:
            raise ValueError("未能获取任何基金数据")
        
        self.nav_data = pd.DataFrame(all_nav).sort_index().ffill().dropna()
        print("\n✅ 数据加载完成：{} 个交易日".format(len(self.nav_data)))
        return self.nav_data
    
    def get_rebalance_dates(self):
        if self.nav_data is None:
            self.load_all_funds_data()
        
        dates = []
        for year in sorted(set(self.nav_data.index.year)):
            mask = (self.nav_data.index.year == year) & (self.nav_data.index.month == self.rebalance_month)
            month_dates = self.nav_data.index[mask]
            if len(month_dates) > 0:
                dates.append(month_dates[0])
        
        self.rebalance_dates = dates
        return dates
    
    def run_backtest(self):
        if self.nav_data is None:
            self.load_all_funds_data()
        
        rebal_dates = self.get_rebalance_dates()
        if not rebal_dates:
            raise ValueError("未找到再平衡日期")
        
        values, dates_list = [], []
        capital = self.initial_capital
        
        print("\n🚀 回测：{:,} 元，{} 次再平衡".format(self.initial_capital, len(rebal_dates)))
        
        for i, rebal_date in enumerate(rebal_dates):
            end_date = rebal_dates[i + 1] - pd.Timedelta(days=1) if i < len(rebal_dates) - 1 else self.nav_data.index[-1]
            end_date = min(end_date, self.nav_data.index[-1])
            
            mask = (self.nav_data.index >= rebal_date) & (self.nav_data.index <= end_date)
            seg_nav = self.nav_data[mask]
            
            if len(seg_nav) == 0:
                continue
            
            normalized = seg_nav / seg_nav.iloc[0]
            seg_port = normalized.dot(self.weights) * capital
            
            values.extend(seg_port.values)
            dates_list.extend(seg_nav.index.tolist())
            capital = seg_port.iloc[-1]
        
        self.portfolio_nav = pd.Series(values, index=pd.to_datetime(dates_list))
        print("✅ 完成：{} 天".format(len(self.portfolio_nav)))
        
        return self.calc_metrics()
    
    def calc_metrics(self):
        total_days = (self.portfolio_nav.index[-1] - self.portfolio_nav.index[0]).days
        total_years = total_days / 365.25
        
        total_return = (self.portfolio_nav.iloc[-1] - self.initial_capital) / self.initial_capital
        cagr = (self.portfolio_nav.iloc[-1] / self.initial_capital) ** (1 / total_years) - 1
        
        rolling_max = self.portfolio_nav.cummax()
        drawdown = (self.portfolio_nav - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        daily_ret = self.portfolio_nav.pct_change().dropna()
        volatility = daily_ret.std() * np.sqrt(252)
        
        sharpe = (cagr - 0.03) / volatility if volatility > 0 else 0
        calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # 年度收益
        yearly = []
        for year in sorted(set(self.portfolio_nav.index.year)):
            y_nav = self.portfolio_nav[self.portfolio_nav.index.year == year]
            if len(y_nav) < 2:
                continue
            ret = (y_nav.iloc[-1] - y_nav.iloc[0]) / y_nav.iloc[0]
            dd = ((y_nav - y_nav.cummax()) / y_nav.cummax()).min()
            yearly.append({'year': year, 'return': ret, 'max_drawdown': dd})
        
        # 季度收益
        quarterly = []
        for year in sorted(set(self.portfolio_nav.index.year)):
            for q in range(1, 5):
                q_nav = self.portfolio_nav[
                    (self.portfolio_nav.index.year == year) &
                    (self.portfolio_nav.index.month >= (q-1)*3+1) &
                    (self.portfolio_nav.index.month <= q*3)
                ]
                if len(q_nav) < 2:
                    continue
                quarterly.append({'year': year, 'quarter': 'Q{}'.format(q), 'return': (q_nav.iloc[-1]-q_nav.iloc[0])/q_nav.iloc[0]})
        
        return {
            'total_return': total_return, 'cagr': cagr, 'max_drawdown': max_drawdown,
            'volatility': volatility, 'sharpe_ratio': sharpe, 'calmar_ratio': calmar,
            'total_days': total_days, 'total_years': total_years,
            'initial_capital': self.initial_capital, 'final_value': self.portfolio_nav.iloc[-1],
            'yearly_returns': yearly, 'quarterly_returns': quarterly,
            'rebalance_dates': [d.strftime('%Y-%m-%d') for d in self.rebalance_dates],
            'fund_codes': self.fund_codes, 'weights': self.weights.tolist()
        }
    
    def report(self, m):
        lines = [
            "=" * 70,
            "📊 基金组合回测（天天基金实时数据）",
            "=" * 70, "",
            "📋 配置:"
        ]
        for c, w in zip(m['fund_codes'], m['weights']):
            lines.append("   {} {:.1f}%".format(c, w*100))
        lines.extend([
            "", "回测：{} ~ {}".format(self.start_date, self.end_date),
            "再平衡：每年{} 月 ({} 次)".format(self.rebalance_month, len(m['rebalance_dates'])),
            "资金：{:,} → {:,} 元".format(int(m['initial_capital']), int(m['final_value'])),
            "天数：{} ({:.2f} 年)".format(m['total_days'], m['total_years']),
            "", "📈 指标:", "-" * 50,
            "累计收益： {:+.2f}%".format(m['total_return']*100),
            "年化收益： {:+.2f}%".format(m['cagr']*100),
            "波动率：   {:.2f}%".format(m['volatility']*100),
            "最大回撤： {:+.2f}%".format(m['max_drawdown']*100),
            "夏普比率： {:.2f}".format(m['sharpe_ratio']),
            "卡玛比率： {:.2f}".format(m['calmar_ratio']),
            "", "📅 年度:", "-" * 50
        ])
        for y in m['yearly_returns']:
            lines.append("  {}: {:+.2f}% (回撤：{:+.2f}%)".format(y['year'], y['return']*100, y['max_drawdown']*100))
        lines.extend(["", "=" * 70, "⚠️  历史数据不代表未来", "=" * 70])
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--funds', required=True)
    parser.add_argument('--weights', required=True)
    parser.add_argument('--start-date', default='2019-01-01')
    parser.add_argument('--end-date')
    parser.add_argument('--rebalance-month', type=int, default=1)
    parser.add_argument('--initial-capital', type=float, default=1000000)
    parser.add_argument('--json', action='store_true')
    
    args = parser.parse_args()
    
    funds = [c.strip() for c in args.funds.split(',')]
    weights = [float(w.strip()) for w in args.weights.split(',')]
    
    if abs(sum(weights) - 1.0) > 0.01:
        print("❌ 权重和必须为 1: {}".format(sum(weights)))
        sys.exit(1)
    
    if len(funds) != len(weights):
        print("❌ 基金数与权重数不匹配")
        sys.exit(1)
    
    bt = TiantianFundBacktester(
        fund_codes=funds, weights=weights, start_date=args.start_date,
        end_date=args.end_date, rebalance_month=args.rebalance_month,
        initial_capital=args.initial_capital
    )
    
    try:
        m = bt.run_backtest()
        if args.json:
            print(json.dumps(m, indent=2, default=str))
        else:
            print(bt.report(m))
    except Exception as e:
        print("❌ 失败：{}".format(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

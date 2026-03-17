#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金组合回测工具 - 腾讯证券 API 版
数据源：腾讯证券基金接口
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import subprocess

import numpy as np
import pandas as pd


class TencentFundBacktester:
    """腾讯证券 API 基金回测器"""
    
    def __init__(self, fund_codes, weights, start_date="2019-01-01", end_date=None,
                 rebalance_month=1, initial_capital=1000000,
                 cache_dir="~/.openclaw/workspace/skills/fund-optimizer/cache"):
        self.fund_codes = fund_codes
        self.target_weights = np.array(weights)
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        self.rebalance_month = rebalance_month
        self.initial_capital = initial_capital
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.nav_data = None
        self.portfolio_values = None
        self.rebalance_log = []
    
    def fetch_fund_nav_tencent(self, fund_code):
        """从腾讯证券获取基金净值数据"""
        cache_file = self.cache_dir / f"{fund_code}_tencent_nav.csv"
        
        # 尝试读取缓存
        if cache_file.exists():
            try:
                df = pd.read_csv(cache_file, parse_dates=['净值日期'])
                df = df[(df['净值日期'] >= self.start_date) & (df['净值日期'] <= self.end_date)]
                if len(df) > 0:
                    print(f"  ✓ 缓存：{len(df)} 条")
                    return df
            except:
                pass
        
        print(f"  📡 腾讯 API 获取...", end=" ")
        
        # 腾讯证券基金净值接口
        all_data = []
        page = 1
        
        while True:
            try:
                url = f"http://api.fund.qq.com/f10/lsjz?fundcode={fund_code}&page={page}&pagesize=100"
                result = subprocess.run(
                    ['curl', '-s', '-m', '10', url],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    universal_newlines=True, timeout=15
                )
                
                if not result.stdout.strip():
                    break
                
                data = json.loads(result.stdout)
                fund_list = data.get('data', {}).get('list', [])
                
                if not fund_list:
                    break
                
                for item in fund_list:
                    nav_date = item.get('fsrq', '')
                    unit_nav = item.get('dwjz', '')
                    if nav_date and unit_nav:
                        all_data.append({
                            '净值日期': nav_date,
                            '单位净值': float(unit_nav)
                        })
                
                if len(fund_list) < 100:
                    break
                
                page += 1
                time.sleep(0.2)
                
            except Exception as e:
                print(f"获取失败：{e}")
                break
        
        if not all_data:
            # 备用接口：腾讯基金详情
            try:
                url = f"http://fund.gtimg.cn/fund/net/{fund_code}.js"
                result = subprocess.run(
                    ['curl', '-s', '-m', '10', url],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    universal_newlines=True, timeout=15
                )
                if result.stdout and 'data' in result.stdout:
                    # 解析腾讯基金数据
                    pass
            except:
                pass
        
        if not all_data:
            print("✗ 无数据")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_data)
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df = df.dropna(subset=['单位净值'])
        df = df[(df['净值日期'] >= self.start_date) & (df['净值日期'] <= self.end_date)]
        df = df.sort_values('净值日期').drop_duplicates('净值日期', keep='last')
        
        # 保存到缓存
        df.to_csv(cache_file, index=False)
        print(f"✓ {len(df)} 条")
        
        return df
    
    def load_all_funds_data(self):
        """加载所有基金数据"""
        if self.nav_data is not None:
            return self.nav_data
        
        print("\n📊 从腾讯证券加载基金数据...")
        all_nav = {}
        
        for code in self.fund_codes:
            df = self.fetch_fund_nav_tencent(code)
            if df.empty:
                continue
            df = df.set_index('净值日期')['单位净值']
            df = df.rename(code)
            all_nav[code] = df
        
        if not all_nav:
            raise ValueError("未能获取任何基金数据")
        
        # 合并数据，前向填充
        self.nav_data = pd.DataFrame(all_nav).sort_index().ffill().dropna()
        print(f"\n✅ 数据加载完成：{len(self.nav_data)} 个交易日")
        
        return self.nav_data
    
    def get_annual_rebalance_dates(self):
        """获取年度再平衡日期"""
        dates = []
        for year in sorted(set(self.nav_data.index.year)):
            mask = (self.nav_data.index.year == year) & (self.nav_data.index.month == self.rebalance_month)
            month_dates = self.nav_data.index[mask]
            if len(month_dates) > 0:
                dates.append(month_dates[0])
        return dates
    
    def run_backtest(self):
        """运行回测"""
        if self.nav_data is None:
            self.load_all_funds_data()
        
        annual_dates = set(self.get_annual_rebalance_dates())
        
        capital = self.initial_capital
        current_weights = self.target_weights.copy()
        portfolio_values = []
        portfolio_dates = []
        
        initial_nav = self.nav_data.iloc[0]
        shares = (capital * self.target_weights) / initial_nav
        
        last_rebalance_date = self.nav_data.index[0]
        
        print(f"\n🚀 回测：{self.initial_capital:,.0f} 元，{len(annual_dates)} 次再平衡")
        
        rebalance_count = 0
        
        for i, (date, nav) in enumerate(self.nav_data.iterrows()):
            current_values = shares * nav
            total_value = current_values.sum()
            current_weights = current_values / total_value
            
            need_rebalance = False
            rebalance_reason = ""
            
            if date in annual_dates and date > last_rebalance_date:
                need_rebalance = True
                rebalance_reason = "年度平衡"
                rebalance_count += 1
            
            if need_rebalance:
                self.rebalance_log.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'reason': rebalance_reason,
                    'total_value': total_value
                })
                shares = (total_value * self.target_weights) / nav
                last_rebalance_date = date
            
            portfolio_values.append(total_value)
            portfolio_dates.append(date)
        
        self.portfolio_values = pd.Series(portfolio_values, index=portfolio_dates)
        
        print(f"✅ 完成：{len(portfolio_dates)} 天")
        
        return self.calculate_metrics()
    
    def calculate_metrics(self):
        """计算回测指标"""
        if self.portfolio_values is None:
            self.run_backtest()
        
        total_days = (self.portfolio_values.index[-1] - self.portfolio_values.index[0]).days
        total_years = total_days / 365.25
        
        total_return = (self.portfolio_values.iloc[-1] - self.initial_capital) / self.initial_capital
        cagr = (self.portfolio_values.iloc[-1] / self.initial_capital) ** (1 / total_years) - 1
        
        rolling_max = self.portfolio_values.cummax()
        drawdown = (self.portfolio_values - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        daily_ret = self.portfolio_values.pct_change().dropna()
        volatility = daily_ret.std() * np.sqrt(252)
        
        sharpe = (cagr - 0.03) / volatility if volatility > 0 else 0
        calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0
        
        yearly = []
        for year in sorted(set(self.portfolio_values.index.year)):
            y_nav = self.portfolio_values[self.portfolio_values.index.year == year]
            if len(y_nav) < 2:
                continue
            ret = (y_nav.iloc[-1] - y_nav.iloc[0]) / y_nav.iloc[0]
            dd = ((y_nav - y_nav.cummax()) / y_nav.cummax()).min()
            yearly.append({'year': year, 'return': ret, 'max_drawdown': dd})
        
        return {
            'total_return': total_return,
            'cagr': cagr,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'calmar_ratio': calmar,
            'total_days': total_days,
            'total_years': total_years,
            'initial_capital': self.initial_capital,
            'final_value': self.portfolio_values.iloc[-1],
            'yearly_returns': yearly,
            'rebalance_count': rebalance_count,
            'fund_codes': self.fund_codes,
            'weights': self.target_weights.tolist()
        }


def main():
    parser = argparse.ArgumentParser(description='基金组合回测 - 腾讯证券 API')
    parser.add_argument('--funds', required=True, help='基金代码，逗号分隔')
    parser.add_argument('--weights', required=True, help='权重，逗号分隔')
    parser.add_argument('--start-date', default='2019-01-01', help='开始日期')
    parser.add_argument('--end-date', help='结束日期')
    parser.add_argument('--rebalance-month', type=int, default=1, help='年度平衡月份')
    parser.add_argument('--initial-capital', type=float, default=1000000, help='初始资金')
    parser.add_argument('--json', action='store_true', help='输出 JSON')
    
    args = parser.parse_args()
    
    funds = [c.strip() for c in args.funds.split(',')]
    weights = [float(w.strip()) for w in args.weights.split(',')]
    
    if abs(sum(weights) - 1.0) > 0.01:
        print(f"❌ 权重和必须为 1: {sum(weights)}")
        sys.exit(1)
    
    if len(funds) != len(weights):
        print("❌ 基金数与权重数不匹配")
        sys.exit(1)
    
    bt = TencentFundBacktester(
        fund_codes=funds,
        weights=weights,
        start_date=args.start_date,
        end_date=args.end_date,
        rebalance_month=args.rebalance_month,
        initial_capital=args.initial_capital
    )
    
    metrics = bt.run_backtest()
    
    if args.json:
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    else:
        m = metrics
        print("\n" + "=" * 70)
        print("📊 基金组合回测报告（腾讯证券数据）")
        print("=" * 70)
        print(f"\n累计收益：{m['total_return']*100:+.2f}%")
        print(f"年化收益：{m['cagr']*100:+.2f}%")
        print(f"最大回撤：{m['max_drawdown']*100:+.2f}%")
        print(f"夏普比率：{m['sharpe_ratio']:.2f}")
        print(f"卡玛比率：{m['calmar_ratio']:.2f}")
        print(f"\n资金：{int(m['initial_capital']):,} → {int(m['final_value']):,} 元")
        print("=" * 70)


if __name__ == "__main__":
    main()

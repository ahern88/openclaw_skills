#!/usr/bin/env python3
"""
基金组合对比回测 - 红利低波加入方案对比
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

class PortfolioBacktester:
    def __init__(self, portfolio: dict, start_date: str = "2019-09-24", end_date: str = None):
        self.portfolio = portfolio
        self.fund_codes = list(portfolio.keys())
        self.fund_names = {code: info['name'] for code, info in portfolio.items()}
        self.weights = np.array([info['weight'] for code, info in portfolio.items()])
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        self.cache_dir = Path("~/.openclaw/workspace/skills/fund-optimizer/cache").expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.nav_data = None
        self.returns = None
        
    def fetch_fund_nav(self, fund_code: str) -> pd.DataFrame:
        cache_file = self.cache_dir / f"{fund_code}_nav.csv"
        if cache_file.exists():
            try:
                df = pd.read_csv(cache_file, parse_dates=['净值日期'])
                return df
            except:
                pass
        
        try:
            df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
            df.to_csv(cache_file, index=False)
            return df
        except Exception as e:
            print(f"  ✗ {fund_code} - 失败：{e}")
            return None
    
    def load_data(self, show_progress=False):
        if self.nav_data is not None:
            return self.nav_data
        
        all_nav = {}
        for code in self.fund_codes:
            if show_progress:
                print(f"获取 {code}...")
            df = self.fetch_fund_nav(code)
            if df is None or len(df) == 0:
                continue
            
            if '净值日期' in df.columns:
                df = df[['净值日期', '单位净值']].copy()
                df.columns = ['date', 'nav']
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')['nav']
                df = df.rename(code)
                all_nav[code] = df
        
        self.nav_data = pd.DataFrame(all_nav).sort_index()
        self.nav_data = self.nav_data[(self.nav_data.index >= self.start_date) & (self.nav_data.index <= self.end_date)]
        self.nav_data = self.nav_data.ffill().dropna()
        self.returns = self.nav_data.pct_change().dropna()
        return self.nav_data
    
    def backtest_yearly_rebalance(self):
        if self.nav_data is None:
            self.load_data()
        
        nav = self.nav_data.copy()
        weights = self.weights.copy()
        initial_capital = 1000000
        
        start_date = nav.index[0]
        current_date = start_date
        
        shares = {}
        for i, code in enumerate(self.fund_codes):
            if code in nav.columns:
                price = nav.loc[current_date, code]
                allocation = initial_capital * weights[i]
                shares[code] = allocation / price
        
        last_rebalance_date = current_date
        daily_values = []
        
        for date in nav.index:
            daily_value = sum(shares.get(code, 0) * nav.loc[date, code] for code in self.fund_codes if code in nav.columns)
            daily_values.append({'date': date, 'value': daily_value, 'nav': daily_value / initial_capital})
            
            if (date - last_rebalance_date).days >= 365:
                new_shares = {}
                for i, code in enumerate(self.fund_codes):
                    if code in nav.columns:
                        price = nav.loc[date, code]
                        allocation = daily_value * weights[i]
                        new_shares[code] = allocation / price
                shares = new_shares
                last_rebalance_date = date
        
        portfolio_df = pd.DataFrame(daily_values).set_index('date')
        
        total_return = (portfolio_df['nav'].iloc[-1] - 1) * 100
        days = (portfolio_df.index[-1] - portfolio_df.index[0]).days
        years = days / 365.25
        annualized_return = ((portfolio_df['nav'].iloc[-1]) ** (1 / years) - 1) * 100
        
        rolling_max = portfolio_df['nav'].cummax()
        drawdown = (portfolio_df['nav'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100
        
        daily_returns = portfolio_df['nav'].pct_change().dropna()
        annualized_vol = daily_returns.std() * np.sqrt(252) * 100
        
        risk_free_rate = 3.0
        sharpe_ratio = (annualized_return - risk_free_rate) / annualized_vol if annualized_vol > 0 else 0
        
        return {
            'years': years,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'annualized_volatility': annualized_vol,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'final_value': portfolio_df['nav'].iloc[-1] * initial_capital
        }


def main():
    print("=" * 80)
    print("🔬 红利低波加入方案对比回测")
    print("=" * 80)
    print()
    
    # 原组合
    portfolio_original = {
        '110017': {'name': '易方达增强回报债券 A', 'weight': 0.078},
        '002943': {'name': '广发多因子混合', 'weight': 0.152},
        '000216': {'name': '华安黄金 ETF 联接 A', 'weight': 0.08},
        '159985': {'name': '豆粕 ETF', 'weight': 0.102},
        '217022': {'name': '招商产业债券 A', 'weight': 0.15},
        '004011': {'name': '华泰柏瑞鼎利混合 C', 'weight': 0.12},
        '004993': {'name': '中欧可转债债券 A', 'weight': 0.04},
        '539001': {'name': '建信纳斯达克 100 指数 (QDII)', 'weight': 0.03},
        '166301': {'name': '华商新趋势混合', 'weight': 0.078},
        '006373': {'name': '国富全球科技互联混合 (QDII)', 'weight': 0.05},
        '002849': {'name': '金信智能中国 2025 混合', 'weight': 0.12}
    }
    
    # 方案 A：卖出 5.2% 豆粕 → 3.2% 红利低波 + 2% 恒生科技
    portfolio_A = portfolio_original.copy()
    portfolio_A['159985']['weight'] = 0.05
    portfolio_A['005561'] = {'name': '中证红利低波 ETF 联接 A', 'weight': 0.032}
    portfolio_A['005885'] = {'name': '恒生科技 ETF 联接 A', 'weight': 0.02}
    
    # 方案 B：卖出 5% 豆粕 → 5% 红利低波
    portfolio_B = portfolio_original.copy()
    portfolio_B['159985']['weight'] = 0.052
    portfolio_B['005561'] = {'name': '中证红利低波 ETF 联接 A', 'weight': 0.05}
    
    # 方案 C：卖出 3% 豆粕 → 3% 红利低波
    portfolio_C = portfolio_original.copy()
    portfolio_C['159985']['weight'] = 0.072
    portfolio_C['005561'] = {'name': '中证红利低波 ETF 联接 A', 'weight': 0.03}
    
    # 方案 D：卖出 3% 豆粕 + 2% 金信 → 5% 红利低波
    portfolio_D = portfolio_original.copy()
    portfolio_D['159985']['weight'] = 0.072
    portfolio_D['002849']['weight'] = 0.10
    portfolio_D['005561'] = {'name': '中证红利低波 ETF 联接 A', 'weight': 0.05}
    
    scenarios = [
        ('原组合', portfolio_original, '📊'),
        ('方案 A: 豆粕→红利低波 + 恒生科技', portfolio_A, '🔀'),
        ('方案 B: 豆粕→红利低波 5%', portfolio_B, '💰'),
        ('方案 C: 豆粕→红利低波 3%', portfolio_C, '📈'),
        ('方案 D: 豆粕 + 金信→红利低波 5%', portfolio_D, '⚖️'),
    ]
    
    results = []
    
    for name, portfolio, emoji in scenarios:
        print(f"{emoji} 回测：{name}...")
        backtester = PortfolioBacktester(portfolio)
        backtester.load_data()
        result = backtester.backtest_yearly_rebalance()
        result['name'] = name
        result['emoji'] = emoji
        results.append(result)
        print(f"  年化：{result['annualized_return']:.2f}% | 回撤：{result['max_drawdown']:.2f}% | 夏普：{result['sharpe_ratio']:.2f}")
    
    print()
    print("=" * 80)
    print("📊 对比结果")
    print("=" * 80)
    print()
    
    print(f"{'方案':<25} {'年化收益':>12} {'最大回撤':>12} {'夏普比率':>12} {'累计收益':>12} {'期末价值':>12}")
    print("-" * 95)
    
    for r in results:
        final_value_str = f"¥{r['final_value']/10000:.0f}万"
        print(f"{r['name']:<25} {r['annualized_return']:>11.2f}% {r['max_drawdown']:>11.2f}% {r['sharpe_ratio']:>12.2f} {r['total_return']:>11.2f}% {final_value_str:>12}")
    
    print()
    print("=" * 80)
    print("💡 推荐分析")
    print("=" * 80)
    
    # 找出最佳
    best_return = max(results, key=lambda x: x['annualized_return'])
    best_sharpe = max(results, key=lambda x: x['sharpe_ratio'])
    lowest_drawdown = min(results, key=lambda x: x['max_drawdown'])
    
    print(f"🏆 年化收益最高：{best_return['name']} ({best_return['annualized_return']:.2f}%)")
    print(f"🏆 夏普比率最高：{best_sharpe['name']} ({best_sharpe['sharpe_ratio']:.2f})")
    print(f"🏆 回撤最小：{lowest_drawdown['name']} ({lowest_drawdown['max_drawdown']:.2f}%)")
    
    print()
    print("=" * 80)
    print("🎯 最终推荐")
    print("=" * 80)
    print()
    
    # 综合评分
    for r in results:
        if r['name'] == '原组合':
            continue
        score = (r['annualized_return'] * 0.4 + (10 - abs(r['max_drawdown'])) * 0.3 + r['sharpe_ratio'] * 10 * 0.3)
        r['score'] = score
    
    best_overall = max([r for r in results if r['name'] != '原组合'], key=lambda x: x['score'])
    
    print(f"✅ 推荐：{best_overall['name']}")
    print()
    print("理由:")
    print(f"  • 年化收益：{best_overall['annualized_return']:.2f}%")
    print(f"  • 最大回撤：{best_overall['max_drawdown']:.2f}%")
    print(f"  • 夏普比率：{best_overall['sharpe_ratio']:.2f}")
    print()

if __name__ == '__main__':
    main()

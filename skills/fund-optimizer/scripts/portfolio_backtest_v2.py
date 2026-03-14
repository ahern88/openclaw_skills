#!/usr/bin/env python3
"""
基金组合回测工具 - 年平衡策略（版本 2）
对比原组合 vs 新组合
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
                print(f"  ✓ {fund_code} - 缓存")
                return df
            except:
                pass
        
        try:
            df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
            df.to_csv(cache_file, index=False)
            print(f"  ✓ {fund_code} - API")
            return df
        except Exception as e:
            print(f"  ✗ {fund_code} - 失败：{e}")
            return None
    
    def load_data(self):
        if self.nav_data is not None:
            return self.nav_data
        
        all_nav = {}
        for code in self.fund_codes:
            print(f"获取 {code} ({self.fund_names[code]})...")
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
        
        print(f"\n数据加载完成：{len(self.nav_data)} 个交易日")
        print(f"日期范围：{self.nav_data.index.min().strftime('%Y-%m-%d')} 至 {self.nav_data.index.max().strftime('%Y-%m-%d')}")
        return self.nav_data
    
    def backtest_yearly_rebalance(self):
        if self.nav_data is None:
            self.load_data()
        
        nav = self.nav_data.copy()
        weights = self.weights.copy()
        initial_capital = 1000000
        capital = initial_capital
        
        start_date = nav.index[0]
        current_date = start_date
        
        shares = {}
        for i, code in enumerate(self.fund_codes):
            if code in nav.columns:
                price = nav.loc[current_date, code]
                allocation = capital * weights[i]
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
        
        fund_contributions = {}
        for i, code in enumerate(self.fund_codes):
            if code in nav.columns:
                fund_return = (nav.loc[nav.index[-1], code] / nav.loc[nav.index[0], code] - 1) * 100
                weighted_contribution = fund_return * weights[i]
                fund_contributions[code] = {
                    'name': self.fund_names[code],
                    'weight': weights[i] * 100,
                    'return': fund_return,
                    'contribution': weighted_contribution
                }
        
        return {
            'start_date': portfolio_df.index[0].strftime('%Y-%m-%d'),
            'end_date': portfolio_df.index[-1].strftime('%Y-%m-%d'),
            'trading_days': len(portfolio_df),
            'years': years,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'annualized_volatility': annualized_vol,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'initial_capital': initial_capital,
            'final_value': portfolio_df['nav'].iloc[-1] * initial_capital,
            'fund_contributions': fund_contributions
        }
    
    def generate_report(self, result: dict, title: str = "基金组合回测报告") -> str:
        report = []
        report.append("=" * 75)
        report.append(f"📊 {title}")
        report.append("=" * 75)
        report.append("")
        report.append(f"📅 回测区间：{result['start_date']} 至 {result['end_date']} ({result['years']:.2f}年)")
        report.append("")
        report.append("📈 核心指标:")
        report.append("-" * 50)
        report.append(f"  累计收益率：  {result['total_return']:>10.2f}%")
        report.append(f"  年化收益率：  {result['annualized_return']:>10.2f}%")
        report.append(f"  年化波动率：  {result['annualized_volatility']:>10.2f}%")
        report.append(f"  最大回撤：    {result['max_drawdown']:>10.2f}%")
        report.append(f"  夏普比率：    {result['sharpe_ratio']:>10.2f}")
        report.append("")
        report.append("💰 资金变化:")
        report.append(f"  初始资金：    ¥{result['initial_capital']:>10,.0f}")
        report.append(f"  期末价值：    ¥{result['final_value']:>10,.0f}")
        report.append(f"  绝对收益：    ¥{result['final_value'] - result['initial_capital']:>10,.0f}")
        report.append("")
        report.append("📋 基金明细:")
        report.append("-" * 75)
        report.append(f"{'代码':<10} {'名称':<25} {'权重':>8} {'收益':>10} {'贡献':>10}")
        report.append("-" * 75)
        for code, info in result['fund_contributions'].items():
            report.append(f"{code:<10} {info['name']:<25} {info['weight']:>7.1f}% {info['return']:>9.2f}% {info['contribution']:>9.2f}%")
        report.append("-" * 75)
        return "\n".join(report)


def main():
    print("=" * 75)
    print("🔬 基金组合对比回测 - 年平衡策略")
    print("=" * 75)
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
    
    # 新组合：卖出 5.2% 豆粕，买入 3.2% 红利低波 + 2% 恒生科技
    portfolio_new = {
        '110017': {'name': '易方达增强回报债券 A', 'weight': 0.078},
        '002943': {'name': '广发多因子混合', 'weight': 0.152},
        '000216': {'name': '华安黄金 ETF 联接 A', 'weight': 0.08},
        '159985': {'name': '豆粕 ETF', 'weight': 0.05},  # 从 10.2% 降到 5%
        '217022': {'name': '招商产业债券 A', 'weight': 0.15},
        '004011': {'name': '华泰柏瑞鼎利混合 C', 'weight': 0.12},
        '004993': {'name': '中欧可转债债券 A', 'weight': 0.04},
        '539001': {'name': '建信纳斯达克 100 指数 (QDII)', 'weight': 0.03},
        '166301': {'name': '华商新趋势混合', 'weight': 0.078},
        '006373': {'name': '国富全球科技互联混合 (QDII)', 'weight': 0.05},
        '002849': {'name': '金信智能中国 2025 混合', 'weight': 0.12},
        # 新增基金
        '005561': {'name': '中证红利低波 ETF 联接 A', 'weight': 0.032},  # 新增 3.2%
        '005885': {'name': '恒生科技 ETF 联接 A', 'weight': 0.02}  # 新增 2%
    }
    
    # 验证权重
    total_orig = sum(info['weight'] for info in portfolio_original.values())
    total_new = sum(info['weight'] for info in portfolio_new.values())
    print(f"原组合权重总和：{total_orig:.4f}")
    print(f"新组合权重总和：{total_new:.4f}")
    print()
    
    # 回测原组合
    print("=" * 75)
    print("📊 回测原组合...")
    print("=" * 75)
    backtester_orig = PortfolioBacktester(portfolio_original, start_date="2019-09-24")
    result_orig = backtester_orig.backtest_yearly_rebalance()
    report_orig = backtester_orig.generate_report(result_orig, "原组合回测报告")
    print(report_orig)
    print()
    
    # 回测新组合
    print("=" * 75)
    print("📊 回测新组合...")
    print("=" * 75)
    backtester_new = PortfolioBacktester(portfolio_new, start_date="2019-09-24")
    result_new = backtester_new.backtest_yearly_rebalance()
    report_new = backtester_new.generate_report(result_new, "新组合回测报告")
    print(report_new)
    print()
    
    # 对比分析
    print("=" * 75)
    print("📈 组合对比分析")
    print("=" * 75)
    print()
    print(f"{'指标':<20} {'原组合':>15} {'新组合':>15} {'变化':>15}")
    print("-" * 75)
    print(f"{'年化收益率':<20} {result_orig['annualized_return']:>14.2f}% {result_new['annualized_return']:>14.2f}% {(result_new['annualized_return']-result_orig['annualized_return']):>+14.2f}%")
    print(f"{'最大回撤':<20} {result_orig['max_drawdown']:>14.2f}% {result_new['max_drawdown']:>14.2f}% {(result_new['max_drawdown']-result_orig['max_drawdown']):>+14.2f}%")
    print(f"{'年化波动率':<20} {result_orig['annualized_volatility']:>14.2f}% {result_new['annualized_volatility']:>14.2f}% {(result_new['annualized_volatility']-result_orig['annualized_volatility']):>+14.2f}%")
    print(f"{'夏普比率':<20} {result_orig['sharpe_ratio']:>14.2f} {result_new['sharpe_ratio']:>14.2f} {(result_new['sharpe_ratio']-result_orig['sharpe_ratio']):>+14.2f}")
    print(f"{'累计收益率':<20} {result_orig['total_return']:>14.2f}% {result_new['total_return']:>14.2f}% {(result_new['total_return']-result_orig['total_return']):>+14.2f}%")
    print(f"{'期末价值 (万)':<20} {result_orig['final_value']/10000:>14.0f} {result_new['final_value']/10000:>14.0f} {(result_new['final_value']-result_orig['final_value'])/10000:>+14.0f}")
    print()
    
    # 结论
    print("=" * 75)
    print("💡 结论与建议")
    print("=" * 75)
    
    if result_new['annualized_return'] > result_orig['annualized_return']:
        print("✅ 新组合年化收益更高")
    else:
        print("⚠️ 新组合年化收益略低")
    
    if result_new['max_drawdown'] > result_orig['max_drawdown']:
        print("⚠️ 新组合最大回撤更大（风险增加）")
    else:
        print("✅ 新组合最大回撤更小（风险降低）")
    
    if result_new['sharpe_ratio'] > result_orig['sharpe_ratio']:
        print("✅ 新组合夏普比率更高（风险收益比更好）")
    else:
        print("⚠️ 新组合夏普比率略低")
    
    print()
    print("📊 调整说明:")
    print("  - 卖出 5.2% 豆粕 ETF（高位止盈）")
    print("  - 买入 3.2% 红利低波（稳健增值）")
    print("  - 买入 2% 恒生科技（港股科技弹性）")
    print()

if __name__ == '__main__':
    main()

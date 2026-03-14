#!/usr/bin/env python3
"""
基金组合回测工具 - 年平衡策略
计算指定基金组合从 2019-09-24 至今的年化收益和最大回撤
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# 尝试导入 akshare
try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False
    print("警告：akshare 未安装")


class PortfolioBacktester:
    """基金组合回测器 - 年平衡策略"""
    
    def __init__(
        self,
        portfolio: Dict[str, Dict],
        start_date: str = "2019-09-24",
        end_date: Optional[str] = None,
        cache_dir: str = "~/.openclaw/workspace/skills/fund-optimizer/cache"
    ):
        self.portfolio = portfolio
        self.fund_codes = list(portfolio.keys())
        self.fund_names = {code: info['name'] for code, info in portfolio.items()}
        self.initial_weights = np.array([info['weight'] for code, info in portfolio.items()])
        
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.nav_data: Optional[pd.DataFrame] = None
        self.returns: Optional[pd.DataFrame] = None
        
    def fetch_fund_nav(self, fund_code: str) -> pd.DataFrame:
        """获取基金历史净值数据"""
        cache_file = self.cache_dir / f"{fund_code}_nav.csv"
        
        # 检查缓存（30 天内有效）
        if cache_file.exists():
            cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - cache_time < timedelta(days=30):
                try:
                    df = pd.read_csv(cache_file, parse_dates=['净值日期'])
                    print(f"  ✓ {fund_code} - 从缓存加载")
                    return df
                except:
                    pass
        
        # 获取数据
        if HAS_AKSHARE:
            try:
                df = ak.fund_open_fund_info_em(
                    symbol=fund_code,
                    indicator="单位净值走势"
                )
                # 缓存数据
                df.to_csv(cache_file, index=False)
                print(f"  ✓ {fund_code} - 从 API 获取")
                return df
            except Exception as e:
                print(f"  ✗ {fund_code} - 获取失败：{e}")
        
        return None
    
    def load_data(self) -> pd.DataFrame:
        """加载所有基金数据"""
        if self.nav_data is not None:
            return self.nav_data
        
        all_nav = {}
        for code in self.fund_codes:
            print(f"正在获取基金 {code} ({self.fund_names[code]}) 数据...")
            df = self.fetch_fund_nav(code)
            
            if df is None:
                print(f"  跳过 {code}")
                continue
            
            # 数据清洗
            if '净值日期' in df.columns:
                date_col = '净值日期'
                nav_col = '单位净值'
            elif 'date' in df.columns:
                date_col = 'date'
                nav_col = 'nav'
            else:
                print(f"  基金 {code} 数据格式未知，跳过")
                continue
            
            df = df[[date_col, nav_col]].copy()
            df.columns = ['date', 'nav']
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')['nav']
            df = df.rename(code)
            
            all_nav[code] = df
        
        # 合并数据
        self.nav_data = pd.DataFrame(all_nav)
        self.nav_data = self.nav_data.sort_index()
        
        # 过滤日期范围
        self.nav_data = self.nav_data[
            (self.nav_data.index >= self.start_date) & 
            (self.nav_data.index <= self.end_date)
        ]
        
        # 前向填充缺失值（不同基金可能有不同的交易日）
        self.nav_data = self.nav_data.ffill()
        
        # 删除仍有 NaN 的行
        self.nav_data = self.nav_data.dropna()
        
        # 计算日收益率
        self.returns = self.nav_data.pct_change().dropna()
        
        print(f"\n数据加载完成：{len(self.nav_data)} 个交易日")
        print(f"日期范围：{self.nav_data.index.min().strftime('%Y-%m-%d')} 至 {self.nav_data.index.max().strftime('%Y-%m-%d')}")
        return self.nav_data
    
    def backtest_yearly_rebalance(self) -> Dict:
        """执行年平衡回测"""
        if self.nav_data is None:
            self.load_data()
        
        nav = self.nav_data.copy()
        weights = self.initial_weights.copy()
        
        # 初始投资
        initial_capital = 1000000  # 100 万初始资金
        capital = initial_capital
        
        # 记录组合净值
        portfolio_values = []
        dates = nav.index.tolist()
        
        # 找到第一个 rebalance 日期
        start_date = nav.index[0]
        current_date = start_date
        
        # 第一次建仓
        shares = {}
        for i, code in enumerate(self.fund_codes):
            if code in nav.columns:
                price = nav.loc[current_date, code]
                allocation = capital * weights[i]
                shares[code] = allocation / price
        
        last_rebalance_date = current_date
        daily_values = []
        
        # 逐日计算组合价值
        for date in nav.index:
            # 计算当日组合价值
            daily_value = 0
            for code in self.fund_codes:
                if code in nav.columns and code in shares:
                    daily_value += shares[code] * nav.loc[date, code]
            
            daily_values.append({
                'date': date,
                'value': daily_value,
                'nav': daily_value / initial_capital
            })
            
            # 检查是否需要年平衡（距离上次 rebalance 超过 1 年）
            if (date - last_rebalance_date).days >= 365:
                # Rebalance：调整到目标权重
                new_shares = {}
                for i, code in enumerate(self.fund_codes):
                    if code in nav.columns:
                        price = nav.loc[date, code]
                        allocation = daily_value * weights[i]
                        new_shares[code] = allocation / price
                shares = new_shares
                last_rebalance_date = date
        
        # 转换为 DataFrame
        portfolio_df = pd.DataFrame(daily_values).set_index('date')
        
        # 计算指标
        total_return = (portfolio_df['nav'].iloc[-1] - 1) * 100
        
        # 年化收益率
        days = (portfolio_df.index[-1] - portfolio_df.index[0]).days
        years = days / 365.25
        annualized_return = ((portfolio_df['nav'].iloc[-1]) ** (1 / years) - 1) * 100
        
        # 最大回撤
        rolling_max = portfolio_df['nav'].cummax()
        drawdown = (portfolio_df['nav'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100
        
        # 年化波动率
        daily_returns = portfolio_df['nav'].pct_change().dropna()
        annualized_vol = daily_returns.std() * np.sqrt(252) * 100
        
        # 夏普比率（假设无风险利率 3%）
        risk_free_rate = 3.0
        sharpe_ratio = (annualized_return - risk_free_rate) / annualized_vol if annualized_vol > 0 else 0
        
        # 各基金贡献
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
            'fund_contributions': fund_contributions,
            'portfolio_nav': portfolio_df['nav'].tolist(),
            'portfolio_dates': portfolio_df.index.strftime('%Y-%m-%d').tolist()
        }
    
    def generate_report(self, result: Dict) -> str:
        """生成回测报告"""
        report = []
        report.append("=" * 70)
        report.append("📊 基金组合回测报告（年平衡策略）")
        report.append("=" * 70)
        report.append("")
        
        # 回测区间
        report.append("📅 回测区间:")
        report.append(f"   {result['start_date']} 至 {result['end_date']}")
        report.append(f"   共 {result['trading_days']} 个交易日，{result['years']:.2f} 年")
        report.append("")
        
        # 核心指标
        report.append("📈 核心指标:")
        report.append("-" * 50)
        report.append(f"   累计收益率：    {result['total_return']:>10.2f}%")
        report.append(f"   年化收益率：    {result['annualized_return']:>10.2f}%")
        report.append(f"   年化波动率：    {result['annualized_volatility']:>10.2f}%")
        report.append(f"   最大回撤：      {result['max_drawdown']:>10.2f}%")
        report.append(f"   夏普比率：      {result['sharpe_ratio']:>10.2f}")
        report.append("")
        
        # 资金变化
        report.append("💰 资金变化:")
        report.append(f"   初始资金：      ¥{result['initial_capital']:,.0f}")
        report.append(f"   期末价值：      ¥{result['final_value']:,.0f}")
        report.append(f"   绝对收益：      ¥{result['final_value'] - result['initial_capital']:,.0f}")
        report.append("")
        
        # 基金明细
        report.append("📋 基金明细及贡献:")
        report.append("-" * 70)
        report.append(f"{'代码':<10} {'名称':<25} {'权重':>8} {'收益':>10} {'贡献':>10}")
        report.append("-" * 70)
        
        for code, info in result['fund_contributions'].items():
            report.append(
                f"{code:<10} {info['name']:<25} {info['weight']:>7.1f}% "
                f"{info['return']:>9.2f}% {info['contribution']:>9.2f}%"
            )
        report.append("")
        
        # 风险提示
        report.append("=" * 70)
        report.append("⚠️ 风险提示:")
        report.append("   1. 历史数据不代表未来表现")
        report.append("   2. 回测未考虑申购赎回费用")
        report.append("   3. 年平衡策略假设每年调仓一次，实际可能有偏差")
        report.append("   4. QDII 基金可能存在数据延迟")
        report.append("=" * 70)
        
        return "\n".join(report)


def main():
    # 用户的基金组合
    portfolio = {
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
    
    # 验证权重总和
    total_weight = sum(info['weight'] for info in portfolio.values())
    print(f"权重总和：{total_weight:.4f}")
    if abs(total_weight - 1.0) > 0.01:
        print(f"警告：权重总和不为 1，当前为 {total_weight}")
    
    # 创建回测器
    backtester = PortfolioBacktester(
        portfolio=portfolio,
        start_date="2019-09-24",
        end_date=datetime.now().strftime("%Y-%m-%d")
    )
    
    # 执行回测
    print("\n开始回测...\n")
    result = backtester.backtest_yearly_rebalance()
    
    # 生成报告
    report = backtester.generate_report(result)
    print("\n" + report)
    
    # 输出 JSON 结果
    print("\n\n📄 JSON 结果:")
    print(json.dumps({
        'start_date': result['start_date'],
        'end_date': result['end_date'],
        'years': round(result['years'], 2),
        'annualized_return': round(result['annualized_return'], 2),
        'max_drawdown': round(result['max_drawdown'], 2),
        'sharpe_ratio': round(result['sharpe_ratio'], 2),
        'total_return': round(result['total_return'], 2)
    }, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()

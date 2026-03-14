#!/usr/bin/env python3
"""
基金组合回测工具 - 支持年平衡策略
计算年化收益、最大回撤、卡玛比率、季度/年度收益列表
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import calendar

import numpy as np
import pandas as pd

# 尝试导入 akshare
try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False
    print("警告：akshare 未安装，将使用模拟数据")


class FundBacktester:
    """基金组合回测器"""
    
    def __init__(
        self,
        fund_codes: List[str],
        weights: List[float],
        start_date: str = "2019-01-01",
        end_date: Optional[str] = None,
        rebalance_month: int = 1,  # 1 月再平衡
        initial_capital: float = 1000000,
        cache_dir: str = "~/.openclaw/workspace/skills/fund-optimizer/cache"
    ):
        self.fund_codes = fund_codes
        self.weights = np.array(weights)
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        self.rebalance_month = rebalance_month
        self.initial_capital = initial_capital
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.nav_data: Optional[pd.DataFrame] = None
        self.returns: Optional[pd.DataFrame] = None
        self.portfolio_nav: Optional[pd.Series] = None
        self.rebalance_dates: List[str] = []
        
    def fetch_fund_nav(self, fund_code: str) -> pd.DataFrame:
        """获取基金历史净值数据"""
        cache_file = self.cache_dir / f"{fund_code}_nav.csv"
        
        # 检查缓存（7 天内有效）
        if cache_file.exists():
            cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - cache_time < timedelta(days=7):
                try:
                    df = pd.read_csv(cache_file, parse_dates=['净值日期'])
                    return df
                except:
                    pass
        
        # 获取数据
        if HAS_AKSHARE:
            try:
                df = ak.fund_open_fund_info_em(
                    fund=fund_code,
                    indicator="单位净值走势"
                )
                # 缓存数据
                df.to_csv(cache_file, index=False)
                return df
            except Exception as e:
                print(f"获取基金 {fund_code} 数据失败：{e}")
        
        # 返回模拟数据（用于测试）
        return self._generate_mock_data(fund_code)
    
    def _generate_mock_data(self, fund_code: str) -> pd.DataFrame:
        """生成模拟数据（当无法获取真实数据时）"""
        np.random.seed(hash(fund_code) % 2**32)
        dates = pd.date_range(self.start_date, self.end_date, freq='B')
        
        # 根据基金代码生成不同特征的模拟数据
        base_return = 0.0003 + np.random.randn() * 0.0002
        volatility = 0.01 + np.random.rand() * 0.015
        
        nav = 1.0
        nav_list = []
        for _ in dates:
            nav *= (1 + base_return + np.random.randn() * volatility)
            nav_list.append(nav)
        
        return pd.DataFrame({
            '净值日期': dates,
            '单位净值': nav_list
        })
    
    def load_data(self) -> pd.DataFrame:
        """加载所有基金数据并计算收益率"""
        if self.nav_data is not None:
            return self.nav_data
        
        all_nav = {}
        for code in self.fund_codes:
            print(f"正在获取基金 {code} 数据...")
            df = self.fetch_fund_nav(code)
            
            # 数据清洗
            if '净值日期' in df.columns:
                date_col = '净值日期'
                nav_col = '单位净值'
            elif 'date' in df.columns:
                date_col = 'date'
                nav_col = 'nav'
            else:
                print(f"基金 {code} 数据格式未知，跳过")
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
        
        # 前向填充缺失值
        self.nav_data = self.nav_data.ffill()
        
        # 计算日收益率
        self.returns = self.nav_data.pct_change().dropna()
        
        print(f"数据加载完成：{len(self.nav_data)} 个交易日")
        return self.nav_data
    
    def get_rebalance_dates(self) -> List[pd.Timestamp]:
        """获取再平衡日期列表（每年指定月份）"""
        if self.nav_data is None:
            self.load_data()
        
        rebalance_dates = []
        years = sorted(set(self.nav_data.index.year))
        
        for year in years:
            # 获取指定月份的所有交易日
            month_mask = (
                (self.nav_data.index.year == year) & 
                (self.nav_data.index.month == self.rebalance_month)
            )
            month_dates = self.nav_data.index[month_mask]
            
            if len(month_dates) > 0:
                # 选择第一个交易日作为再平衡日
                rebalance_dates.append(month_dates[0])
        
        self.rebalance_dates = rebalance_dates
        return rebalance_dates
    
    def run_backtest(self) -> Dict:
        """运行回测（年平衡策略）"""
        if self.nav_data is None:
            self.load_data()
        
        # 获取再平衡日期
        rebalance_dates = self.get_rebalance_dates()
        
        # 初始化
        portfolio_values = []
        portfolio_dates = []
        
        # 初始持仓
        capital = self.initial_capital
        weights = self.weights.copy()
        
        print(f"开始回测，初始资金：{self.initial_capital:,.0f} 元")
        print(f"再平衡月份：每年 {self.rebalance_month} 月")
        
        # 按再平衡周期分段计算
        for i, rebalance_date in enumerate(rebalance_dates):
            # 确定本段的结束日期
            if i < len(rebalance_dates) - 1:
                end_date = rebalance_dates[i + 1] - pd.Timedelta(days=1)
            else:
                end_date = self.nav_data.index[-1]
            
            # 确保结束日期在数据范围内
            end_date = min(end_date, self.nav_data.index[-1])
            
            # 获取本段数据
            segment_mask = (
                (self.nav_data.index >= rebalance_date) & 
                (self.nav_data.index <= end_date)
            )
            segment_nav = self.nav_data[segment_mask]
            
            if len(segment_nav) == 0:
                continue
            
            # 计算本段组合净值
            # 归一化净值
            normalized_nav = segment_nav / segment_nav.iloc[0]
            
            # 组合净值
            segment_portfolio = normalized_nav.dot(weights)
            
            # 转换为实际金额
            if i == 0:
                segment_portfolio = segment_portfolio * capital
            else:
                segment_portfolio = segment_portfolio * capital
            
            portfolio_values.extend(segment_portfolio.values)
            portfolio_dates.extend(segment_nav.index.tolist())
            
            # 更新资本（再平衡时的市值）
            capital = segment_portfolio.iloc[-1]
        
        # 创建组合净值序列
        self.portfolio_nav = pd.Series(
            portfolio_values,
            index=pd.to_datetime(portfolio_dates),
            name='portfolio'
        )
        
        print(f"回测完成：{len(self.portfolio_nav)} 个交易日")
        
        # 计算各项指标
        return self.calculate_all_metrics()
    
    def calculate_all_metrics(self) -> Dict:
        """计算所有回测指标"""
        if self.portfolio_nav is None:
            self.run_backtest()
        
        # 基础指标
        total_days = (self.portfolio_nav.index[-1] - self.portfolio_nav.index[0]).days
        total_years = total_days / 365.25
        
        # 累计收益
        total_return = (self.portfolio_nav.iloc[-1] - self.initial_capital) / self.initial_capital
        
        # 年化收益率
        cagr = (self.portfolio_nav.iloc[-1] / self.initial_capital) ** (1 / total_years) - 1
        
        # 最大回撤
        rolling_max = self.portfolio_nav.cummax()
        drawdown = (self.portfolio_nav - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # 年化波动率
        daily_returns = self.portfolio_nav.pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252)
        
        # 夏普比率（假设无风险利率 3%）
        risk_free_rate = 0.03
        sharpe_ratio = (cagr - risk_free_rate) / volatility
        
        # 卡玛比率
        calmar_ratio = cagr / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # 年度收益列表
        yearly_returns = self.calculate_yearly_returns()
        
        # 季度收益列表
        quarterly_returns = self.calculate_quarterly_returns()
        
        # 月度收益列表
        monthly_returns = self.calculate_monthly_returns()
        
        return {
            'total_return': total_return,
            'cagr': cagr,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'calmar_ratio': calmar_ratio,
            'total_days': total_days,
            'total_years': total_years,
            'initial_capital': self.initial_capital,
            'final_value': self.portfolio_nav.iloc[-1],
            'yearly_returns': yearly_returns,
            'quarterly_returns': quarterly_returns,
            'monthly_returns': monthly_returns,
            'rebalance_dates': [d.strftime('%Y-%m-%d') for d in self.rebalance_dates],
            'fund_codes': self.fund_codes,
            'weights': self.weights.tolist()
        }
    
    def calculate_yearly_returns(self) -> List[Dict]:
        """计算年度收益列表"""
        if self.portfolio_nav is None:
            return []
        
        yearly = []
        years = sorted(set(self.portfolio_nav.index.year))
        
        for year in years:
            year_mask = self.portfolio_nav.index.year == year
            year_nav = self.portfolio_nav[year_mask]
            
            if len(year_nav) < 2:
                continue
            
            start_value = year_nav.iloc[0]
            end_value = year_nav.iloc[-1]
            year_return = (end_value - start_value) / start_value
            
            # 计算该年最大回撤
            rolling_max = year_nav.cummax()
            drawdown = (year_nav - rolling_max) / rolling_max
            year_max_dd = drawdown.min()
            
            yearly.append({
                'year': year,
                'return': year_return,
                'start_value': start_value,
                'end_value': end_value,
                'max_drawdown': year_max_dd
            })
        
        return yearly
    
    def calculate_quarterly_returns(self) -> List[Dict]:
        """计算季度收益列表"""
        if self.portfolio_nav is None:
            return []
        
        quarterly = []
        years = sorted(set(self.portfolio_nav.index.year))
        
        for year in years:
            for quarter in range(1, 5):
                # 季度月份范围
                month_start = (quarter - 1) * 3 + 1
                month_end = quarter * 3
                
                quarter_mask = (
                    (self.portfolio_nav.index.year == year) &
                    (self.portfolio_nav.index.month >= month_start) &
                    (self.portfolio_nav.index.month <= month_end)
                )
                quarter_nav = self.portfolio_nav[quarter_mask]
                
                if len(quarter_nav) < 2:
                    continue
                
                start_value = quarter_nav.iloc[0]
                end_value = quarter_nav.iloc[-1]
                quarter_return = (end_value - start_value) / start_value
                
                quarterly.append({
                    'year': year,
                    'quarter': f'Q{quarter}',
                    'return': quarter_return,
                    'start_value': start_value,
                    'end_value': end_value
                })
        
        return quarterly
    
    def calculate_monthly_returns(self) -> List[Dict]:
        """计算月度收益列表"""
        if self.portfolio_nav is None:
            return []
        
        monthly = []
        years = sorted(set(self.portfolio_nav.index.year))
        
        for year in years:
            for month in range(1, 13):
                month_mask = (
                    (self.portfolio_nav.index.year == year) &
                    (self.portfolio_nav.index.month == month)
                )
                month_nav = self.portfolio_nav[month_mask]
                
                if len(month_nav) < 2:
                    continue
                
                start_value = month_nav.iloc[0]
                end_value = month_nav.iloc[-1]
                month_return = (end_value - start_value) / start_value
                
                monthly.append({
                    'year': year,
                    'month': month,
                    'return': month_return,
                    'start_value': start_value,
                    'end_value': end_value
                })
        
        return monthly
    
    def generate_report(self, metrics: Dict) -> str:
        """生成回测报告"""
        report = []
        report.append("=" * 70)
        report.append("📊 基金组合回测报告（年平衡策略）")
        report.append("=" * 70)
        report.append("")
        
        # 基本信息
        report.append("📋 组合信息:")
        report.append("-" * 50)
        for i, (code, weight) in enumerate(zip(metrics['fund_codes'], metrics['weights'])):
            report.append(f"  {i+1}. {code}: {weight*100:.1f}%")
        report.append("")
        report.append(f"回测期间：{self.start_date} 至 {self.end_date}")
        report.append(f"再平衡：每年 {self.rebalance_month} 月")
        report.append(f"初始资金：{metrics['initial_capital']:,.0f} 元")
        report.append(f"最终市值：{metrics['final_value']:,.2f} 元")
        report.append(f"交易天数：{metrics['total_days']} 天 ({metrics['total_years']:.2f} 年)")
        report.append("")
        
        # 核心指标
        report.append("📈 核心指标:")
        report.append("-" * 50)
        report.append(f"累计收益率：  {metrics['total_return']*100:>10.2f}%")
        report.append(f"年化收益率：  {metrics['cagr']*100:>10.2f}%")
        report.append(f"年化波动率：  {metrics['volatility']*100:>10.2f}%")
        report.append(f"最大回撤：    {metrics['max_drawdown']*100:>10.2f}%")
        report.append(f"夏普比率：    {metrics['sharpe_ratio']:>10.2f}")
        report.append(f"卡玛比率：    {metrics['calmar_ratio']:>10.2f}")
        report.append("")
        
        # 年度收益
        report.append("📅 年度收益列表:")
        report.append("-" * 50)
        report.append(f"{'年份':<8} {'收益率':>12} {'最大回撤':>12} {'起止市值':>20}")
        report.append("-" * 50)
        for year_data in metrics['yearly_returns']:
            report.append(
                f"{year_data['year']:<8} "
                f"{year_data['return']*100:>+11.2f}% "
                f"{year_data['max_drawdown']*100:>+11.2f}% "
                f"{year_data['start_value']:,.0f}→{year_data['end_value']:,.0f}"
            )
        report.append("")
        
        # 季度收益
        report.append("📅 季度收益列表:")
        report.append("-" * 50)
        report.append(f"{'年份':<8} {'Q1':>10} {'Q2':>10} {'Q3':>10} {'Q4':>10}")
        report.append("-" * 50)
        
        # 按年份分组季度数据
        years = sorted(set(q['year'] for q in metrics['quarterly_returns']))
        for year in years:
            year_quarters = [q for q in metrics['quarterly_returns'] if q['year'] == year]
            row = f"{year:<8} "
            for q in year_quarters:
                row += f"{q['return']*100:>+9.2f}% "
            report.append(row)
        report.append("")
        
        # 再平衡日期
        report.append("🔄 再平衡日期:")
        report.append("-" * 50)
        for i, date in enumerate(metrics['rebalance_dates']):
            if i < 10:
                report.append(f"  {date}")
            elif i == 10:
                report.append(f"  ... 共 {len(metrics['rebalance_dates'])} 次再平衡")
                break
        report.append("")
        
        report.append("=" * 70)
        report.append("⚠️ 风险提示：历史数据不代表未来表现，投资需谨慎")
        report.append("=" * 70)
        
        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description='基金组合回测工具')
    parser.add_argument('--funds', required=True, help='基金代码列表，逗号分隔')
    parser.add_argument('--weights', required=True, help='配置比例，逗号分隔')
    parser.add_argument('--start-date', default='2019-01-01', help='开始日期')
    parser.add_argument('--end-date', help='结束日期（默认今天）')
    parser.add_argument('--rebalance-month', type=int, default=1, help='再平衡月份（1-12，默认 1 月）')
    parser.add_argument('--initial-capital', type=float, default=1000000, help='初始资金')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    
    args = parser.parse_args()
    
    # 解析参数
    fund_codes = args.funds.split(',')
    weights = [float(w) for w in args.weights.split(',')]
    
    # 验证权重
    if abs(sum(weights) - 1.0) > 0.01:
        print(f"错误：权重总和必须为 1，当前为 {sum(weights)}")
        sys.exit(1)
    
    if len(fund_codes) != len(weights):
        print(f"错误：基金数量 ({len(fund_codes)}) 与权重数量 ({len(weights)}) 不匹配")
        sys.exit(1)
    
    # 创建回测器
    backtester = FundBacktester(
        fund_codes=fund_codes,
        weights=weights,
        start_date=args.start_date,
        end_date=args.end_date,
        rebalance_month=args.rebalance_month,
        initial_capital=args.initial_capital
    )
    
    # 运行回测
    metrics = backtester.run_backtest()
    
    # 输出结果
    if args.json:
        print(json.dumps(metrics, indent=2, ensure_ascii=False, default=str))
    else:
        report = backtester.generate_report(metrics)
        print(report)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
基金组合优化器 v2 - 支持年平衡再平衡和 Top N 组合
基于现代投资组合理论 (MPT)
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd

# 尝试导入 akshare
try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False
    print("⚠️  警告：akshare 未安装，将使用模拟数据")

# 尝试导入 scipy 用于优化
try:
    from scipy.optimize import minimize
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


class FundOptimizer:
    """基金组合优化器 - 支持年平衡再平衡"""
    
    def __init__(
        self,
        fund_codes: List[str],
        fund_names: Dict[str, str],
        initial_weights: List[float],
        start_date: str = "2019-01-01",
        end_date: Optional[str] = None,
        risk_free_rate: float = 0.03,
        cache_dir: str = "~/.cache/fund-optimizer"
    ):
        self.fund_codes = fund_codes
        self.fund_names = fund_names
        self.initial_weights = np.array(initial_weights)
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        self.risk_free_rate = risk_free_rate
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.nav_data: Optional[pd.DataFrame] = None
        self.returns: Optional[pd.DataFrame] = None
        
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
                df.to_csv(cache_file, index=False)
                return df
            except Exception as e:
                print(f"获取基金 {fund_code} 数据失败：{e}")
        
        # 返回模拟数据
        return self._generate_mock_data(fund_code)
    
    def _generate_mock_data(self, fund_code: str) -> pd.DataFrame:
        """生成模拟数据"""
        np.random.seed(hash(fund_code) % 2**32)
        dates = pd.date_range(self.start_date, self.end_date, freq='B')
        
        # 根据基金类型生成不同特征
        bond_funds = ['110017', '217022', '004993']
        gold_funds = ['000216']
        commodity_funds = ['159985']
        qdii_funds = ['539001', '006373']
        
        if fund_code in bond_funds:
            base_return = 0.0002
            volatility = 0.003
        elif fund_code in gold_funds:
            base_return = 0.0004
            volatility = 0.012
        elif fund_code in commodity_funds:
            base_return = 0.0003
            volatility = 0.015
        elif fund_code in qdii_funds:
            base_return = 0.0005
            volatility = 0.018
        else:
            base_return = 0.00035
            volatility = 0.014
        
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
        """加载所有基金数据"""
        if self.nav_data is not None:
            return self.nav_data
        
        all_nav = {}
        for code in self.fund_codes:
            print(f"  获取基金 {code} 数据...")
            df = self.fetch_fund_nav(code)
            
            if '净值日期' in df.columns:
                date_col = '净值日期'
                nav_col = '单位净值'
            else:
                continue
            
            df = df[[date_col, nav_col]].copy()
            df.columns = ['date', 'nav']
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')['nav']
            df = df.rename(code)
            
            all_nav[code] = df
        
        self.nav_data = pd.DataFrame(all_nav)
        self.nav_data = self.nav_data.sort_index()
        self.nav_data = self.nav_data[
            (self.nav_data.index >= self.start_date) & 
            (self.nav_data.index <= self.end_date)
        ]
        
        self.returns = self.nav_data.pct_change().dropna()
        
        print(f"✓ 数据加载完成：{len(self.nav_data)} 个交易日 ({self.start_date} ~ {self.end_date})")
        return self.nav_data
    
    def calculate_yearly_rebalance_returns(
        self, 
        weights: np.ndarray
    ) -> pd.Series:
        """计算年平衡再平衡策略的累计收益"""
        if self.nav_data is None:
            self.load_data()
        
        # 获取每年最后一个交易日
        yearly_dates = self.nav_data.resample('Y').last().dropna().index
        
        if len(yearly_dates) < 2:
            # 数据不足，使用简单持有
            portfolio_nav = (self.nav_data / self.nav_data.iloc[0]).dot(weights)
            return portfolio_nav
        
        # 初始化
        portfolio_value = 1.0
        result = []
        result_dates = []
        
        current_weights = weights.copy()
        
        for i in range(len(yearly_dates)):
            year_end = yearly_dates[i]
            if i == 0:
                year_start = self.nav_data.index[0]
            else:
                year_start = yearly_dates[i-1]
            
            # 获取这一年内的数据
            year_data = self.nav_data[(self.nav_data.index >= year_start) & 
                                       (self.nav_data.index <= year_end)]
            
            if len(year_data) < 2:
                continue
            
            # 计算这一年内的组合收益
            year_nav = (year_data / year_data.iloc[0])
            year_returns = year_nav.dot(current_weights)
            
            # 年末组合价值
            portfolio_value *= year_returns.iloc[-1]
            
            result.append(portfolio_value)
            result_dates.append(year_end)
            
            # 再平衡：重置权重为初始比例
            current_weights = weights.copy()
        
        return pd.Series(result, index=result_dates)
    
    def calculate_metrics(self, weights: np.ndarray) -> Dict:
        """计算组合各项指标"""
        if self.returns is None:
            self.load_data()
        
        # 年平衡收益曲线
        portfolio_returns = self.calculate_yearly_rebalance_returns(weights)
        
        # 年化收益率
        n_years = len(self.nav_data) / 252
        total_return = portfolio_returns.iloc[-1] / portfolio_returns.iloc[0] - 1
        annual_return = (1 + total_return) ** (1/n_years) - 1
        
        # 年化波动率（使用日收益计算）
        daily_portfolio_returns = self.returns.dot(weights)
        annual_volatility = daily_portfolio_returns.std() * np.sqrt(252)
        
        # 夏普比率（玛卡率）
        sharpe_ratio = (annual_return - self.risk_free_rate) / annual_volatility
        
        # 最大回撤
        cumulative = (1 + daily_portfolio_returns).cumprod()
        rolling_max = cumulative.cummax()
        drawdown = (cumulative - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # 最大收益（最佳年份收益）
        yearly_returns = portfolio_returns.pct_change().dropna()
        max_yearly_return = yearly_returns.max() if len(yearly_returns) > 0 else 0
        
        return {
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_yearly_return': max_yearly_return,
            'total_return': total_return
        }
    
    def optimize_top_n(
        self, 
        simulations: int = 50000,
        top_n: int = 10
    ) -> List[Dict]:
        """寻找 Top N 最优组合（按夏普比率）"""
        if self.returns is None:
            self.load_data()
        
        n_funds = len(self.fund_codes)
        
        print(f"🚀 开始蒙特卡洛模拟 ({simulations:,} 次)...")
        
        all_results = []
        
        for i in range(simulations):
            # 随机生成权重
            weights = np.random.random(n_funds)
            weights = weights / weights.sum()
            
            # 计算指标
            metrics = self.calculate_metrics(weights)
            
            all_results.append({
                'weights': weights.tolist(),
                **metrics
            })
            
            if (i + 1) % 10000 == 0:
                print(f"  进度：{i + 1:,}/{simulations:,}")
        
        # 按夏普比率排序
        all_results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        
        # 返回 Top N
        top_results = all_results[:top_n]
        
        # 计算初始组合指标
        initial_metrics = self.calculate_metrics(self.initial_weights)
        
        print(f"✓ 优化完成！最佳夏普比率：{top_results[0]['sharpe_ratio']:.3f}")
        
        return {
            'top_combinations': top_results,
            'initial_metrics': initial_metrics,
            'fund_codes': self.fund_codes,
            'fund_names': self.fund_names
        }
    
    def generate_report(self, results: Dict) -> str:
        """生成详细报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("📊 基金组合优化报告 - Top 10 最优组合 (年平衡再平衡)")
        lines.append("=" * 80)
        lines.append("")
        
        # 基金列表
        lines.append("📋 基金池:")
        for code, name in results['fund_names'].items():
            lines.append(f"  • {code} - {name}")
        lines.append("")
        
        # 回测区间
        lines.append(f"📅 回测区间：{self.start_date} ~ {self.end_date}")
        lines.append(f"🔄 再平衡策略：年平衡")
        lines.append("")
        
        # 初始组合指标
        init = results['initial_metrics']
        lines.append("📈 初始组合表现:")
        lines.append("-" * 60)
        lines.append(f"  年化收益率：  {init['annual_return']:>8.2%}")
        lines.append(f"  年化波动率：  {init['annual_volatility']:>8.2%}")
        lines.append(f"  夏普比率：    {init['sharpe_ratio']:>8.3f}")
        lines.append(f"  最大回撤：    {init['max_drawdown']:>8.2%}")
        lines.append(f"  最大年收益：  {init['max_yearly_return']:>8.2%}")
        lines.append("")
        
        # Top 10 组合
        lines.append("🏆 Top 10 最优组合 (按夏普比率排序):")
        lines.append("=" * 80)
        
        for i, combo in enumerate(results['top_combinations'], 1):
            lines.append("")
            lines.append(f"【第 {i} 名】夏普比率：{combo['sharpe_ratio']:.3f}")
            lines.append("-" * 60)
            lines.append(f"  年化收益率：  {combo['annual_return']:>8.2%}  |  最大回撤：  {combo['max_drawdown']:>8.2%}")
            lines.append(f"  年化波动率：  {combo['annual_volatility']:>8.2%}  |  最大年收益：{combo['max_yearly_return']:>8.2%}")
            lines.append("")
            lines.append("  配置比例:")
            
            # 按权重排序显示
            weight_pairs = list(zip(results['fund_codes'], combo['weights']))
            weight_pairs.sort(key=lambda x: x[1], reverse=True)
            
            for code, weight in weight_pairs:
                name = results['fund_names'].get(code, '')
                if weight > 0.01:  # 只显示>1% 的
                    lines.append(f"    {code} {name:<20} {weight:>6.1%}")
        
        lines.append("")
        lines.append("=" * 80)
        lines.append("⚠️  风险提示：历史数据不代表未来表现，优化结果仅供参考")
        lines.append("   年平衡策略：每年末再平衡至目标比例")
        lines.append("=" * 80)
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='基金组合优化器 v2')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # optimize 命令
    opt_parser = subparsers.add_parser('optimize', help='优化组合比例')
    opt_parser.add_argument('--funds', required=True, help='基金代码列表，逗号分隔')
    opt_parser.add_argument('--names', help='基金名称列表，逗号分隔（可选）')
    opt_parser.add_argument('--weights', required=True, help='初始配置比例，逗号分隔')
    opt_parser.add_argument('--start-date', default='2019-01-01', help='开始日期')
    opt_parser.add_argument('--end-date', help='结束日期')
    opt_parser.add_argument('--simulations', type=int, default=50000, help='模拟次数')
    opt_parser.add_argument('--top-n', type=int, default=10, help='返回 Top N 组合')
    opt_parser.add_argument('--risk-free-rate', type=float, default=0.03, help='无风险利率')
    opt_parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 解析参数
    fund_codes = [c.strip() for c in args.funds.split(',')]
    weights = [float(w.strip()) for w in args.weights.split(',')]
    
    # 解析名称（如果提供）
    fund_names = {}
    if args.names:
        names = [n.strip() for n in args.names.split(',')]
        for code, name in zip(fund_codes, names):
            fund_names[code] = name
    else:
        fund_names = {code: code for code in fund_codes}
    
    # 验证
    if abs(sum(weights) - 1.0) > 0.01:
        print(f"⚠️  警告：权重总和为 {sum(weights):.2%}，将自动归一化")
        weights = [w/sum(weights) for w in weights]
    
    if len(fund_codes) != len(weights):
        print(f"错误：基金数量 ({len(fund_codes)}) 与权重数量 ({len(weights)}) 不匹配")
        sys.exit(1)
    
    # 创建优化器
    optimizer = FundOptimizer(
        fund_codes=fund_codes,
        fund_names=fund_names,
        initial_weights=weights,
        start_date=args.start_date,
        end_date=args.end_date,
        risk_free_rate=args.risk_free_rate
    )
    
    # 执行优化
    results = optimizer.optimize_top_n(
        simulations=args.simulations,
        top_n=args.top_n
    )
    
    # 输出
    if args.json:
        output = {
            'top_combinations': results['top_combinations'],
            'initial_metrics': results['initial_metrics'],
            'fund_codes': results['fund_codes'],
            'fund_names': results['fund_names']
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        report = optimizer.generate_report(results)
        print(report)


if __name__ == '__main__':
    main()

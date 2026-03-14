#!/usr/bin/env python3
"""
基金组合优化器 - 基于现代投资组合理论 (MPT)
使用历史数据寻找最优基金配置比例
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd

# 尝试导入 akshare
try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False
    print("警告：akshare 未安装，将使用模拟数据")

# 尝试导入 scipy 用于优化
try:
    from scipy.optimize import minimize
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("警告：scipy 未安装，将使用简化优化")


class FundOptimizer:
    """基金组合优化器"""
    
    def __init__(
        self,
        fund_codes: List[str],
        initial_weights: List[float],
        start_date: str = "2019-01-01",
        end_date: Optional[str] = None,
        risk_free_rate: float = 0.03,
        cache_dir: str = "~/.openclaw/workspace/skills/fund-optimizer/cache"
    ):
        self.fund_codes = fund_codes
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
        
        # 计算日收益率
        self.returns = self.nav_data.pct_change().dropna()
        
        print(f"数据加载完成：{len(self.nav_data)} 个交易日")
        return self.nav_data
    
    def calculate_portfolio_metrics(
        self, 
        weights: np.ndarray
    ) -> Tuple[float, float, float]:
        """计算组合指标：预期收益、波动率、夏普比率"""
        if self.returns is None:
            self.load_data()
        
        # 年化收益率（252 个交易日）
        mean_returns = self.returns.mean() * 252
        portfolio_return = np.dot(weights, mean_returns)
        
        # 年化波动率
        cov_matrix = self.returns.cov() * 252
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        
        # 夏普比率
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        return portfolio_return, portfolio_volatility, sharpe_ratio
    
    def calculate_max_drawdown(self, weights: np.ndarray) -> float:
        """计算最大回撤"""
        if self.nav_data is None:
            self.load_data()
        
        # 计算组合净值
        portfolio_nav = (self.nav_data / self.nav_data.iloc[0]).dot(weights)
        
        # 计算回撤
        rolling_max = portfolio_nav.cummax()
        drawdown = (portfolio_nav - rolling_max) / rolling_max
        
        return drawdown.min()
    
    def optimize_portfolio(
        self, 
        simulations: int = 5000
    ) -> Dict:
        """使用蒙特卡洛模拟优化组合"""
        if self.returns is None:
            self.load_data()
        
        n_funds = len(self.fund_codes)
        
        # 存储结果
        results = {
            'weights': [],
            'returns': [],
            'volatilities': [],
            'sharpe_ratios': []
        }
        
        best_sharpe = -np.inf
        best_weights = None
        
        print(f"正在进行蒙特卡洛模拟 ({simulations} 次)...")
        
        for i in range(simulations):
            # 随机生成权重
            weights = np.random.random(n_funds)
            weights = weights / weights.sum()
            
            # 计算指标
            ret, vol, sharpe = self.calculate_portfolio_metrics(weights)
            
            results['weights'].append(weights)
            results['returns'].append(ret)
            results['volatilities'].append(vol)
            results['sharpe_ratios'].append(sharpe)
            
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_weights = weights.copy()
            
            if (i + 1) % 1000 == 0:
                print(f"  进度：{i + 1}/{simulations}")
        
        # 计算最优组合的其他指标
        best_return, best_vol, _ = self.calculate_portfolio_metrics(best_weights)
        best_drawdown = self.calculate_max_drawdown(best_weights)
        
        # 计算初始组合指标
        initial_ret, initial_vol, initial_sharpe = self.calculate_portfolio_metrics(
            self.initial_weights
        )
        initial_drawdown = self.calculate_max_drawdown(self.initial_weights)
        
        return {
            'optimal_weights': best_weights.tolist(),
            'expected_return': best_return,
            'volatility': best_vol,
            'sharpe_ratio': best_sharpe,
            'max_drawdown': best_drawdown,
            'initial_weights': self.initial_weights.tolist(),
            'initial_return': initial_ret,
            'initial_volatility': initial_vol,
            'initial_sharpe': initial_sharpe,
            'initial_drawdown': initial_drawdown,
            'improvement': {
                'return': (best_return - initial_ret) / abs(initial_ret) if initial_ret != 0 else 0,
                'sharpe': (best_sharpe - initial_sharpe) / initial_sharpe if initial_sharpe != 0 else 0,
                'drawdown': (best_drawdown - initial_drawdown) / abs(initial_drawdown) if initial_drawdown != 0 else 0
            },
            'simulation_results': results
        }
    
    def generate_report(self, optimization_result: Dict) -> str:
        """生成优化报告"""
        report = []
        report.append("=" * 60)
        report.append("📊 基金组合优化报告")
        report.append("=" * 60)
        report.append("")
        
        # 基金列表
        report.append("📋 基金列表:")
        for i, code in enumerate(self.fund_codes):
            report.append(f"  {i+1}. {code}")
        report.append("")
        
        # 优化前后对比
        report.append("📈 优化前后对比:")
        report.append("-" * 40)
        report.append(f"{'指标':<20} {'优化前':>12} {'优化后':>12} {'改善':>10}")
        report.append("-" * 40)
        
        opt = optimization_result
        report.append(f"{'年化收益率':<20} {opt['initial_return']:>10.2%} {opt['expected_return']:>10.2%} {opt['improvement']['return']:>+9.1%}")
        report.append(f"{'年化波动率':<20} {opt['initial_volatility']:>10.2%} {opt['volatility']:>10.2%} {(opt['initial_volatility']-opt['volatility'])/opt['initial_volatility']:>+9.1%}")
        report.append(f"{'夏普比率':<20} {opt['initial_sharpe']:>10.2f} {opt['sharpe_ratio']:>10.2f} {opt['improvement']['sharpe']:>+9.1%}")
        report.append(f"{'最大回撤':<20} {opt['initial_drawdown']:>10.2%} {opt['max_drawdown']:>10.2%} {opt['improvement']['drawdown']:>+9.1%}")
        report.append("")
        
        # 最优配置比例
        report.append("🎯 最优配置比例:")
        report.append("-" * 40)
        for i, (code, weight) in enumerate(zip(self.fund_codes, opt['optimal_weights'])):
            initial_weight = self.initial_weights[i]
            change = weight - initial_weight
            report.append(f"  {code}: {weight:>6.1%} (初始：{initial_weight:>6.1%}, 调整：{change:>+6.1%})")
        report.append("")
        
        # 调仓建议
        report.append("💡 调仓建议:")
        report.append("-" * 40)
        for i, (code, weight) in enumerate(zip(self.fund_codes, opt['optimal_weights'])):
            initial_weight = self.initial_weights[i]
            if abs(weight - initial_weight) > 0.05:  # 变化超过 5% 才建议调整
                if weight > initial_weight:
                    report.append(f"  ✅ 增持 {code}: +{(weight-initial_weight)*100:.1f}%")
                else:
                    report.append(f"  ⬇️ 减持 {code}: {(weight-initial_weight)*100:.1f}%")
        report.append("")
        
        report.append("=" * 60)
        report.append("⚠️ 风险提示：历史数据不代表未来表现，投资需谨慎")
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description='基金组合优化器')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # optimize 命令
    opt_parser = subparsers.add_parser('optimize', help='优化组合比例')
    opt_parser.add_argument('--funds', required=True, help='基金代码列表，逗号分隔')
    opt_parser.add_argument('--weights', required=True, help='初始配置比例，逗号分隔')
    opt_parser.add_argument('--start-date', default='2019-01-01', help='开始日期')
    opt_parser.add_argument('--end-date', help='结束日期（默认今天）')
    opt_parser.add_argument('--simulations', type=int, default=5000, help='模拟次数')
    opt_parser.add_argument('--risk-free-rate', type=float, default=0.03, help='无风险利率')
    opt_parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    
    # report 命令
    report_parser = subparsers.add_parser('report', help='生成详细报告')
    report_parser.add_argument('--funds', required=True, help='基金代码列表，逗号分隔')
    report_parser.add_argument('--weights', required=True, help='初始配置比例，逗号分隔')
    report_parser.add_argument('--start-date', default='2019-01-01', help='开始日期')
    report_parser.add_argument('--end-date', help='结束日期')
    report_parser.add_argument('--simulations', type=int, default=5000, help='模拟次数')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
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
    
    # 创建优化器
    optimizer = FundOptimizer(
        fund_codes=fund_codes,
        initial_weights=weights,
        start_date=args.start_date,
        end_date=args.end_date,
        risk_free_rate=args.risk_free_rate
    )
    
    # 执行优化
    result = optimizer.optimize_portfolio(simulations=args.simulations)
    
    # 输出结果
    if args.command == 'optimize':
        if args.json:
            # 移除不适合 JSON 序列化的数据
            output = {k: v for k, v in result.items() if k != 'simulation_results'}
            print(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            report = optimizer.generate_report(result)
            print(report)
    
    elif args.command == 'report':
        report = optimizer.generate_report(result)
        print(report)


if __name__ == '__main__':
    main()

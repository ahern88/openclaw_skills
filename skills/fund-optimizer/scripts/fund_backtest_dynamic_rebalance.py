#!/usr/bin/env python3
"""
基金组合回测工具 - 动态平衡策略版
支持：
1. 阈值平衡：当任何基金涨跌幅超过±20% 时触发再平衡
2. 年度平衡：每年固定月份再平衡
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import subprocess

import numpy as np
import pandas as pd


class DynamicRebalanceBacktester:
    """动态平衡策略回测器"""
    
    def __init__(self, fund_codes, weights, start_date="2019-01-01", end_date=None,
                 rebalance_month=1, threshold=0.20, initial_capital=1000000,
                 cache_dir="~/.openclaw/workspace/skills/fund-optimizer/cache"):
        self.fund_codes = fund_codes
        self.target_weights = np.array(weights)
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        self.rebalance_month = rebalance_month
        self.threshold = threshold  # 再平衡阈值（如 20%）
        self.initial_capital = initial_capital
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.nav_data = None
        self.portfolio_values = None
        self.portfolio_dates = None
        self.rebalance_log = []
    
    def fetch_fund_nav(self, fund_code):
        """获取基金历史净值（复用现有缓存）"""
        cache_file = self.cache_dir / f"{fund_code}_nav.csv"
        
        if cache_file.exists():
            try:
                df = pd.read_csv(cache_file, parse_dates=['净值日期'])
                df = df[(df['净值日期'] >= self.start_date) & (df['净值日期'] <= self.end_date)]
                if len(df) > 0:
                    return df
            except:
                pass
        
        # 调用天天基金接口
        import time
        all_data = []
        page_index = 1
        page_size = 100
        
        headers = [
            '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            '-H', 'Accept: application/json, text/javascript, */*; q=0.01',
            '-H', f'Referer: http://fund.eastmoney.com/{fund_code}.html',
            '-H', 'X-Requested-With: XMLHttpRequest',
        ]
        
        while len(all_data) < 5000:
            url = f"http://api.fund.eastmoney.com/f10/lsjz?fundCode={fund_code}&pageIndex={page_index}&pageSize={page_size}"
            
            result = subprocess.run(
                ['curl', '-s', url] + headers,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True, timeout=30
            )
            
            if not result.stdout.strip():
                break
            
            try:
                data = json.loads(result.stdout)
            except:
                break
            
            if data.get('ErrCode', 0) != 0:
                break
            
            fund_data = data.get('Data', {}).get('LSJZList', [])
            if not fund_data:
                break
            
            all_data.extend(fund_data)
            
            if len(fund_data) < page_size:
                break
            
            page_index += 1
            time.sleep(0.15)
        
        if not all_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_data)
        df = df.rename(columns={'FSRQ': '净值日期', 'DWJZ': '单位净值'})
        df = df[['净值日期', '单位净值']].copy()
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df['单位净值'] = pd.to_numeric(df['单位净值'], errors='coerce')
        df = df.dropna()
        df = df[(df['净值日期'] >= self.start_date) & (df['净值日期'] <= self.end_date)]
        
        df.to_csv(cache_file, index=False)
        return df
    
    def load_all_funds_data(self):
        """加载所有基金数据"""
        if self.nav_data is not None:
            return self.nav_data
        
        all_nav = {}
        for code in self.fund_codes:
            df = self.fetch_fund_nav(code)
            if df.empty:
                continue
            df = df.set_index('净值日期')['单位净值']
            df = df.rename(code)
            all_nav[code] = df
        
        if not all_nav:
            raise ValueError("未能获取任何基金数据")
        
        self.nav_data = pd.DataFrame(all_nav).sort_index().ffill().dropna()
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
    
    def check_threshold_rebalance(self, current_weights, date_idx):
        """检查是否需要阈值再平衡"""
        # 计算当前权重偏离
        deviation = np.abs(current_weights - self.target_weights)
        max_deviation = np.max(deviation)
        
        # 如果任何基金偏离超过阈值，需要再平衡
        return max_deviation >= self.threshold, deviation
    
    def run_backtest(self):
        """运行动态平衡回测"""
        if self.nav_data is None:
            self.load_all_funds_data()
        
        # 获取年度再平衡日期
        annual_dates = set(self.get_annual_rebalance_dates())
        
        # 初始化
        capital = self.initial_capital
        current_weights = self.target_weights.copy()
        portfolio_values = []
        portfolio_dates = []
        
        # 持仓份额（用于计算实际权重）
        # 假设初始按目标权重分配
        initial_nav = self.nav_data.iloc[0]
        shares = (capital * self.target_weights) / initial_nav
        
        last_rebalance_date = self.nav_data.index[0]
        last_rebalance_nav = initial_nav.copy()
        
        print(f"\n🚀 动态平衡回测")
        print(f"   初始资金：{self.initial_capital:,.0f} 元")
        print(f"   平衡策略：阈值±{self.threshold*100:.0f}% + 每年{self.rebalance_month} 月")
        print(f"   交易日数：{len(self.nav_data)}")
        
        rebalance_count = 0
        threshold_count = 0
        annual_count = 0
        
        for i, (date, nav) in enumerate(self.nav_data.iterrows()):
            # 计算当前市值和权重
            current_values = shares * nav
            total_value = current_values.sum()
            current_weights = current_values / total_value
            
            # 检查是否需要再平衡
            need_rebalance = False
            rebalance_reason = ""
            
            # 1. 检查年度再平衡
            if date in annual_dates and date > last_rebalance_date:
                need_rebalance = True
                rebalance_reason = "年度平衡"
                annual_count += 1
            
            # 2. 检查阈值再平衡（至少间隔 5 个交易日，避免过度交易）
            elif date > last_rebalance_date:
                need, deviation = self.check_threshold_rebalance(current_weights, i)
                if need:
                    days_since_last = (date - last_rebalance_date).days
                    if days_since_last >= 5:
                        need_rebalance = True
                        max_dev_fund = self.fund_codes[np.argmax(deviation)]
                        rebalance_reason = "阈值平衡 ({} 偏离{:.1f}%)".format(
                            max_dev_fund, np.max(deviation)*100)
                        threshold_count += 1
            
            # 执行再平衡
            if need_rebalance:
                rebalance_count += 1
                self.rebalance_log.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'reason': rebalance_reason,
                    'type': 'annual' if '年度' in rebalance_reason else 'threshold',
                    'total_value': total_value,
                    'deviation': np.max(np.abs(current_weights - self.target_weights)) * 100
                })
                
                # 再平衡：调整份额到目标权重
                shares = (total_value * self.target_weights) / nav
                last_rebalance_date = date
                last_rebalance_nav = nav.copy()
            
            # 记录组合市值
            portfolio_values.append(total_value)
            portfolio_dates.append(date)
        
        self.portfolio_values = pd.Series(portfolio_values, index=portfolio_dates)
        
        print(f"\n✅ 回测完成")
        print(f"   再平衡次数：{rebalance_count} 次")
        print(f"   - 年度平衡：{annual_count} 次")
        print(f"   - 阈值平衡：{threshold_count} 次")
        print(f"   最终市值：{portfolio_values[-1]:,.0f} 元")
        
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
        
        # 年度收益
        yearly = []
        for year in sorted(set(self.portfolio_values.index.year)):
            y_nav = self.portfolio_values[self.portfolio_values.index.year == year]
            if len(y_nav) < 2:
                continue
            ret = (y_nav.iloc[-1] - y_nav.iloc[0]) / y_nav.iloc[0]
            dd = ((y_nav - y_nav.cummax()) / y_nav.cummax()).min()
            yearly.append({'year': year, 'return': ret, 'max_drawdown': dd})
        
        # 季度收益
        quarterly = []
        for year in sorted(set(self.portfolio_values.index.year)):
            for q in range(1, 5):
                q_nav = self.portfolio_values[
                    (self.portfolio_values.index.year == year) &
                    (self.portfolio_values.index.month >= (q-1)*3+1) &
                    (self.portfolio_values.index.month <= q*3)
                ]
                if len(q_nav) < 2:
                    continue
                quarterly.append({'year': year, 'quarter': f'Q{q}', 'return': (q_nav.iloc[-1]-q_nav.iloc[0])/q_nav.iloc[0]})
        
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
            'quarterly_returns': quarterly,
            'rebalance_log': self.rebalance_log,
            'rebalance_count': len(self.rebalance_log),
            'fund_codes': self.fund_codes,
            'weights': self.weights.tolist() if hasattr(self, 'weights') else self.target_weights.tolist()
        }
    
    def generate_report(self, m):
        """生成回测报告"""
        lines = [
            "=" * 70,
            "📊 基金组合回测（动态平衡策略）",
            "=" * 70,
            "",
            "📋 配置:",
        ]
        for c, w in zip(m['fund_codes'], m['weights']):
            lines.append("   {} {:.1f}%".format(c, w*100))
        
        lines.extend([
            "", "回测：{} ~ {}".format(self.start_date, self.end_date),
            "策略：阈值±{:.0f}% + 每年{} 月再平衡".format(self.threshold*100, self.rebalance_month),
            "再平衡：{} 次 (年度{} 次，阈值{} 次)".format(
                m['rebalance_count'],
                sum(1 for r in m['rebalance_log'] if r['type']=='annual'),
                sum(1 for r in m['rebalance_log'] if r['type']=='threshold')
            ),
            "资金：{:,} → {:,} 元".format(int(m['initial_capital']), int(m['final_value'])),
            "天数：{} ({:.2f} 年)".format(m['total_days'], m['total_years']),
            "", "📈 指标:", "-" * 50,
            "累计收益：{:+.2f}%".format(m['total_return']*100),
            "年化收益：{:+.2f}%".format(m['cagr']*100),
            "波动率：   {:.2f}%".format(m['volatility']*100),
            "最大回撤： {:+.2f}%".format(m['max_drawdown']*100),
            "夏普比率： {:.2f}".format(m['sharpe_ratio']),
            "卡玛比率： {:.2f}".format(m['calmar_ratio']),
            "", "📅 年度:", "-" * 50
        ])
        
        for y in m['yearly_returns']:
            lines.append("  {}: {:+.2f}% (回撤：{:+.2f}%)".format(
                y['year'], y['return']*100, y['max_drawdown']*100))
        
        # 再平衡记录（最近 10 次）
        lines.extend(["", "🔄 最近再平衡记录:", "-" * 50])
        for r in m['rebalance_log'][-10:]:
            lines.append("  {} {} (偏离{:.1f}%)".format(
                r['date'], r['reason'], r['deviation']))
        
        lines.extend(["", "=" * 70, "⚠️  历史数据不代表未来", "=" * 70])
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='基金组合动态平衡回测')
    parser.add_argument('--funds', required=True, help='基金代码，逗号分隔')
    parser.add_argument('--weights', required=True, help='权重，逗号分隔')
    parser.add_argument('--start-date', default='2019-01-01', help='开始日期')
    parser.add_argument('--end-date', help='结束日期')
    parser.add_argument('--rebalance-month', type=int, default=1, help='年度平衡月份')
    parser.add_argument('--threshold', type=float, default=0.20, help='阈值平衡触发点（默认 20%）')
    parser.add_argument('--initial-capital', type=float, default=1000000, help='初始资金')
    parser.add_argument('--json', action='store_true', help='输出 JSON')
    
    args = parser.parse_args()
    
    funds = [c.strip() for c in args.funds.split(',')]
    weights = [float(w.strip()) for w in args.weights.split(',')]
    
    if abs(sum(weights) - 1.0) > 0.01:
        print("❌ 权重和必须为 1: {}".format(sum(weights)))
        sys.exit(1)
    
    if len(funds) != len(weights):
        print("❌ 基金数与权重数不匹配")
        sys.exit(1)
    
    bt = DynamicRebalanceBacktester(
        fund_codes=funds,
        weights=weights,
        start_date=args.start_date,
        end_date=args.end_date,
        rebalance_month=args.rebalance_month,
        threshold=args.threshold,
        initial_capital=args.initial_capital
    )
    
    try:
        m = bt.run_backtest()
        if args.json:
            print(json.dumps(m, indent=2, default=str))
        else:
            print(bt.generate_report(m))
    except Exception as e:
        print("❌ 失败：{}".format(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

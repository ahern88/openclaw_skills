#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场内 ETF 回测工具 - 腾讯证券 API 版
数据源：腾讯证券 ETF 历史 K 线
支持：159985(豆粕 ETF), 518880(黄金 ETF) 等场内 ETF
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
import requests
import numpy as np
import pandas as pd


class TencentETFBacktester:
    """腾讯证券 ETF 回测器"""
    
    def __init__(self, etf_codes, weights, start_date="2019-01-01", end_date=None,
                 initial_capital=1000000, cache_dir="~/.openclaw/workspace/skills/fund-optimizer/cache"):
        self.etf_codes = etf_codes
        self.target_weights = np.array(weights)
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        self.initial_capital = initial_capital
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.price_data = None
        self.portfolio_values = None
    
    def fetch_etf_history_tencent(self, etf_code):
        """从腾讯证券获取 ETF 历史 K 线数据"""
        cache_file = self.cache_dir / f"{etf_code}_tencent_daily.csv"
        
        # 尝试读取缓存
        if cache_file.exists():
            try:
                df = pd.read_csv(cache_file, parse_dates=['date'])
                df = df[(df['date'] >= self.start_date) & (df['date'] <= self.end_date)]
                if len(df) > 0:
                    print(f"  ✓ 缓存：{len(df)} 条")
                    return df
            except:
                pass
        
        print(f"  📡 腾讯 API 获取...", end=" ")
        
        # 腾讯证券 ETF 日线接口
        # 接口 1: 腾讯基金 K 线
        try:
            # 确定市场前缀
            if etf_code.startswith('15') or etf_code.startswith('16'):
                market = 'sz'
            elif etf_code.startswith('51'):
                market = 'sh'
            else:
                market = 'sh'
            
            # 腾讯日线数据接口
            url = f"http://web.ifzq.gtimg.cn/fund/newfund/fundKline/kline?app=1&code={market}{etf_code}&period=daily&begin=20190101&end={datetime.now().strftime('%Y%m%d')}"
            
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == 0 and data.get('data'):
                    kline_data = data['data']
                    all_data = []
                    
                    for item in kline_data:
                        # [日期，开盘，最高，最低，收盘，成交量，成交额]
                        if len(item) >= 5:
                            date_str = str(item[0])
                            if len(date_str) == 8:
                                date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                            all_data.append({
                                'date': date_str,
                                'open': float(item[1]) if item[1] else 0,
                                'high': float(item[2]) if item[2] else 0,
                                'low': float(item[3]) if item[3] else 0,
                                'close': float(item[4]) if item[4] else 0,
                                'volume': float(item[5]) if len(item) > 5 and item[5] else 0,
                                'amount': float(item[6]) if len(item) > 6 and item[6] else 0,
                            })
                    
                    if all_data:
                        df = pd.DataFrame(all_data)
                        df['date'] = pd.to_datetime(df['date'])
                        df = df[(df['date'] >= self.start_date) & (df['date'] <= self.end_date)]
                        df = df.sort_values('date').drop_duplicates('date', keep='last')
                        df = df[df['close'] > 0]  # 过滤无效数据
                        
                        if len(df) > 0:
                            df.to_csv(cache_file, index=False)
                            print(f"✓ {len(df)} 条")
                            return df
        except Exception as e:
            pass
        
        # 接口 2: 腾讯行情历史数据（备用）
        try:
            if etf_code.startswith('15') or etf_code.startswith('16'):
                market = 'sz'
            else:
                market = 'sh'
            
            url = f"http://data.gtimg.cn/flashdata/hushen/daily/{market}{etf_code}.js"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and resp.text:
                # 解析腾讯 flash 数据
                content = resp.text
                if '(' in content and ')' in content:
                    content = content[content.find('(')+1:content.rfind(')')]
                    data = json.loads(content)
                    # 处理数据...
        except:
            pass
        
        # 接口 3: 新浪财经 ETF 历史（最终备用）
        try:
            if etf_code.startswith('15') or etf_code.startswith('16'):
                market = 'sz'
            else:
                market = 'sh'
            
            all_data = []
            for year in range(2019, datetime.now().year + 1):
                for season in range(1, 5):
                    url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={market}{etf_code}&scale=240&ma=no&datalen={year-2018}"
                    try:
                        resp = requests.get(url, timeout=5)
                        if resp.status_code == 200:
                            data = resp.json()
                            for item in data:
                                all_data.append({
                                    'date': item['day'],
                                    'open': float(item['open']),
                                    'high': float(item['high']),
                                    'low': float(item['low']),
                                    'close': float(item['close']),
                                    'volume': float(item['volume']),
                                })
                    except:
                        pass
                    time.sleep(0.2)
            
            if all_data:
                df = pd.DataFrame(all_data)
                df['date'] = pd.to_datetime(df['date'])
                df = df[(df['date'] >= self.start_date) & (df['date'] <= self.end_date)]
                df = df.sort_values('date').drop_duplicates('date', keep='last')
                df = df[df['close'] > 0]
                
                if len(df) > 0:
                    df.to_csv(cache_file, index=False)
                    print(f"✓ {len(df)} 条 (新浪备用)")
                    return df
        except:
            pass
        
        print("✗ 无数据")
        return pd.DataFrame()
    
    def load_all_etf_data(self):
        """加载所有 ETF 数据"""
        if self.price_data is not None:
            return self.price_data
        
        print("\n📊 从腾讯证券加载 ETF 历史数据...")
        all_prices = {}
        
        for code in self.etf_codes:
            df = self.fetch_etf_history_tencent(code)
            if df.empty:
                continue
            df = df.set_index('date')['close']
            df = df.rename(code)
            all_prices[code] = df
        
        if not all_prices:
            raise ValueError("未能获取任何 ETF 数据")
        
        self.price_data = pd.DataFrame(all_prices).sort_index().ffill().dropna()
        print(f"\n✅ 数据加载完成：{len(self.price_data)} 个交易日")
        
        return self.price_data
    
    def run_backtest(self):
        """运行回测（年平衡策略）"""
        if self.price_data is None:
            self.load_all_etf_data()
        
        # 获取年度再平衡日期
        rebalance_dates = []
        for year in sorted(set(self.price_data.index.year)):
            mask = (self.price_data.index.year == year) & (self.price_data.index.month == 1)
            month_dates = self.price_data.index[mask]
            if len(month_dates) > 0:
                rebalance_dates.append(month_dates[0])
        
        # 初始化
        capital = self.initial_capital
        initial_price = self.price_data.iloc[0]
        shares = (capital * self.target_weights) / initial_price
        
        portfolio_values = []
        portfolio_dates = []
        last_rebalance_idx = 0
        
        print(f"\n🚀 回测：{self.initial_capital:,.0f} 元，{len(rebalance_dates)} 次再平衡")
        
        for i, (date, price) in enumerate(self.price_data.iterrows()):
            # 计算当前市值
            current_values = shares * price
            total_value = current_values.sum()
            
            # 检查是否需要再平衡
            if date in rebalance_dates and i > last_rebalance_idx:
                shares = (total_value * self.target_weights) / price
                last_rebalance_idx = i
            
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
            'final_value': float(self.portfolio_values.iloc[-1]),
            'yearly_returns': yearly,
            'etf_codes': self.etf_codes,
            'weights': self.target_weights.tolist()
        }


def main():
    parser = argparse.ArgumentParser(description='场内 ETF 回测 - 腾讯证券 API')
    parser.add_argument('--etfs', required=True, help='ETF 代码，逗号分隔')
    parser.add_argument('--weights', required=True, help='权重，逗号分隔')
    parser.add_argument('--start-date', default='2019-01-01', help='开始日期')
    parser.add_argument('--end-date', help='结束日期')
    parser.add_argument('--initial-capital', type=float, default=1000000, help='初始资金')
    parser.add_argument('--json', action='store_true', help='输出 JSON')
    
    args = parser.parse_args()
    
    etfs = [c.strip() for c in args.etfs.split(',')]
    weights = [float(w.strip()) for w in args.weights.split(',')]
    
    if abs(sum(weights) - 1.0) > 0.01:
        print(f"❌ 权重和必须为 1: {sum(weights)}")
        sys.exit(1)
    
    bt = TencentETFBacktester(
        etf_codes=etfs,
        weights=weights,
        start_date=args.start_date,
        end_date=args.end_date,
        initial_capital=args.initial_capital
    )
    
    metrics = bt.run_backtest()
    
    if args.json:
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    else:
        m = metrics
        print("\n" + "=" * 70)
        print("📊 ETF 组合回测报告（腾讯证券数据）")
        print("=" * 70)
        print(f"\n累计收益：{m['total_return']*100:+.2f}%")
        print(f"年化收益：{m['cagr']*100:+.2f}%")
        print(f"最大回撤：{m['max_drawdown']*100:+.2f}%")
        print(f"夏普比率：{m['sharpe_ratio']:.2f}")
        print(f"\n资金：{int(m['initial_capital']):,} → {int(m['final_value']):,} 元")
        print("=" * 70)


if __name__ == "__main__":
    main()

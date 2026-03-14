#!/usr/bin/env python3
"""
基金组合自动生成器
- 自动生成多个优化组合方案
- 考虑 QDII 限购（权重控制）
- 回测 2019-09-24 至今
- 控制在 10 只基金以内
"""

import json
import subprocess
import pandas as pd
import numpy as np
from datetime import datetime
from itertools import combinations
from typing import List, Dict, Tuple


# 基金池（按类别分组）
FUND_POOL = {
    # 股票/混合基金（进攻型）
    'equity': [
        {'code': '002943', 'name': '广发多因子混合', 'risk': 'high'},
        {'code': '166301', 'name': '华商新趋势混合', 'risk': 'high'},
        {'code': '004011', 'name': '华泰柏瑞鼎利混合 C', 'risk': 'medium'},
        {'code': '165531', 'name': '中信保诚多策略混合', 'risk': 'high'},
        {'code': '519212', 'name': '万家宏观择时多策略', 'risk': 'medium'},
        {'code': '002258', 'name': '大成国企改革混合', 'risk': 'medium'},
        {'code': '001323', 'name': '东吴移动互联混合 A', 'risk': 'high'},
    ],
    
    # 债券基金（防守型）
    'bond': [
        {'code': '110017', 'name': '易方达增强回报债券 A', 'risk': 'low'},
        {'code': '217022', 'name': '招商产业债券 A', 'risk': 'low'},
        {'code': '004993', 'name': '中欧可转债债券 A', 'risk': 'medium'},
    ],
    
    # QDII（海外配置，限购）
    'qdii': [
        {'code': '006373', 'name': '国富全球科技互联 (QDII)', 'limit': 500, 'risk': 'high'},
        {'code': '539001', 'name': '建信纳斯达克 100(QDII)', 'limit': 100, 'risk': 'high'},
        {'code': '161128', 'name': '易方达标普信息科技 (QDII)', 'limit': 100, 'risk': 'high'},
    ],
    
    # 黄金/商品（抗通胀）
    'commodity': [
        {'code': '000216', 'name': '华安黄金 ETF 联接 A', 'risk': 'medium'},
        {'code': '518880', 'name': '华安黄金 ETF', 'risk': 'medium'},
        {'code': '159985', 'name': '豆粕 ETF', 'risk': 'medium'},
    ],
    
    # 指数/策略
    'index': [
        {'code': '005561', 'name': '中证红利低波', 'risk': 'medium'},
    ],
}


def generate_portfolio_config(
    portfolio_type: str,
    total_funds: int = 8
) -> Dict:
    """
    生成组合配置
    
    Args:
        portfolio_type: 组合类型 ('conservative', 'balanced', 'aggressive')
        total_funds: 基金总数（默认 8 只）
    
    Returns:
        配置字典 {code: weight, ...}
    """
    config = {}
    
    if portfolio_type == 'conservative':
        # 保守型：债券 40% + 股票 30% + 商品 20% + QDII 10%
        allocation = {'bond': 0.40, 'equity': 0.30, 'commodity': 0.20, 'qdii': 0.10}
    elif portfolio_type == 'balanced':
        # 平衡型：股票 40% + 债券 25% + 商品 20% + QDII 15%
        allocation = {'equity': 0.40, 'bond': 0.25, 'commodity': 0.20, 'qdii': 0.15}
    elif portfolio_type == 'aggressive':
        # 进取型：股票 55% + QDII 20% + 商品 15% + 债券 10%
        allocation = {'equity': 0.55, 'qdii': 0.20, 'commodity': 0.15, 'bond': 0.10}
    else:
        raise ValueError(f"未知组合类型：{portfolio_type}")
    
    # 按类别分配基金
    for category, target_weight in allocation.items():
        funds = FUND_POOL.get(category, [])
        if not funds:
            continue
        
        # 计算该类别应选基金数量
        n_funds = max(1, int(total_funds * target_weight))
        n_funds = min(n_funds, len(funds))
        
        # 选择基金（简单按顺序，可改为随机或优化）
        selected = funds[:n_funds]
        weight_per_fund = target_weight / n_funds
        
        for fund in selected:
            code = fund['code']
            # QDII 限购处理：权重不超过 10%（大额资金无法买入）
            if category == 'qdii' and weight_per_fund > 0.10:
                weight_per_fund = 0.10
            
            config[code] = round(weight_per_fund, 3)
    
    # 归一化权重（确保总和=1）
    total = sum(config.values())
    config = {k: round(v / total, 3) for k, v in config.items()}
    
    return config


def run_backtest(funds: List[str], weights: List[float], start_date: str = "2019-09-24") -> Dict:
    """运行回测"""
    cmd = [
        'python3', 'scripts/fund_backtest_tiantian.py',
        '--funds', ','.join(funds),
        '--weights', ','.join(map(str, weights)),
        '--start-date', start_date,
        '--json'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=120,
            cwd='/home/admin/.openclaw/workspace/skills/fund-optimizer'
        )
        
        # JSON 可能在 stdout 或 stderr
        for output in [result.stdout, result.stderr]:
            output = output.strip()
            if not output:
                continue
            # 尝试找到第一个 { 或 [
            start = min(output.find('{'), output.find('['))
            if start < 0:
                start = 0
            elif start > 0:
                output = output[start:]
            
            try:
                return json.loads(output)
            except:
                continue
        
        return {'error': '无法解析 JSON 输出'}
    except Exception as e:
        return {'error': str(e)}
    except Exception as e:
        return {'error': str(e)}


def evaluate_portfolio(metrics: Dict) -> float:
    """
    评估组合得分（综合考虑收益和风险）
    得分 = 夏普比率 * 0.4 + 卡玛比率 * 0.3 + 年化收益 * 0.3
    """
    if 'error' in metrics:
        return -999
    
    sharpe = metrics.get('sharpe_ratio', 0)
    calmar = metrics.get('calmar_ratio', 0)
    cagr = metrics.get('cagr', 0)
    
    # 标准化得分
    score = sharpe * 0.4 + calmar * 0.3 + cagr * 0.3
    return score


def generate_auto_portfolios():
    """自动生成多个组合方案并回测"""
    print("=" * 70)
    print("🤖 基金组合自动生成器")
    print("=" * 70)
    print(f"回测期间：2019-09-24 至今")
    print(f"基金池：{sum(len(v) for v in FUND_POOL.values())} 只基金")
    print()
    
    # 生成不同类型的组合
    portfolio_types = ['conservative', 'balanced', 'aggressive']
    results = []
    
    for ptype in portfolio_types:
        print(f"\n📊 生成 {ptype} 组合...")
        
        # 生成配置
        config = generate_portfolio_config(ptype, total_funds=8)
        funds = list(config.keys())
        weights = list(config.values())
        
        print(f"   基金数量：{len(funds)}")
        print(f"   QDII 占比：{sum(w for f, w in config.items() if f in [q['code'] for q in FUND_POOL['qdii']]):.1%}")
        
        # 运行回测
        print(f"   回测中...", end=" ", flush=True)
        metrics = run_backtest(funds, weights)
        
        if 'error' not in metrics:
            score = evaluate_portfolio(metrics)
            results.append({
                'type': ptype,
                'funds': funds,
                'weights': weights,
                'config': config,
                'metrics': metrics,
                'score': score
            })
            print(f"✓ 得分：{score:.3f}")
        else:
            print(f"✗ 失败：{metrics['error']}")
    
    # 排序并展示结果
    print("\n" + "=" * 70)
    print("📈 组合对比")
    print("=" * 70)
    
    results.sort(key=lambda x: x['score'], reverse=True)
    
    for i, r in enumerate(results, 1):
        m = r['metrics']
        print(f"\n【方案 {i}】{r['type']} (得分：{r['score']:.3f})")
        print("-" * 50)
        print(f"年化收益：{m['cagr']*100:.2f}%")
        print(f"最大回撤：{m['max_drawdown']*100:.2f}%")
        print(f"夏普比率：{m['sharpe_ratio']:.2f}")
        print(f"卡玛比率：{m['calmar_ratio']:.2f}")
        print(f"100 万→{m['final_value']/10000:.1f}万")
        print()
        print("配置:")
        for code, weight in sorted(zip(r['funds'], r['weights']), key=lambda x: -x[1]):
            name = next((f['name'] for cat in FUND_POOL.values() for f in cat if f['code'] == code), code)
            qdii_flag = " [QDII]" if code in [q['code'] for q in FUND_POOL['qdii']] else ""
            print(f"  {code} {name[:15]:<15} {weight*100:5.1f}%{qdii_flag}")
    
    # 保存最优组合
    if results:
        best = results[0]
        print("\n" + "=" * 70)
        print("🏆 推荐组合（方案 1）")
        print("=" * 70)
        
        # 生成回测命令
        funds_str = ','.join(best['funds'])
        weights_str = ','.join(map(str, best['weights']))
        print(f"\n运行回测命令:")
        print(f"python3 scripts/fund_backtest_tiantian.py \\")
        print(f"  --funds {funds_str} \\")
        print(f"  --weights {weights_str} \\")
        print(f"  --start-date 2019-09-24")
        
        # 详细回测
        print("\n详细回测:")
        cmd = [
            'python3', 'scripts/fund_backtest_tiantian.py',
            '--funds', funds_str,
            '--weights', weights_str,
            '--start-date', '2019-09-24'
        ]
        result = subprocess.run(cmd, cwd='/home/admin/.openclaw/workspace/skills/fund-optimizer')
    
    return results


if __name__ == '__main__':
    generate_auto_portfolios()

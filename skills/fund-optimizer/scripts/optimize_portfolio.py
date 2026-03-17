#!/usr/bin/env python3
"""
基金组合优化器 - 寻找最优配置
约束：黄金 11.5%、豆粕 8%、QDII 8.3%
目标：收益最大化 + 回撤最小化
"""

import subprocess
import json
import itertools
from typing import List, Dict, Tuple

# 基金池（按类别）
FUNDS = {
    '债券': [
        {'code': '217022', 'name': '招商产业债券 A'},
        {'code': '110017', 'name': '易方达增强回报债券 A'},
        {'code': '004993', 'name': '中欧可转债债券 A'},
    ],
    '混合': [
        {'code': '002943', 'name': '广发多因子混合'},
        {'code': '166301', 'name': '华商新趋势混合'},
        {'code': '002849', 'name': '金信智能中国 2025 混合'},
        {'code': '004011', 'name': '华泰柏瑞鼎利混合 C'},
        {'code': '519212', 'name': '万家宏观择时多策略'},
        {'code': '002258', 'name': '大成国企改革混合 A'},
        {'code': '001323', 'name': '东吴移动互联混合 A'},
        {'code': '004206', 'name': '华商元亨混合 A'},
        {'code': '005561', 'name': '中证红利低波'},
    ],
    '黄金': [
        {'code': '518880', 'name': '华安黄金 ETF'},
        {'code': '000216', 'name': '华安黄金 ETF 联接 A'},
    ],
    '商品': [
        {'code': '159985', 'name': '华夏饲料豆粕期货 ETF'},
    ],
    'QDII': [
        {'code': '006373', 'name': '国富全球科技互联 (QDII)'},
        {'code': '539001', 'name': '建信纳斯达克 100(QDII)'},
        {'code': '161128', 'name': '易方达标普信息科技 (QDII)'},
    ],
}

# 固定约束
FIXED = {
    '黄金': 11.5,
    '商品': 8.0,
    'QDII': 8.3,
}

# 剩余可配置比例
REMAINING = 100 - sum(FIXED.values())  # 72.2%

print("=" * 80)
print("🔍 基金组合优化器 - 寻找最优配置")
print("=" * 80)
print(f"\n固定约束:")
for asset, weight in FIXED.items():
    print(f"  {asset}: {weight}%")
print(f"\n剩余可配置：{REMAINING}%")
print(f"\n基金池：{sum(len(v) for v in FUNDS.values())} 只基金")
print("=" * 80)

# 生成测试组合
test_portfolios = []

# 方案 1: 债券 30% + 混合 42.2%
test_portfolios.append({
    'name': '稳健型 (债券 30%)',
    'config': {
        '债券': 30.0,
        '混合': 42.2,
    }
})

# 方案 2: 债券 25% + 混合 47.2%
test_portfolios.append({
    'name': '平衡型 (债券 25%)',
    'config': {
        '债券': 25.0,
        '混合': 47.2,
    }
})

# 方案 3: 债券 20% + 混合 52.2%
test_portfolios.append({
    'name': '进取型 (债券 20%)',
    'config': {
        '债券': 20.0,
        '混合': 52.2,
    }
})

# 方案 4: 债券 35% + 混合 37.2%
test_portfolios.append({
    'name': '保守型 (债券 35%)',
    'config': {
        '债券': 35.0,
        '混合': 37.2,
    }
})

results = []

for portfolio in test_portfolios:
    print(f"\n测试：{portfolio['name']}")
    print("-" * 60)
    
    # 构建具体配置
    bond_weight = portfolio['config'].get('债券', 0)
    equity_weight = portfolio['config'].get('混合', 0)
    
    # 选择基金并分配权重
    funds = []
    weights = []
    
    # 固定部分
    funds.extend(['518880', '159985', '006373', '539001'])
    weights.extend([8.0, 8.0, 5.0, 3.3])  # 黄金 8%+ 商品 8%+QDII 8.3%
    
    # 债券部分（选择 2 只）
    if bond_weight > 0:
        funds.extend(['217022', '110017'])
        weights.extend([bond_weight * 0.7, bond_weight * 0.3])
    
    # 混合部分（选择 6 只）
    if equity_weight > 0:
        equity_funds = ['002943', '166301', '004011', '519212', '002258', '001323']
        equity_weights = [0.25, 0.20, 0.18, 0.15, 0.12, 0.10]
        for code, w in zip(equity_funds, equity_weights):
            funds.append(code)
            weights.append(equity_weight * w)
    
    # 归一化权重
    total = sum(weights)
    weights = [w / total * 100 for w in weights]
    
    # 运行回测
    funds_str = ','.join(funds)
    weights_str = ','.join([f'{w:.2f}' for w in weights])
    
    cmd = f"python3 scripts/fund_backtest_tiantian.py --funds {funds_str} --weights {weights_str} --start-date 2019-09-24 --json"
    
    result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
    stdout, _ = result.communicate()
    
    try:
        output = stdout.strip()
        start = output.find('{')
        if start > 0:
            output = output[start:]
        data = json.loads(output)
        
        # 计算得分（夏普*0.4 + 卡玛*0.3 + 年化*0.3）
        score = data['sharpe_ratio'] * 0.4 + data['calmar_ratio'] * 0.3 + data['cagr'] * 0.3
        
        results.append({
            'name': portfolio['name'],
            'funds': funds,
            'weights': weights,
            'metrics': data,
            'score': score
        })
        
        print(f"  年化收益：{data['cagr']*100:.2f}%")
        print(f"  最大回撤：{data['max_drawdown']*100:.2f}%")
        print(f"  夏普比率：{data['sharpe_ratio']:.2f}")
        print(f"  卡玛比率：{data['calmar_ratio']:.2f}")
        print(f"  综合得分：{score:.3f}")
        print(f"  100 万→{data['final_value']/10000:.1f}万")
        
    except Exception as e:
        print(f"  回测失败：{e}")

# 排序并展示结果
print("\n" + "=" * 80)
print("🏆 优化结果排名")
print("=" * 80)

results.sort(key=lambda x: x['score'], reverse=True)

for i, r in enumerate(results, 1):
    m = r['metrics']
    print(f"\n【第{i}名】{r['name']} (得分：{r['score']:.3f})")
    print("-" * 60)
    print(f"  年化收益：{m['cagr']*100:.2f}%")
    print(f"  最大回撤：{m['max_drawdown']*100:.2f}%")
    print(f"  波动率：{m['volatility']*100:.2f}%")
    print(f"  夏普比率：{m['sharpe_ratio']:.2f}")
    print(f"  卡玛比率：{m['calmar_ratio']:.2f}")
    print(f"  100 万→{m['final_value']/10000:.1f}万")
    
    # 展示配置
    print(f"\n  配置明细:")
    for code, weight in zip(r['funds'], r['weights']):
        name = next((f['name'] for cat in FUNDS.values() for f in cat if f['code'] == code), code)
        print(f"    {code} {name[:20]:<20} {weight:>6.2f}%")

# 保存最优组合
if results:
    best = results[0]
    print("\n" + "=" * 80)
    print("🎯 推荐最优组合")
    print("=" * 80)
    
    m = best['metrics']
    print(f"\n组合名称：{best['name']}")
    print(f"\n核心指标:")
    print(f"  年化收益：{m['cagr']*100:.2f}%")
    print(f"  最大回撤：{m['max_drawdown']*100:.2f}%")
    print(f"  夏普比率：{m['sharpe_ratio']:.2f}")
    print(f"  卡玛比率：{m['calmar_ratio']:.2f}")
    print(f"  100 万→{m['final_value']/10000:.1f}万")
    
    print(f"\n配置明细:")
    for code, weight in zip(best['funds'], best['weights']):
        name = next((f['name'] for cat in FUNDS.values() for f in cat if f['code'] == code), code)
        print(f"  {code} {name:<25} {weight:>6.2f}%")
    
    # 生成回测命令
    funds_str = ','.join(best['funds'])
    weights_str = ','.join([f'{w:.2f}' for w in best['weights']])
    
    print(f"\n回测命令:")
    print(f"python3 scripts/fund_backtest_tiantian.py \\")
    print(f"  --funds {funds_str} \\")
    print(f"  --weights {weights_str} \\")
    print(f"  --start-date 2019-09-24")

print("\n" + "=" * 80)
print("✅ 优化完成")
print("=" * 80)

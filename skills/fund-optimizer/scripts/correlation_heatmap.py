#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金相关性热力图生成器
计算持仓基金之间的相关系数，生成热力图
"""

import json
import sys
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd

# 尝试导入 matplotlib
try:
    import matplotlib.pyplot as plt
    import matplotlib
    HAS_MATPLOTLIB = True
except:
    HAS_MATPLOTLIB = False
    print("⚠️  matplotlib 未安装，将生成文本版热力图")


def fetch_fund_nav(fund_code, start_date="2019-01-01", cache_dir="~/.openclaw/workspace/skills/fund-optimizer/cache"):
    """获取基金历史净值"""
    cache_file = Path(cache_dir).expanduser() / f"{fund_code}_nav.csv"
    
    if cache_file.exists():
        try:
            df = pd.read_csv(cache_file, parse_dates=['净值日期'])
            df = df[df['净值日期'] >= start_date]
            if len(df) > 0:
                return df.set_index('净值日期')['单位净值']
        except:
            pass
    
    # 从天天基金获取
    import subprocess
    all_data = []
    page = 1
    
    while page <= 20:
        try:
            url = f"http://api.fund.eastmoney.com/f10/lsjz?fundCode={fund_code}&pageIndex={page}&pageSize=100"
            result = subprocess.run(
                ['curl', '-s', '-m', '10', url],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True, timeout=15
            )
            
            if not result.stdout.strip():
                break
            
            data = json.loads(result.stdout)
            fund_list = data.get('Data', {}).get('LSJZList', [])
            
            if not fund_list:
                break
            
            for item in fund_list:
                nav_date = item.get('FSRQ', '')
                unit_nav = item.get('DWJZ', '')
                if nav_date and unit_nav:
                    all_data.append({
                        '净值日期': nav_date,
                        '单位净值': float(unit_nav)
                    })
            
            if len(fund_list) < 100:
                break
            
            page += 1
        except:
            break
    
    if not all_data:
        return pd.Series()
    
    df = pd.DataFrame(all_data)
    df['净值日期'] = pd.to_datetime(df['净值日期'])
    df = df.dropna(subset=['单位净值'])
    df = df[df['净值日期'] >= start_date]
    df = df.sort_values('净值日期').drop_duplicates('净值日期', keep='last')
    
    if cache_file.parent.exists():
        df.to_csv(cache_file, index=False)
    
    return df.set_index('净值日期')['单位净值']


def calculate_correlation(fund_codes, start_date="2019-01-01"):
    """计算基金相关性矩阵"""
    print("📊 获取基金历史数据...")
    
    nav_data = {}
    for code in fund_codes:
        print(f"  📡 {code}...", end=" ")
        nav = fetch_fund_nav(code, start_date)
        if len(nav) > 0:
            nav_data[code] = nav
            print(f"✓ {len(nav)} 条")
        else:
            print("✗ 无数据")
    
    if not nav_data:
        print("❌ 未能获取任何基金数据")
        return None, None
    
    # 合并数据
    nav_df = pd.DataFrame(nav_data)
    nav_df = nav_df.ffill().dropna()
    
    # 计算日收益率
    returns_df = nav_df.pct_change().dropna()
    
    # 计算相关性矩阵
    corr_matrix = returns_df.corr()
    
    return corr_matrix, nav_df


def plot_text_heatmap(corr_matrix):
    """生成文本版热力图"""
    print("\n" + "=" * 80)
    print("📊 基金相关性热力图 (基于日收益率)")
    print("=" * 80)
    print()
    
    funds = corr_matrix.columns.tolist()
    n = len(funds)
    
    # 基金简称映射
    fund_names = {
        '006373': '国富全球',
        '040046': '纳斯达克',
        '159985': '豆粕 ETF',
        '005561': '红利低波',
        '166301': '华商新趋势',
        '002849': '金信智能',
        '002943': '广发多因子',
        '000216': '黄金 ETF',
        '217022': '招商债券',
        '004011': '华泰鼎利',
        '110017': '易方达债券',
        '004993': '中欧可转债',
    }
    
    # 打印表头
    print(f"{'':>12}", end="")
    for code in funds:
        name = fund_names.get(code, code[:6])
        print(f"{name:>8}", end="")
    print()
    print("-" * (12 + n * 8))
    
    # 打印相关性矩阵
    for i, row_code in enumerate(funds):
        row_name = fund_names.get(row_code, row_code[:6])
        print(f"{row_name:>10}", end="")
        
        for j, col_code in enumerate(funds):
            corr = corr_matrix.iloc[i, j]
            
            # 使用字符表示相关性强度
            if corr >= 0.9:
                symbol = "▓▓"  # 极高相关
            elif corr >= 0.7:
                symbol = "▒▒"  # 高相关
            elif corr >= 0.5:
                symbol = "░░"  # 中等相关
            elif corr >= 0.3:
                symbol = "·░"  # 低相关
            elif corr >= 0.1:
                symbol = "··"  # 极低相关
            elif corr >= -0.1:
                symbol = "  "  # 无相关
            elif corr >= -0.3:
                symbol = "·-"  # 负相关
            else:
                symbol = "--"  # 强负相关
            
            print(f"{symbol:>8}", end="")
        print()
    
    print()
    print("=" * 80)
    print()
    
    # 图例
    print("📋 图例:")
    print("  ▓▓ 极高相关 (≥0.9)")
    print("  ▒▒ 高相关 (0.7-0.9)")
    print("  ░░ 中等相关 (0.5-0.7)")
    print("  ·░ 低相关 (0.3-0.5)")
    print("  ·· 极低相关 (0.1-0.3)")
    print("    无相关 (-0.1-0.1)")
    print("  ·- 负相关 (-0.3 至 -0.1)")
    print("  -- 强负相关 (<-0.3)")
    print()
    
    # 找出最高和最低相关性
    print("🔍 关键发现:")
    print("-" * 80)
    
    # 上三角矩阵
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    # 最高相关性
    max_corr = upper.stack().max()
    max_idx = upper.stack().idxmax()
    print(f"  📈 最高相关性：{max_corr:.3f}")
    print(f"     {fund_names.get(max_idx[0], max_idx[0])} ↔ {fund_names.get(max_idx[1], max_idx[1])}")
    print()
    
    # 最低相关性
    min_corr = upper.stack().min()
    min_idx = upper.stack().idxmin()
    print(f"  📉 最低相关性：{min_corr:.3f}")
    print(f"     {fund_names.get(min_idx[0], min_idx[0])} ↔ {fund_names.get(min_idx[1], min_idx[1])}")
    print()
    
    # 平均相关性
    avg_corr = upper.stack().mean()
    print(f"  📊 平均相关性：{avg_corr:.3f}")
    print()
    
    # 与其他基金平均相关性最低的基金（最分散）
    avg_corrs = upper.stack().groupby(level=0).mean()
    min_avg_fund = avg_corrs.idxmin()
    print(f"  🎯 最分散基金：{fund_names.get(min_avg_fund, min_avg_fund)} (平均相关 {avg_corrs[min_avg_fund]:.3f})")
    print()
    
    # 与其他基金平均相关性最高的基金（最集中）
    max_avg_fund = avg_corrs.idxmax()
    print(f"  🎯 最集中基金：{fund_names.get(max_avg_fund, max_avg_fund)} (平均相关 {avg_corrs[max_avg_fund]:.3f})")
    print()
    
    print("=" * 80)


def plot_matplotlib_heatmap(corr_matrix, output_dir="~/.openclaw/workspace/skills/fund-optimizer/charts"):
    """使用 matplotlib 生成热力图"""
    if not HAS_MATPLOTLIB:
        return
    
    output_dir = Path(output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    fund_names = {
        '006373': '国富全球',
        '040046': '纳斯达克',
        '159985': '豆粕 ETF',
        '005561': '红利低波',
        '166301': '华商新趋势',
        '002849': '金信智能',
        '002943': '广发多因子',
        '000216': '黄金 ETF',
        '217022': '招商债券',
        '004011': '华泰鼎利',
        '110017': '易方达债券',
        '004993': '中欧可转债',
    }
    
    # 创建热力图
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # 绘制热力图
    im = ax.imshow(corr_matrix, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)
    
    # 设置标签
    labels = [fund_names.get(code, code) for code in corr_matrix.columns]
    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
    ax.set_yticklabels(labels, fontsize=10)
    
    # 添加数值
    for i in range(len(labels)):
        for j in range(len(labels)):
            text = ax.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                          ha="center", va="center", color="black", fontsize=8)
    
    # 颜色条
    cbar = ax.figure.colorbar(im)
    cbar.ax.set_ylabel('相关系数', rotation=-90, va="bottom", fontsize=12)
    
    plt.title('基金持仓相关性热力图 (基于日收益率)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    plt.savefig(output_dir / 'correlation_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ 热力图已保存：{output_dir / 'correlation_heatmap.png'}")


def main():
    # 当前持仓 12 只基金
    fund_codes = [
        '006373',  # 国富全球科技互联
        '040046',  # 华安纳斯达克 100
        '159985',  # 华夏饲料豆粕 ETF
        '005561',  # 创金合信红利低波
        '166301',  # 华商新趋势
        '002849',  # 金信智能中国 2025
        '002943',  # 广发多因子
        '000216',  # 华安黄金 ETF 联接
        '217022',  # 招商产业债券
        '004011',  # 华泰柏瑞鼎利混合
        '110017',  # 易方达增强回报债券
        '004993',  # 中欧可转债债券
    ]
    
    print("=" * 80)
    print("📊 基金持仓相关性分析")
    print("=" * 80)
    print()
    
    # 计算相关性
    corr_matrix, nav_df = calculate_correlation(fund_codes, start_date="2019-09-24")
    
    if corr_matrix is None:
        return
    
    print(f"\n✅ 数据加载完成：{len(nav_df)} 个交易日")
    print(f"   时间范围：{nav_df.index[0].strftime('%Y-%m-%d')} 至 {nav_df.index[-1].strftime('%Y-%m-%d')}")
    print()
    
    # 生成文本版热力图
    plot_text_heatmap(corr_matrix)
    
    # 尝试生成 PNG 热力图
    if HAS_MATPLOTLIB:
        plot_matplotlib_heatmap(corr_matrix)
    
    print("\n💡 相关性分析建议:")
    print("-" * 80)
    print("  ✅ 相关<0.3: 分散效果好，建议保持")
    print("  ⚠️  相关 0.5-0.7: 中度相关，可接受")
    print("  ❌ 相关>0.8: 高度相关，考虑替换为低相关基金")
    print()
    print("  🎯 理想组合：平均相关性<0.4，最大相关性<0.7")
    print("=" * 80)


if __name__ == "__main__":
    main()

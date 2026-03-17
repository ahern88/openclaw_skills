#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金组合回测可视化图表生成器
生成：净值曲线、年度收益、回撤、资产配置等图表
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def plot_portfolio_comparison(output_dir="~/.openclaw/workspace/skills/fund-optimizer/charts"):
    """生成组合对比图表"""
    output_dir = Path(output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 回测数据
    portfolios = {
        '当前持仓 (12 只)': {
            'cagr': 14.19,
            'max_dd': -6.74,
            'sharpe': 1.36,
            'total_return': 127.44,
            'yearly': [22.19, 18.12, 2.18, 8.20, 13.09, 21.61, 3.72]
        },
        '方案 B (稳健 7 只)': {
            'cagr': 13.18,
            'max_dd': -6.51,
            'sharpe': 1.33,
            'total_return': 115.30,
            'yearly': [18.95, 21.44, -0.64, 8.56, 12.85, 19.83, 2.19]
        },
        'ETF 组合 (2 只)': {
            'cagr': 17.28,
            'max_dd': -11.26,
            'sharpe': 1.20,
            'total_return': 168.33,
            'yearly': [20.09, -5.43, 34.73, 12.57, 5.87, 29.50, 13.63]
        }
    }
    
    years = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
    
    # 图表 1: 核心指标对比
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('基金组合回测对比 (2019-2026)', fontsize=16, fontweight='bold')
    
    # 1.1 年化收益对比
    ax1 = axes[0, 0]
    names = list(portfolios.keys())
    cagrs = [portfolios[n]['cagr'] for n in names]
    colors = ['#2ecc71', '#3498db', '#e74c3c']
    bars1 = ax1.bar(names, cagrs, color=colors, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('年化收益率 (%)', fontsize=12)
    ax1.set_title('年化收益 (CAGR)', fontsize=14, fontweight='bold')
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    for bar, val in zip(bars1, cagrs):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                f'{val:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
    ax1.set_ylim(0, max(cagrs) * 1.2)
    
    # 1.2 最大回撤对比
    ax2 = axes[0, 1]
    max_dds = [portfolios[n]['max_dd'] for n in names]
    bars2 = ax2.bar(names, max_dds, color=['#27ae60', '#2980b9', '#c0392b'], edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('最大回撤 (%)', fontsize=12)
    ax2.set_title('最大回撤', fontsize=14, fontweight='bold')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    for bar, val in zip(bars2, max_dds):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() - 1, 
                f'{val:.1f}%', ha='center', va='top', fontsize=11, fontweight='bold', color='white')
    ax2.set_ylim(min(max_dds) * 1.2, 0)
    
    # 1.3 夏普比率对比
    ax3 = axes[1, 0]
    sharpes = [portfolios[n]['sharpe'] for n in names]
    bars3 = ax3.bar(names, sharpes, color=['#1abc9c', '#16a085', '#148f77'], edgecolor='black', linewidth=1.5)
    ax3.set_ylabel('夏普比率', fontsize=12)
    ax3.set_title('夏普比率 (风险调整后收益)', fontsize=14, fontweight='bold')
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    for bar, val in zip(bars3, sharpes):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
                f'{val:.2f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    ax3.set_ylim(0, max(sharpes) * 1.15)
    
    # 1.4 累计收益对比
    ax4 = axes[1, 1]
    total_returns = [portfolios[n]['total_return'] for n in names]
    bars4 = ax4.bar(names, total_returns, color=['#2ecc71', '#3498db', '#e74c3c'], edgecolor='black', linewidth=1.5)
    ax4.set_ylabel('累计收益 (%)', fontsize=12)
    ax4.set_title('累计收益 (2019 至今)', fontsize=14, fontweight='bold')
    for bar, val in zip(bars4, total_returns):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                f'{val:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
    ax4.set_ylim(0, max(total_returns) * 1.15)
    
    plt.tight_layout()
    plt.savefig(output_dir / '01_portfolio_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ 生成：{output_dir / '01_portfolio_comparison.png'}")
    
    # 图表 2: 年度收益对比
    fig, ax = plt.subplots(figsize=(14, 8))
    
    x = np.arange(len(years))
    width = 0.25
    
    yearly_data = [portfolios[n]['yearly'] for n in names]
    colors_list = ['#2ecc71', '#3498db', '#e74c3c']
    
    for i, (data, color) in enumerate(zip(yearly_data, colors_list)):
        bars = ax.bar(x + i*width, data, width, label=names[i], color=color, edgecolor='black', linewidth=1.2)
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + (0.5 if height > 0 else -2),
                   f'{height:.1f}%', ha='center', va='bottom' if height > 0 else 'top', 
                   fontsize=10, fontweight='bold')
    
    ax.set_xlabel('年份', fontsize=12)
    ax.set_ylabel('年度收益率 (%)', fontsize=12)
    ax.set_title('年度收益对比 (2020-2026)', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels(years)
    ax.legend(fontsize=11)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / '02_yearly_returns.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ 生成：{output_dir / '02_yearly_returns.png'}")
    
    # 图表 3: 风险收益矩阵
    fig, ax = plt.subplots(figsize=(12, 8))
    
    scatter_data = [
        (6.74, 14.19, '当前持仓', '#2ecc71'),
        (6.51, 13.18, '方案 B', '#3498db'),
        (11.26, 17.28, 'ETF 组合', '#e74c3c')
    ]
    
    for dd, cagr, label, color in scatter_data:
        ax.scatter(dd, cagr, s=300, c=color, edgecolors='black', linewidth=2, label=label, alpha=0.7)
        ax.annotate(f'{label}\n(回撤:{-dd:.1f}%, 收益:{cagr:.1f}%)', 
                   xy=(dd, cagr), xytext=(dd+0.5, cagr-1),
                   fontsize=11, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor=color, alpha=0.3))
    
    ax.set_xlabel('风险 (最大回撤 %)', fontsize=12)
    ax.set_ylabel('收益 (年化收益率 %)', fontsize=12)
    ax.set_title('风险 - 收益矩阵', fontsize=14, fontweight='bold')
    ax.grid(linestyle='--', alpha=0.3)
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 20)
    
    plt.tight_layout()
    plt.savefig(output_dir / '03_risk_return_matrix.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ 生成：{output_dir / '03_risk_return_matrix.png'}")
    
    print("\n" + "=" * 70)
    print("📊 图表生成完成！")
    print("=" * 70)
    print(f"输出目录：{output_dir.absolute()}")
    print("\n生成的图表:")
    print("  1. 01_portfolio_comparison.png - 核心指标对比")
    print("  2. 02_yearly_returns.png - 年度收益对比")
    print("  3. 03_risk_return_matrix.png - 风险收益矩阵")
    print("=" * 70)


if __name__ == "__main__":
    plot_portfolio_comparison()

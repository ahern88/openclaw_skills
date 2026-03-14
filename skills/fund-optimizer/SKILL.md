---
name: fund-optimizer
description: 基金组合优化与回测技能。支持天天基金实时数据、动态平衡策略（阈值 + 年度）、组合优化、自动组合生成。
author: Assistant
version: 2.0.0
metadata: {"clawdbot":{"emoji":"📊","requires":{"bins":["python3","curl"]},"config":{"env":{"FUND_CACHE_DIR":{"description":"数据缓存目录","default":"~/.openclaw/workspace/skills/fund-optimizer/cache","required":false}}}}}
---

# 基金组合优化与回测技能

基于**天天基金网实时数据**和现代投资组合理论（MPT），提供基金组合优化、回测和动态平衡功能。

## 功能

### 📊 组合优化
- 📈 获取基金历史净值数据（2019 年至今，天天基金实时数据）
- 🎯 计算有效前沿（Efficient Frontier）
- 🏆 寻找最优夏普比率组合
- 📊 生成风险分析报告
- 💡 提供调仓建议

### 🔄 组合回测
- 📊 年化收益率（CAGR）
- 📉 最大回撤（Max Drawdown）
- 🎯 卡玛比率（Calmar Ratio）
- 📅 年度/季度收益列表
- 🔄 年平衡策略支持
- 🎯 **动态平衡策略**（阈值±20% + 年度平衡）

### 🤖 自动组合生成
- 🎲 自动生成保守/平衡/进取三种组合
- 🎯 考虑 QDII 限购因素
- 📊 自动回测评分推荐最优

### 📈 数据源
- **天天基金网**: `fund.eastmoney.com/pingzhongdata/{基金代码}.js`
- 自动缓存（7 天有效期）
- 支持 17+ 只基金池

## 使用方法

### 🚀 快速开始（推荐）

#### 1. 回测你的组合（天天基金数据）
```bash
python3 {baseDir}/scripts/fund_backtest_tiantian.py \
  --funds 110017,159985,166301,217022,539001,000216,002849,002943,004011,004993,005561,006373 \
  --weights 0.075,0.08,0.08,0.167,0.031,0.115,0.10,0.13,0.085,0.04,0.045,0.052 \
  --start-date 2019-09-24
```

#### 2. 动态平衡策略（阈值±20% + 年度）
```bash
python3 {baseDir}/scripts/fund_backtest_dynamic_rebalance.py \
  --funds 110017,159985,166301,217022,539001,000216,002849,002943,004011,004993,005561,006373 \
  --weights 0.075,0.08,0.08,0.167,0.031,0.115,0.10,0.13,0.085,0.04,0.045,0.052 \
  --start-date 2019-09-24 \
  --threshold 0.20 \
  --rebalance-month 1
```

#### 3. 自动生成优化组合
```bash
python3 {baseDir}/scripts/auto_portfolio_generator.py
```

### 📊 组合回测（年平衡策略）

#### 基础回测
```bash
python3 {baseDir}/scripts/fund_backtest_tiantian.py \
  --funds 110017,002943,000216,217022 \
  --weights 0.25,0.25,0.25,0.25
```

#### 指定回测期间
```bash
python3 {baseDir}/scripts/fund_backtest_tiantian.py \
  --funds 110017,002943,000216,217022 \
  --weights 0.25,0.25,0.25,0.25 \
  --start-date 2019-09-24 \
  --end-date 2026-03-14
```

#### 自定义再平衡月份（如每年 6 月）
```bash
python3 {baseDir}/scripts/fund_backtest_tiantian.py \
  --funds 110017,002943,000216,217022 \
  --weights 0.25,0.25,0.25,0.25 \
  --rebalance-month 6
```

#### 输出 JSON 格式
```bash
python3 {baseDir}/scripts/fund_backtest_tiantian.py \
  --funds 110017,002943,000216,217022 \
  --weights 0.25,0.25,0.25,0.25 \
  --json
```

### 🔄 动态平衡策略

#### 阈值±20% + 年度平衡
```bash
python3 {baseDir}/scripts/fund_backtest_dynamic_rebalance.py \
  --funds 002943,159985,166301,000216 \
  --weights 0.3,0.2,0.3,0.2 \
  --threshold 0.20 \
  --rebalance-month 1 \
  --start-date 2019-09-24
```

#### 仅阈值平衡（无年度）
```bash
python3 {baseDir}/scripts/fund_backtest_dynamic_rebalance.py \
  --funds 002943,159985,166301 \
  --weights 0.4,0.3,0.3 \
  --threshold 0.15 \
  --rebalance-month 0
```

### 🎯 组合优化

#### 基础优化
```bash
python3 {baseDir}/scripts/fund_optimizer.py optimize \
  --funds 110017,002943,000216,217022 \
  --weights 0.25,0.25,0.25,0.25
```

#### 蒙特卡洛模拟（10000 次）
```bash
python3 {baseDir}/scripts/fund_optimizer.py optimize \
  --funds 110017,002943,000216,217022 \
  --weights 0.25,0.25,0.25,0.25 \
  --simulations 10000
```

## 参数说明

### 回测器参数（fund_backtest_tiantian.py）

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `--funds` | 基金代码列表，逗号分隔 | 是 | - |
| `--weights` | 配置比例，逗号分隔（总和=1） | 是 | - |
| `--start-date` | 回测开始日期 YYYY-MM-DD | 否 | 2019-01-01 |
| `--end-date` | 回测结束日期 YYYY-MM-DD | 否 | 今天 |
| `--rebalance-month` | 再平衡月份（1-12） | 否 | 1 |
| `--initial-capital` | 初始资金 | 否 | 1000000 |
| `--json` | 输出 JSON 格式 | 否 | False |

### 动态平衡参数（fund_backtest_dynamic_rebalance.py）

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `--funds` | 基金代码列表 | 是 | - |
| `--weights` | 目标权重列表 | 是 | - |
| `--threshold` | 阈值平衡触发点（如 0.20=20%） | 否 | 0.20 |
| `--rebalance-month` | 年度平衡月份（0=禁用） | 否 | 1 |
| `--start-date` | 回测开始日期 | 否 | 2019-01-01 |
| `--json` | 输出 JSON 格式 | 否 | False |

### 优化器参数（fund_optimizer.py）

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `--funds` | 基金代码列表 | 是 | - |
| `--weights` | 初始配置比例 | 是 | - |
| `--simulations` | 蒙特卡洛模拟次数 | 否 | 5000 |
| `--start-date` | 回测开始日期 | 否 | 2019-01-01 |
| `--json` | 输出 JSON 格式 | 否 | False |

## 输出说明

### 优化结果（fund_optimizer.py）
```json
{
  "optimal_weights": [0.35, 0.25, 0.20, 0.20],
  "expected_return": 0.085,
  "volatility": 0.12,
  "sharpe_ratio": 0.58,
  "max_drawdown": -0.15,
  "comparison": {
    "initial_sharpe": 0.42,
    "optimized_sharpe": 0.58,
    "improvement": "38%"
  }
}
```

### 回测结果（fund_backtest.py）
```json
{
  "total_return": 1.09,           // 累计收益率
  "cagr": 0.1198,                 // 年化收益率
  "max_drawdown": -0.1045,        // 最大回撤
  "volatility": 0.1311,           // 年化波动率
  "sharpe_ratio": 1.87,           // 夏普比率
  "calmar_ratio": 2.35,           // 卡玛比率
  "yearly_returns": [             // 年度收益列表
    {"year": 2020, "return": 0.15, "max_drawdown": -0.08},
    {"year": 2021, "return": 0.08, "max_drawdown": -0.05}
  ],
  "quarterly_returns": [          // 季度收益列表
    {"year": 2020, "quarter": "Q1", "return": 0.03},
    {"year": 2020, "quarter": "Q2", "return": 0.05}
  ]
}
```

### 指标解释
#### 优化器指标
- **expected_return**: 预期年化收益率
- **volatility**: 年化波动率（风险）
- **sharpe_ratio**: 夏普比率（风险调整后收益）
- **max_drawdown**: 最大回撤

#### 回测器指标
- **total_return**: 累计收益率（整个回测期间）
- **cagr**: 年化复合增长率（Compound Annual Growth Rate）
- **max_drawdown**: 最大回撤（历史最大亏损幅度）
- **volatility**: 年化波动率（风险指标）
- **sharpe_ratio**: 夏普比率（每单位风险获得的超额收益）
- **calmar_ratio**: 卡玛比率（年化收益/最大回撤，衡量风险收益比）
- **yearly_returns**: 各年度收益列表
- **quarterly_returns**: 各季度收益列表

## 依赖

```bash
pip install pandas numpy requests
```

## 注意事项

1. **数据源**: 天天基金网实时数据（`fund.eastmoney.com/pingzhongdata/`）
2. **缓存**: 数据自动缓存 7 天，避免重复请求
3. **QDII 基金**: 可能存在 1-2 天延迟，限购需控制权重（建议<10%）
4. **动态平衡**: 阈值平衡最小间隔 5 个交易日，避免过度交易
5. **风险提示**: 历史数据不代表未来表现，投资需谨慎

## 脚本说明

| 脚本 | 功能 | 适用场景 |
|------|------|---------|
| `fund_backtest_tiantian.py` | 年平衡回测 | 基础回测，每年固定月份再平衡 |
| `fund_backtest_dynamic_rebalance.py` | 动态平衡回测 | 阈值 + 年度双重平衡策略 |
| `fund_optimizer.py` | 组合优化 | 寻找最优配置比例 |
| `auto_portfolio_generator.py` | 自动生成组合 | 快速生成保守/平衡/进取组合 |

## 示例：用户的 12 只基金组合

```bash
# 回测当前组合
python3 scripts/fund_backtest_tiantian.py \
  --funds 110017,159985,166301,217022,539001,000216,002849,002943,004011,004993,005561,006373 \
  --weights 0.075,0.08,0.08,0.167,0.031,0.115,0.10,0.13,0.085,0.04,0.045,0.052 \
  --start-date 2019-09-24

# 动态平衡策略（20% 阈值）
python3 scripts/fund_backtest_dynamic_rebalance.py \
  --funds 110017,159985,166301,217022,539001,000216,002849,002943,004011,004993,005561,006373 \
  --weights 0.075,0.08,0.08,0.167,0.031,0.115,0.10,0.13,0.085,0.04,0.045,0.052 \
  --threshold 0.20 \
  --rebalance-month 1 \
  --start-date 2019-09-24

# 自动生成优化组合
python3 scripts/auto_portfolio_generator.py
```

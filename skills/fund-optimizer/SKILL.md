---
name: fund-optimizer
description: 基金组合优化与回测技能。基于历史数据（2019 年至今）使用现代投资组合理论（MPT）计算最优配置比例，支持年平衡策略回测。
author: Assistant
version: 1.1.0
metadata: {"clawdbot":{"emoji":"📊","requires":{"bins":["python3","uv"]},"config":{"env":{"AKSHARE_CACHE_DIR":{"description":"数据缓存目录","default":"~/.openclaw/workspace/skills/fund-optimizer/cache","required":false}}}}}
---

# 基金组合优化与回测技能

基于现代投资组合理论（Modern Portfolio Theory, MPT）和历史数据，提供基金组合优化和回测功能。

## 功能

### 组合优化
- 📈 获取基金历史净值数据（2019 年至今）
- 🎯 计算有效前沿（Efficient Frontier）
- 🏆 寻找最优夏普比率组合
- 📊 生成风险分析报告
- 💡 提供调仓建议

### 组合回测
- 📊 年化收益率（CAGR）
- 📉 最大回撤（Max Drawdown）
- 🎯 卡玛比率（Calmar Ratio）
- 📅 年度收益列表
- 📅 季度收益列表
- 🔄 年平衡策略支持

## 使用方法

### 🎯 组合优化

#### 基础优化
```bash
uv run {baseDir}/scripts/fund_optimizer.py optimize \
  --funds 110017,002943,000216,217022 \
  --weights 0.25,0.25,0.25,0.25
```

#### 指定日期范围
```bash
uv run {baseDir}/scripts/fund_optimizer.py optimize \
  --funds 110017,002943,000216 \
  --weights 0.4,0.3,0.3 \
  --start-date 2019-01-01 \
  --end-date 2026-03-11
```

#### 蒙特卡洛模拟（更精确）
```bash
uv run {baseDir}/scripts/fund_optimizer.py optimize \
  --funds 110017,002943,000216,217022 \
  --weights 0.25,0.25,0.25,0.25 \
  --simulations 10000
```

#### 查看详细报告
```bash
uv run {baseDir}/scripts/fund_optimizer.py report \
  --funds 110017,002943,000216 \
  --weights 0.3,0.4,0.3
```

### 📊 组合回测（年平衡策略）

#### 基础回测
```bash
uv run {baseDir}/scripts/fund_backtest.py \
  --funds 110017,002943,000216,217022 \
  --weights 0.25,0.25,0.25,0.25
```

#### 指定回测期间
```bash
uv run {baseDir}/scripts/fund_backtest.py \
  --funds 110017,002943,000216,217022 \
  --weights 0.25,0.25,0.25,0.25 \
  --start-date 2019-09-01 \
  --end-date 2026-03-13
```

#### 自定义再平衡月份（如每年 6 月）
```bash
uv run {baseDir}/scripts/fund_backtest.py \
  --funds 110017,002943,000216,217022 \
  --weights 0.25,0.25,0.25,0.25 \
  --rebalance-month 6
```

#### 输出 JSON 格式（便于程序处理）
```bash
uv run {baseDir}/scripts/fund_backtest.py \
  --funds 110017,002943,000216,217022 \
  --weights 0.25,0.25,0.25,0.25 \
  --json
```

#### 自定义初始资金
```bash
uv run {baseDir}/scripts/fund_backtest.py \
  --funds 110017,002943,000216,217022 \
  --weights 0.25,0.25,0.25,0.25 \
  --initial-capital 500000
```

## 参数说明

### 优化器参数（fund_optimizer.py）

| 参数 | 说明 | 必填 |
|------|------|------|
| `--funds` | 基金代码列表，逗号分隔 | 是 |
| `--weights` | 初始配置比例，逗号分隔（总和=1） | 是 |
| `--start-date` | 回测开始日期，默认 2019-01-01 | 否 |
| `--end-date` | 回测结束日期，默认今天 | 否 |
| `--simulations` | 蒙特卡洛模拟次数，默认 5000 | 否 |
| `--risk-free-rate` | 无风险利率（年化），默认 0.03 | 否 |
| `--json` | 输出 JSON 格式 | 否 |

### 回测器参数（fund_backtest.py）

| 参数 | 说明 | 必填 |
|------|------|------|
| `--funds` | 基金代码列表，逗号分隔 | 是 |
| `--weights` | 配置比例，逗号分隔（总和=1） | 是 |
| `--start-date` | 回测开始日期，默认 2019-01-01 | 否 |
| `--end-date` | 回测结束日期，默认今天 | 否 |
| `--rebalance-month` | 再平衡月份（1-12），默认 1 月 | 否 |
| `--initial-capital` | 初始资金，默认 1,000,000 | 否 |
| `--json` | 输出 JSON 格式 | 否 |

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
uv pip install pandas numpy scipy akshare matplotlib
```

## 注意事项

1. **数据源**: 使用 AkShare 获取基金历史净值
2. **缓存**: 数据会自动缓存，避免重复请求
3. **QDII 基金**: 可能存在数据延迟
4. **风险提示**: 历史数据不代表未来表现，优化结果仅供参考

## 示例：优化用户的基金组合

用户当前持仓 12 只基金，可以先按类别分组优化：

```bash
# 债券类优化
uv run scripts/fund_optimizer.py optimize \
  --funds 110017,217022,004993 \
  --weights 0.33,0.34,0.33

# A 股混合类优化
uv run scripts/fund_optimizer.py optimize \
  --funds 002943,004011,166301,002849 \
  --weights 0.25,0.25,0.25,0.25

# QDII 类优化
uv run scripts/fund_optimizer.py optimize \
  --funds 017641,539001,006373,539002 \
  --weights 0.25,0.25,0.25,0.25
```

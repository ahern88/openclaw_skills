# 🚀 基金回测技能 - 快速使用指南

**版本**: 2.0.0  
**最后更新**: 2026-03-14

---

## 📋 一键回测（最常用）

### 回测你的 12 只基金组合

```bash
cd /home/admin/.openclaw/workspace/skills/fund-optimizer

python3 scripts/fund_backtest_tiantian.py \
  --funds 110017,159985,166301,217022,539001,000216,002849,002943,004011,004993,005561,006373 \
  --weights 0.075,0.08,0.08,0.167,0.031,0.115,0.10,0.13,0.085,0.04,0.045,0.052 \
  --start-date 2019-09-24
```

### 动态平衡策略（20% 阈值 + 年度）

```bash
python3 scripts/fund_backtest_dynamic_rebalance.py \
  --funds 110017,159985,166301,217022,539001,000216,002849,002943,004011,004993,005561,006373 \
  --weights 0.075,0.08,0.08,0.167,0.031,0.115,0.10,0.13,0.085,0.04,0.045,0.052 \
  --threshold 0.20 \
  --rebalance-month 1 \
  --start-date 2019-09-24
```

---

## 🎯 常用命令速查

### 1. 基础回测（年平衡）

```bash
# 任意组合回测
python3 scripts/fund_backtest_tiantian.py \
  --funds 基金代码 1，基金代码 2,... \
  --weights 权重 1，权重 2,... \
  --start-date 2019-09-24
```

### 2. 动态平衡

```bash
# 阈值 20% + 年度平衡
python3 scripts/fund_backtest_dynamic_rebalance.py \
  --funds 基金代码 1，基金代码 2,... \
  --weights 权重 1，权重 2,... \
  --threshold 0.20 \
  --rebalance-month 1
```

### 3. 自动生成组合

```bash
# 生成保守/平衡/进取三种方案
python3 scripts/auto_portfolio_generator.py
```

### 4. 组合优化

```bash
# 寻找最优配置
python3 scripts/fund_optimizer.py optimize \
  --funds 基金代码 1，基金代码 2,... \
  --weights 权重 1，权重 2,... \
  --simulations 10000
```

### 5. 输出 JSON

```bash
# 所有脚本都支持--json 参数
python3 scripts/fund_backtest_tiantian.py \
  --funds ... --weights ... --json > result.json
```

---

## 📊 你的组合配置（已保存）

**文件**: `recommended_portfolios.json`

### 平衡型（推荐）

| 代码 | 名称 | 权重 |
|------|------|------|
| 000216 | 华安黄金 ETF 联接 A | 21.1% |
| 002943 | 广发多因子混合 | 14.0% |
| 166301 | 华商新趋势混合 | 14.0% |
| 004011 | 华泰柏瑞鼎利混合 C | 14.0% |
| 110017 | 易方达增强回报债券 A | 13.2% |
| 217022 | 招商产业债券 A | 13.2% |
| 006373 | 国富全球科技互联 (QDII) | 10.5% |

**回测结果**: 年化 15.64%，回撤 8.87%，夏普 1.36

---

## 📁 文件结构

```
skills/fund-optimizer/
├── scripts/
│   ├── fund_backtest_tiantian.py          # 年平衡回测（推荐）
│   ├── fund_backtest_dynamic_rebalance.py # 动态平衡回测
│   ├── fund_optimizer.py                  # 组合优化
│   └── auto_portfolio_generator.py        # 自动生成组合
├── cache/                                  # 数据缓存（自动创建）
├── SKILL.md                               # 技能文档
├── README.md                              # 使用说明
├── DYNAMIC_REBALANCE_GUIDE.md            # 动态平衡指南
├── AUTO_PORTFOLIO_RESULTS.md             # 组合优化结果
├── recommended_portfolios.json           # 推荐组合配置
└── QUICK_START.md                        # 本文件
```

---

## 🔧 依赖安装

```bash
# 首次使用需要安装依赖
pip install pandas numpy requests
```

---

## 📈 输出指标说明

| 指标 | 说明 | 优秀标准 |
|------|------|---------|
| 年化收益 (CAGR) | 年化复合增长率 | >12% |
| 最大回撤 | 历史最大亏损 | >-10% |
| 夏普比率 | 风险调整后收益 | >1.0 |
| 卡玛比率 | 收益/回撤比 | >1.5 |
| 波动率 | 年化波动率 | <15% |

---

## 💡 常见问题

### Q: 数据从哪里来？
A: 天天基金网实时数据，自动缓存 7 天。

### Q: QDII 限购怎么办？
A: 权重控制在 10% 以内，自动生成器已考虑此因素。

### Q: 多久再平衡一次？
A: 建议每年 1 月（年度平衡），或偏离>20% 时（阈值平衡）。

### Q: 缓存在哪里？
A: `cache/` 目录，7 天自动更新。

### Q: 如何修改阈值？
A: 修改 `--threshold` 参数，如 `--threshold 0.15` 表示 15%。

---

## 📞 快速帮助

```bash
# 查看脚本帮助
python3 scripts/fund_backtest_tiantian.py --help
python3 scripts/fund_backtest_dynamic_rebalance.py --help
```

---

**保存时间**: 2026-03-14  
**技能版本**: 2.0.0  
**下次使用**: 直接运行上面的命令即可！

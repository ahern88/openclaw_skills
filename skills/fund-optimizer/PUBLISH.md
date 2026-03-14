# 📦 基金回测技能发布指南

## ✅ 已完成

1. ✅ 代码已保存到 `skills/fund-optimizer/` 目录
2. ✅ README 文档已创建
3. ✅ .gitignore 已配置（排除缓存和虚拟环境）
4. ✅ Git 提交已完成

## 🚀 发布到 GitHub

### 方法 1: 使用 GitHub Desktop（推荐新手）

1. 下载并安装 [GitHub Desktop](https://desktop.github.com/)
2. File → Add Local Repository → 选择 `/home/admin/.openclaw/workspace`
3. 点击 Publish repository
4. 仓库名：`openclaw-skills`
5. 勾选 "Keep this code private"（如果需要）

### 方法 2: 使用命令行

```bash
cd /home/admin/.openclaw/workspace

# 生成 GitHub Token
# 访问 https://github.com/settings/tokens
# 创建新 token，勾选 repo 权限

# 使用 token 推送
git remote set-url origin https://<YOUR_TOKEN>@github.com/ahern88/openclaw-skills.git
git push -u origin master

# 或使用 SSH（需要先配置 SSH key）
git remote set-url origin git@github.com:ahern88/openclaw-skills.git
git push -u origin master
```

### 方法 3: 直接上传 ZIP

1. 打包文件：
```bash
cd /home/admin/.openclaw/workspace
tar -czvf fund-optimizer-skill.tar.gz skills/fund-optimizer/
```

2. 在 GitHub 创建新仓库 `openclaw-skills`
3. Upload files → 选择 `skills/fund-optimizer/` 目录下的文件上传

## 📋 仓库结构

```
openclaw-skills/
├── skills/
│   └── fund-optimizer/
│       ├── README.md          # 使用说明
│       ├── SKILL.md           # OpenClaw 技能定义
│       ├── requirements.txt   # Python 依赖
│       ├── .gitignore        # Git 忽略配置
│       └── scripts/
│           ├── fund_backtest_tiantian.py  # 主回测脚本
│           ├── fund_optimizer.py          # 组合优化脚本
│           └── fund_backtest.py           # 旧版回测脚本
└── README.md
```

## 📝 使用示例

```bash
cd skills/fund-optimizer

# 安装依赖
pip install -r requirements.txt

# 运行回测
python scripts/fund_backtest_tiantian.py \
  --funds 002943,159985,165531 \
  --weights 0.4,0.3,0.3 \
  --start-date 2019-01-01
```

## 🎯 回测结果示例

你的组合（2019-09-24 ~ 2026-03-14）：

- **累计收益**: +261.51%
- **年化收益**: +23.06%
- **最大回撤**: -10.39%
- **夏普比率**: 1.51
- **卡玛比率**: 2.22

100 万 → 361.5 万

## ⚠️ 注意事项

1. 缓存数据（`cache/*.csv`）已排除，首次运行会自动下载
2. 虚拟环境（`.venv/`）已排除，需要重新创建
3. 数据源：天天基金网，请确保网络可达

## 📄 License

MIT License

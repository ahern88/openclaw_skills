# OpenClaw Skills 仓库

🦞 小艾的龙虾技能仓库 - 存储和管理 OpenClaw 技能

---

## 📚 技能列表

| 技能 | 说明 | 状态 |
|------|------|------|
| 🔍 **searxng** | 隐私保护的搜索引擎 | ✅ 已同步 |

---

## 🚀 使用方法

### 同步 Skills 到 GitHub

每次创建或更新 skill 后，执行：

```bash
cd /home/admin/.openclaw/workspace/openclaw_skills
git add .
git commit -m "feat: 添加/更新 xxx skill"
git push origin master
```

### 从 GitHub 同步 Skills 到本地

```bash
cd /home/admin/.openclaw/workspace
cp -r openclaw_skills/* skills/
```

---

## 📁 目录结构

```
openclaw_skills/
├── README.md          # 本文件
├── searxng/           # SearXNG 搜索技能
│   ├── SKILL.md       # 技能配置
│   ├── scripts/       # 脚本文件
│   └── ...
└── ...                # 其他技能
```

---

## 🛠️ 创建新 Skill 流程

1. **在本地创建 skill**
   ```bash
   mkdir -p /home/admin/.openclaw/workspace/skills/my-skill
   ```

2. **编写 skill 文件**
   - `SKILL.md` - 技能配置
   - 其他脚本和依赖

3. **测试 skill**
   - 确保功能正常

4. **同步到 GitHub**
   ```bash
   cd /home/admin/.openclaw/workspace/openclaw_skills
   cp -r ../skills/my-skill .
   git add .
   git commit -m "feat: 添加 my-skill 技能"
   git push origin master
   ```

---

## 📝 更新现有 Skill

1. **在本地修改 skill**

2. **测试功能**

3. **同步到 GitHub**
   ```bash
   cd /home/admin/.openclaw/workspace/openclaw_skills
   cp -r ../skills/my-skill .
   git add .
   git commit -m "fix: 更新 my-skill 功能"
   git push origin master
   ```

---

## ⚠️ 注意事项

1. **只同步成熟的 skills** - 确保功能稳定后再提交
2. **写好文档** - 每个 skill 要有清晰的说明
3. **版本管理** - 使用语义化版本号
4. **依赖管理** - 记录所有外部依赖

---

## 📖 参考资料

- [OpenClaw 官方文档](https://docs.openclaw.ai)
- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [Skill 开发指南](https://docs.openclaw.ai/skills)

---

_🦞 Created by 小艾的龙虾 | 2026-03-06_

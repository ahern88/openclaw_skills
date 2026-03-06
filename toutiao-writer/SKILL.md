---
name: toutiao-writer
description: 今日头条文章自动发布技能。支持文章生成、素材管理、定时发布。
author: 小艾的龙虾
version: 1.0.0
metadata: {"clawdbot":{"emoji":"📰","requires":{"bins":["python3","curl"]},"config":{"env":{"TOUTIAO_APP_KEY":{"description":"头条号 App Key","required":false},"TOUTIAO_APP_SECRET":{"description":"头条号 App Secret","required":false},"TOUTIAO_ACCESS_TOKEN":{"description":"访问 Token","required":false}}}}}
---

# 今日头条文章发布技能

自动发布文章到今日头条（头条号）平台。

---

## 📋 功能

1. **文章生成** - AI 自动生成文章内容
2. **素材管理** - 自动上传和管理图片
3. **定时发布** - 支持定时推送
4. **数据查询** - 查看阅读、评论等数据

---

## 🔧 配置方式

### 方式一：官方 API（推荐）

**步骤：**

1. **申请开发者账号**
   - 访问：https://open.toutiao.com/
   - 注册开发者账号
   - 创建应用

2. **获取凭证**
   - App Key
   - App Secret
   - Access Token

3. **配置技能**
   ```json
   {
     "toutiao": {
       "app_key": "your_app_key",
       "app_secret": "your_app_secret",
       "access_token": "your_access_token"
     }
   }
   ```

### 方式二：浏览器自动化（备选）

如果无法申请 API，可以使用浏览器自动化：

1. 手动登录头条号
2. 使用脚本模拟发布
3. ⚠️ 注意风控风险

---

## 🚀 使用方式

### 发布文章

```
帮我写一篇关于 xxx 的文章，发布到今日头条
```

AI 会自动：
1. 生成文章内容
2. 上传封面图
3. 发布到头条号
4. 返回文章链接

### 定时发布

```
每天早上 9 点发布一篇 AI 领域的文章到今日头条
```

### 查看数据

```
查看我昨天发布的文章数据
```

---

## 📁 目录结构

```
toutiao-writer/
├── SKILL.md              # 技能配置
├── README.md             # 使用说明
├── scripts/
│   ├── publish.py        # 发布脚本
│   ├── upload-media.py   # 素材上传
│   └── get-stats.py      # 数据查询
├── templates/
│   └── article.md        # 文章模板
└── references/
    └── api-docs.md       # API 文档
```

---

## ⚠️ 注意事项

1. **API 权限** - 需要申请头条号开发者权限
2. **内容质量** - 确保文章原创，避免抄袭
3. **发布频率** - 避免短时间大量发布
4. **风控风险** - 浏览器自动化可能触发风控

---

## 📖 参考资料

- [头条号开放平台](https://open.toutiao.com/)
- [API 文档](https://open.toutiao.com/docs)
- [开发者社区](https://open.toutiao.com/community)

---

_🦞 Created by 小艾的龙虾_

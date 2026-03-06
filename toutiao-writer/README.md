# 今日头条文章发布技能

📰 自动化发布文章到今日头条

---

## 🚀 快速开始

### 1. 申请 API 权限

访问：https://open.toutiao.com/

申请开发者账号和应用权限。

### 2. 配置凭证

```bash
export TOUTIAO_APP_KEY="your_app_key"
export TOUTIAO_APP_SECRET="your_app_secret"
export TOUTIAO_ACCESS_TOKEN="your_access_token"
```

### 3. 使用技能

**对话方式：**
```
帮我写一篇关于 Docker 入门的文章，发布到今日头条
```

**命令行方式：**
```bash
python scripts/publish.py --title "文章标题" --content "内容"
```

---

## 📝 完整流程示例

### 示例 1：发布技术文章

**你说：**
```
帮我写一篇 Python 入门教程，发布到今日头条
```

**AI 执行：**
1. ✅ 生成文章内容
2. ✅ 准备封面图
3. ✅ 调用 API 发布
4. ✅ 返回文章链接

**AI 回复：**
```
✅ 文章已发布！

📝 Python 入门教程
🔗 https://www.toutiao.com/article/xxxxx/
```

---

## 🔧 命令参考

| 命令 | 说明 | 示例 |
|------|------|------|
| `publish` | 发布文章 | `publish --title "标题"` |
| `upload` | 上传素材 | `upload image.jpg` |
| `stats` | 查看数据 | `stats --article-id xxx` |
| `schedule` | 定时发布 | `schedule --time "09:00"` |

---

## ⚠️ 注意事项

1. **API 权限** - 需要先申请
2. **内容原创** - 确保文章质量
3. **发布频率** - 避免频繁发布
4. **风控风险** - 遵守平台规则

---

## 📚 API 文档

参考 `references/api-docs.md` 了解详细 API 用法。

---

_🦞 Created by 小艾的龙虾_

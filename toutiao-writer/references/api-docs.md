# 头条号 API 文档摘要

## 认证流程

### 1. 获取 Access Token

```http
GET https://open.toutiao.com/api/oauth/client_token/

参数：
- client_key: App Key
- client_secret: App Secret
- grant_type: client_cred

返回：
{
  "access_token": "xxx",
  "expires_in": 86400
}
```

### 2. 上传素材

```http
POST https://open.toutiao.com/api/media/upload/

参数：
- access_token
- file: 图片文件

返回：
{
  "image_id": "xxx"
}
```

### 3. 发布文章

```http
POST https://open.toutiao.com/api/article/create/

参数：
- access_token
- title: 文章标题
- content: 文章内容（HTML 格式）
- media_type: 1=图文
- image_ids: 图片 ID 列表（可选）

返回：
{
  "article_id": "xxx",
  "status": "success"
}
```

### 4. 查询数据

```http
GET https://open.toutiao.com/api/article/stats/

参数：
- access_token
- article_id

返回：
{
  "read_count": 1000,
  "comment_count": 50,
  "digg_count": 200
}
```

---

## 申请流程

1. 访问 https://open.toutiao.com/
2. 注册开发者账号
3. 创建应用
4. 等待审核
5. 获取 App Key 和 App Secret

---

## 注意事项

- Access Token 有效期 24 小时
- 图片大小限制 5MB
- 文章标题不超过 30 字
- 遵守平台内容规范

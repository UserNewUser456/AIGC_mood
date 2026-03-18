# API接口文档

## 服务器地址
```
http://49.235.105.137:5005
```

---

# 一、管理员后台API

### 1. 健康检查
- **URL**: `/health`
- **方法**: GET
- **响应**: `{"status": "ok"}`

### 2. 管理员登录
- **URL**: `/api/admin/login`
- **方法**: POST
- **请求体**:
```json
{
    "username": "admin",
    "password": "admin123"
}
```
- **响应（成功）**:
```json
{
    "success": true,
    "data": {
        "token": "xxxxx",
        "username": "admin"
    }
}
```
- **响应（失败）**:
```json
{
    "success": false,
    "error": "用户名或密码错误"
}
```

### 3. 管理员登出
- **URL**: `/api/admin/logout`
- **方法**: POST
- **Headers**: `Authorization: Bearer <token>`

### 4. 检查登录状态
- **URL**: `/api/admin/check`
- **方法**: GET
- **Headers**: `Authorization: Bearer <token>`
- **响应**:
```json
{
    "success": true,
    "username": "admin"
}
```

### 5. 获取统计数据
- **URL**: `/api/admin/stats`
- **方法**: GET
- **Headers**: `Authorization: Bearer <token>`
- **响应**:
```json
{
    "success": true,
    "data": {
        "today_users": 5,
        "total_users": 100,
        "high_risk_alerts": 2,
        "today_sales": 1500.00,
        "total_sales": 50000.00
    }
}
```

### 6. 获取商品列表
- **URL**: `/api/admin/products`
- **方法**: GET
- **Headers**: `Authorization: Bearer <token>`

### 7. 添加商品
- **URL**: `/api/admin/products`
- **方法**: POST
- **Headers**: `Authorization: Bearer <token>`
- **请求体**:
```json
{
    "name": "商品名称",
    "description": "商品描述",
    "price": 99.00,
    "stock": 100,
    "category": "category1"
}
```

### 8. 删除商品
- **URL**: `/api/admin/products/<id>`
- **方法**: DELETE
- **Headers**: `Authorization: Bearer <token>`

### 9. 获取风险预警列表
- **URL**: `/api/admin/risks`
- **方法**: GET
- **Headers**: `Authorization: Bearer <token>`

### 10. 处理风险预警
- **URL**: `/api/admin/risks/<id>/handle`
- **方法**: POST
- **Headers**: `Authorization: Bearer <token>`
- **请求体**:
```json
{
    "handle_method": "已联系用户",
    "handle_result": "已跟进"
}
```

### 11. 获取订单列表
- **URL**: `/api/admin/orders`
- **方法**: GET
- **Headers**: `Authorization: Bearer <token>`

### 12. 更新订单状态
- **URL**: `/api/admin/orders/<id>`
- **方法**: PUT
- **Headers**: `Authorization: Bearer <token>`
- **请求体**:
```json
{
    "status": "shipped"
}
```

### 13. 获取用户列表
- **URL**: `/api/admin/users`
- **方法**: GET
- **Headers**: `Authorization: Bearer <token>`

---

# 二、RAG知识库API

### 1. RAG问答
- **URL**: `/api/rag-knowledge/rag`
- **方法**: POST
- **请求体**:
```json
{
    "question": "如何缓解焦虑？"
}
```
- **响应**:
```json
{
    "success": true,
    "data": {
        "question": "如何缓解焦虑？",
        "answer": "缓解焦虑的方法包括...",
        "intent": "health_advice",
        "expanded_query": "如何缓解焦虑 焦虑症",
        "sources": [
            {"title": "心理健康知识", "score": 0.95}
        ]
    }
}
```

### 2. 搜索知识
- **URL**: `/api/rag-knowledge?keyword=焦虑&category=健康`
- **方法**: GET
- **参数**:
  - keyword: 搜索关键词
  - category: 分类筛选
- **响应**:
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "category": "健康",
            "title": "焦虑的应对方法",
            "content": "内容...",
            "tags": "焦虑,心理"
        }
    ]
}
```

### 3. 添加知识
- **URL**: `/api/rag-knowledge`
- **方法**: POST
- **请求体**:
```json
{
    "category": "健康",
    "title": "如何缓解焦虑",
    "content": "详细内容...",
    "tags": "焦虑,放松"
}
```

### 4. 更新知识
- **URL**: `/api/rag-knowledge/<id>`
- **方法**: PUT
- **请求体**:
```json
{
    "category": "健康",
    "title": "新标题",
    "content": "新内容",
    "tags": "新标签"
}
```

### 5. 删除知识
- **URL**: `/api/rag-knowledge/<id>`
- **方法**: DELETE

### 6. 获取分类列表
- **URL**: `/api/rag-knowledge/categories`
- **方法**: GET

---

# 三、错误响应格式

```json
{
    "success": false,
    "error": "错误信息"
}
```

常见状态码：
- 200: 成功
- 400: 请求参数错误
- 401: 未授权（未登录或token无效）
- 404: 资源不存在
- 500: 服务器内部错误

---

# 四、前端调用示例

```javascript
// 1. 管理员登录
const loginRes = await fetch('http://49.235.105.137:5005/api/admin/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: 'admin123' })
});
const { token } = await loginRes.json();

// 2. 获取统计数据
const statsRes = await fetch('http://49.235.105.137:5005/api/admin/stats', {
    headers: { 'Authorization': `Bearer ${token}` }
});

// 3. RAG问答
const ragRes = await fetch('http://49.235.105.137:5005/api/rag-knowledge/rag', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: '如何缓解焦虑？' })
});
```

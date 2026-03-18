# API接口文档

## 服务器地址
```
http://49.235.105.137:5005  (管理员后台)
http://49.235.105.137:5001  (RAG知识库)
```

---

# 一、管理员后台API (端口5005)

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

### 3. 管理员登出
- **URL**: `/api/admin/logout`
- **方法**: POST
- **Headers**: `Authorization: Bearer <token>`

### 4. 检查登录状态
- **URL**: `/api/admin/check`
- **方法**: GET
- **Headers**: `Authorization: Bearer <token>`

### 5. 获取统计数据
- **URL**: `/api/admin/stats`
- **方法**: GET
- **Headers**: `Authorization: Bearer <token>`

### 6. 商品管理
- **获取列表**: GET `/api/admin/products`
- **添加商品**: POST `/api/admin/products`
- **删除商品**: DELETE `/api/admin/products/<id>`

### 7. 风险预警
- **获取列表**: GET `/api/admin/risks`
- **处理预警**: POST `/api/admin/risks/<id>/handle`

### 8. 订单管理
- **获取列表**: GET `/api/admin/orders`
- **更新状态**: PUT `/api/admin/orders/<id>`

### 9. 用户管理
- **获取列表**: GET `/api/admin/users`

---

# 二、智能知识库RAG API (端口5001)

## 核心功能：结合知识库 + AI大模型 + 情绪安抚

### 1. 智能对话 (核心接口)
- **URL**: `/api/rag-knowledge/chat`
- **方法**: POST
- **功能**：
  - 检测用户情绪状态
  - 从知识库检索相关内容
  - 调用AI大模型生成专业、温暖的回答
  - 危机情况自动预警

**请求体**:
```json
{
    "question": "我最近总是很焦虑，晚上睡不着",
    "user_id": 123,
    "stream": false
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "question": "我最近总是很焦虑，晚上睡不着",
        "answer": "我理解你现在的焦虑感，这种感觉确实让人不舒服...\n\n根据心理学研究，焦虑性失眠是很常见的...\n\n你可以尝试以下方法...",
        "emotion": "焦虑",
        "risk_level": "medium",
        "sources": [
            {"id": 1, "title": "焦虑症的自我调节", "category": "心理问题", "score": 0.95},
            {"id": 5, "title": "失眠的认知行为疗法", "category": "睡眠问题", "score": 0.88}
        ]
    }
}
```

### 2. 流式对话
- **URL**: `/api/rag-knowledge/chat`
- **方法**: POST
- **请求体**: `{"question": "...", "stream": true}`
- **返回**: SSE流式数据

### 3. 知识库管理

#### 3.1 搜索知识
- **URL**: `/api/rag-knowledge?keyword=焦虑&category=心理问题&page=1`
- **方法**: GET

#### 3.2 获取知识详情
- **URL**: `/api/rag-knowledge/<id>`
- **方法**: GET

#### 3.3 添加知识
- **URL**: `/api/rag-knowledge`
- **方法**: POST
- **请求体**:
```json
{
    "category": "心理问题",
    "title": "焦虑症的自我调节方法",
    "content": "详细内容...",
    "tags": "焦虑,自我调节,心理健康",
    "source": "心理学书籍《XX》"
}
```

#### 3.4 更新知识
- **URL**: `/api/rag-knowledge/<id>`
- **方法**: PUT

#### 3.5 删除知识
- **URL**: `/api/rag-knowledge/<id>`
- **方法**: DELETE

#### 3.6 获取分类列表
- **URL**: `/api/rag-knowledge/categories`
- **方法**: GET

#### 3.7 批量导入
- **URL**: `/api/rag-knowledge/batch`
- **方法**: POST
- **请求体**:
```json
{
    "items": [
        {"title": "...", "content": "...", "category": "..."},
        {"title": "...", "content": "...", "category": "..."}
    ]
}
```

### 4. 健康检查
- **URL**: `/health`
- **方法**: GET

---

# 三、RAG系统特点

## 1. 情绪检测能力
系统能自动识别用户情绪：
- **焦虑**：紧张、不安、担心
- **抑郁**：低落、沮丧、绝望
- **愤怒**：生气、暴躁、不满
- **恐惧**：害怕、惊恐
- **孤独**：寂寞、没人理解
- **危机**：自杀、自残想法

## 2. 智能安抚
根据检测到的情绪，AI会自动：
- 先表达理解和共情
- 提供专业的心理学解释
- 给出具体可行的方法
- 温暖的鼓励

## 3. 危机干预
当检测到严重风险词时，系统会：
- 立即提供危机干预信息
- 显示紧急求助热线
- 强烈建议寻求专业帮助

## 4. 知识库支持
- 支持导入心理学专业书籍内容
- 智能检索相关知识
- 支持分类管理

---

# 四、前端调用示例

```javascript
// 智能对话
const res = await fetch('http://49.235.105.137:5001/api/rag-knowledge/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        question: '我最近压力很大，怎么办？',
        user_id: 123
    })
});
const data = await res.json();
console.log(data.data.answer);  // AI生成的温暖回答

// 流式对话
const eventSource = new EventSource(
    'http://49.235.105.137:5001/api/rag-knowledge/chat',
    { method: 'POST', body: JSON.stringify({question: '...', stream: true}) }
);
eventSource.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.type === 'content') {
        console.log(data.content);  // 逐字显示
    }
};
```

---

# 五、错误响应

```json
{
    "success": false,
    "error": "错误信息"
}
```

状态码：
- 200: 成功
- 400: 参数错误
- 401: 未授权
- 404: 资源不存在
- 500: 服务器错误

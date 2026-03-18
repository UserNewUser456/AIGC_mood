# API接口文档

## 服务器地址
```
http://49.235.105.137:5005  (管理员后台)
http://49.235.105.137:5001  (RAG知识图谱)
```

---

# 一、管理员后台API (端口5005)

## 1.1 基础接口

### 1. 健康检查
- **URL**: `/health`
- **方法**: GET
- **响应**:
```json
{
    "status": "ok",
    "time": "2024-01-07T10:00:00",
    "neo4j": "connected"
}
```

### 2. 管理员登录
- **URL**: `POST /api/admin/login`
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
- **URL**: `POST /api/admin/logout`
- **Headers**: `Authorization: Bearer <token>`

### 4. 检查登录状态
- **URL**: `GET /api/admin/check`
- **Headers**: `Authorization: Bearer <token>`

---

## 1.2 统计与 Dashboard

### 5. 获取统计数据
- **URL**: `GET /api/admin/stats`
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

---

## 1.3 商品管理

### 6. 获取商品列表
- **URL**: `GET /api/admin/products`
- **Headers**: `Authorization: Bearer <token>`

### 7. 添加商品
- **URL**: `POST /api/admin/products`
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
- **URL**: `DELETE /api/admin/products/<id>`
- **Headers**: `Authorization: Bearer <token>`

---

## 1.4 风险预警

### 9. 获取风险预警列表
- **URL**: `GET /api/admin/risks`
- **Headers**: `Authorization: Bearer <token>`

### 10. 处理风险预警
- **URL**: `POST /api/admin/risks/<id>/handle`
- **Headers**: `Authorization: Bearer <token>`
- **请求体**:
```json
{
    "handle_method": "已联系用户",
    "handle_result": "已跟进"
}
```

---

## 1.5 订单管理

### 11. 获取订单列表
- **URL**: `GET /api/admin/orders`
- **Headers**: `Authorization: Bearer <token>`

### 12. 更新订单状态
- **URL**: `PUT /api/admin/orders/<id>`
- **Headers**: `Authorization: Bearer <token>`
- **请求体**:
```json
{
    "status": "shipped"
}
```

---

## 1.6 用户管理

### 13. 获取用户列表
- **URL**: `GET /api/admin/users`
- **Headers**: `Authorization: Bearer <token>`

---

# 二、知识库管理API (端口5005，需管理员权限)

## 2.1 核心功能：从文本自动构建知识图谱

### 14. 从文本导入知识 ⭐核心接口
- **URL**: `POST /api/admin/knowledge/import`
- **Headers**: `Authorization: Bearer <token>`
- **功能**：自动解析心理学文本，提取实体和关系，构建知识图谱

**请求体**:
```json
{
    "title": "《焦虑症治疗指南》第一章",
    "source": "《焦虑症治疗指南》",
    "text": "焦虑症是一种常见的心理障碍，表现为心慌、失眠等症状。认知行为疗法是治疗焦虑的有效方法，包括深呼吸练习等技巧..."
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "成功导入知识，提取了5个实体和3个关系",
    "data": {
        "import_id": 1,
        "entities": [
            {"type": "Emotion", "name": "焦虑症", "description": "常见的心理障碍"},
            {"type": "Symptom", "name": "心慌", "description": "..."},
            {"type": "Symptom", "name": "失眠", "description": "..."},
            {"type": "Treatment", "name": "认知行为疗法", "description": "..."},
            {"type": "Technique", "name": "深呼吸练习", "description": "..."}
        ],
        "relationships": [
            {"from": "焦虑症", "to": "心慌", "type": "LEADS_TO"},
            {"from": "焦虑症", "to": "失眠", "type": "LEADS_TO"},
            {"from": "焦虑症", "to": "认知行为疗法", "type": "RELIEVED_BY"}
        ]
    }
}
```

**说明**：
- 使用AI大模型自动从文本中提取实体和关系
- 支持的实体类型：Emotion(情绪)、Symptom(症状)、Treatment(治疗)、Technique(技巧)、Cause(原因)
- 支持的关系类型：LEADS_TO(导致)、RELIEVED_BY(缓解)、HAS_TECHNIQUE(有技巧)、CAUSED_BY(由...引起)

### 15. 获取导入记录
- **URL**: `GET /api/admin/knowledge/imports?page=1&per_page=20`
- **Headers**: `Authorization: Bearer <token>`
- **响应**:
```json
{
    "success": true,
    "data": {
        "list": [
            {
                "id": 1,
                "title": "《焦虑症治疗指南》第一章",
                "source": "《焦虑症治疗指南》",
                "content_preview": "焦虑症是一种常见的心理障碍...",
                "entity_count": 5,
                "relation_count": 3,
                "imported_by": "admin",
                "import_time": "2024-01-07 10:00"
            }
        ],
        "total": 10,
        "page": 1,
        "per_page": 20
    }
}
```

### 16. 获取知识图谱可视化数据
- **URL**: `GET /api/admin/knowledge/graph?emotion=焦虑`
- **Headers**: `Authorization: Bearer <token>`
- **功能**：获取知识图谱的节点和关系数据，用于可视化展示
- **响应**:
```json
{
    "success": true,
    "data": {
        "nodes": [
            {"id": 1, "name": "焦虑", "type": "Emotion", "description": "..."},
            {"id": 2, "name": "心慌", "type": "Symptom", "description": "..."},
            {"id": 3, "name": "认知行为疗法", "type": "Treatment", "description": "..."}
        ],
        "links": [
            {"source": 1, "target": 2, "type": "LEADS_TO"},
            {"source": 1, "target": 3, "type": "RELIEVED_BY"}
        ]
    }
}
```

---

## 2.2 知识图谱节点管理

### 17. 获取节点列表
- **URL**: `GET /api/admin/knowledge/nodes?type=Emotion&keyword=焦虑`
- **Headers**: `Authorization: Bearer <token>`
- **参数**：
  - `type`: 节点类型（可选）
  - `keyword`: 搜索关键词（可选）

### 18. 手动创建节点
- **URL**: `POST /api/admin/knowledge/node`
- **Headers**: `Authorization: Bearer <token>`
- **请求体**:
```json
{
    "type": "Treatment",
    "name": "音乐疗法",
    "description": "通过聆听音乐来调节情绪的方法"
}
```

### 19. 删除节点
- **URL**: `DELETE /api/admin/knowledge/node/<name>`
- **Headers**: `Authorization: Bearer <token>`
- **说明**：删除节点及其所有关系

---

## 2.3 知识图谱关系管理

### 20. 手动创建关系
- **URL**: `POST /api/admin/knowledge/relationship`
- **Headers**: `Authorization: Bearer <token>`
- **请求体**:
```json
{
    "from": "焦虑症",
    "to": "音乐疗法",
    "type": "RELIEVED_BY"
}
```
- **说明**：在Neo4j中创建 `焦虑症-[:RELIEVED_BY]->音乐疗法` 关系

---

## 2.4 统计信息

### 21. 获取知识图谱统计
- **URL**: `GET /api/admin/knowledge/stats`
- **Headers**: `Authorization: Bearer <token>`
- **响应**:
```json
{
    "success": true,
    "data": {
        "emotion_count": 6,
        "symptom_count": 12,
        "treatment_count": 8,
        "technique_count": 5,
        "cause_count": 3,
        "relationship_count": 35,
        "import_count": 10
    }
}
```

---

# 三、用户端RAG API (端口5001)

## 3.1 智能对话

### 22. 智能对话（核心）
- **URL**: `POST /api/rag-knowledge/chat`
- **功能**：情绪检测 + 知识图谱检索 + AI生成回答

**请求体**:
```json
{
    "question": "我最近总是很焦虑，晚上睡不着",
    "user_id": 123,
    "stream": false
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "question": "我最近总是很焦虑，晚上睡不着",
        "answer": "我理解你现在的焦虑感...根据知识图谱...",
        "emotion": "焦虑",
        "risk_level": "medium",
        "knowledge_items": [...],
        "knowledge_paths": [...]
    }
}
```

### 23. 获取情绪知识图谱
- **URL**: `GET /api/rag-knowledge/emotion/{情绪名}`
- **示例**: `GET /api/rag-knowledge/emotion/焦虑`
- **响应**：完整的情绪知识图谱（症状、治疗方法、技巧等）

### 24. 搜索知识图谱
- **URL**: `GET /api/rag-knowledge/search?keyword=焦虑`

### 25. 获取所有情绪类型
- **URL**: `GET /api/rag-knowledge/emotions`

### 26. 获取图谱统计
- **URL**: `GET /api/rag-knowledge/graph-stats`

---

# 四、知识图谱结构

## 4.1 节点类型
- **Emotion（情绪）**: 焦虑、抑郁、愤怒、恐惧、孤独、失眠
- **Symptom（症状）**: 心慌、肌肉紧张、注意力难集中、睡眠障碍等
- **Treatment（治疗方法）**: 认知行为疗法、正念冥想、运动疗法等
- **Technique（技巧）**: 4-7-8呼吸法、渐进式肌肉放松、思维记录表等
- **Cause（原因）**: 工作压力、人际关系、生活事件等

## 4.2 关系类型
- `LEADS_TO`: 情绪导致症状（如：焦虑 → 心慌）
- `CAUSED_BY`: 情绪由什么原因引起
- `RELIEVED_BY`: 情绪可通过什么方法缓解（如：焦虑 → 认知行为疗法）
- `HAS_TECHNIQUE`: 治疗方法包含什么技巧
- `HAS_SYMPTOM`: 问题有什么症状

---

# 五、前端调用示例

## 5.1 管理员导入心理学书籍

```javascript
// 1. 登录获取token
const loginRes = await fetch('http://49.235.105.137:5005/api/admin/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: 'admin123' })
});
const { token } = await loginRes.json();

// 2. 导入心理学文本
const importRes = await fetch('http://49.235.105.137:5005/api/admin/knowledge/import', {
    method: 'POST',
    headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
        title: '《焦虑症治疗指南》第一章',
        source: '《焦虑症治疗指南》',
        text: '焦虑症是一种常见的心理障碍，表现为心慌、失眠等症状...'
    })
});
const importData = await importRes.json();
console.log(importData.data.entities);  // 提取的实体
console.log(importData.data.relationships);  // 提取的关系

// 3. 查看知识图谱
const graphRes = await fetch('http://49.235.105.137:5005/api/admin/knowledge/graph?emotion=焦虑', {
    headers: { 'Authorization': `Bearer ${token}` }
});
const graphData = await graphRes.json();
// 使用 graphData.data.nodes 和 graphData.data.links 进行可视化
```

## 5.2 用户智能对话

```javascript
// 用户提问
const res = await fetch('http://49.235.105.137:5001/api/rag-knowledge/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        question: '我最近压力很大，怎么办？'
    })
});
const data = await res.json();
console.log(data.data.answer);  // AI生成的温暖回答
console.log(data.data.knowledge_items);  // 知识图谱检索结果
```

---

# 六、部署说明

## 6.1 安装Neo4j
```bash
# Linux服务器安装Neo4j
wget https://neo4j.com/artifact.php?name=neo4j-community-5.15.0-unix.tar.gz -O neo4j.tar.gz
tar -xzf neo4j.tar.gz
mv neo4j-community-5.15.0 /opt/neo4j
/opt/neo4j/bin/neo4j start
```

## 6.2 启动服务
```bash
# 管理员后台（端口5005）
python3 admin_server.py

# RAG知识图谱服务（端口5001）
python3 my_rag_knowledge_api.py
```

## 6.3 安装依赖
```bash
pip install neo4j flask flask-cors requests pymysql
```

---

# 七、错误响应

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

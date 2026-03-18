# API接口文档

## 服务器地址
```
http://49.235.105.137:5005  (管理员后台)
http://49.235.105.137:5001  (RAG知识图谱)
```

---

# 一、管理员后台API (端口5005)

### 1. 健康检查
- **URL**: `/health`
- **方法**: GET

### 2. 管理员登录
- **URL**: `POST /api/admin/login`
- **请求体**: `{"username": "admin", "password": "admin123"}`

### 3. 获取统计数据
- **URL**: `GET /api/admin/stats`
- **Headers**: `Authorization: Bearer <token>`

### 4. 商品管理
- **获取列表**: `GET /api/admin/products`
- **添加商品**: `POST /api/admin/products`
- **删除商品**: `DELETE /api/admin/products/<id>`

### 5. 风险预警
- **获取列表**: `GET /api/admin/risks`
- **处理预警**: `POST /api/admin/risks/<id>/handle`

### 6. 订单管理
- **获取列表**: `GET /api/admin/orders`
- **更新状态**: `PUT /api/admin/orders/<id>`

### 7. 用户管理
- **获取列表**: `GET /api/admin/users`

---

# 二、基于Neo4j知识图谱的RAG API (端口5001)

## 核心功能：知识图谱推理 + AI大模型 + 情绪安抚

### 1. 智能对话（核心接口）
- **URL**: `POST /api/rag-knowledge/chat`
- **功能**：
  - 检测用户情绪状态
  - 从Neo4j知识图谱检索相关知识
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
        "answer": "我理解你现在的焦虑感...根据知识图谱...",
        "emotion": "焦虑",
        "risk_level": "medium",
        "knowledge_items": [
            {"type": "Emotion", "name": "焦虑", "description": "..."},
            {"type": "Symptom", "name": "睡眠障碍", "description": "..."},
            {"type": "Treatment", "name": "认知行为疗法", "description": "..."}
        ],
        "knowledge_paths": [
            {
                "nodes": [{"name": "焦虑", "type": "Emotion"}, {"name": "睡眠障碍", "type": "Symptom"}],
                "relationships": ["LEADS_TO"]
            }
        ]
    }
}
```

### 2. 获取情绪知识图谱
- **URL**: `GET /api/rag-knowledge/emotion/{情绪名}`
- **示例**: `GET /api/rag-knowledge/emotion/焦虑`
- **响应**:
```json
{
    "success": true,
    "data": {
        "emotion": "焦虑",
        "description": "一种紧张、不安的情绪状态...",
        "symptoms": [
            {"name": "心慌", "description": "..."},
            {"name": "肌肉紧张", "description": "..."}
        ],
        "causes": [...],
        "treatments": [
            {"name": "认知行为疗法", "description": "..."},
            {"name": "正念冥想", "description": "..."}
        ],
        "techniques": [
            {"name": "4-7-8呼吸法", "description": "..."}
        ]
    }
}
```

### 3. 搜索知识图谱
- **URL**: `GET /api/rag-knowledge/search?keyword=焦虑`
- **返回**: 匹配的节点列表（情绪、症状、治疗方法等）

### 4. 获取所有情绪类型
- **URL**: `GET /api/rag-knowledge/emotions`
- **返回**: 系统中所有情绪类型的列表

### 5. 获取知识图谱统计
- **URL**: `GET /api/rag-knowledge/graph-stats`
- **返回**:
```json
{
    "success": true,
    "data": {
        "emotion_count": 6,
        "symptom_count": 4,
        "treatment_count": 4,
        "technique_count": 3,
        "relationship_count": 15
    }
}
```

### 6. 健康检查
- **URL**: `GET /health`

---

# 三、知识图谱结构

## 节点类型
- **Emotion（情绪）**: 焦虑、抑郁、愤怒、恐惧、孤独、失眠
- **Symptom（症状）**: 心慌、肌肉紧张、注意力难集中、睡眠障碍等
- **Treatment（治疗方法）**: 认知行为疗法、正念冥想、运动疗法等
- **Technique（技巧）**: 4-7-8呼吸法、渐进式肌肉放松、思维记录表等
- **Cause（原因）**: 工作压力、人际关系、生活事件等

## 关系类型
- `LEADS_TO`: 情绪导致症状（如：焦虑 → 心慌）
- `CAUSED_BY`: 情绪由什么原因引起
- `RELIEVED_BY`: 情绪可通过什么方法缓解（如：焦虑 → 认知行为疗法）
- `HAS_TECHNIQUE`: 治疗方法包含什么技巧
- `HAS_SYMPTOM`: 问题有什么症状

---

# 四、RAG系统特点

## 1. 情绪检测能力
自动识别用户情绪：焦虑、抑郁、愤怒、恐惧、孤独、失眠、危机

## 2. 知识图谱推理
- 根据情绪类型检索相关知识
- 展示情绪-症状-治疗方法的关联路径
- 支持复杂关系查询

## 3. 智能安抚
- 先表达理解和共情
- 基于知识图谱提供专业解释
- 给出具体可行的方法
- 温暖的鼓励

## 4. 危机干预
当检测到严重风险词时，系统会：
- 立即提供危机干预信息
- 显示紧急求助热线
- 强烈建议寻求专业帮助

---

# 五、前端调用示例

```javascript
// 智能对话
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
console.log(data.data.knowledge_paths);  // 知识路径

// 获取焦虑的完整知识图谱
const emotionRes = await fetch('http://49.235.105.137:5001/api/rag-knowledge/emotion/焦虑');
const emotionData = await emotionRes.json();
console.log(emotionData.data.treatments);  // 治疗方法
console.log(emotionData.data.techniques);  // 相关技巧

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

# 六、错误响应

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

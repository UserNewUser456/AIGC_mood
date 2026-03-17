# API接口文档

## 服务器地址
```
http://49.235.105.137:5005
```

---

## 一、用户认证接口

### 1. 用户注册
- **URL**: `/api/b-auth/register`
- **方法**: POST
- **请求体**:
```json
{
    "username": "用户名",
    "password": "密码",
    "email": "邮箱(可选)"
}
```
- **响应**:
```json
{
    "success": true,
    "message": "注册成功",
    "user_id": 1
}
```

### 2. 用户登录
- **URL**: `/api/b-auth/login`
- **方法**: POST
- **请求体**:
```json
{
    "username": "用户名",
    "password": "密码"
}
```
- **响应**:
```json
{
    "success": true,
    "message": "登录成功",
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "id": 1,
        "username": "用户名"
    }
}
```
- **说明**: 登录成功后返回token，后续请求需要在Header中携带token:
  ```
  Authorization: Bearer <token>
  ```

### 3. 获取用户信息
- **URL**: `/api/b-auth/user`
- **方法**: GET
- **Headers**: `Authorization: Bearer <token>`
- **响应**:
```json
{
    "success": true,
    "user": {
        "id": 1,
        "username": "用户名",
        "email": "邮箱"
    }
}
```

---

## 二、情绪记录接口

### 1. 记录情绪
- **URL**: `/api/b-emotion/emotion`
- **方法**: POST
- **Headers**: `Authorization: Bearer <token>`
- **请求体**:
```json
{
    "emotion": "开心",
    "score": 8.5,
    "text": "今天很高兴..."
}
```
- **参数说明**:
  - emotion: 情绪类型（开心/平静/焦虑/悲伤/愤怒/兴奋等）
  - score: 分数（0-10）
  - text: 备注（可选）

- **响应**:
```json
{
    "success": true,
    "message": "情绪记录成功",
    "data": {
        "id": 1,
        "emotion": "开心",
        "score": 8.5
    }
}
```

### 2. 获取情绪历史
- **URL**: `/api/b-emotion/history`
- **方法**: GET
- **Headers**: `Authorization: Bearer <token>`
- **参数**:
  - days: 获取最近几天的数据（默认7）
- **响应**:
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "emotion": "开心",
            "score": 8.5,
            "text": "今天很高兴",
            "created_at": "2024-01-07T10:00:00"
        }
    ]
}
```

### 3. 获取情绪统计
- **URL**: `/api/b-emotion/stats`
- **方法**: GET
- **Headers**: `Authorization: Bearer <token>`
- **参数**:
  - days: 获取最近几天的数据（默认7）
- **响应**:
```json
{
    "success": true,
    "data": {
        "totalRecords": 10,
        "avgScore": 7.5,
        "dominantEmotion": "开心",
        "emotionDistribution": {
            "开心": 5,
            "平静": 3,
            "焦虑": 2
        }
    }
}
```

---

## 三、AI对话接口

### 1. 获取可用医生列表
- **URL**: `/api/b-knowledge/doctors`
- **方法**: GET
- **响应**:
```json
{
    "success": true,
    "doctors": [
        {
            "doctor_type": "gentle",
            "name": "温柔医生",
            "description": "以温暖、关怀的方式提供支持"
        },
        {
            "doctor_type": "rational",
            "name": "理性医生",
            "description": "以逻辑分析帮助用户理解情绪"
        },
        {
            "doctor_type": "humorous",
            "name": "幽默医生",
            "description": "用幽默的方式缓解用户压力"
        }
    ]
}
```

### 2. 创建对话
- **URL**: `/api/b-knowledge/conversations`
- **方法**: POST
- **Headers**: `Authorization: Bearer <token>`
- **请求体**:
```json
{
    "doctor_type": "gentle"
}
```
- **响应**:
```json
{
    "success": true,
    "message": "对话创建成功",
    "conversation": {
        "id": 1,
        "title": "与温柔医生的对话",
        "doctor_type": "gentle"
    },
    "welcome_message": {
        "id": 1,
        "role": "system",
        "content": "我是温柔医生，今天有什么想和我分享的吗？"
    }
}
```

### 3. 发送消息（流式回复）
- **URL**: `/api/b-knowledge/conversations/<conversation_id>/messages/stream`
- **方法**: POST
- **Headers**: `Authorization: Bearer <token>`
- **请求体**:
```json
{
    "content": "我今天心情不好"
}
```
- **响应**: SSE流式返回
- **返回格式**:
```
data: {"content": "我"}

data: {"content": "理解"}

data: {"content": "您"}

data: {"content": "的"}

data: {"content": "感受"}
...
data: {"done": true, "emotion": {...}}
```

### 4. 获取对话历史
- **URL**: `/api/b-knowledge/conversations/<conversation_id>`
- **方法**: GET
- **Headers**: `Authorization: Bearer <token>`
- **响应**:
```json
{
    "success": true,
    "conversation": {...},
    "messages": [
        {"role": "system", "content": "欢迎消息"},
        {"role": "user", "content": "用户消息"},
        {"role": "assistant", "content": "AI回复"}
    ]
}
```

---

## 四、管理员后台接口

### 1. 管理员登录
- **URL**: `/api/admin/login`
- **方法**: POST
- **请求体**:
```json
{
    "username": "admin",
    "password": "admin123"
}
```

### 2. 获取统计数据
- **URL**: `/api/admin/stats`
- **方法**: GET
- **Headers**: `Authorization: Bearer <admin_token>`

### 3. 商品管理
- **URL**: `/api/admin/products`
- **方法**: GET/POST
- **Headers**: `Authorization: Bearer <admin_token>`

---

## 五、通用接口

### 健康检查
- **URL**: `/health`
- **方法**: GET
- **响应**: `{"status": "ok"}`

---

## 六、错误响应格式

```json
{
    "success": false,
    "message": "错误信息"
}
```

常见状态码：
- 200: 成功
- 400: 请求参数错误
- 401: 未授权（token无效或过期）
- 404: 资源不存在
- 500: 服务器内部错误

---

## 七、前端调用示例

### JavaScript/Fetch
```javascript
// 登录获取token
const loginRes = await fetch('http://49.235.105.137:5005/api/b-auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'test', password: 'test123' })
});
const { token } = await loginRes.json();

// 记录情绪
await fetch('http://49.235.105.137:5005/api/b-emotion/emotion', {
    method: 'POST',
    headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ emotion: '开心', score: 8.5 })
});
```

### Axios
```javascript
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://49.235.105.137:5005'
});

// 登录
const { data } = await api.post('/api/b-auth/login', {
    username: 'test',
    password: 'test123'
});

const token = data.token;

// 后续请求自动携带token
api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
```

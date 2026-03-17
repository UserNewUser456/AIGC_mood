# 后端API接口文档

## 后端公网地址
```
https://cayden-septal-halley.ngrok-free.dev
```

---

## 接口列表

### 1. 健康检查
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 检查服务是否在线 |

### 2. 用户认证 /api/auth
| 方法 | 路径 | 说明 | 请求参数 |
|------|------|------|----------|
| POST | `/api/auth/register` | 用户注册 | `{"username": "xxx", "password": "123456", "email": "xxx@example.com"}` |
| POST | `/api/auth/login` | 用户登录 | `{"username": "xxx", "password": "123456"}` |
| POST | `/api/auth/logout` | 退出登录 | 需要Header带token |

### 3. 情绪识别 /api/emotion
| 方法 | 路径 | 说明 | 请求参数 |
|------|------|------|----------|
| POST | `/api/emotion/analyze` | 分析情绪 | `{"text": "今天很开心"}` |
| POST | `/api/emotion/record` | 记录情绪 | `{"user_id": 1, "emotion": "happy", "score": 8, "text": "xxx"}` |
| GET | `/api/emotion/history` | 获取历史 | `user_id=1&days=7` |
| GET | `/api/emotion/stats` | 获取统计 | `user_id=1` |

### 4. 知识库 /api/knowledge
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledge/` | 获取知识库列表 |
| GET | `/api/knowledge/search` | 搜索知识 |
| GET | `/api/knowledge/categories` | 获取分类 |

### 5. 商城 /api/store
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/store/products` | 商品列表 |
| GET | `/api/store/categories` | 分类列表 |
| GET | `/api/store/products/<id>` | 商品详情 |

### 6. 推荐 /api/recommend
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/recommend/products` | 商品推荐 |
| GET | `/api/recommend/knowledge` | 知识推荐 |

### 7. 报告 /api/report
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/report/weekly` | 周报 |
| GET | `/api/report/monthly` | 月报 |

---

## 完整请求示例

### 登录示例
```javascript
fetch("https://cayden-septal-halley.ngrok-free.dev/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        username: "testuser",
        password: "123456"
    })
})
```

### 情绪分析示例
```javascript
fetch("https://cayden-septal-halley.ngrok-free.dev/api/emotion/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        text: "今天工作完成了，感觉很开心！"
    })
})
```

---

## 注意事项

1. 后端服务需要一直运行
2. ngrok需要一直运行
3. 如果重启ngrok，公网地址可能会变化

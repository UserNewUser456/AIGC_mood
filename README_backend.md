# 后端代码说明

## 文件清单

| 文件 | 说明 |
|------|------|
| `admin_server.py` | 管理员后台API服务 |
| `my_rag_knowledge_api.py` | RAG知识库API服务 |
| `backend_requirements.txt` | Python依赖 |

## 部署步骤

### 1. 安装依赖
```bash
pip install -r backend_requirements.txt
```

### 2. 配置数据库
修改文件中的数据库配置：
```python
DB_CONFIG = {
    'host': 'localhost',      # 数据库地址
    'user': 'root',           # 用户名
    'password': '12345678',   # 密码
    'database': 'emotion_db', # 数据库名
    'charset': 'utf8mb4'
}
```

### 3. 初始化数据库
确保数据库 `emotion_db` 已创建，所有表结构已创建（参考数据库结构.md）。

### 4. 启动服务

**管理员后台服务（端口5000）：**
```bash
python admin_server.py
```

**RAG知识库服务（端口5001）：**
```bash
python my_rag_knowledge_api.py
```

## API接口

### 管理员后台 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/admin/login` | POST | 登录 |
| `/api/admin/logout` | POST | 登出 |
| `/api/admin/check` | GET | 检查登录状态 |
| `/api/admin/stats` | GET | 统计数据 |
| `/api/admin/products` | GET/POST | 商品列表/发布 |
| `/api/admin/products/<id>` | DELETE | 删除商品 |
| `/api/admin/risks` | GET | 风险预警列表 |
| `/api/admin/risks/<id>/handle` | POST | 处理预警 |
| `/api/admin/orders` | GET | 订单列表 |
| `/api/admin/users` | GET | 用户列表 |

### RAG知识库 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/rag-knowledge/rag` | POST | RAG问答 |
| `/api/rag-knowledge` | GET | 搜索知识 |
| `/api/rag-knowledge` | POST | 添加知识 |
| `/api/rag-knowledge/categories` | GET | 获取分类 |

## 注意事项

1. 生产环境请修改 `SECRET_KEY`
2. Token存储建议使用Redis
3. 建议使用Nginx反向代理
4. 建议配置HTTPS

# 情绪愈疗平台 - Flask后端系统

基于Flask + MySQL + SQLAlchemy的情绪愈疗平台后端系统，提供用户管理、AI对话、情绪记录和风险预警功能。

## 🚀 功能特性

### 1. 用户管理系统
- **注册/登录**: 支持用户名密码注册登录
- **匿名模式**: 无需注册即可体验
- **JWT认证**: 安全的令牌认证机制
- **个人档案**: 用户信息管理

### 2. AI对话系统
- **多轮对话**: 完整的对话上下文管理
- **医生形象配置**: 支持温柔型、理性型、幽默型医生
- **情绪检测**: 实时分析用户情绪状态
- **智能回复**: 基于情绪状态的个性化回复

### 3. 情绪记录系统
- **情绪记录**: 记录情绪类型和分数
- **历史查询**: 按时间范围查询情绪记录
- **统计分析**: 情绪趋势和分布分析
- **周报生成**: 自动生成情绪周报

### 4. 风险预警系统
- **风险监测**: 实时监测高风险情绪
- **预警通知**: 高风险时自动预警
- **紧急联系**: 提供心理援助热线
- **处理跟踪**: 预警处理状态管理

## 📋 技术栈

- **后端框架**: Flask 2.3.3
- **数据库**: MySQL + SQLAlchemy ORM
- **认证**: JWT (JSON Web Tokens)
- **安全**: Flask-Bcrypt密码加密
- **跨域**: Flask-CORS
- **部署**: Railway (云平台)

## 🛠️ 快速开始

### 环境要求

- Python 3.8+
- MySQL 5.7+
- pip (Python包管理器)

### 1. 克隆项目

```bash
git clone <项目地址>
cd AIGC_mood
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 数据库配置

创建MySQL数据库：

```sql
CREATE DATABASE emotion_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 环境配置

复制并编辑 `.env` 文件：

```bash
cp .env.example .env
# 编辑 .env 文件，设置数据库连接信息
```

### 5. 初始化数据库

```bash
python init_db.py
```

### 6. 启动服务

```bash
python app.py
```

服务将在 http://localhost:5000 启动

## 📡 API接口文档

### 认证相关

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/anonymous` | POST | 创建匿名用户 |
| `/api/auth/profile` | GET | 获取用户档案 |
| `/api/auth/profile` | PUT | 更新用户档案 |

### 对话相关

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/conversations` | POST | 创建对话 |
| `/api/conversations` | GET | 获取对话列表 |
| `/api/conversations/{id}` | GET | 获取对话详情 |
| `/api/conversations/{id}/messages` | POST | 发送消息 |
| `/api/conversations/{id}/messages` | GET | 获取消息列表 |

### 情绪相关

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/emotion` | POST | 记录情绪 |
| `/api/emotion/history` | GET | 获取情绪历史 |
| `/api/emotion/stats` | GET | 获取情绪统计 |
| `/api/emotion/weekly-report` | GET | 获取周报 |

### 风险预警相关

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/risk/alerts` | GET | 获取预警列表 |
| `/api/risk/alerts/{id}` | GET | 获取预警详情 |
| `/api/risk/alerts/{id}` | PUT | 处理预警 |
| `/api/risk/dashboard` | GET | 风险仪表盘 |
| `/api/risk/emergency-contacts` | GET | 紧急联系方式 |

## 🚀 部署到Railway

### 1. 准备部署

确保以下文件已配置：
- `railway.toml` - Railway配置文件
- `requirements.txt` - Python依赖
- `.env` - 环境变量

### 2. Railway部署步骤

1. 在Railway官网创建新项目
2. 连接GitHub仓库
3. 设置环境变量：
   - `SECRET_KEY`
   - `JWT_SECRET_KEY` 
   - `DATABASE_URL` (Railway会自动提供)

### 3. 自动部署

Railway会自动检测项目并部署，部署完成后会提供访问URL。

## 🔧 开发指南

### 项目结构

```
AIGC_mood/
├── app.py                 # 主应用入口
├── models.py              # 数据模型定义
├── extensions.py          # 扩展配置
├── routes/                # 路由模块
│   ├── auth.py           # 认证路由
│   ├── conversation.py   # 对话路由
│   ├── emotion.py        # 情绪路由
│   └── risk.py           # 风险路由
├── init_db.py            # 数据库初始化
├── requirements.txt       # 依赖列表
├── .env                  # 环境变量
├── railway.toml          # Railway配置
└── README.md             # 项目文档
```

### 数据库模型

核心数据表：
- `users` - 用户表
- `emotion_records` - 情绪记录表
- `conversations` - 对话会话表
- `messages` - 消息记录表
- `risk_alerts` - 风险预警表
- `knowledge_base` - 心理知识库
- `resources` - 资源推荐表

### 开发注意事项

1. **JWT认证**: 所有需要认证的接口都需要在请求头中添加 `Authorization: Bearer <token>`
2. **错误处理**: 统一使用JSON格式返回错误信息
3. **数据验证**: 所有输入数据都需要进行验证
4. **安全考虑**: 密码使用bcrypt加密，敏感信息不记录日志

## 🔒 安全考虑

- 密码使用bcrypt加密存储
- JWT令牌有过期机制
- SQL注入防护（使用SQLAlchemy ORM）
- CORS跨域配置
- 输入数据验证和清理

## 📞 支持与联系

如有问题或建议，请联系开发团队。

## 📄 许可证

本项目仅供学习和研究使用。
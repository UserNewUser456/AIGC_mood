# 情绪分析仪表盘 - 详细开发指南

## 项目概述

- **项目名称**: Emotion Dashboard (情绪分析仪表盘)
- **技术栈**: Python Flask + ECharts + MySQL
- **项目类型**: 独立全栈Web应用

---

## 一、项目结构设计

```
emotion-dashboard/
├── app.py                  # Flask主应用
├── config.py               # 配置文件
├── requirements.txt        # 依赖包
├── .env                    # 环境变量配置
├── static/
│   ├── css/
│   │   └── style.css       # 仪表盘样式
│   ├── js/
│   │   ├── app.js          # 前端主逻辑
│   │   └── chart-config.js # ECharts配置
│   └── images/             # 静态图片
├── templates/
│   └── index.html          # 仪表盘主页
├── api/
│   ├── __init__.py
│   ├── emotion_routes.py   # 情绪数据API
│   └── report_routes.py    # 周报API
├── models/
│   ├── __init__.py
│   └── database.py         # 数据库模型
├── utils/
│   ├── __init__.py
│   └── analyzer.py         # 数据分析逻辑
└── README.md
```

---

## 二、数据库设计 (MySQL)

### 表结构: emotion_records

```sql
CREATE DATABASE IF NOT EXISTS emotion_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE emotion_db;

CREATE TABLE IF NOT EXISTS emotion_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    emotion VARCHAR(32) NOT NULL,
    score FLOAT NOT NULL,
    text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 三、后端API开发

### 3.1 情绪数据接收接口

**POST /api/emotion**
- 功能: 接收情绪数据上报
- 请求体:
```json
{
    "user_id": "user_123",
    "emotion": "happy",
    "score": 8.5,
    "text": "今天心情很好"
}
```
- 响应:
```json
{
    "success": true,
    "message": "情绪记录已保存",
    "data": {
        "id": 1,
        "emotion": "happy",
        "timestamp": "2026-03-09T10:30:00"
    }
}
```

### 3.2 历史情绪查询接口

**GET /api/emotion/history**
- 参数:
  - `user_id`: 用户ID (必填)
  - `days`: 查询天数 (默认7，可选7/30/90)
- 响应:
```json
{
    "success": true,
    "data": {
        "records": [
            {"date": "2026-03-09", "emotion": "happy", "score": 8.5},
            {"date": "2026-03-08", "emotion": "calm", "score": 7.0}
        ],
        "summary": {
            "avg_score": 7.5,
            "total_records": 10,
            "dominant_emotion": "happy"
        }
    }
}
```

### 3.3 周报生成接口

**GET /api/report/weekly**
- 参数: `user_id` (必填)
- 响应:
```json
{
    "success": true,
    "data": {
        "week_range": "2026-03-03 ~ 2026-03-09",
        "total_entries": 15,
        "avg_score": 7.2,
        "emotion_distribution": {
            "happy": 5,
            "calm": 4,
            "anxious": 3,
            "sad": 2,
            "angry": 1
        },
        "trend": "up",  // up/down/stable
        "insights": [
            "本周你的情绪整体偏积极",
            "周末情绪明显优于工作日",
            "建议增加户外活动提升心情"
        ]
    }
}
```

---

## 四、数据分析逻辑

### 4.1 情绪趋势计算

```python
def calculate_trend(records):
    """计算情绪趋势: up/down/stable"""
    if len(records) < 2:
        return "stable"
    
    first_half = sum(r['score'] for r in records[:len(records)//2]) / (len(records)//2)
    second_half = sum(r['score'] for r in records[len(records)//2:]) / (len(records)//2)
    
    diff = second_half - first_half
    if diff > 0.5:
        return "up"
    elif diff < -0.5:
        return "down"
    return "stable"
```

### 4.2 情绪波动性计算

```python
def calculate_volatility(records):
    """计算情绪波动性 (标准差)"""
    if len(records) < 2:
        return 0
    
    scores = [r['score'] for r in records]
    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    return round(math.sqrt(variance), 2)
```

### 4.3 主要情绪分布

```python
def get_emotion_distribution(records):
    """获取情绪占比分布"""
    emotion_count = {}
    for r in records:
        emotion = r['emotion']
        emotion_count[emotion] = emotion_count.get(emotion, 0) + 1
    
    total = len(records)
    return {e: round(c/total*100, 1) for e, c in emotion_count.items()}
```

---

## 五、前端仪表盘开发

### 5.1 页面布局

```
+----------------------------------------------------------+
|  情绪分析仪表盘                              [用户切换]   |
+----------------------------------------------------------+
|                                                          |
|  +------------------+  +------------------+              |
|  |   本周概览卡片    |  |   情绪趋势卡片    |              |
|  |   平均分: 7.5    |  |   📈 上升趋势     |              |
|  +------------------+  +------------------+              |
|                                                          |
|  +----------------------------------------------------+  |
|  |              情绪变化折线图 (ECharts)               |  |
|  |                                                    |  |
|  +----------------------------------------------------+  |
|                                                          |
|  +--------------------+  +---------------------------+  |
|  |   情绪分布饼图     |  |     情绪日历热力图        |  |
|  |                    |  |   |月|火|水|木|金|土|日|  |  |
|  +--------------------+  +---------------------------+  |
|                                                          |
+----------------------------------------------------------+
```

### 5.2 ECharts 图表配置

#### 折线图 (情绪变化趋势)
```javascript
option = {
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', min: 0, max: 10 },
    series: [{
        type: 'line',
        smooth: true,
        data: scores,
        areaStyle: { opacity: 0.3 }
    }]
};
```

#### 饼图 (情绪分布)
```javascript
option = {
    series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        data: emotionData
    }]
};
```

#### 热力图 (情绪日历)
```javascript
option = {
    xAxis: { type: 'category', data: ['周一','周二',...] },
    yAxis: { type: 'category', data: weeks },
    visualMap: { min: 0, max: 10, inRange: { color: ['#ff6b6b','#ffd93d','#6bcb77'] }},
    series: [{ type: 'heatmap', data: heatmapData }]
};
```

---

## 六、用户标识方案

### 6.1 匿名用户ID生成

```javascript
function getOrCreateUserId() {
    let userId = localStorage.getItem('emotion_user_id');
    if (!userId) {
        userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('emotion_user_id', userId);
    }
    return userId;
}
```

### 6.2 用户名设置 (可选)

```javascript
function setUsername(name) {
    localStorage.setItem('emotion_username', name);
    document.getElementById('username-display').textContent = name;
}
```

---

## 七、数据接收方式

### 7.1 iframe消息监听

```javascript
// 在子应用中监听父页面消息
window.addEventListener('message', async (event) => {
    if (event.data.type === 'emotion-data') {
        try {
            await fetch('https://emotion-dashboard.onrender.com/api/emotion', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(event.data.data)
            });
            console.log('情绪数据已同步');
        } catch (err) {
            console.error('数据同步失败:', err);
        }
    }
});
```

### 7.2 跨域API调用支持

在Flask中配置CORS:
```python
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

---

## 八、部署指南

### 8.1 Render部署步骤

1. **创建GitHub仓库**
   - 初始化Git仓库
   - 提交所有代码
   - 推送到GitHub

2. **在Render创建Web Service**
   - 登录 render.com
   - 创建新的Web Service
   - 连接到GitHub仓库
   - 配置:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn app:app`

3. **环境变量配置**
   - `FLASK_ENV`: production
   - `SECRET_KEY`: 随机密钥

### 8.2 目录结构要求

确保项目根目录有:
- `app.py` - 主应用文件
- `requirements.txt` - 依赖列表
- `runtime.txt` - Python版本 (如 `python-3.11.0`)

---

## 九、开发里程碑

### 第一阶段: 后端基础 (Day 1-2)
- [ ] Flask项目初始化
- [ ] 数据库模型创建
- [ ] POST /api/emotion 接口
- [ ] GET /api/emotion/history 接口
- [ ] GET /api/report/weekly 接口

### 第二阶段: 数据分析 (Day 3)
- [ ] 情绪趋势计算
- [ ] 情绪波动性分析
- [ ] 情绪分布统计

### 第三阶段: 前端开发 (Day 4-5)
- [ ] 仪表盘HTML页面
- [ ] 折线图实现
- [ ] 饼图实现
- [ ] 热力图实现

### 第四阶段: 用户功能 (Day 6)
- [ ] 用户ID生成与存储
- [ ] 用户切换功能
- [ ] 数据隔离验证

### 第五阶段: 部署上线 (Day 7)
- [ ] 部署到Render
- [ ] API文档编写
- [ ] 嵌入说明文档

---

## 十、关键代码示例

### .env 环境配置

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-in-production

# MySQL配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=emotion_db
DB_USER=root
DB_PASSWORD=your-password
```

### app.py 主应用

```python
import os
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from models.database import init_db, save_emotion, get_emotion_history
from utils.analyzer import analyze_emotions, generate_weekly_report

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/emotion', methods=['POST'])
def add_emotion():
    data = request.get_json()
    result = save_emotion(
        user_id=data.get('user_id'),
        emotion=data.get('emotion'),
        score=data.get('score'),
        text=data.get('text', '')
    )
    return jsonify({'success': True, 'data': result})

@app.route('/api/emotion/history', methods=['GET'])
def get_history():
    user_id = request.args.get('user_id')
    days = int(request.args.get('days', 7))
    records = get_emotion_history(user_id, days)
    analysis = analyze_emotions(records)
    return jsonify({'success': True, 'data': {'records': records, 'summary': analysis}})

@app.route('/api/report/weekly', methods=['GET'])
def weekly_report():
    user_id = request.args.get('user_id')
    report = generate_weekly_report(user_id)
    return jsonify({'success': True, 'data': report})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
```

---

## 十一、数据库模型代码

### models/database.py

```python
import pymysql
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'emotion_db'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    """初始化数据库表"""
    conn = pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        charset='utf8mb4'
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS emotion_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute("USE emotion_db")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emotion_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(64) NOT NULL,
                    emotion VARCHAR(32) NOT NULL,
                    score FLOAT NOT NULL,
                    text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        conn.commit()
    finally:
        conn.close()

def save_emotion(user_id, emotion, score, text=''):
    """保存情绪记录"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO emotion_records (user_id, emotion, score, text) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (user_id, emotion, score, text))
            conn.commit()
            return {'id': cursor.lastrowid, 'emotion': emotion}
    finally:
        conn.close()

def get_emotion_history(user_id, days=7):
    """获取历史情绪记录"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT id, user_id, emotion, score, text, created_at 
                FROM emotion_records 
                WHERE user_id = %s AND created_at >= %s
                ORDER BY created_at DESC
            """
            start_date = datetime.now() - timedelta(days=days)
            cursor.execute(sql, (user_id, start_date))
            results = cursor.fetchall()
            
            # 转换datetime为字符串
            for r in results:
                if r['created_at']:
                    r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    r['date'] = r['created_at'].split()[0]
            return results
    finally:
        conn.close()

def get_all_emotions(user_id, days=7):
    """获取所有情绪记录用于分析"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT emotion, score, created_at 
                FROM emotion_records 
                WHERE user_id = %s AND created_at >= %s
                ORDER BY created_at ASC
            """
            start_date = datetime.now() - timedelta(days=days)
            cursor.execute(sql, (user_id, start_date))
            results = cursor.fetchall()
            
            for r in results:
                if r['created_at']:
                    r['date'] = r['created_at'].strftime('%Y-%m-%d')
            return results
    finally:
        conn.close()
```

## 十二、依赖包

### requirements.txt

```
Flask==3.0.0
Flask-CORS==4.0.0
PyMySQL==1.1.0
python-dotenv==1.0.0
gunicorn==21.2.0
```

---

## 十三、部署环境变量 (Render)

在Render dashboard中配置以下环境变量：

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| FLASK_ENV | 运行环境 | production |
| SECRET_KEY | 安全密钥 | (随机生成) |
| DB_HOST | MySQL主机 | 应该是Render提供的内网地址 |
| DB_PORT | MySQL端口 | 3306 |
| DB_NAME | 数据库名 | emotion_db |
| DB_USER | 数据库用户 | (Render提供) |
| DB_PASSWORD | 数据库密码 | (Render提供) |

**注意**: Render部署MySQL需要使用Render的MySQL addon，或者使用外部MySQL服务(如ClearDB、PlanetScale等)。

---

## 十四、下一步行动

1. **立即开始**: 创建项目目录结构
2. **安装MySQL**: 确保本地有MySQL环境
3. **创建 requirements.txt**
4. **编写后端API**
5. **开发前端页面**
6. **本地测试**
7. **部署上线**

---

是否需要我开始为你创建这个项目的实际代码？

"""
情绪愈疗平台 - Flask后端主应用
技术栈：Python Flask + MySQL + SQLAlchemy + JWT

功能模块：
1. 用户管理：注册/登录/匿名模式/JWT认证
2. 对话系统：LLM共情对话/多轮对话上下文/医生形象配置
3. 风险预警：风险监测模型/高风险警报/人工跟进通知
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from extensions import db
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建Flask应用
app = Flask(__name__)

# 基础配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'emotion-healing-secret-key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # 开发环境不设置过期时间

# 数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:root1234@localhost:3306/emotion_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 启用CORS
CORS(app)

# JWT管理
jwt = JWTManager(app)

# 数据库初始化
from extensions import db
db.init_app(app)

# 注册蓝图
from routes.auth import auth_bp
from routes.conversation import conversation_bp
from routes.emotion import emotion_bp
from routes.risk import risk_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(conversation_bp, url_prefix='/api/conversations')
app.register_blueprint(emotion_bp, url_prefix='/api/emotion')
app.register_blueprint(risk_bp, url_prefix='/api/risk')

# 健康检查端点
@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "emotion-healing-api",
        "version": "1.0.0"
    })

@app.route('/')
def index():
    return jsonify({
        "message": "情绪愈疗平台API服务",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth",
            "conversations": "/api/conversations",
            "emotion": "/api/emotion",
            "risk": "/api/risk"
        }
    })

if __name__ == '__main__':
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    print("=" * 50)
    print("情绪愈疗平台API服务启动中...")
    print("访问地址: http://localhost:5000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
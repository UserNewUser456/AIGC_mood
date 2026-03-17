"""
后端工程师B - 模块集成示例
情绪愈疗平台 - 后端服务

使用说明：
1. 将 my_emotion_api.py, my_store_api.py, my_knowledge_api.py, my_security_api.py 放到项目目录
2. 确保 models.py, extensions.py 在同一目录
3. 运行此文件启动服务

API路由：
- /api/b-emotion/*    情绪识别 + 健康报告
- /api/b-store/*     商城 + 推荐
- /api/b-knowledge/*  知识库
- /api/b-auth/*      用户认证
- /api/b-security/*   数据安全
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# 导入数据库
from extensions import db

# 导入各模块蓝图
from my_emotion_api import emotion_bp
from my_store_api import store_bp
from my_knowledge_api import knowledge_bp
from my_security_api import security_bp


def create_app():
    """应用工厂"""
    app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'emotion-healing-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # 数据库配置
    db_uri = os.getenv('DATABASE_URL', 'mysql+pymysql://root:root@localhost:3306/emotion_db')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 初始化JWT
    jwt = JWTManager(app)
    
    # 初始化数据库
    db.init_app(app)
    
    # 注册蓝图
    app.register_blueprint(emotion_bp, url_prefix='/api/b-emotion')
    app.register_blueprint(store_bp, url_prefix='/api/b-store')
    app.register_blueprint(knowledge_bp, url_prefix='/api/b-knowledge')
    app.register_blueprint(security_bp, url_prefix='/api/b-auth')
    
    # 健康检查
    @app.route('/')
    def index():
        return jsonify({
            "service": "情绪愈疗平台 - 后端B",
            "version": "1.0.0",
            "modules": {
                "emotion": "/api/b-emotion/*",
                "store": "/api/b-store/*",
                "knowledge": "/api/b-knowledge/*",
                "auth": "/api/b-auth/*"
            }
        })
    
    @app.route('/api/health')
    def health():
        return jsonify({"status": "healthy"})
    
    return app


# 创建数据库表
def init_db(app):
    with app.app_context():
        db.create_all()
        print("数据库表创建成功！")


if __name__ == '__main__':
    app = create_app()
    
    # 初始化数据库（首次运行）
    # init_db(app)
    
    print("=" * 50)
    print("情绪愈疗平台 - 后端服务启动")
    print("API模块:")
    print("  - 情绪识别: /api/b-emotion/*")
    print("  - 商城推荐: /api/b-store/*")
    print("  - 知识库:   /api/b-knowledge/*")
    print("  - 用户认证: /api/b-auth/*")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

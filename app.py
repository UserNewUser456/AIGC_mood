"""
情绪愈疗平台 - Flask后端主应用
技术栈：Python Flask + MySQL + SQLAlchemy + JWT
功能模块：
1. 用户管理：注册/登录/匿名模式/JWT认证
2. 对话系统：LLM共情对话/多轮对话上下文/医生形象配置
3. 风险预警：风险监测模型/高风险警报/人工跟进通知
"""

import os
import json
from flask import Flask, jsonify, Response, send_from_directory, request
from flask_cors import CORS
from extensions import db
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from datetime import timedelta

# 加载环境变量
load_dotenv()

# 配置文件
config = {
    'development': 'config.DevelopmentConfig',
    'production': 'config.ProductionConfig',
    'testing': 'config.TestingConfig'
}

def create_app(config_name='development'):
    """应用工厂模式"""
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config.get(config_name, 'config.DevelopmentConfig'))

    # 基础配置
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'emotion-healing-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)  # 设置token过期时间
    app.config['JWT_TOKEN_LOCATION'] = ['headers']  # token位置
    app.config['JWT_HEADER_NAME'] = 'Authorization'  # header名称
    app.config['JWT_HEADER_TYPE'] = 'Bearer'  # token类型

    # 数据库配置
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:root1234@localhost:3306/emotion_db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 启用CORS - 配置为允许前端域名访问
    # 在 create_app 函数中，修改 CORS 配置部分

    # 启用CORS - 配置为允许前端域名访问
    CORS(app,
         supports_credentials=True,
         origins=[
             "http://452e9a87.r6.cpolar.top",  # 前端地址
             "https://452e9a87.r6.cpolar.top",
             "http://localhost:5000",
             "https://cometary-mousily-han.ngrok-free.dev",
             "http://localhost:3000",  # 常见前端开发端口
             "http://localhost:63342",  # WebStorm/Idea 默认端口
             "http://127.0.0.1:5000",
             "http://127.0.0.1:3000",
             "http://127.0.0.1:63342",  # WebStorm/Idea 默认端口
             "http://localhost:63342",  # 前端开发端口
         ],
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         expose_headers=["Content-Type", "Authorization"])

    # JWT管理
    jwt = JWTManager(app)

    # 数据库初始化
    db.init_app(app)

    # 初始化Bcrypt
    from models import bcrypt
    bcrypt.init_app(app)

    # 注册蓝图（移到函数内部避免循环导入）
    from routes.auth import auth_bp
    from routes.conversation import conversation_bp
    from routes.emotion import emotion_bp
    from routes.risk import risk_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(conversation_bp, url_prefix='/api/conversations')
    app.register_blueprint(emotion_bp, url_prefix='/api/emotion')
    app.register_blueprint(risk_bp, url_prefix='/api/risk')

    from routes.flask_routes import compatibility_bp

    # ...其他蓝图注册...
    app.register_blueprint(compatibility_bp)  # 注册兼容性路由（无url_prefix）

    # 页面目录路径
    PAGE_DIR = os.path.join(os.path.dirname(__file__), 'page')
    STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')

    # ==================== 错误处理中间件 ====================

    # 处理OPTIONS请求（CORS预检）
    @app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
    @app.route('/<path:path>', methods=['OPTIONS'])
    def handle_options(path):
        """处理所有OPTIONS请求"""
        response = app.response_class()
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Max-Age', '3600')
        return response, 200

    # Token黑名单验证
    from routes.auth import token_blacklist
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        return jti in token_blacklist

    # 404错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "message": "请求的资源不存在",
            "error": "404 Not Found"
        }), 404

    # 500错误处理
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "服务器内部错误",
            "error": "500 Internal Server Error"
        }), 500

    # 400错误处理
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "message": "请求参数错误",
            "error": "400 Bad Request"
        }), 400

    # 401错误处理
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            "success": False,
            "message": "未授权，请登录",
            "error": "401 Unauthorized"
        }), 401

    # 403错误处理
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            "success": False,
            "message": "禁止访问",
            "error": "403 Forbidden"
        }), 403

    # JWT错误处理
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "success": False,
            "message": "登录已过期，请重新登录"
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            "success": False,
            "message": "无效的token"
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            "success": False,
            "message": "缺少访问令牌"
        }), 401

    # ==================== 请求处理 ====================

    # 处理ngrok的headers
    @app.after_request
    def handle_ngrok_headers(response):
        response.headers.pop('ngrok-skip-browser-warning', None)
        return response

    # 中文响应处理和CORS头
    # 中文响应处理和CORS头

    # ==================== 路由 ====================

    # 健康检查端点
    @app.route('/health')
    def health_check():
        data = {
            "status": "healthy",
            "service": "emotion-healing-api",
            "version": "1.0.0"
        }
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        return Response(json_str, content_type='application/json; charset=utf-8')

    # API状态检查
    @app.route('/api/status')
    def api_status():
        """前端可以调用此接口检查API状态"""
        data = {
            "status": "online",
            "service": "emotion-healing-api",
            "version": "1.0.0",
            "timestamp": str(datetime.datetime.now())
        }
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        return Response(json_str, content_type='application/json; charset=utf-8')

    # 根路由
    @app.route('/')
    def index():
        vue_path = os.path.join(PAGE_DIR, 'vue_main.html')
        if os.path.exists(vue_path):
            return send_from_directory(PAGE_DIR, 'vue_main.html')

        # 返回API信息，包含前端地址
        data = {
            "message": "情绪愈疗平台API服务",
            "version": "1.0.0",
            "frontend_url": "http://452e9a87.r6.cpolar.top",
            "endpoints": {
                "auth": {
                    "login": "/api/auth/login",
                    "register": "/api/auth/register",
                    "anonymous": "/api/auth/anonymous"
                },
                "conversations": "/api/conversations",
                "emotion": "/api/emotion",
                "risk": "/api/risk"
            },
            "status": "running"
        }
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        return Response(json_str, content_type='application/json; charset=utf-8')

    # 前端页面 - 用于开发测试
    @app.route('/index.html')
    def frontend():
        vue_path = os.path.join(PAGE_DIR, 'vue_main.html')
        if os.path.exists(vue_path):
            return send_from_directory(PAGE_DIR, 'vue_main.html')
        return jsonify({"message": "前端页面未找到"}), 404

    # API 信息
    @app.route('/api')
    def api_info():
        data = {
            "message": "情绪愈疗平台API服务",
            "version": "1.0.0",
            "frontend_url": "http://452e9a87.r6.cpolar.top",
            "endpoints": {
                "auth": {
                    "login": "/api/auth/login (POST)",
                    "register": "/api/auth/register (POST)",
                    "anonymous": "/api/auth/anonymous (POST)",
                    "logout": "/api/auth/logout (POST)"
                },
                "conversations": {
                    "send_message": "/api/conversations/send (POST)",
                    "history": "/api/conversations/history (GET)"
                },
                "emotion": {
                    "analysis": "/api/emotion/analyze (POST)",
                    "report": "/api/emotion/report (GET)"
                },
                "risk": {
                    "check": "/api/risk/check (POST)",
                    "status": "/api/risk/status (GET)"
                }
            }
        }
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        return Response(json_str, content_type='application/json; charset=utf-8')

    # 静态资源路由
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """提供静态文件（头像等）"""
        file_path = os.path.join(STATIC_DIR, filename)
        if os.path.exists(file_path):
            response = send_from_directory(STATIC_DIR, filename)
            # 添加CORS头
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        return jsonify({"error": "文件未找到"}), 404

    # 通用静态文件路由
    @app.route('/<path:filename>')
    def static_files(filename):
        if filename.endswith(('.html', '.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico')):
            file_path = os.path.join(PAGE_DIR, filename)
            if os.path.exists(file_path):
                response = send_from_directory(PAGE_DIR, filename)
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
        return jsonify({"error": "文件未找到"}), 404

    return app

# 创建应用实例（开发环境）
app = create_app('development')

# 如果前端需要测试连接，添加一个测试端点
@app.route('/api/test-connection', methods=['GET', 'POST', 'OPTIONS'])
def test_connection():
    """测试前后端连接是否正常"""
    if request.method == 'OPTIONS':
        return handle_options('')

    data = {
        "success": True,
        "message": "连接成功",
        "data": {
            "method": request.method,
            "headers": dict(request.headers),
            "timestamp": str(datetime.datetime.now())
        }
    }
    return jsonify(data)

# 添加datetime导入
import datetime

if __name__ == '__main__':
    # 创建数据库表
    with app.app_context():
        db.create_all()
        print("[OK] 数据库表创建完成")

    print("=" * 60)
    print("情绪愈疗平台API服务启动中...")
    print("=" * 60)
    print("后端服务地址: https://cometary-mousily-han.ngrok-free.dev")
    print("前端应用地址: http://452e9a87.r6.cpolar.top")
    print("-" * 60)
    print("API端点测试:")
    print("  GET  /health - 健康检查")
    print("  GET  /api/status - API状态")
    print("  POST /api/test-connection - 连接测试")
    print("  POST /api/auth/login - 用户登录")
    print("  POST /api/auth/register - 用户注册")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=True)
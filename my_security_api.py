"""
数据安全模块
后端工程师B - 任务6

功能：
1. 用户数据加密
2. 隐私保护
3. API鉴权
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from extensions import db
from datetime import datetime, timedelta
import hashlib
import os
import re

security_bp = Blueprint('security_b', __name__)

# ==================== 用户认证 ====================

@security_bp.route('/register', methods=['POST'])
def register():
    """
    POST /api/b-auth/register - 用户注册
    请求: {"username": "用户名", "password": "密码", "email": "邮箱(可选)"}
    """
    try:
        data = request.get_json() or {}
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        
        if not username or not password:
            return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400
        
        if len(password) < 6:
            return jsonify({"success": False, "message": "密码长度至少6位"}), 400
        
        from models import User
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({"success": False, "message": "用户名已存在"}), 400
        
        # 检查邮箱是否已存在（如果提供了邮箱）
        if email and User.query.filter_by(email=email).first():
            return jsonify({"success": False, "message": "邮箱已被注册"}), 400
        
        # 创建用户（密码会被Bcrypt加密）
        user = User(
            username=username,
            email=email if email else None,
            user_type='registered',
            is_anonymous=False
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # 生成token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            "success": True,
            "message": "注册成功",
            "data": {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "token": access_token
            }
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@security_bp.route('/login', methods=['POST'])
def login():
    """
    POST /api/b-auth/login - 用户登录
    请求: {"username": "用户名", "password": "密码"}
    """
    try:
        data = request.get_json() or {}
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400
        
        from models import User
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({"success": False, "message": "用户名或密码错误"}), 401
        
        # 生成token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            "success": True,
            "message": "登录成功",
            "data": {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "token": access_token
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==================== 数据加密工具 ====================

def encrypt_data(data, key=None):
    """
    加密数据（简单加密，实际生产建议使用Fernet）
    """
    if key is None:
        key = os.getenv('ENCRYPTION_KEY', 'default-key-change-me')
    
    # 简单加密：Base64 + XOR
    data_str = str(data)
    key_bytes = key.encode()
    data_bytes = data_str.encode()
    
    result = bytearray()
    for i, b in enumerate(data_bytes):
        result.append(b ^ key_bytes[i % len(key_bytes)])
    
    import base64
    return base64.b64encode(bytes(result)).decode()


def decrypt_data(encrypted_data, key=None):
    """
    解密数据
    """
    if key is None:
        key = os.getenv('ENCRYPTION_KEY', 'default-key-change-me')
    
    import base64
    try:
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        key_bytes = key.encode()
        
        result = bytearray()
        for i, b in enumerate(encrypted_bytes):
            result.append(b ^ key_bytes[i % len(key_bytes)])
        
        return bytes(result).decode()
    except:
        return None


def hash_sensitive_data(data):
    """
    对敏感数据进行哈希处理（不可解密，用于校验）
    """
    return hashlib.sha256(data.encode()).hexdigest()


# ==================== 隐私保护API ====================

@security_bp.route('/encrypt', methods=['POST'])
@jwt_required()
def encrypt_user_data():
    """
    POST /api/b-security/encrypt - 加密用户数据
    请求: {"data": "要加密的数据"}
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        plain_data = data.get('data', '')
        
        if not plain_data:
            return jsonify({"success": False, "message": "没有要加密的数据"}), 400
        
        encrypted = encrypt_data(plain_data)
        
        return jsonify({
            "success": True,
            "data": {
                "original": plain_data,
                "encrypted": encrypted
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@security_bp.route('/decrypt', methods=['POST'])
@jwt_required()
def decrypt_user_data():
    """
    POST /api/b-security/decrypt - 解密用户数据
    请求: {"encrypted_data": "加密的数据"}
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        encrypted = data.get('encrypted_data', '')
        
        if not encrypted:
            return jsonify({"success": False, "message": "没有要解密的数据"}), 400
        
        decrypted = decrypt_data(encrypted)
        
        if decrypted is None:
            return jsonify({"success": False, "message": "解密失败"}), 400
        
        return jsonify({
            "success": True,
            "data": {
                "encrypted": encrypted,
                "decrypted": decrypted
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@security_bp.route('/mask', methods=['POST'])
def mask_sensitive_data():
    """
    POST /api/b-security/mask - 脱敏处理
    请求: {"data": "13812345678", "type": "phone"}
    类型: phone(手机号), idcard(身份证), email(邮箱), name(姓名)
    """
    try:
        data = request.get_json() or {}
        
        content = data.get('data', '')
        data_type = data.get('type', 'phone')
        
        if not content:
            return jsonify({"success": False, "message": "没有要脱敏的数据"}), 400
        
        masked = content
        
        if data_type == 'phone':
            # 手机号脱敏：138****5678
            if len(content) == 11:
                masked = content[:3] + '****' + content[7:]
        
        elif data_type == 'idcard':
            # 身份证脱敏：310***********1234
            if len(content) >= 15:
                masked = content[:3] + '*' * (len(content) - 7) + content[-4:]
        
        elif data_type == 'email':
            # 邮箱脱敏：a***@example.com
            if '@' in content:
                parts = content.split('@')
                if len(parts[0]) > 2:
                    masked = parts[0][:1] + '***@' + parts[1]
        
        elif data_type == 'name':
            # 姓名脱敏：张*
            if len(content) >= 2:
                masked = content[0] + '*'
        
        return jsonify({
            "success": True,
            "data": {
                "original": content,
                "masked": masked,
                "type": data_type
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==================== 数据导出/删除（GDPR合规） ====================

@security_bp.route('/export', methods=['GET'])
@jwt_required()
def export_user_data():
    """
    GET /api/b-security/export - 导出用户数据
    """
    try:
        current_user_id = get_jwt_identity()
        
        from models import User, EmotionRecord, Conversation
        
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404
        
        # 收集用户数据
        emotion_records = EmotionRecord.query.filter_by(user_id=current_user_id).all()
        conversations = Conversation.query.filter_by(user_id=current_user_id).all()
        
        export_data = {
            "user_info": {
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "emotion_records": [r.to_dict() for r in emotion_records],
            "conversations": [c.to_dict() for c in conversations],
            "export_time": datetime.utcnow().isoformat()
        }
        
        return jsonify({
            "success": True,
            "data": export_data
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@security_bp.route('/delete', methods=['DELETE'])
@jwt_required()
def delete_user_data():
    """
    DELETE /api/b-security/delete - 删除用户数据（注销）
    """
    try:
        current_user_id = get_jwt_identity()
        
        from models import User, EmotionRecord, Conversation, Message, RiskAlert
        
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404
        
        # 删除关联数据
        EmotionRecord.query.filter_by(user_id=current_user_id).delete()
        
        conversations = Conversation.query.filter_by(user_id=current_user_id).all()
        for conv in conversations:
            Message.query.filter_by(conversation_id=conv.id).delete()
        Conversation.query.filter_by(user_id=current_user_id).delete()
        
        RiskAlert.query.filter_by(user_id=current_user_id).delete()
        
        # 删除用户
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "用户数据已全部删除"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==================== Token刷新 ====================

@security_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_token():
    """
    POST /api/b-auth/refresh - 刷新Token
    """
    try:
        current_user_id = get_jwt_identity()
        
        # 创建新的token
        access_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            "success": True,
            "data": {
                "token": access_token
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# 注册路由示例（在app.py中）
"""
from my_security_api import security_bp
app.register_blueprint(security_bp, url_prefix='/api/b-auth')

# 需要配置JWT
from flask_jwt_extended import JWTManager
jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
"""

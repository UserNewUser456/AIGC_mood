"""
用户认证路由
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from models import User, db
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('username') or not data.get('password'):
            return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"success": False, "message": "用户名已存在"}), 400
        
        # 创建新用户
        user = User(
            username=data['username'],
            email=data.get('email'),
            user_type='registered'
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # 生成访问令牌
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            "success": True,
            "message": "注册成功",
            "user": user.to_dict(),
            "access_token": access_token
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('username') or not data.get('password'):
            return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400
        
        # 查找用户
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({"success": False, "message": "用户名或密码错误"}), 401
        
        # 生成访问令牌
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            "success": True,
            "message": "登录成功",
            "user": user.to_dict(),
            "access_token": access_token
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@auth_bp.route('/anonymous', methods=['POST'])
def create_anonymous_user():
    """创建匿名用户"""
    try:
        # 生成唯一用户名
        username = f"anonymous_{uuid.uuid4().hex[:8]}"
        
        # 创建匿名用户
        user = User(
            username=username,
            user_type='anonymous'
        )
        
        db.session.add(user)
        db.session.commit()
        
        # 生成访问令牌
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            "success": True,
            "message": "匿名用户创建成功",
            "user": user.to_dict(),
            "access_token": access_token
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取用户档案"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404
        
        return jsonify({
            "success": True,
            "user": user.to_dict()
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户档案"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404
        
        data = request.get_json()
        
        # 更新用户名（如果提供且不重复）
        if 'username' in data and data['username']:
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({"success": False, "message": "用户名已存在"}), 400
            user.username = data['username']
        
        # 更新邮箱
        if 'email' in data:
            user.email = data['email']
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "档案更新成功",
            "user": user.to_dict()
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
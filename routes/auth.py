"""
用户认证路由
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity, get_jwt
from models import User, db, bcrypt
import uuid
import re
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

auth_bp = Blueprint('auth', __name__)

# Token黑名单存储（生产环境建议用Redis）
token_blacklist = set()

# 允许的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_password(password):
    """验证密码强度"""
    if len(password) < 8:
        return False, "密码长度至少8位"
    if not re.search(r"[A-Z]", password):
        return False, "密码必须包含至少一个大写字母"
    if not re.search(r"[a-z]", password):
        return False, "密码必须包含至少一个小写字母"
    if not re.search(r"\d", password):
        return False, "密码必须包含至少一个数字"
    return True, "密码强度合格"

# 兼容前端：创建用户（匿名用户）
@auth_bp.route('/users', methods=['POST'])
def create_user():
    """创建用户（兼容前端）"""
    try:
        data = request.get_json() or {}
        username = data.get('username', f"user_{uuid.uuid4().hex[:8]}")
        user_type = data.get('user_type', 'anonymous')

        # 创建用户
        if user_type == 'anonymous':
            user = User(username=username, user_type='anonymous')
        else:
            user = User(username=username, user_type='registered')

        db.session.add(user)
        db.session.commit()

        # 生成token
        access_token = create_access_token(identity=str(user.id))

        return jsonify({
            "success": True,
            "user_id": user.id,
            "username": user.username,
            "access_token": access_token
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('username') or not data.get('password'):
            return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400

        # 验证密码强度
        is_valid, msg = validate_password(data['password'])
        if not is_valid:
            return jsonify({"success": False, "message": msg}), 400

        # 检查用户名是否已存在
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"success": False, "message": "用户名已存在"}), 400

        # 检查邮箱是否已存在（如果提供）
        if data.get('email'):
            if User.query.filter_by(email=data['email']).first():
                return jsonify({"success": False, "message": "邮箱已被使用"}), 400

        # 创建新用户
        user = User(
            username=data['username'],
            email=data.get('email'),
            user_type='registered'  # 注册用户类型
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        # 生成访问令牌和刷新令牌
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "user_type": user.user_type,
                "username": user.username
            },
            expires_delta=timedelta(hours=1)
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            expires_delta=timedelta(days=7)
        )

        return jsonify({
            "success": True,
            "message": "注册成功",
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"注册错误: {str(e)}")
        return jsonify({"success": False, "message": "注册失败，请稍后重试"}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('username') or not data.get('password'):
            return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400

        # 查找用户（支持用户名或邮箱登录）
        user = User.query.filter(
            (User.username == data['username']) | (User.email == data['username'])
        ).first()

        if not user or not user.check_password(data['password']):
            return jsonify({"success": False, "message": "用户名或密码错误"}), 401

        # 检查用户类型（匿名用户不能登录）
        if user.user_type == 'anonymous':
            return jsonify({"success": False, "message": "匿名用户无法登录，请注册账号"}), 403

        # 生成访问令牌和刷新令牌
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "user_type": user.user_type,
                "username": user.username
            },
            expires_delta=timedelta(hours=1)
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            expires_delta=timedelta(days=7)
        )

        return jsonify({
            "success": True,
            "message": "登录成功",
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token
        })

    except Exception as e:
        current_app.logger.error(f"登录错误: {str(e)}")
        return jsonify({"success": False, "message": "登录失败，请稍后重试"}), 500

@auth_bp.route('/anonymous', methods=['POST'])
def create_anonymous_user():
    """创建匿名用户"""
    try:
        # 生成唯一用户名
        username = f"anonymous_{uuid.uuid4().hex[:8]}"

        # 创建匿名用户
        user = User(
            username=username,
            user_type='anonymous'  # 匿名用户类型
        )

        db.session.add(user)
        db.session.commit()

        # 生成访问令牌（匿名用户令牌有效期较短）
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "user_type": "anonymous",
                "username": user.username
            },
            expires_delta=timedelta(days=1)  # 匿名用户令牌有效期1天
        )

        return jsonify({
            "success": True,
            "message": "匿名用户创建成功",
            "user": user.to_dict(),
            "access_token": access_token
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建匿名用户错误: {str(e)}")
        return jsonify({"success": False, "message": "创建匿名用户失败"}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取用户档案"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404

        # 获取用户统计数据
        stats = {
            "emotion_count": user.emotion_records.count() if hasattr(user, 'emotion_records') else 0,
            "conversation_count": user.conversations.count() if hasattr(user, 'conversations') else 0,
            "risk_alert_count": user.risk_alerts.count() if hasattr(user, 'risk_alerts') else 0
        }

        user_data = user.to_dict()
        user_data['stats'] = stats

        return jsonify({
            "success": True,
            "user": user_data
        })

    except Exception as e:
        current_app.logger.error(f"获取档案错误: {str(e)}")
        return jsonify({"success": False, "message": "获取档案失败"}), 500

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

        # 匿名用户不能更新档案
        if user.user_type == 'anonymous':
            return jsonify({"success": False, "message": "匿名用户无法更新档案"}), 403

        # 更新用户名（如果提供且不重复）
        if 'username' in data and data['username']:
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({"success": False, "message": "用户名已存在"}), 400
            user.username = data['username']

        # 更新邮箱
        if 'email' in data:
            if data['email']:  # 如果提供了邮箱
                existing_user = User.query.filter_by(email=data['email']).first()
                if existing_user and existing_user.id != user.id:
                    return jsonify({"success": False, "message": "邮箱已被使用"}), 400
            user.email = data['email'] or None

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "档案更新成功",
            "user": user.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新档案错误: {str(e)}")
        return jsonify({"success": False, "message": "更新档案失败"}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """修改密码"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404

        # 匿名用户不能修改密码
        if user.user_type == 'anonymous':
            return jsonify({"success": False, "message": "匿名用户无法修改密码"}), 403

        data = request.get_json()

        # 验证必填字段
        if not data.get('old_password') or not data.get('new_password'):
            return jsonify({"success": False, "message": "请提供旧密码和新密码"}), 400

        # 验证旧密码
        if not user.check_password(data['old_password']):
            return jsonify({"success": False, "message": "旧密码错误"}), 401

        # 验证新密码强度
        is_valid, msg = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({"success": False, "message": msg}), 400

        # 更新密码
        user.set_password(data['new_password'])
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "密码修改成功"
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"修改密码错误: {str(e)}")
        return jsonify({"success": False, "message": "修改密码失败"}), 500

@auth_bp.route('/upgrade-account', methods=['POST'])
@jwt_required()
def upgrade_account():
    """匿名用户升级为注册用户"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404

        # 检查是否为匿名用户
        if user.user_type != 'anonymous':
            return jsonify({"success": False, "message": "只有匿名用户可以升级账号"}), 400

        data = request.get_json()

        # 验证必填字段
        if not data.get('username') or not data.get('password'):
            return jsonify({"success": False, "message": "请提供用户名和密码"}), 400

        # 验证密码强度
        is_valid, msg = validate_password(data['password'])
        if not is_valid:
            return jsonify({"success": False, "message": msg}), 400

        # 检查用户名是否已存在
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"success": False, "message": "用户名已存在"}), 400

        # 检查邮箱是否已存在（如果提供）
        if data.get('email'):
            if User.query.filter_by(email=data['email']).first():
                return jsonify({"success": False, "message": "邮箱已被使用"}), 400

        # 升级账号
        user.username = data['username']
        user.email = data.get('email')
        user.user_type = 'registered'
        user.set_password(data['password'])

        db.session.commit()

        # 生成新的令牌
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "user_type": user.user_type,
                "username": user.username
            }
        )
        refresh_token = create_refresh_token(identity=str(user.id))

        return jsonify({
            "success": True,
            "message": "账号升级成功",
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"升级账号错误: {str(e)}")
        return jsonify({"success": False, "message": "升级账号失败"}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新Access Token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404

        # 生成新的访问令牌
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "user_type": user.user_type,
                "username": user.username
            }
        )

        return jsonify({
            "success": True,
            "access_token": access_token
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@auth_bp.route('/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """上传用户头像（只保留这一个版本）"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404

        # 检查是否有文件
        if 'avatar' not in request.files:
            return jsonify({"success": False, "message": "请选择头像文件"}), 400

        file = request.files['avatar']

        if file.filename == '':
            return jsonify({"success": False, "message": "未选择文件"}), 400

        if file and allowed_file(file.filename):
            # 生成唯一文件名
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"avatar_{user.id}_{uuid.uuid4().hex[:8]}.{ext}"

            # 创建上传目录
            upload_folder = os.path.join(
                current_app.root_path,
                'static',
                'avatars'
            )
            os.makedirs(upload_folder, exist_ok=True)

            # 保存文件
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)

            # 删除旧头像（如果有）
            if hasattr(user, 'avatar_url') and user.avatar_url:
                old_avatar_path = os.path.join(
                    current_app.root_path,
                    user.avatar_url.lstrip('/')
                )
                if os.path.exists(old_avatar_path) and 'default' not in old_avatar_path:
                    try:
                        os.remove(old_avatar_path)
                    except:
                        pass

            # 更新用户头像URL
            avatar_url = f"/static/avatars/{filename}"
            user.avatar_url = avatar_url
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "头像上传成功",
                "avatar_url": avatar_url
            })

        return jsonify({"success": False, "message": "不支持的图片格式，请上传png、jpg、jpeg、gif、webp格式的图片"}), 400

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"上传头像错误: {str(e)}")
        return jsonify({"success": False, "message": f"上传失败: {str(e)}"}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出（将token加入黑名单）"""
    try:
        # 获取当前token的jti
        jti = get_jwt()['jti']
        token_blacklist.add(jti)

        return jsonify({
            "success": True,
            "message": "登出成功"
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@auth_bp.route('/revoke', methods=['POST'])
@jwt_required()
def revoke_token():
    """撤销当前Token"""
    try:
        jti = get_jwt()['jti']
        token_blacklist.add(jti)

        return jsonify({
            "success": True,
            "message": "Token已撤销"
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
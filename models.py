"""
数据库模型定义
"""

from datetime import datetime
from extensions import db
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=True)  # 匿名用户无密码
    user_type = db.Column(db.Enum('anonymous', 'registered'), default='anonymous')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    emotion_records = db.relationship('EmotionRecord', backref='user', lazy='dynamic')
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic')
    risk_alerts = db.relationship('RiskAlert', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """验证密码"""
        if not self.password_hash:
            return False
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'user_type': self.user_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class EmotionRecord(db.Model):
    """情绪记录模型"""
    __tablename__ = 'emotion_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    emotion = db.Column(db.String(32), nullable=False)
    score = db.Column(db.Float, nullable=False)
    text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'emotion': self.emotion,
            'score': self.score,
            'text': self.text,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Conversation(db.Model):
    """对话会话模型"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_type = db.Column(db.String(32), default='gentle')  # gentle, rational, humorous
    title = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', order_by='Message.created_at')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'doctor_type': self.doctor_type,
            'title': self.title,
            'message_count': self.messages.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Message(db.Model):
    """消息模型"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.Enum('user', 'assistant', 'system'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    emotion_detected = db.Column(db.String(32))
    score_detected = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'emotion_detected': self.emotion_detected,
            'score_detected': self.score_detected,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RiskAlert(db.Model):
    """风险预警模型"""
    __tablename__ = 'risk_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=True)
    risk_level = db.Column(db.Enum('low', 'medium', 'high', 'critical'), nullable=False)
    risk_type = db.Column(db.String(64))  # suicide, self_harm, depression, etc.
    content = db.Column(db.Text)
    handled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'conversation_id': self.conversation_id,
            'risk_level': self.risk_level,
            'risk_type': self.risk_type,
            'content': self.content,
            'handled': self.handled,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class KnowledgeBase(db.Model):
    """心理知识库模型"""
    __tablename__ = 'knowledge_base'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(255))
    source = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'category': self.category,
            'title': self.title,
            'content': self.content,
            'tags': self.tags,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Resource(db.Model):
    """心理资源模型"""
    __tablename__ = 'resources'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum('meditation', 'article', 'music', 'product', 'consultation'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(512))
    applicable_emotions = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'applicable_emotions': self.applicable_emotions,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
"""
配置文件 - 开发/生产环境分离
"""
import os
from datetime import timedelta


class Config:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'emotion-healing-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # 数据库
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False

    # 开发数据库
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:root1234@localhost:3306/emotion_db'
    )

    # JWT配置
    JWT_ACCESS_TOKEN_EXPIRES = False  # 开发环境不过期


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False

    # 生产数据库（从环境变量读取）
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

    # JWT配置
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # 安全配置
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    TESTING = True

    # 测试数据库
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # JWT配置
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)

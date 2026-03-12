"""
数据库初始化脚本
"""

import os
from app import app
from extensions import db
from models import User, KnowledgeBase, Resource, DoctorProfile
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def init_database():
    """初始化数据库"""
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("✓ 数据库表创建成功")
        
        # 检查是否已有数据
        if User.query.first():
            print("○ 数据库已有数据，跳过示例数据插入")
            return
        
        # 插入示例数据
        insert_sample_data()
        print("✓ 示例数据插入成功")

def insert_sample_data():
    """插入示例数据"""
    
    # 示例用户
    users = [
        {
            'username': 'demo_user',
            'email': 'demo@example.com',
            'password': 'demo123',
            'user_type': 'registered'
        },
        {
            'username': 'anonymous_test',
            'user_type': 'anonymous'
        }
    ]
    
    for user_data in users:
        user = User(
            username=user_data['username'],
            email=user_data.get('email'),
            user_type=user_data['user_type']
        )
        
        if 'password' in user_data:
            user.set_password(user_data['password'])
        
        db.session.add(user)
    
    # 心理知识库
    knowledge_items = [
        {
            'category': '情绪管理',
            'title': '深呼吸放松法',
            'content': '深呼吸是一种简单有效的放松技巧。找一个安静的地方，坐下或躺下，用鼻子慢慢吸气4秒，屏住呼吸4秒，然后用口慢慢呼气6秒。重复5-10次可以帮助缓解焦虑。',
            'tags': '深呼吸,放松,焦虑',
            'source': '心理健康指南'
        },
        {
            'category': '情绪管理',
            'title': '情绪ABC理论',
            'content': '情绪ABC理论认为：诱发事件A只是间接原因，而我们对事件的信念和解释B才是直接原因。改变不合理的信念，就能改善情绪。',
            'tags': 'ABC理论,认知,情绪调节',
            'source': '认知行为疗法'
        },
        {
            'category': '睡眠改善',
            'title': '睡前放松技巧',
            'content': '睡前1小时避免使用电子设备，可以听轻音乐、泡热水澡或进行冥想。保持卧室凉爽黑暗，有助于提高睡眠质量。',
            'tags': '睡眠,放松,健康',
            'source': '睡眠健康指南'
        },
        {
            'category': '压力缓解',
            'title': '正念冥想入门',
            'content': '正念是一种专注当下的练习。找一个舒适的姿势，闭眼专注呼吸，当杂念出现时，温和地把注意力带回呼吸。每天10-15分钟即可。',
            'tags': '正念,冥想,放松',
            'source': '正念疗法'
        }
    ]
    
    for knowledge_data in knowledge_items:
        knowledge = KnowledgeBase(**knowledge_data)
        db.session.add(knowledge)
    
    # 心理资源
    resources = [
        {
            'type': 'meditation',
            'title': '5分钟正念冥想',
            'description': '适合初学者的简短冥想课程，帮助放松身心',
            'url': 'https://example.com/meditation1',
            'applicable_emotions': '焦虑,压力,失眠'
        },
        {
            'type': 'article',
            'title': '如何应对焦虑',
            'description': '了解焦虑的成因及应对方法',
            'url': 'https://example.com/article1',
            'applicable_emotions': '焦虑,情绪管理'
        },
        {
            'type': 'music',
            'title': '放松减压音乐',
            'description': '轻音乐帮助缓解压力和焦虑',
            'url': 'https://example.com/music1',
            'applicable_emotions': '压力,焦虑,放松'
        }
    ]
    
    for resource_data in resources:
        resource = Resource(**resource_data)
        db.session.add(resource)
    
    # 医生形象数据
    doctors = [
        {
            'name': '温柔心理师',
            'personality': '温暖、共情、耐心，善于倾听来访者的内心声音',
            'greeting': '你好，我是温柔心理师。在这里，你可以放心地倾诉，我会一直陪在你身边。',
            'avatar_url': '/images/doctor_gentle.png',
            'doctor_type': 'gentle'
        },
        {
            'name': '理性分析师',
            'personality': '冷静、客观、逻辑性强，帮助来访者理清思路',
            'greeting': '你好，我是理性分析师。让我们一起客观地分析你的问题，找到解决方案。',
            'avatar_url': '/images/doctor_rational.png',
            'doctor_type': 'rational'
        },
        {
            'name': '幽默治疗师',
            'personality': '乐观、幽默、轻松，帮助来访者缓解负面情绪',
            'greeting': '你好，我是幽默治疗师！虽然生活中有不如意，但保持乐观很重要，让我们一起找回笑容吧！',
            'avatar_url': '/images/doctor_humorous.png',
            'doctor_type': 'humorous'
        }
    ]
    
    for doctor_data in doctors:
        doctor = DoctorProfile(**doctor_data)
        db.session.add(doctor)
    
    db.session.commit()

if __name__ == '__main__':
    print("=" * 50)
    print("开始初始化数据库...")
    print("=" * 50)
    
    try:
        init_database()
        print("=" * 50)
        print("数据库初始化完成！")
        print("=" * 50)
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        print("=" * 50)
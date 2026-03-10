"""
================================================================================
情绪愈疗平台 - 数据库初始化脚本
================================================================================

文件名: database.py
功能: 创建MySQL数据库和所有数据表结构，并插入示例数据
依赖: pymysql, python-dotenv

使用方法:
    python database.py

注意: 运行前请确保已配置 .env 文件中的数据库连接信息
================================================================================
"""

import pymysql
import os
from dotenv import load_dotenv

# ================================================================================
# 第一部分：环境配置加载
# ================================================================================

# 加载 .env 文件中的环境变量
# .env 文件应包含: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
load_dotenv()

# ================================================================================
# 第二部分：数据库连接配置
# ================================================================================

# 数据库连接配置字典
# 配置项说明:
#   - host: MySQL服务器地址，默认 localhost
#   - port: MySQL端口，默认 3306
#   - user: 数据库用户名，默认 root
#   - password: 数据库密码
#   - charset: 字符编码，使用 utf8mb4 支持emoji和中文
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),        # 数据库主机地址
    'port': int(os.getenv('DB_PORT', 3306)),         # 数据库端口号
    'user': os.getenv('DB_USER', 'root'),            # 数据库用户名
    'password': os.getenv('DB_PASSWORD', 'root'),     # 数据库密码
    'charset': 'utf8mb4'                              # 字符编码（支持中文）
}

# 数据库名称配置
# 从环境变量获取，默认使用 'emotion_db'
DATABASE_NAME = os.getenv('DB_NAME', 'emotion_db')


# ================================================================================
# 第三部分：数据库初始化函数
# ================================================================================

def create_database():
    """
    创建数据库（如果不存在）
    
    功能说明:
        连接到MySQL服务器，创建一个新的数据库（如果不存在）
        使用 utf8mb4_unicode_ci 排序规则，支持中文和emoji
    
    执行流程:
        1. 先连接到MySQL服务器（不指定数据库）
        2. 执行 CREATE DATABASE 语句
        3. 提交事务并关闭连接
    
    返回值: 无
    
    异常处理:
        - 打印错误信息但不中断程序
    """
    # ============================================================================
    # 步骤1: 连接到MySQL服务器（不指定数据库，因为要创建数据库本身）
    # ============================================================================
    # 从配置字典中移除 'database' 键，因为此时数据库还不存在
    config_no_db = {k: v for k, v in DB_CONFIG.items() if k != 'database'}
    
    # 建立数据库连接
    conn = pymysql.connect(**config_no_db)
    
    try:
        # ============================================================================
        # 步骤2: 执行 CREATE DATABASE 语句
        # ============================================================================
        with conn.cursor() as cursor:
            # 执行创建数据库的SQL语句
            # IF NOT EXISTS: 如果数据库已存在则不报错
            # CHARACTER SET utf8mb4: 使用UTF-8编码，支持更多字符
            # COLLATE utf8mb4_unicode_ci: 排序规则，对中文更友好
            cursor.execute(f"""
                CREATE DATABASE IF NOT EXISTS {DATABASE_NAME} 
                CHARACTER SET utf8mb4 
                COLLATE utf8mb4_unicode_ci
            """)
        
        # ============================================================================
        # 步骤3: 提交事务
        # ============================================================================
        conn.commit()
        print(f"✓ 数据库 '{DATABASE_NAME}' 创建成功")
        
    except Exception as e:
        # 捕获异常并打印错误信息
        print(f"✗ 数据库创建失败: {e}")
        
    finally:
        # ============================================================================
        # 步骤4: 关闭数据库连接（无论成功或失败都执行）
        # ============================================================================
        conn.close()


def create_tables():
    """
    创建所有数据表
    
    功能说明:
        在已创建的数据库中创建7张数据表，用于存储不同业务数据
    
    数据表说明:
        1. users              - 用户表，存储用户基本信息
        2. emotion_records   - 情绪记录表，存储用户情绪数据
        3. conversations     - 对话会话表，存储AI对话会话
        4. messages          - 消息记录表，存储对话中的每条消息
        5. risk_alerts       - 风险预警表，存储心理风险预警记录
        6. knowledge_base    - 心理知识库表，存储心理知识文章
        7. resources         - 资源推荐表，存储推荐的心理资源
    
    执行流程:
        1. 连接到指定数据库
        2. 依次执行7个 CREATE TABLE 语句
        3. 提交事务并关闭连接
    
    返回值: 无
    """
    # ============================================================================
    # 步骤1: 连接到数据库
    # ============================================================================
    conn = pymysql.connect(**DB_CONFIG, database=DATABASE_NAME)
    
    try:
        with conn.cursor() as cursor:
            
            # =========================================================================
            # 表1: users - 用户表
            # =========================================================================
            # 用途: 存储用户基本信息，支持匿名用户和注册用户
            # 字段说明:
            #   - id: 用户ID，主键自增
            #   - username: 用户名/昵称，唯一且不能为空
            #   - user_type: 用户类型，anonymous(匿名用户) 或 registered(注册用户)
            #   - created_at: 创建时间，默认当前时间戳
            #   - updated_at: 更新时间，自动更新
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(64) NOT NULL UNIQUE COMMENT '用户名/昵称',
                    user_type ENUM('anonymous', 'registered') DEFAULT 'anonymous' COMMENT '用户类型',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX idx_username (username),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表'
            """)
            
            # =========================================================================
            # 表2: emotion_records - 情绪记录表
            # =========================================================================
            # 用途: 存储用户每次记录的情绪数据
            # 字段说明:
            #   - id: 记录ID，主键自增
            #   - user_id: 用户ID，外键关联users表
            #   - emotion: 情绪类型，如"开心"、"焦虑"等
            #   - score: 情绪分数，范围0-10
            #   - text: 备注文字，可选
            #   - created_at: 记录时间，默认当前时间戳
            # 索引说明:
            #   - idx_user_id: 加速按用户查询
            #   - idx_created_at: 加速按时间查询
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emotion_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL COMMENT '用户ID',
                    emotion VARCHAR(32) NOT NULL COMMENT '情绪类型',
                    score FLOAT NOT NULL COMMENT '情绪分数 0-10',
                    text TEXT COMMENT '备注文字',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='情绪记录表'
            """)
            
            # =========================================================================
            # 表3: conversations - 对话会话表
            # =========================================================================
            # 用途: 存储用户与AI医生的对话会话信息
            # 字段说明:
            #   - id: 会话ID，主键自增
            #   - user_id: 用户ID，外键关联users表
            #   - doctor_type: 医生类型，如 gentle(温柔型)、rational(理性型)、humorous(幽默型)
            #   - created_at: 会话开始时间
            #   - updated_at: 最后活动时间，用于判断会话是否活跃
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL COMMENT '用户ID',
                    doctor_type VARCHAR(32) NOT NULL DEFAULT 'gentle' COMMENT '医生类型',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '对话开始时间',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后活动时间',
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话会话表'
            """)
            
            # =========================================================================
            # 表4: messages - 消息记录表
            # =========================================================================
            # 用途: 存储对话中的每条消息（用户消息和AI回复）
            # 字段说明:
            #   - id: 消息ID，主键自增
            #   - conversation_id: 会话ID，外键关联conversations表
            #   - role: 消息角色，user(用户)、assistant(AI助手)、system(系统)
            #   - content: 消息内容
            #   - emotion_detected: 检测到的情绪（用于AI回复）
            #   - score_detected: 情绪分数
            #   - created_at: 发送时间
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    conversation_id INT NOT NULL COMMENT '对话ID',
                    role ENUM('user', 'assistant', 'system') NOT NULL COMMENT '消息角色',
                    content TEXT NOT NULL COMMENT '消息内容',
                    emotion_detected VARCHAR(32) COMMENT '检测到的情绪',
                    score_detected FLOAT COMMENT '情绪分数',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',
                    INDEX idx_conversation_id (conversation_id),
                    INDEX idx_created_at (created_at),
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息记录表'
            """)
            
            # =========================================================================
            # 表5: risk_alerts - 风险预警表
            # =========================================================================
            # 用途: 存储检测到的心理风险预警信息
            # 字段说明:
            #   - id: 预警ID，主键自增
            #   - user_id: 用户ID，外键关联users表
            #   - conversation_id: 关联的对话ID，可为空
            #   - risk_level: 风险等级，low(低)、medium(中)、high(高)、critical(严重)
            #   - risk_type: 风险类型，如 suicide(自杀)、self_harm(自伤)、depression(抑郁)等
            #   - content: 触发风险预警的内容
            #   - handled: 是否已处理，0-未处理，1-已处理
            #   - created_at: 预警生成时间
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS risk_alerts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL COMMENT '用户ID',
                    conversation_id INT COMMENT '关联对话ID',
                    risk_level ENUM('low', 'medium', 'high', 'critical') NOT NULL COMMENT '风险等级',
                    risk_type VARCHAR(64) COMMENT '风险类型',
                    content TEXT COMMENT '触发内容',
                    handled TINYINT DEFAULT 0 COMMENT '是否已处理',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '预警时间',
                    INDEX idx_user_id (user_id),
                    INDEX idx_risk_level (risk_level),
                    INDEX idx_handled (handled),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='风险预警表'
            """)
            
            # =========================================================================
            # 表6: knowledge_base - 心理知识库表
            # =========================================================================
            # 用途: 存储心理健康知识文章，用于RAG检索增强
            # 字段说明:
            #   - id: 知识ID，主键自增
            #   - category: 知识分类，如"情绪管理"、"睡眠改善"等
            #   - title: 文章标题
            #   - content: 文章内容
            #   - tags: 标签，逗号分隔，用于关键词搜索
            #   - source: 来源，如"心理健康指南"
            #   - created_at/updated_at: 创建和更新时间
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category VARCHAR(64) NOT NULL COMMENT '知识分类',
                    title VARCHAR(255) NOT NULL COMMENT '标题',
                    content TEXT NOT NULL COMMENT '内容',
                    tags VARCHAR(255) COMMENT '标签（逗号分隔）',
                    source VARCHAR(128) COMMENT '来源',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX idx_category (category),
                    INDEX idx_tags (tags)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='心理知识库'
            """)
            
            # =========================================================================
            # 表7: resources - 资源推荐表
            # =========================================================================
            # 用途: 存储心理资源推荐，如冥想课程、文章、音乐等
            # 字段说明:
            #   - id: 资源ID，主键自增
            #   - type: 资源类型，meditation(冥想)、article(文章)、music(音乐)、product(商品)、consultation(咨询)
            #   - title: 资源标题
            #   - description: 资源描述
            #   - url: 资源链接
            #   - applicable_emotions: 适用情绪，逗号分隔
            #   - created_at: 创建时间
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    type ENUM('meditation', 'article', 'music', 'product', 'consultation') NOT NULL COMMENT '资源类型',
                    title VARCHAR(255) NOT NULL COMMENT '资源标题',
                    description TEXT COMMENT '资源描述',
                    url VARCHAR(512) COMMENT '资源链接',
                    applicable_emotions VARCHAR(128) COMMENT '适用情绪（逗号分隔）',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    INDEX idx_type (type),
                    INDEX idx_applicable_emotions (applicable_emotions)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='心理资源表'
            """)
            
        # ============================================================================
        # 步骤2: 提交事务，使所有表创建生效
        # ============================================================================
        conn.commit()
        print("✓ 所有数据表创建成功")
        
    except Exception as e:
        # 异常处理：打印错误并回滚事务
        print(f"✗ 数据表创建失败: {e}")
        conn.rollback()
        
    finally:
        # 关闭数据库连接
        conn.close()


def insert_sample_data():
    """
    插入示例数据
    
    功能说明:
        向数据库中插入示例数据，用于开发和测试
    
    插入的数据内容:
        1. 示例用户 - 3个测试用户
        2. 情绪记录 - 为前2个用户各生成过去7天的随机情绪数据
        3. 心理知识 - 5条心理健康知识
        4. 资源推荐 - 5个推荐资源（冥想、文章、音乐、商品）
    
    执行流程:
        1. 检查是否已有数据（避免重复插入）
        2. 插入示例用户
        3. 生成并插入随机情绪记录
        4. 插入心理知识文章
        5. 插入资源推荐
    
    返回值: 无
    """
    # ============================================================================
    # 步骤1: 连接到数据库
    # ============================================================================
    conn = pymysql.connect(**DB_CONFIG, database=DATABASE_NAME)
    
    try:
        with conn.cursor() as cursor:
            
            # =========================================================================
            # 步骤2: 检查是否已有数据
            # =========================================================================
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] > 0:
                print("○ 示例数据已存在，跳过插入")
                return
            
            # =========================================================================
            # 步骤3: 插入示例用户
            # =========================================================================
            # 插入3个测试用户:
            #   - demo_user: 演示用户（匿名）
            #   - anonymous_001: 匿名用户1（匿名）
            #   - test_user: 测试用户（注册用户）
            cursor.execute("""
                INSERT INTO users (username, user_type) VALUES 
                ('demo_user', 'anonymous'),
                ('anonymous_001', 'anonymous'),
                ('test_user', 'registered')
            """)
            
            # =========================================================================
            # 步骤4: 生成并插入随机情绪记录
            # =========================================================================
            # 导入随机数和日期时间模块
            import random
            from datetime import datetime, timedelta
            
            # 情绪类型和对应基准分数映射表
            # 用于生成具有一定规律的随机情绪数据
            emotions = [
                ('开心', 8.5),    # 开心情绪，分数较高
                ('平静', 7.0),    # 平静情绪，分数中等偏高
                ('焦虑', 4.5),    # 焦虑情绪，分数较低
                ('悲伤', 3.5),    # 悲伤情绪，分数低
                ('愤怒', 3.0),    # 愤怒情绪，分数低
                ('兴奋', 8.0),    # 兴奋情绪，分数高
                ('沮丧', 4.0),    # 沮丧情绪，分数较低
                ('放松', 7.5)     # 放松情绪，分数中等偏高
            ]
            
            # 为用户ID 1 和 2 生成过去7天的随机情绪数据
            for user_id in [1, 2]:
                # 遍历过去7天
                for day in range(7):
                    # 每天生成1-3条随机记录
                    for _ in range(random.randint(1, 3)):
                        # 随机选择一种情绪
                        emotion, base_score = random.choice(emotions)
                        
                        # 在基准分数基础上添加随机波动（-1到+1之间）
                        score = min(10, max(0, base_score + random.uniform(-1, 1)))
                        
                        # 随机生成过去的小时数
                        hours_ago = random.randint(0, day * 24)
                        # 计算记录时间
                        created_at = datetime.now() - timedelta(hours=hours_ago)
                        
                        # 执行插入语句
                        cursor.execute("""
                            INSERT INTO emotion_records (user_id, emotion, score, text, created_at) 
                            VALUES (%s, %s, %s, %s, %s)
                        """, (user_id, emotion, round(score, 1), f'自动记录的情绪数据', created_at))
            
            # =========================================================================
            # 步骤5: 插入心理知识文章
            # =========================================================================
            # 知识库内容列表，每条包含：分类、标题、内容、标签、来源
            knowledge_items = [
                # 情绪管理类知识
                ('情绪管理', '深呼吸放松法', 
                 '深呼吸是一种简单有效的放松技巧。找一个安静的地方，坐下或躺下，用鼻子慢慢吸气4秒，屏住呼吸4秒，然后用口慢慢呼气6秒。重复5-10次可以帮助缓解焦虑。', 
                 '深呼吸,放松,焦虑', '心理健康指南'),
                
                ('情绪管理', '情绪ABC理论', 
                 '情绪ABC理论认为：诱发事件A（Activating event）只是间接原因，而我们对事件的信念和解释B（Belief）才是直接原因。改变不合理的信念，就能改善情绪。', 
                 'ABC理论,认知,情绪调节', '认知行为疗法'),
                
                # 睡眠改善类知识
                ('睡眠改善', '睡前放松技巧', 
                 '睡前1小时避免使用电子设备，可以听轻音乐、泡热水澡或进行冥想。保持卧室凉爽黑暗，有助于提高睡眠质量。', 
                 '睡眠,放松,健康', '睡眠健康指南'),
                
                # 压力缓解类知识
                ('压力缓解', '正念冥想入门', 
                 '正念是一种专注当下的练习。找一个舒适的姿势，闭眼专注呼吸，当杂念出现时，温和地把注意力带回呼吸。每天10-15分钟即可。', 
                 '正念,冥想,放松', '正念疗法'),
                
                # 情绪识别类知识
                ('情绪识别', '常见情绪类型', 
                 '基本情绪包括：快乐、悲伤、恐惧、愤怒、惊讶、厌恶。复合情绪如焦虑是恐惧和期待的混合，愧疚是悲伤和责任的混合。', 
                 '情绪,心理学,识别', '情绪心理学'),
            ]
            
            # 遍历并插入每条知识
            for category, title, content, tags, source in knowledge_items:
                cursor.execute("""
                    INSERT INTO knowledge_base (category, title, content, tags, source) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (category, title, content, tags, source))
            
            # =========================================================================
            # 步骤6: 插入资源推荐
            # =========================================================================
            # 资源列表，每条包含：类型、标题、描述、链接、适用情绪
            resources = [
                ('meditation', '5分钟正念冥想', 
                 '适合初学者的简短冥想课程，帮助放松身心', 
                 'https://example.com/meditation1', '焦虑,压力,失眠'),
                
                ('meditation', '深度放松冥想', 
                 '20分钟深度放松训练，缓解紧张情绪', 
                 'https://example.com/meditation2', '紧张,焦虑,疲惫'),
                
                ('article', '如何应对焦虑', 
                 '了解焦虑的成因及应对方法', 
                 'https://example.com/article1', '焦虑,情绪管理'),
                
                ('music', '放松减压音乐', 
                 '轻音乐帮助缓解压力和焦虑', 
                 'https://example.com/music1', '压力,焦虑,放松'),
                
                ('product', '薰衣草香薰', 
                 '天然薰衣草精油，帮助放松和改善睡眠', 
                 'https://example.com/product1', '失眠,焦虑,放松'),
            ]
            
            # 遍历并插入每条资源
            for type_, title, description, url, emotions in resources:
                cursor.execute("""
                    INSERT INTO resources (type, title, description, url, applicable_emotions) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (type_, title, description, url, emotions))
            
        # ============================================================================
        # 步骤7: 提交事务
        # ============================================================================
        conn.commit()
        print("✓ 示例数据插入成功")
        
    except Exception as e:
        # 异常处理
        print(f"✗ 示例数据插入失败: {e}")
        conn.rollback()
        
    finally:
        # 关闭连接
        conn.close()


# ================================================================================
# 第四部分：主函数入口
# ================================================================================

def init_database():
    """
    数据库初始化主函数
    
    功能说明:
        执行完整的数据库初始化流程
    
    执行流程:
        1. 打印开始提示
        2. 创建数据库
        3. 创建数据表
        4. 插入示例数据
        5. 打印完成提示
    
    返回值: 无
    
    使用方法:
        在命令行运行: python database.py
        或在其他Python文件中导入: from database import init_database; init_database()
    """
    # 打印分隔线
    print("=" * 50)
    print("开始初始化数据库...")
    print("=" * 50)
    
    # 执行初始化步骤
    create_database()      # 创建数据库
    create_tables()        # 创建数据表
    insert_sample_data()   # 插入示例数据
    
    # 打印完成信息
    print("=" * 50)
    print("数据库初始化完成！")
    print("=" * 50)


# ================================================================================
# 程序入口
# ================================================================================

# 当直接运行此脚本时，执行初始化
if __name__ == '__main__':
    init_database()

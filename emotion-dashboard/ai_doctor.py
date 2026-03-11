"""
================================================================================
情绪愈疗平台 - AI智能体模块（情绪愈疗医生）
================================================================================

文件名: ai_doctor.py
功能: 提供AI对话、智能情绪分析、风险检测、心理资源推荐等功能
依赖: database（数据库模块，可选）

主要功能:
    1. AI医生人格配置 - 支持温柔型、理性型、幽默型三种医生
    2. 情绪识别 - 基于关键词检测用户情绪
    3. 风险检测 - 识别自杀、自伤、抑郁等心理风险
    4. 对话生成 - 生成共情式回复（模拟LLM）
    5. 资源推荐 - 根据情绪推荐心理资源
    6. 知识查询 - 检索心理知识库

使用方法:
    # 创建对话会话
    from ai_doctor import AIConversation
    
    conv = AIConversation(user_id=1, doctor_type='gentle')
    response = conv.chat("我今天心情不好")
    print(response['response'])
================================================================================
"""

import os
import json
import re
import requests
from datetime import datetime
from functools import wraps

# ================================================================================
# 阿里云百炼平台配置
# ================================================================================
DASHSCOPE_API_KEY = "sk-cd1941be1ff64ce58eddb6e7bb69de71"
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
DEFAULT_MODEL = "qwen-plus"  # 可选: qwen-max, qwen-plus, qwen-turbo

def call_llm_api(messages, model=DEFAULT_MODEL):
    """
    调用阿里云百炼平台LLM API
    
    参数:
        messages: 消息列表，格式为 [{"role": "user/assistant/system", "content": "..."}]
        model: 模型名称，默认qwen-plus
    
    返回:
        str: AI回复内容
    """
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(
            DASHSCOPE_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"API调用失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"API调用异常: {e}")
        return None

# 导入数据库操作（可选，如果数据库未初始化则使用模拟模式）
try:
    from database import query_db, execute_db
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("警告: 数据库模块不可用，将使用模拟模式")

# ================================================================================
# 第一部分：AI医生人格配置
# ================================================================================

# AI医生人格定义字典
# 包含三种类型的AI医生，每种有不同的对话风格
DOCTOR_PERSONAS = {
    # 温柔型医生
    'gentle': {
        'name': '温柔型医生',
        'description': '温暖、耐心、充满同理心，善于倾听和安慰',
        'system_prompt': '''你是一位温柔的心理咨询师助手。你的语气温暖、亲切、有耐心。
你的回复风格：
- 使用简短温和的句子
- 经常表达理解和共情
- 避免直接给建议，而是引导用户思考
- 适当使用鼓励性语言
- 保持积极但真诚的态度

记住：你是在陪伴和支持，不是治疗。用户可能只是需要被倾听。''',
    },
    
    # 理性型医生
    'rational': {
        'name': '理性型医生',
        'description': '冷静、客观、善于分析，提供逻辑清晰的建议',
        'system_prompt': '''你是一位理性的心理咨询师助手。你的风格冷静、客观、有逻辑。
你的回复风格：
- 善于分析问题的各个方面
- 提供清晰的思路和建议
- 用理性但不失温暖的方式表达
- 适当提供心理学知识
- 帮助用户建立理性思维模式

记住：理性不等于冷漠，保持温度的同时帮助用户理清思路。''',
    },
    
    # 幽默型医生
    'humorous': {
        'name': '幽默型医生',
        'description': '轻松、活泼、善于用幽默缓解情绪',
        'system_prompt': '''你是一位幽默的心理咨询师助手。你的风格轻松、活泼、有趣。
你的回复风格：
- 适当使用轻松幽默的语言
- 用积极的方式解读问题
- 帮助用户看到生活中积极的一面
- 避免过度沉重的话题
- 保持友好和亲切

记住：幽默是化解负面情绪的良药，但不要变成敷衍。'''
    }
}

# ================================================================================
# 第二部分：风险关键词配置
# ================================================================================

# 心理风险关键词配置
# 用于检测用户是否表达出自杀、自伤、抑郁等风险
RISK_KEYWORDS = {
    # ========== 自杀相关 ==========
    'suicide': {
        'keywords': [
            '自杀', '不想活', '不想活了', '想死', '死掉', 
            '结束生命', '轻生', '自杀念头'
        ],
        'risk_level': 'critical',  # 严重风险
        'response': '我听到你提到了让你痛苦的事情。你现在安全吗？如果你有伤害自己的想法，请立即寻求帮助。心理援助热线：400-161-9995。'
    },
    
    # ========== 自伤相关 ==========
    'self_harm': {
        'keywords': [
            '自残', '割腕', '伤害自己', '想发泄', '想伤害自己'
        ],
        'risk_level': 'high',  # 高风险
        'response': '我理解你可能正在经历很大的痛苦。请记住，伤害自己并不是解决问题的办法。你可以尝试深呼吸，或者联系心理援助热线：400-161-9995。'
    },
    
    # ========== 抑郁相关 ==========
    'depression': {
        'keywords': [
            '绝望', '没意思', '不想动', '没兴趣', 
            '活着没意义', '空虚', '无助'
        ],
        'risk_level': 'medium',  # 中等风险
        'response': '听起来你最近很低落。这种感觉确实很难受，我想告诉你，你的感受是被理解的。情绪低落时，小小的进步也值得肯定。'
    },
    
    # ========== 焦虑相关 ==========
    'anxiety': {
        'keywords': [
            '紧张', '担心', '害怕', '焦虑', '不安', '恐惧', '慌'
        ],
        'risk_level': 'low',  # 低风险
        'response': '我能感觉到你有些紧张。深呼吸，慢慢呼气。焦虑只是情绪的一种，它会来的，也会走的。'
    }
}

# ================================================================================
# 第三部分：情绪识别功能
# ================================================================================

def detect_emotion(text):
    """
    识别文本中的情绪
    
    功能: 基于关键词匹配，识别用户输入文本中的情绪类型
    
    参数:
        text: 用户输入的文本字符串
    
    返回值:
        dict: 包含两个键值对
            - emotion: 情绪类型字符串（开心/平静/焦虑/悲伤/愤怒/惊讶/厌恶）
            - score: 情绪分数（0-10）
    
    算法说明:
        1. 将输入文本转换为小写进行匹配
        2. 遍历情绪关键词字典，查找匹配的关键词
        3. 找到第一个匹配后返回对应情绪和分数
        4. 未匹配到任何关键词时返回"平静"和5.0分
    
    使用示例:
        >>> detect_emotion("我今天很开心")
        {'emotion': '开心', 'score': 8.0}
        
        >>> detect_emotion("我好焦虑啊")
        {'emotion': '焦虑', 'score': 4.0}
    """
    # 将文本转换为小写，便于匹配
    text = text.lower()
    
    # 情绪关键词映射表
    # 格式: 情绪名称 -> [关键词列表]
    emotion_keywords = {
        '开心': ['开心', '高兴', '快乐', '喜悦', '愉快', '兴奋', 'happy', 'joy'],
        '平静': ['平静', '安宁', '放松', '舒服', '宁静', '轻松', 'calm'],
        '焦虑': ['焦虑', '紧张', '担心', '害怕', '不安', '恐惧', '慌', 'anxious'],
        '悲伤': ['悲伤', '难过', '伤心', '痛苦', '沮丧', '失落', 'sad'],
        '愤怒': ['愤怒', '生气', '恼火', '气愤', '烦躁', 'angry'],
        '惊讶': ['惊讶', '吃惊', '意外', '震惊', '惊讶'],
        '厌恶': ['讨厌', '恶心', '反感', '厌恶', 'disgust'],
    }
    
    # 遍历情绪关键词，查找匹配
    for emotion, keywords in emotion_keywords.items():
        for keyword in keywords:
            if keyword in text:
                # 情绪对应的基准分数
                scores = {
                    '开心': 8.0,      # 开心情绪分数较高
                    '平静': 7.0,      # 平静情绪分数中等偏高
                    '惊讶': 6.0,      # 惊讶情绪分数中等
                    '焦虑': 4.0,      # 焦虑情绪分数较低
                    '悲伤': 3.0,      # 悲伤情绪分数低
                    '愤怒': 3.5,      # 愤怒情绪分数较低
                    '厌恶': 4.0       # 厌恶情绪分数略高于焦虑
                }
                return {'emotion': emotion, 'score': scores.get(emotion, 5.0)}
    
    # 未匹配到任何情绪，返回默认中性情绪
    return {'emotion': '平静', 'score': 5.0}


def analyze_risk(text):
    """
    分析文本中的心理风险
    
    功能: 检测用户输入是否包含自杀、自伤、抑郁等风险内容
    
    参数:
        text: 用户输入的文本字符串
    
    返回值:
        dict: 包含以下键值对
            - risk_level: 风险等级 ('low'/'medium'/'high'/'critical')
            - risk_type: 风险类型 ('suicide'/'self_harm'/'depression'/'anxiety')
            - needs_alert: 是否需要预警 (bool)
            - response: 预设的风险回应文本
    
    算法说明:
        1. 将文本转换为小写
        2. 遍历风险关键词配置，查找匹配
        3. 找到匹配后返回对应的风险信息和预设回应
        4. 未匹配时返回低风险
    
    使用示例:
        >>> analyze_risk("我不想活了")
        {
            'risk_level': 'critical',
            'risk_type': 'suicide',
            'needs_alert': True,
            'response': '我听到你提到了...'
        }
    """
    # 转换为小写进行匹配
    text_lower = text.lower()
    
    # 遍历风险类型配置
    for risk_type, config in RISK_KEYWORDS.items():
        # 检查是否包含该类型的任何一个关键词
        for keyword in config['keywords']:
            if keyword in text_lower:
                # 返回风险信息
                return {
                    'risk_level': config['risk_level'],      # 风险等级
                    'risk_type': risk_type,                  # 风险类型
                    'needs_alert': config['risk_level'] in ['critical', 'high'],  # 严重风险需要预警
                    'response': config['response']           # 预设回应
                }
    
    # 未检测到风险，返回默认低风险
    return {
        'risk_level': 'low', 
        'risk_type': None, 
        'needs_alert': False, 
        'response': None
    }

# ================================================================================
# 第四部分：AI对话生成功能
# ================================================================================

def generate_response(user_message, conversation_history=None, doctor_type='gentle'):
    """
    生成AI回复
    
    功能: 根据用户消息和对话历史，生成AI医生的回复
    
    参数:
        user_message: 用户输入的消息
        conversation_history: 对话历史列表（可选）
        doctor_type: AI医生类型，默认为'gentle'
    
    返回值:
        dict: 包含以下键值对
            - response: AI生成的回复文本
            - emotion: 检测到的用户情绪
            - risk_info: 风险分析信息
            - is_risk_response: 是否为风险响应
    
    执行流程:
        1. 首先进行风险检测，如有风险返回风险提示
        2. 获取对应类型的医生人格配置
        3. 构建对话上下文
        4. 生成回复（调用LLM或使用模拟回复）
    """
    # 步骤1: 风险检测
    risk_info = analyze_risk(user_message)
    
    # 如果检测到风险，返回风险提示响应
    if risk_info['needs_alert'] or risk_info['response']:
        return {
            'response': risk_info['response'],
            'emotion': detect_emotion(user_message),
            'risk_info': risk_info,
            'is_risk_response': True
        }
    
    # 步骤2: 获取医生人格配置
    persona = DOCTOR_PERSONAS.get(doctor_type, DOCTOR_PERSONAS['gentle'])
    
    # 步骤3: 构建对话上下文
    context = build_context(user_message, conversation_history, persona)
    
    # 步骤4: 生成回复 - 调用阿里云百炼平台LLM API
    response = generate_llm_response(user_message, conversation_history, persona)
    
    return {
        'response': response,
        'emotion': detect_emotion(user_message),
        'risk_info': risk_info,
        'is_risk_response': False
    }


def build_context(user_message, history, persona):
    """
    构建对话上下文
    
    功能: 将系统提示、历史消息和当前消息整合为完整的对话上下文
    
    参数:
        user_message: 当前用户消息
        history: 历史消息列表
        persona: 医生人格配置字典
    
    返回值:
        dict: 包含以下键值对
            - system: 系统提示词
            - history: 历史对话文本
            - current: 当前用户消息
    """
    # 系统提示词
    system_prompt = persona['system_prompt']
    
    # 历史消息处理
    history_text = ""
    if history:
        # 取最近5轮对话（10条消息）
        recent_history = history[-10:] if len(history) > 10 else history
        for msg in recent_history:
            # 转换角色标识
            role = "用户" if msg.get('role') == 'user' else "助手"
            history_text += f"{role}：{msg.get('content', '')}\n"
    
    return {
        'system': system_prompt,
        'history': history_text,
        'current': user_message
    }


def generate_llm_response(user_message, history, persona):
    """
    调用阿里云百炼平台LLM生成回复
    
    参数:
        user_message: 用户消息
        history: 对话历史
        persona: 医生人格配置
    
    返回值:
        str: LLM生成的回复文本
    """
    # 构建消息列表
    messages = []
    
    # 添加系统提示
    messages.append({
        "role": "system",
        "content": persona['system_prompt']
    })
    
    # 添加历史消息（最近10轮）
    if history:
        recent_history = history[-10:] if len(history) > 10 else history
        for msg in recent_history:
            role = "user" if msg.get('role') == 'user' else "assistant"
            messages.append({
                "role": role,
                "content": msg.get('content', '')
            })
    
    # 添加当前用户消息
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    # 调用LLM API
    response = call_llm_api(messages)
    
    # 如果API调用失败，使用模拟回复作为后备
    if response is None:
        print("LLM API调用失败，使用模拟回复")
        return generate_mock_response(user_message, history, persona)
    
    return response


def generate_mock_response(user_message, history, persona):
    """
    生成模拟回复
    
    功能: 模拟LLM生成回复（实际项目中应替换为真实的LLM API调用）
    
    参数:
        user_message: 用户消息
        history: 对话历史
        persona: 医生人格配置
    
    返回值:
        str: 生成的回复文本
    
    算法说明:
        1. 根据消息内容关键词匹配预设的回复模板
        2. 如果没有匹配，生成通用的共情回复
        3. 回复风格根据医生人格类型有所不同
    """
    # 导入随机模块（用于选择回复）
    import random
    
    # 各类型的默认回复列表
    responses = {
        'gentle': [
            "我听到你了。",
            "谢谢你愿意分享这些。",
            "我能感觉到你的不容易。",
            "慢慢来，不用着急。",
            "你已经很勇敢了。",
        ],
        'rational': [
            "让我帮你分析一下这个问题。",
            "从心理学角度看，这很正常。",
            "我们可以一起来理清思路。",
            "你可以尝试这样做...",
            "这是一个很好的反思。",
        ],
        'humorous': [
            "嘿，别太给自己压力啦！",
            "生活总会有起起落落，很正常！",
            "你已经很棒了！",
            "来，笑一个！",
            "明天会更好哦！",
        ]
    }
    
    # ========== 根据消息内容选择合适的回复 ==========
    
    # 转换为小写便于匹配
    text = user_message.lower()
    
    # 感谢类消息
    if any(w in text for w in ['谢谢', '感谢', '感恩']):
        return "不客气！我很高兴能陪伴你。如果有任何需要，随时告诉我哦~"
    
    # 疲惫类消息
    if any(w in text for w in ['累', '疲惫', '困', '想睡觉']):
        if persona['name'] == '幽默型医生':
            return "听起来你真的很累了！要不要先休息一下？睡眠是最好的充电器哦~"
        return "你看起来很疲惫。也许现在需要好好休息一下，给自己充充电？"
    
    # 焦虑类消息
    if any(w in text for w in ['焦虑', '紧张', '担心', '害怕']):
        if persona['name'] == '理性型医生':
            return "焦虑是一种常见的情绪反应。我们可以试着深呼吸，或者把担心的事情写下来，一件一件面对。"
        return "我感觉到你的焦虑了。深呼吸，慢慢地吸气......呼气......有没有好一点？"
    
    # 悲伤类消息
    if any(w in text for w in ['难过', '伤心', '哭', '悲伤']):
        return "我真的很心疼你。想哭就哭出来吧，这是情绪释放的一种方式。我在这里陪着你。"
    
    # 开心类消息
    if any(w in text for w in ['开心', '高兴', '快乐']):
        return "太好了！我能感受到你的快乐！生活中有这么多值得开心的事情，真好！"
    
    # ========== 默认回复 ==========
    
    # 根据医生类型选择默认回复
    doctor_responses = responses.get(doctor_type, responses['gentle'])
    base_response = random.choice(doctor_responses)
    
    # 添加后续追问
    followups = [
        "今天过得怎么样？",
        "愿意和我多说说吗？",
        "我在这里听你说。",
        "你可以继续分享。",
    ]
    
    return f"{base_response} {random.choice(followups)}"

# ================================================================================
# 第五部分：资源推荐功能
# ================================================================================

def recommend_resources(emotion, user_context=None):
    """
    根据情绪推荐心理资源
    
    功能: 根据用户当前的情绪状态，推荐适合的心理健康资源
    
    参数:
        emotion: 当前情绪类型字符串
        user_context: 用户上下文信息（可选，用于个性化推荐）
    
    返回值:
        list: 推荐资源列表，每个元素是包含资源信息的字典
    
    资源类型:
        - meditation: 冥想课程
        - article: 心理文章
        - music: 放松音乐
    
    使用示例:
        >>> recommend_resources('焦虑')
        [
            {'type': 'meditation', 'title': '5分钟正念冥想', 'description': '快速缓解焦虑'},
            {'type': 'article', 'title': '应对焦虑的10个方法', 'description': '实用技巧分享'},
            {'type': 'music', 'title': '放松减压音乐', 'description': '轻音乐帮助放松'}
        ]
    """
    # 资源推荐映射表
    # 根据不同情绪推荐对应的资源
    resource_map = {
        '焦虑': [
            {
                'type': 'meditation',
                'title': '5分钟正念冥想',
                'description': '快速缓解焦虑'
            },
            {
                'type': 'article',
                'title': '应对焦虑的10个方法',
                'description': '实用技巧分享'
            },
            {
                'type': 'music',
                'title': '放松减压音乐',
                'description': '轻音乐帮助放松'
            },
        ],
        '悲伤': [
            {
                'type': 'article',
                'title': '如何面对失落',
                'description': '心理调适指南'
            },
            {
                'type': 'meditation',
                'title': '自我关怀冥想',
                'description': '学会善待自己'
            },
            {
                'type': 'music',
                'title': '治愈系音乐',
                'description': '温暖心灵的旋律'
            },
        ],
        '愤怒': [
            {
                'type': 'meditation',
                'title': '情绪释放冥想',
                'description': '帮助平静下来'
            },
            {
                'type': 'article',
                'title': '愤怒管理技巧',
                'description': '教你如何冷静'
            },
            {
                'type': 'music',
                'title': '舒缓音乐',
                'description': '平复情绪'
            },
        ],
        '开心': [
            {
                'type': 'article',
                'title': '如何保持好心情',
                'description': '延续快乐'
            },
            {
                'type': 'meditation',
                'title': '感恩冥想',
                'description': '培养积极心态'
            },
        ],
        '平静': [
            {
                'type': 'meditation',
                'title': '深度放松冥想',
                'description': '享受当下'
            },
            {
                'type': 'article',
                'title': '正念生活指南',
                'description': '提升幸福感'
            },
        ]
    }
    
    # 返回对应情绪的资源推荐，如果找不到则返回平静状态的资源
    return resource_map.get(emotion, resource_map.get('平静', []))

# ================================================================================
# 第六部分：心理知识查询功能
# ================================================================================

def search_knowledge(keyword):
    """
    搜索心理知识
    
    功能: 从知识库中搜索与关键词相关的心理健康知识
    
    参数:
        keyword: 搜索关键词
    
    返回值:
        list: 知识条目列表，每个元素包含 title, content, category
    
    注意:
        如果数据库不可用，返回预设的模拟数据
    
    使用示例:
        >>> search_knowledge('焦虑')
        [
            {
                'title': '情绪管理技巧',
                'content': '深呼吸是最简单的情绪调节方法...',
                'category': '情绪管理'
            }
        ]
    """
    # 如果数据库不可用，返回预设的模拟数据
    if not DB_AVAILABLE:
        return [
            {
                'title': '情绪管理技巧',
                'content': '深呼吸是最简单的情绪调节方法。当感到焦虑时，尝试4-7-8呼吸法：吸气4秒，屏住呼吸7秒，呼气8秒。',
                'category': '情绪管理'
            },
            {
                'title': '如何应对压力',
                'content': '压力是生活的一部分，但我们可以学会管理它。尝试时间管理、适度运动、充足睡眠等方法。',
                'category': '压力缓解'
            }
        ]
    
    # 从数据库查询
    try:
        results = query_db("""
            SELECT title, content, category 
            FROM knowledge_base 
            WHERE title LIKE %s OR content LIKE %s OR tags LIKE %s
            LIMIT 5
        """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
        
        return results if results else []
    except Exception as e:
        print(f"知识库查询失败: {e}")
        return []

# ================================================================================
# 第七部分：AI对话会话类
# ================================================================================

class AIConversation:
    """
    AI对话会话类
    
    功能: 管理用户与AI医生之间的对话会话
    
    属性:
        user_id: 用户ID
        doctor_type: 医生类型
        history: 对话历史列表
        created_at: 会话创建时间
        conversation_id: 数据库中的会话ID
    
    使用示例:
        conv = AIConversation(user_id=1, doctor_type='gentle')
        response = conv.chat("我今天心情不好")
        print(response['response'])
    """
    
    def __init__(self, user_id, doctor_type='gentle'):
        """
        初始化对话会话
        
        参数:
            user_id: 用户ID
            doctor_type: AI医生类型，默认为'gentle'
        """
        self.user_id = user_id                    # 用户ID
        self.doctor_type = doctor_type            # 医生类型
        self.history = []                          # 对话历史
        self.created_at = datetime.now()           # 创建时间
        
        # 获取或创建会话ID
        if DB_AVAILABLE:
            try:
                # 在数据库中创建新会话
                self.conversation_id = execute_db(
                    "INSERT INTO conversations (user_id, doctor_type) VALUES (%s, %s)",
                    (user_id, doctor_type)
                )
            except:
                # 如果创建失败，设为None
                self.conversation_id = None
        else:
            self.conversation_id = None
    
    def add_message(self, role, content):
        """
        添加消息到对话历史
        
        参数:
            role: 消息角色 ('user' 或 'assistant')
            content: 消息内容
        """
        # 添加到内存历史
        self.history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # 保存到数据库（如果可用）
        if DB_AVAILABLE and self.conversation_id:
            try:
                execute_db(
                    "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
                    (self.conversation_id, role, content)
                )
            except:
                pass
    
    def chat(self, user_message):
        """
        处理用户消息，返回AI回复
        
        功能: 核心对话方法，处理用户输入并生成AI回复
        
        参数:
            user_message: 用户输入的消息
        
        返回值:
            dict: 包含以下键值对
                - response: AI回复内容
                - emotion: 检测到的用户情绪
                - risk_info: 风险分析信息
                - is_risk_response: 是否为风险响应
        """
        # 步骤1: 添加用户消息到历史
        self.add_message('user', user_message)
        
        # 步骤2: 生成回复
        result = generate_response(user_message, self.history, self.doctor_type)
        
        # 步骤3: 添加AI回复到历史
        self.add_message('assistant', result['response'])
        
        # 步骤4: 如果检测到风险，创建预警记录
        if result.get('risk_info', {}).get('needs_alert'):
            self.create_risk_alert(user_message, result['risk_info'])
        
        return result
    
    def create_risk_alert(self, trigger_content, risk_info):
        """
        创建风险预警记录
        
        功能: 当检测到高风险时，在数据库中创建预警记录
        
        参数:
            trigger_content: 触发预警的用户消息
            risk_info: 风险分析信息字典
        """
        # 如果数据库不可用，只打印警告
        if not DB_AVAILABLE:
            print(f"风险预警: {risk_info['risk_level']} - {trigger_content[:50]}")
            return
        
        try:
            # 插入风险预警记录
            execute_db("""
                INSERT INTO risk_alerts (user_id, conversation_id, risk_level, risk_type, content)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                self.user_id,
                self.conversation_id,
                risk_info['risk_level'],
                risk_info.get('risk_type'),
                trigger_content
            ))
        except:
            pass
    
    def get_history(self, limit=20):
        """
        获取对话历史
        
        参数:
            limit: 返回的消息数量限制，默认20条
        
        返回值:
            list: 历史消息列表
        """
        return self.history[-limit:]
    
    def clear_history(self):
        """
        清空对话历史
        
        功能: 清除内存中的对话历史（不会删除数据库中的记录）
        """
        self.history = []


# ================================================================================
# 第八部分：主函数（测试用）
# ================================================================================

def main():
    """
    测试AI医生功能
    
    功能: 演示AI对话系统的基本功能
    
    执行流程:
        1. 创建对话会话
        2. 发送测试消息
        3. 打印AI回复和情绪检测结果
    """
    print("=" * 50)
    print("AI情绪愈疗医生测试")
    print("=" * 50)
    
    # 创建对话会话
    conv = AIConversation(user_id=1, doctor_type='gentle')
    
    # 测试对话消息列表
    test_messages = [
        "我今天工作压力很大，感觉很焦虑",
        "谢谢你的倾听，好多了",
        "我最近总是失眠",
    ]
    
    # 遍历测试消息
    for msg in test_messages:
        print(f"\n用户: {msg}")
        
        # 发送消息并获取回复
        response = conv.chat(msg)
        
        # 打印AI回复
        print(f"AI医生: {response['response']}")
        
        # 打印情绪检测结果
        print(f"检测情绪: {response['emotion']}")


# 程序入口
if __name__ == '__main__':
    main()

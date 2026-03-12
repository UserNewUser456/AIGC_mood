"""
对话系统路由
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Conversation, Message, User, db
from datetime import datetime
import json

conversation_bp = Blueprint('conversation', __name__)

# 医生形象配置
DOCTOR_PROFILES = {
    'gentle': {
        'name': '温柔医生',
        'description': '以温暖、关怀的方式提供支持',
        'prompt': '你是一位温柔体贴的心理医生，用温暖的语言给予用户情感支持。'
    },
    'rational': {
        'name': '理性医生', 
        'description': '以逻辑分析帮助用户理解情绪',
        'prompt': '你是一位理性客观的心理医生，帮助用户分析情绪背后的原因。'
    },
    'humorous': {
        'name': '幽默医生',
        'description': '用幽默的方式缓解用户压力',
        'prompt': '你是一位幽默风趣的心理医生，用轻松的方式帮助用户缓解压力。'
    }
}

@conversation_bp.route('/doctors', methods=['GET'])
def get_doctors():
    """获取可用医生列表"""
    doctors = []
    for doctor_type, profile in DOCTOR_PROFILES.items():
        doctors.append({
            'doctor_type': doctor_type,
            'name': profile['name'],
            'description': profile['description']
        })
    return jsonify({
        "success": True,
        "doctors": doctors
    })

@conversation_bp.route('', methods=['POST'])
@jwt_required()
def create_conversation():
    """创建新对话会话"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证医生类型
        doctor_type = data.get('doctor_type', 'gentle')
        if doctor_type not in DOCTOR_PROFILES:
            return jsonify({"success": False, "message": "不支持的医生类型"}), 400
        
        # 创建对话会话
        conversation = Conversation(
            user_id=current_user_id,
            doctor_type=doctor_type,
            title=f"与{DOCTOR_PROFILES[doctor_type]['name']}的对话"
        )
        
        db.session.add(conversation)
        db.session.commit()
        
        # 添加系统欢迎消息
        welcome_message = Message(
            conversation_id=conversation.id,
            role='system',
            content=f"我是{DOCTOR_PROFILES[doctor_type]['name']}，{DOCTOR_PROFILES[doctor_type]['description']}。今天有什么想和我分享的吗？"
        )
        
        db.session.add(welcome_message)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "对话创建成功",
            "conversation": conversation.to_dict(),
            "welcome_message": welcome_message.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@conversation_bp.route('', methods=['GET'])
@jwt_required()
def get_conversations():
    """获取用户对话列表"""
    try:
        current_user_id = get_jwt_identity()
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 查询对话列表
        conversations = Conversation.query.filter_by(user_id=current_user_id) \
            .order_by(Conversation.updated_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "success": True,
            "conversations": [conv.to_dict() for conv in conversations.items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": conversations.total,
                "pages": conversations.pages
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@conversation_bp.route('/<int:conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation(conversation_id):
    """获取对话详情"""
    try:
        current_user_id = get_jwt_identity()
        
        # 验证对话所有权
        conversation = Conversation.query.filter_by(
            id=conversation_id, 
            user_id=current_user_id
        ).first()
        
        if not conversation:
            return jsonify({"success": False, "message": "对话不存在"}), 404
        
        # 获取消息列表
        messages = Message.query.filter_by(conversation_id=conversation_id) \
            .order_by(Message.created_at.asc()) \
            .all()
        
        return jsonify({
            "success": True,
            "conversation": conversation.to_dict(),
            "messages": [msg.to_dict() for msg in messages]
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@conversation_bp.route('/<int:conversation_id>/messages', methods=['POST'])
@jwt_required()
def send_message(conversation_id):
    """发送用户消息并获取AI回复"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证对话所有权
        conversation = Conversation.query.filter_by(
            id=conversation_id, 
            user_id=current_user_id
        ).first()
        
        if not conversation:
            return jsonify({"success": False, "message": "对话不存在"}), 404
        
        # 验证消息内容
        content = data.get('content', '').strip()
        if not content:
            return jsonify({"success": False, "message": "消息内容不能为空"}), 400
        
        # 保存用户消息
        user_message = Message(
            conversation_id=conversation_id,
            role='user',
            content=content
        )
        
        db.session.add(user_message)
        
        # 检测情绪（简化版）
        emotion_info = detect_emotion(content)
        
        # 生成AI回复
        ai_reply = generate_ai_reply(conversation, content, emotion_info)
        
        # 保存AI回复
        ai_message = Message(
            conversation_id=conversation_id,
            role='assistant',
            content=ai_reply,
            emotion_detected=emotion_info.get('emotion'),
            score_detected=emotion_info.get('score')
        )
        
        db.session.add(ai_message)
        
        # 更新对话时间
        conversation.updated_at = datetime.utcnow()
        
        # 检测风险（如果情绪异常）
        if emotion_info.get('risk_level') in ['high', 'critical']:
            create_risk_alert(current_user_id, conversation_id, content, emotion_info)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "user_message": user_message.to_dict(),
            "ai_reply": ai_message.to_dict(),
            "emotion_detected": emotion_info
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

def detect_emotion(text):
    """简化版情绪检测"""
    # 关键词匹配（实际项目中应使用更复杂的NLP模型）
    positive_words = ['开心', '高兴', '快乐', '幸福', '满意', '放松', '平静']
    negative_words = ['难过', '伤心', '悲伤', '痛苦', '焦虑', '紧张', '压力', '害怕', '恐惧']
    risk_words = ['自杀', '自伤', '不想活', '结束一切', '绝望']
    
    text_lower = text.lower()
    
    # 检测风险词
    for word in risk_words:
        if word in text_lower:
            return {
                'emotion': '严重负面',
                'score': 1.0,
                'risk_level': 'critical',
                'risk_type': 'suicide'
            }
    
    # 情绪分析
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        score = min(10, 5 + positive_count * 0.5)
        return {'emotion': '正面', 'score': score, 'risk_level': 'low'}
    elif negative_count > positive_count:
        score = max(0, 5 - negative_count * 0.5)
        risk_level = 'high' if negative_count > 3 else 'medium'
        return {'emotion': '负面', 'score': score, 'risk_level': risk_level}
    else:
        return {'emotion': '中性', 'score': 5.0, 'risk_level': 'low'}

def generate_ai_reply(conversation, user_message, emotion_info):
    """生成AI回复（调用阿里云百炼平台LLM）"""
    import requests
    
    doctor_profile = DOCTOR_PROFILES[conversation.doctor_type]
    
    # 如果是严重风险，直接返回风险提示
    if emotion_info.get('risk_level') == 'critical':
        return f"{doctor_profile['name']}：我注意到您正在经历非常困难的时刻。请立即联系专业心理咨询师或拨打心理援助热线。您不是一个人在战斗，寻求帮助是勇敢的表现。"
    
    # 构建消息
    messages = [
        {"role": "system", "content": doctor_profile['prompt']}
    ]
    
    # 获取对话历史
    recent_messages = Message.query.filter_by(
        conversation_id=conversation.id
    ).order_by(Message.created_at).limit(10).all()
    
    for msg in recent_messages:
        role = "user" if msg.role == "user" else "assistant"
        messages.append({"role": role, "content": msg.content})
    
    # 添加当前用户消息
    messages.append({"role": "user", "content": user_message})
    
    # 调用阿里云百炼平台API
    try:
        response = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers={
                "Authorization": "Bearer sk-cd1941be1ff64ce58eddb6e7bb69de71",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen-plus",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"LLM API调用失败: {response.status_code}")
    except Exception as e:
        print(f"LLM API异常: {e}")
    
    # 如果API调用失败，使用简化版回复作为后备
    if emotion_info.get('risk_level') == 'high':
        return f"{doctor_profile['name']}：听起来您正在经历很大的压力。让我们一起来面对这些挑战。您可以尝试深呼吸放松，或者告诉我更多关于您的感受。"
    elif emotion_info.get('emotion') == '正面':
        return f"{doctor_profile['name']}：很高兴听到您有积极的情绪！继续保持这种状态很重要。是什么让您感到开心呢？"
    elif emotion_info.get('emotion') == '负面':
        return f"{doctor_profile['name']}：我理解您现在可能感到有些困扰。每个人都会有情绪波动的时候，让我们一起来探索这些感受。"
    else:
        return f"{doctor_profile['name']}：感谢您与我分享。为了更好地理解您的情况，能告诉我更多关于您最近的生活和感受吗？"

def create_risk_alert(user_id, conversation_id, content, emotion_info):
    """创建风险预警"""
    from models import RiskAlert
    
    risk_alert = RiskAlert(
        user_id=user_id,
        conversation_id=conversation_id,
        risk_level=emotion_info.get('risk_level', 'low'),
        risk_type=emotion_info.get('risk_type', 'emotional_distress'),
        content=content
    )
    
    db.session.add(risk_alert)
    # 注意：这里不立即提交，由调用方统一提交

from flask import Response, stream_with_context

@conversation_bp.route('/<int:conversation_id>/messages/stream', methods=['POST'])
@jwt_required()
def send_message_stream(conversation_id):
    """发送消息并获取AI流式回复"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证对话所有权
        conversation = Conversation.query.filter_by(
            id=conversation_id, 
            user_id=current_user_id
        ).first()
        
        if not conversation:
            return jsonify({"success": False, "message": "对话不存在"}), 404
        
        content = data.get('content', '').strip()
        if not content:
            return jsonify({"success": False, "message": "消息内容不能为空"}), 400
        
        # 保存用户消息
        user_message = Message(
            conversation_id=conversation_id,
            role='user',
            content=content
        )
        db.session.add(user_message)
        db.session.commit()
        
        # 检测情绪
        emotion_info = detect_emotion(content)
        
        # 流式生成回复
        def generate():
            doctor_profile = DOCTOR_PROFILES[conversation.doctor_type]
            full_reply = ""
            
            # 如果是严重风险，直接返回提示
            if emotion_info.get('risk_level') == 'critical':
                reply = f"{doctor_profile['name']}：我注意到您正在经历非常困难的时刻。请立即联系专业心理咨询师或拨打心理援助热线。"
                for char in reply:
                    full_reply += char
                    yield f"data: {json.dumps({'content': char})}\n\n"
            else:
                # 构建消息
                messages = [
                    {"role": "system", "content": doctor_profile['prompt']}
                ]
                
                # 获取对话历史
                recent_messages = Message.query.filter_by(
                    conversation_id=conversation.id
                ).order_by(Message.created_at).limit(10).all()
                
                for msg in recent_messages:
                    role = "user" if msg.role == "user" else "assistant"
                    messages.append({"role": role, "content": msg.content})
                
                messages.append({"role": "user", "content": content})
                
                # 流式调用LLM API
                try:
                    import requests
                    response = requests.post(
                        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                        headers={
                            "Authorization": "Bearer sk-cd1941be1ff64ce58eddb6e7bb69de71",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "qwen-plus",
                            "messages": messages,
                            "temperature": 0.7,
                            "max_tokens": 500,
                            "stream": True
                        },
                        stream=True,
                        timeout=30
                    )
                    
                    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk:
                            # 解析SSE流
                            lines = chunk.split('\n')
                            for line in lines:
                                if line.startswith('data: '):
                                    data_str = line[6:]
                                    if data_str.strip() and data_str != '[DONE]':
                                        try:
                                            delta = json.loads(data_str)
                                            content = delta.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                            if content:
                                                full_reply += content
                                                yield f"data: {json.dumps({'content': content})}\n\n"
                                        except:
                                            pass
                                            
                except Exception as e:
                    print(f"LLM流式API异常: {e}")
                    # 后备回复
                    fallback = f"{doctor_profile['name']}：感谢您的分享。我在这里倾听您。"
                    for char in fallback:
                        full_reply += char
                        yield f"data: {json.dumps({'content': char})}\n\n"
            
            # 保存AI完整回复到数据库
            ai_message = Message(
                conversation_id=conversation_id,
                role='assistant',
                content=full_reply,
                emotion_detected=emotion_info.get('emotion'),
                score_detected=emotion_info.get('score')
            )
            db.session.add(ai_message)
            
            # 更新对话时间
            conversation.updated_at = datetime.utcnow()
            
            # 检测风险
            if emotion_info.get('risk_level') in ['high', 'critical']:
                create_risk_alert(current_user_id, conversation_id, content, emotion_info)
            
            db.session.commit()
            
            yield f"data: {json.dumps({'done': True, 'emotion': emotion_info})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            content_type='text/event-stream; charset=utf-8',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no-cache'
            }
        )
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@conversation_bp.route('/<int:conversation_id>', methods=['DELETE'])
@jwt_required()
def delete_conversation(conversation_id):
    """删除对话"""
    try:
        current_user_id = get_jwt_identity()
        
        # 验证对话所有权
        conversation = Conversation.query.filter_by(
            id=conversation_id, 
            user_id=current_user_id
        ).first()
        
        if not conversation:
            return jsonify({"success": False, "message": "对话不存在"}), 404
        
        # 删除相关消息
        Message.query.filter_by(conversation_id=conversation_id).delete()
        
        # 删除对话
        db.session.delete(conversation)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "对话删除成功"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
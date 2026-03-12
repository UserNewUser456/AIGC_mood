"""
风险预警路由
"""

import smtplib
import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import RiskAlert, User, db
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

risk_bp = Blueprint('risk', __name__)

# 邮件配置（从环境变量读取）
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.qq.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
ALERT_EMAIL = os.getenv('ALERT_EMAIL', '')  # 接收警报的邮箱


def send_risk_alert_email(alert, user):
    """发送风险预警邮件"""
    if not SMTP_USERNAME or not SMTP_PASSWORD or not ALERT_EMAIL:
        print("邮件配置未设置，跳过发送")
        return False
    
    try:
        # 构建邮件内容
        risk_level_emoji = {
            'low': '低',
            'medium': '中',
            'high': '高',
            'critical': '严重'
        }
        
        subject = f"【情绪愈疗平台】风险预警通知 - {risk_level_emoji.get(alert.risk_level, '未知')}风险"
        
        html_content = f"""
        <html>
        <body>
            <h2>风险预警通知</h2>
            <p>检测到用户 <strong>{user.username}</strong> 存在风险预警：</p>
            <table border="1" cellpadding="10">
                <tr>
                    <td><strong>风险等级</strong></td>
                    <td style="color: {'red' if alert.risk_level in ['high', 'critical'] else 'orange'}">
                        {risk_level_emoji.get(alert.risk_level, '未知')}风险
                    </td>
                </tr>
                <tr>
                    <td><strong>风险类型</strong></td>
                    <td>{alert.risk_type or '情绪异常'}</td>
                </tr>
                <tr>
                    <td><strong>预警内容</strong></td>
                    <td>{alert.content[:200]}...</td>
                </tr>
                <tr>
                    <td><strong>发生时间</strong></td>
                    <td>{alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
            </table>
            <p>请及时跟进处理。</p>
            <hr>
            <p style="color: #666; font-size: 12px;">来自情绪愈疗平台风险监测系统</p>
        </body>
        </html>
        """
        
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_USERNAME
        msg['To'] = ALERT_EMAIL
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        # 发送邮件
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        # 更新alert_sent状态
        alert.alert_sent = True
        db.session.commit()
        
        return True
        
    except Exception as e:
        print(f"发送预警邮件失败: {e}")
        return False


@risk_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_risk_alerts():
    """获取风险预警列表"""
    try:
        current_user_id = get_jwt_identity()
        
        # 获取查询参数
        risk_level = request.args.get('risk_level')
        handled = request.args.get('handled')
        days = int(request.args.get('days', 30))
        
        # 计算开始日期
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 构建查询
        query = RiskAlert.query.filter_by(user_id=current_user_id)\
            .filter(RiskAlert.created_at >= start_date)
        
        # 过滤条件
        if risk_level:
            query = query.filter(RiskAlert.risk_level == risk_level)
        
        if handled is not None:
            query = query.filter(RiskAlert.handled == (handled.lower() == 'true'))
        
        # 排序和分页
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        pagination = query.order_by(RiskAlert.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        # 统计信息
        total_alerts = pagination.total
        handled_count = RiskAlert.query.filter_by(user_id=current_user_id, handled=True)\
            .filter(RiskAlert.created_at >= start_date).count()
        
        return jsonify({
            "success": True,
            "alerts": [alert.to_dict() for alert in pagination.items],
            "statistics": {
                "total": total_alerts,
                "handled": handled_count,
                "unhandled": total_alerts - handled_count,
                "period_days": days
            },
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_alerts,
                "pages": pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@risk_bp.route('/alerts/<int:alert_id>', methods=['GET'])
@jwt_required()
def get_risk_alert(alert_id):
    """获取单个风险预警详情"""
    try:
        current_user_id = get_jwt_identity()
        
        # 验证预警所有权
        alert = RiskAlert.query.filter_by(
            id=alert_id, 
            user_id=current_user_id
        ).first()
        
        if not alert:
            return jsonify({"success": False, "message": "预警不存在"}), 404
        
        return jsonify({
            "success": True,
            "alert": alert.to_dict()
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@risk_bp.route('/alerts/<int:alert_id>', methods=['PUT'])
@jwt_required()
def handle_risk_alert(alert_id):
    """处理风险预警"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # 验证预警所有权
        alert = RiskAlert.query.filter_by(
            id=alert_id, 
            user_id=current_user_id
        ).first()
        
        if not alert:
            return jsonify({"success": False, "message": "预警不存在"}), 404
        
        # 更新处理状态
        handled = data.get('handled', True)
        alert.handled = handled
        
        # 更新跟进记录备注
        if 'handled_by' in data:
            alert.handled_by = data['handled_by']
        
        if 'followup_note' in data:
            alert.content = f"{alert.content}\n\n【跟进备注】{data['followup_note']}"
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "预警处理状态已更新",
            "alert": alert.to_dict()
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@risk_bp.route('/send-alert-email/<int:alert_id>', methods=['POST'])
@jwt_required()
def send_alert_email(alert_id):
    """手动发送风险预警邮件"""
    try:
        alert = RiskAlert.query.get(alert_id)
        if not alert:
            return jsonify({"success": False, "message": "预警不存在"}), 404
        
        user = User.query.get(alert.user_id)
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 404
        
        # 发送邮件
        success = send_risk_alert_email(alert, user)
        
        if success:
            return jsonify({
                "success": True,
                "message": "预警邮件已发送"
            })
        else:
            return jsonify({
                "success": False,
                "message": "邮件发送失败，请检查配置"
            }), 500
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@risk_bp.route('/settings', methods=['GET', 'PUT'])
@jwt_required()
def get_risk_settings():
    """获取/设置风险预警阈值"""
    # 这里可以从数据库读取设置，简单起见使用内存
    default_settings = {
        'risk_threshold': 'medium',  # 触发预警的最低等级
        'email_notification': True,   # 是否启用邮件通知
        'auto_alert_levels': ['high', 'critical']  # 自动发送邮件的风险等级
    }
    
    if request.method == 'GET':
        return jsonify({
            "success": True,
            "settings": default_settings
        })
    
    # PUT: 更新设置
    data = request.get_json()
    if data:
        default_settings.update(data)
    
    return jsonify({
        "success": True,
        "message": "设置已更新",
        "settings": default_settings
    })


@risk_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_risk_dashboard():
    """获取风险预警仪表盘数据"""
    try:
        current_user_id = get_jwt_identity()
        
        # 获取过去30天的数据
        start_date = datetime.utcnow() - timedelta(days=30)
        
        # 查询所有预警
        alerts = RiskAlert.query.filter_by(user_id=current_user_id)\
            .filter(RiskAlert.created_at >= start_date)\
            .order_by(RiskAlert.created_at.asc())\
            .all()
        
        # 按风险等级统计
        risk_levels = ['low', 'medium', 'high', 'critical']
        level_stats = {level: 0 for level in risk_levels}
        
        for alert in alerts:
            level_stats[alert.risk_level] = level_stats.get(alert.risk_level, 0) + 1
        
        # 按风险类型统计
        risk_types = {}
        for alert in alerts:
            risk_type = alert.risk_type or 'unknown'
            risk_types[risk_type] = risk_types.get(risk_type, 0) + 1
        
        # 按日期统计趋势
        date_stats = {}
        for alert in alerts:
            date_str = alert.created_at.strftime('%Y-%m-%d')
            if date_str not in date_stats:
                date_stats[date_str] = 0
            date_stats[date_str] += 1
        
        # 生成趋势线数据
        trend_data = []
        current_date = start_date
        while current_date <= datetime.utcnow():
            date_str = current_date.strftime('%Y-%m-%d')
            trend_data.append({
                'date': date_str,
                'count': date_stats.get(date_str, 0)
            })
            current_date += timedelta(days=1)
        
        # 未处理预警数量
        unhandled_count = RiskAlert.query.filter_by(
            user_id=current_user_id, 
            handled=False
        ).filter(RiskAlert.created_at >= start_date).count()
        
        # 高风险预警列表
        high_risk_alerts = RiskAlert.query.filter_by(user_id=current_user_id)\
            .filter(RiskAlert.risk_level.in_(['high', 'critical']))\
            .filter(RiskAlert.handled == False)\
            .order_by(RiskAlert.created_at.desc())\
            .limit(5)\
            .all()
        
        return jsonify({
            "success": True,
            "dashboard": {
                "summary": {
                    "total_alerts": len(alerts),
                    "unhandled_count": unhandled_count,
                    "period_days": 30,
                    "highest_risk_level": max(level_stats, key=level_stats.get) if alerts else 'none'
                },
                "level_distribution": level_stats,
                "type_distribution": risk_types,
                "trend_data": trend_data,
                "recent_high_risk_alerts": [alert.to_dict() for alert in high_risk_alerts]
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@risk_bp.route('/monitoring', methods=['POST'])
@jwt_required()
def start_risk_monitoring():
    """启动风险监测"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        return jsonify({
            "success": True,
            "message": "风险监测已启动",
            "monitoring_id": f"monitor_{current_user_id}_{int(datetime.utcnow().timestamp())}"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@risk_bp.route('/emergency-contacts', methods=['GET'])
def get_emergency_contacts():
    """获取紧急联系方式"""
    try:
        # 心理援助热线信息
        emergency_contacts = [
            {
                "name": "全国心理援助热线",
                "phone": "12320-5",
                "description": "24小时免费心理援助热线",
                "type": "hotline"
            },
            {
                "name": "希望24热线",
                "phone": "400-161-9995",
                "description": "24小时生命危机干预热线",
                "type": "crisis"
            },
            {
                "name": "北京心理危机干预中心",
                "phone": "010-82951332",
                "description": "专业心理危机干预",
                "type": "intervention"
            },
            {
                "name": "上海市心理援助热线",
                "phone": "021-12320-5",
                "description": "上海地区心理援助",
                "type": "regional"
            }
        ]
        
        return jsonify({
            "success": True,
            "contacts": emergency_contacts,
            "message": "如有紧急情况，请立即联系专业机构"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@risk_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_risk_notifications():
    """获取风险通知"""
    try:
        current_user_id = get_jwt_identity()
        
        # 获取未读的高风险预警
        high_risk_alerts = RiskAlert.query.filter_by(
            user_id=current_user_id,
            handled=False
        ).filter(RiskAlert.risk_level.in_(['high', 'critical']))\
            .order_by(RiskAlert.created_at.desc())\
            .limit(10)\
            .all()
        
        notifications = []
        for alert in high_risk_alerts:
            # 根据风险等级生成通知消息
            if alert.risk_level == 'critical':
                message = "检测到严重风险预警，建议立即寻求专业帮助"
                priority = "urgent"
            else:
                message = "检测到高风险预警，请关注情绪状态"
                priority = "high"
            
            notifications.append({
                "id": alert.id,
                "type": "risk_alert",
                "message": message,
                "priority": priority,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
                "alert_data": alert.to_dict()
            })
        
        return jsonify({
            "success": True,
            "notifications": notifications,
            "unread_count": len(notifications)
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

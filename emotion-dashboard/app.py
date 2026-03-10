"""
情绪分析仪表盘 - Streamlit版本
独立Web应用：情绪变化折线图（过去7天/30天）
"""

import streamlit as st
import pymysql
import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from streamlit_echarts import st_echarts

load_dotenv()

# ==================== 数据库配置 ====================
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'emotion_db'),
    'charset': 'utf8mb4'
}

# ==================== 数据库操作 ====================
def get_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def init_database():
    """初始化数据库和表"""
    # 先连接不带数据库，创建数据库
    config_no_db = {k: v for k, v in DB_CONFIG.items() if k != 'database'}
    conn = pymysql.connect(**config_no_db)
    try:
        with conn.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS emotion_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
    finally:
        conn.close()
    
    # 连接数据库创建表
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emotion_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(64) NOT NULL,
                    emotion VARCHAR(32) NOT NULL,
                    score FLOAT NOT NULL,
                    text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        conn.commit()
    finally:
        conn.close()

def save_emotion(user_id, emotion, score, text=''):
    """保存情绪记录"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO emotion_records (user_id, emotion, score, text) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (user_id, emotion, score, text))
            conn.commit()
            return {'id': cursor.lastrowid, 'emotion': emotion}
    finally:
        conn.close()

def get_emotion_data(user_id, days=7):
    """获取历史情绪数据"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT id, user_id, emotion, score, text, created_at 
                FROM emotion_records 
                WHERE user_id = %s AND created_at >= %s
                ORDER BY created_at ASC
            """
            start_date = datetime.now() - timedelta(days=days)
            cursor.execute(sql, (user_id, start_date))
            results = cursor.fetchall()
            
            # 转换为DataFrame
            df = pd.DataFrame(results, columns=['id', 'user_id', 'emotion', 'score', 'text', 'created_at'])
            if not df.empty:
                df['date'] = df['created_at'].dt.strftime('%Y-%m-%d')
                df['time'] = df['created_at'].dt.strftime('%H:%M')
            return df
    finally:
        conn.close()

def get_mock_data(days=7):
    """生成模拟数据用于演示"""
    import random
    
    emotions = ['开心', '平静', '焦虑', '悲伤', '愤怒', '兴奋']
    data = []
    
    for i in range(days * 3):  # 每天3条记录
        date = datetime.now() - timedelta(hours=i*8)
        emotion = random.choice(emotions)
        score = random.uniform(4.0, 9.5)
        data.append({
            'id': i + 1,
            'user_id': 'demo_user',
            'emotion': emotion,
            'score': round(score, 1),
            'text': f'今日情绪记录 #{i+1}',
            'created_at': date,
            'date': date.strftime('%Y-%m-%d'),
            'time': date.strftime('%H:%M')
        })
    
    return pd.DataFrame(data)

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="情绪分析仪表盘",
    page_icon="📊",
    layout="wide"
)

# ==================== 样式设置 ====================
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    .card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .title {
        color: #2c3e50;
        font-size: 28px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 30px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== 主应用 ====================
def main():
    # 标题
    st.markdown('<p class="title">📊 情绪分析仪表盘</p>', unsafe_allow_html=True)
    
    # 侧边栏 - 用户设置
    with st.sidebar:
        st.header("👤 用户设置")
        
        # 用户ID输入
        user_id = st.text_input("用户ID", value="demo_user")
        
        # 数据来源选择
        data_source = st.radio("数据来源", ["演示数据", "数据库"], index=0)
        
        st.divider()
        
        # 数据录入区域
        st.subheader("📝 记录情绪")
        
        emotion_options = ['开心', '平静', '焦虑', '悲伤', '愤怒', '兴奋', '沮丧', '放松']
        selected_emotion = st.selectbox("选择情绪", emotion_options)
        
        # 情绪到分数的映射
        emotion_scores = {
            '开心': 8.5, '平静': 7.0, '焦虑': 4.5, '悲伤': 3.5,
            '愤怒': 3.0, '兴奋': 8.0, '沮丧': 4.0, '放松': 7.5
        }
        
        score = st.slider("情绪分数", 0.0, 10.0, emotion_scores[selected_emotion], 0.5)
        emotion_text = st.text_area("备注（可选）", placeholder="今天发生了什么事？")
        
        if st.button("💾 保存记录", type="primary"):
            if data_source == "数据库":
                try:
                    result = save_emotion(user_id, selected_emotion, score, emotion_text)
                    st.success(f"✅ 情绪记录已保存！ID: {result['id']}")
                except Exception as e:
                    st.error(f"❌ 保存失败: {str(e)}")
            else:
                st.warning("演示模式下不能保存到数据库")
    
    # 主内容区
    # 时间范围选择
    col1, col2 = st.columns([3, 1])
    with col1:
        days = st.select_slider(
            "📅 选择时间范围",
            options=[7, 14, 30, 90],
            value=7,
            format_func=lambda x: f"过去 {x} 天"
        )
    
    # 获取数据
    if data_source == "数据库":
        try:
            df = get_emotion_data(user_id, days)
        except Exception as e:
            st.warning(f"数据库连接失败，使用演示数据: {str(e)}")
            df = get_mock_data(days)
    else:
        df = get_mock_data(days)
    
    # 显示数据统计
    if not df.empty:
        # 转换为日期格式用于分组
        df['date'] = pd.to_datetime(df['date'])
        
        # 按日期分组计算平均分
        daily_avg = df.groupby('date')['score'].mean().reset_index()
        daily_avg['date_str'] = daily_avg['date'].dt.strftime('%m-%d')
        
        # 指标卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_score = df['score'].mean()
            st.metric("📈 平均情绪分", f"{avg_score:.1f}/10", 
                     delta=f"{avg_score - 5:.1f}" if avg_score else None)
        
        with col2:
            total_records = len(df)
            st.metric("📝 记录条数", total_records)
        
        with col3:
            dominant_emotion = df['emotion'].mode().iloc[0] if not df.empty else "无"
            st.metric("😊 主要情绪", dominant_emotion)
        
        with col4:
            score_std = df['score'].std() if len(df) > 1 else 0
            volatility = "稳定" if score_std < 1.5 else "波动较大"
            st.metric("🎯 情绪稳定性", volatility)
        
        st.markdown("---")
        
        # ==================== 情绪变化折线图 ====================
        st.subheader(f"📉 情绪变化趋势 (过去 {days} 天)")
        
        # 准备ECharts配置
        dates = daily_avg['date_str'].tolist()
        scores = [round(s, 2) for s in daily_avg['score'].tolist()]
        
        # 获取每日主要情绪
        daily_emotions = df.groupby('date')['emotion'].agg(lambda x: x.mode().iloc[0]).reset_index()
        daily_emotions['date_str'] = daily_emotions['date'].dt.strftime('%m-%d')
        emotion_map = dict(zip(daily_emotions['date_str'], daily_emotions['emotion']))
        
        # ECharts配置
        option = {
            "tooltip": {
                "trigger": "axis",
                "formatter": function(params):
                    score = params[0].value
                    emotion = emotion_map.get(params[0].name, '')
                    return f"{params[0].name}<br/>情绪分数: <b>{score}</b><br/>主要情绪: {emotion}"
            },
            "grid": {
                "left": "3%",
                "right": "4%",
                "bottom": "3%",
                "containLabel": True
            },
            "xAxis": {
                "type": "category",
                "boundaryGap": False,
                "data": dates,
                "axisLine": {"lineStyle": {"color": "#888"}},
                "axisLabel": {"color": "#666"}
            },
            "yAxis": {
                "type": "value",
                "min": 0,
                "max": 10,
                "interval": 2,
                "axisLine": {"lineStyle": {"color": "#888"}},
                "splitLine": {"lineStyle": {"color": "#eee"}}
            },
            "series": [
                {
                    "name": "情绪分数",
                    "type": "line",
                    "smooth": True,
                    "symbol": "circle",
                    "symbolSize": 10,
                    "data": scores,
                    "lineStyle": {
                        "width": 3,
                        "color": {
                            "type": "linear",
                            "x": 0, "y": 0, "x2": 1, "y2": 0,
                            "colorStops": [
                                {"offset": 0, "color": "#667eea"},
                                {"offset": 1, "color": "#764ba2"}
                            ]
                        }
                    },
                    "areaStyle": {
                        "color": {
                            "type": "linear",
                            "x": 0, "y": 0, "x2": 0, "y2": 1,
                            "colorStops": [
                                {"offset": 0, "color": "rgba(102, 126, 234, 0.4)"},
                                {"offset": 1, "color": "rgba(118, 75, 162, 0.1)"}
                            ]
                        }
                    },
                    "itemStyle": {
                        "color": "#764ba2",
                        "borderWidth": 2,
                        "borderColor": "#fff"
                    },
                    "markLine": {
                        "data": [
                            {"yAxis": 5, "name": "中性"},
                            {"yAxis": 7, "name": "良好"},
                        ],
                        "lineStyle": {"type": "dashed", "color": "#999"}
                    }
                }
            ]
        }
        
        # 渲染图表
        st_echarts(options=option, height=400)
        
        # ==================== 详细数据表格 ====================
        st.markdown("---")
        st.subheader("📋 详细记录")
        
        # 格式化显示数据
        display_df = df[['date', 'time', 'emotion', 'score', 'text']].copy()
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        display_df = display_df.sort_values('created_at', ascending=False)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
    else:
        st.info("📭 暂无情绪记录，请先记录您的情绪！")

if __name__ == "__main__":
    # 尝试初始化数据库
    try:
        init_database()
    except Exception as e:
        print(f"数据库初始化跳过: {e}")
    
    main()

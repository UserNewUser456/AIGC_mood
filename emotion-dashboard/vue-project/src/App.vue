<template>
  <div class="app">
    <h1>🌸 情绪愈疗平台</h1>
    
    <!-- 用户区域 -->
    <div class="user-section">
      <input 
        v-model="username" 
        placeholder="请输入用户名"
        @keyup.enter="initUser"
      >
      <button @click="initUser">开始</button>
    </div>
    
    <!-- 主要内容 -->
    <div v-if="userId" class="main-content">
      <!-- 情绪输入 -->
      <div class="emotion-input">
        <h2>记录今日情绪</h2>
        <select v-model="selectedEmotion">
          <option value="开心">开心 😄</option>
          <option value="平静">平静 😌</option>
          <option value="焦虑">焦虑 😰</option>
          <option value="悲伤">悲伤 😢</option>
          <option value="愤怒">愤怒 😠</option>
          <option value="兴奋">兴奋 🤩</option>
        </select>
        <input 
          type="number" 
          v-model.number="emotionScore" 
          min="0" 
          max="10" 
          placeholder="分数 0-10"
        >
        <input 
          v-model="emotionText" 
          placeholder="备注（可选）"
        >
        <button @click="submitEmotion">保存</button>
      </div>
      
      <!-- 统计卡片 -->
      <div class="stats">
        <div class="stat-card">
          <span>记录数</span>
          <strong>{{ stats.totalRecords }}</strong>
        </div>
        <div class="stat-card">
          <span>平均分</span>
          <strong>{{ stats.avgScore }}</strong>
        </div>
        <div class="stat-card">
          <span>主要情绪</span>
          <strong>{{ stats.dominantEmotion || '-' }}</strong>
        </div>
      </div>
      
      <!-- 历史记录 -->
      <div class="history">
        <h2>历史记录</h2>
        <ul>
          <li v-for="item in history" :key="item.id">
            <span>{{ item.created_at?.split('T')[0] }}</span>
            <span>{{ item.emotion }}</span>
            <span>{{ item.score }}分</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'App',
  setup() {
    // 用户名
    const username = ref('')
    const userId = ref(null)
    
    // 情绪输入
    const selectedEmotion = ref('开心')
    const emotionScore = ref(7)
    const emotionText = ref('')
    
    // 数据
    const history = ref([])
    const stats = ref({
      totalRecords: 0,
      avgScore: 0,
      dominantEmotion: ''
    })
    
    // 初始化用户
    const initUser = async () => {
      if (!username.value.trim()) return
      
      try {
        // 先尝试创建用户
        const res = await axios.post('/api/users', {
          username: username.value,
          user_type: 'anonymous'
        }).catch(() => ({ data: { user_id: 1 } }))
        
        // 模拟用户ID（实际应从后端返回）
        userId.value = res.data?.user_id || 1
        
        // 加载数据
        loadData()
      } catch (e) {
        console.error(e)
        // 使用模拟数据
        userId.value = 1
        loadMockData()
      }
    }
    
    // 加载数据
    const loadData = async () => {
      if (!userId.value) return
      
      try {
        const [historyRes, statsRes] = await Promise.all([
          axios.get(`/api/emotion/history?user_id=${userId.value}&days=7`),
          axios.get(`/api/emotion/stats?user_id=${userId.value}&days=7`)
        ])
        
        history.value = historyRes.data?.data || []
        stats.value = statsRes.data?.data || stats.value
      } catch (e) {
        loadMockData()
      }
    }
    
    // 加载模拟数据
    const loadMockData = () => {
      history.value = [
        { id: 1, created_at: '2024-01-07', emotion: '开心', score: 8.5 },
        { id: 2, created_at: '2024-01-06', emotion: '平静', score: 7.0 },
        { id: 3, created_at: '2024-01-05', emotion: '焦虑', score: 4.5 },
        { id: 4, created_at: '2024-01-04', emotion: '悲伤', score: 3.5 },
      ]
      stats.value = {
        totalRecords: 4,
        avgScore: 5.9,
        dominantEmotion: '开心'
      }
    }
    
    // 提交情绪
    const submitEmotion = async () => {
      if (!emotionScore.value || emotionScore.value < 0 || emotionScore.value > 10) {
        alert('请输入0-10之间的分数')
        return
      }
      
      try {
        await axios.post('/api/emotion', {
          user_id: userId.value,
          emotion: selectedEmotion.value,
          score: emotionScore.value,
          text: emotionText.value
        })
        
        // 重新加载数据
        await loadData()
        
        // 重置输入
        emotionText.value = ''
        alert('保存成功！')
      } catch (e) {
        alert('保存失败，请重试')
      }
    }
    
    return {
      username,
      userId,
      selectedEmotion,
      emotionScore,
      emotionText,
      history,
      stats,
      initUser,
      submitEmotion
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: Arial, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 20px;
}

.app {
  max-width: 600px;
  margin: 0 auto;
}

h1 {
  text-align: center;
  color: white;
  margin-bottom: 30px;
}

.user-section {
  background: white;
  padding: 20px;
  border-radius: 10px;
  display: flex;
  gap: 10px;
}

.user-section input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 16px;
}

.user-section button {
  padding: 10px 20px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.main-content {
  margin-top: 20px;
}

.emotion-input {
  background: white;
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 20px;
}

.emotion-input h2 {
  margin-bottom: 15px;
  color: #333;
}

.emotion-input select,
.emotion-input input {
  width: 100%;
  padding: 10px;
  margin-bottom: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 16px;
}

.emotion-input button {
  width: 100%;
  padding: 12px;
  background: #67c23a;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  padding: 15px;
  border-radius: 10px;
  text-align: center;
}

.stat-card span {
  display: block;
  color: #666;
  font-size: 14px;
}

.stat-card strong {
  display: block;
  color: #333;
  font-size: 24px;
  margin-top: 5px;
}

.history {
  background: white;
  padding: 20px;
  border-radius: 10px;
}

.history h2 {
  margin-bottom: 15px;
  color: #333;
}

.history ul {
  list-style: none;
}

.history li {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.history li:last-child {
  border-bottom: none;
}
</style>

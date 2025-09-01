import axios from 'axios'
import { ElMessage } from 'element-plus'

// 創建 axios 實例
const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2分鐘超時
  headers: {
    'Content-Type': 'application/json'
  }
})

// 請求攔截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 回應攔截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API 請求錯誤:', error)
    
    let message = '請求失敗'
    if (error.response?.data?.detail) {
      message = error.response.data.detail
    } else if (error.response?.status) {
      message = `請求失敗 (${error.response.status})`
    } else if (error.message) {
      message = error.message
    }

    ElMessage.error(message)
    return Promise.reject(new Error(message))
  }
)

// API 服務
const apiService = {
  // 健康檢查
  async checkHealth() {
    const response = await api.get('/health')
    return response.data
  },

  // 語音轉文字
  async speechToText(formData) {
    const response = await api.post('/stt', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  // LLM 對話
  async chat(text, conversationId = null) {
    const formData = new FormData()
    formData.append('text', text)
    if (conversationId) {
      formData.append('conversation_id', conversationId)
    }

    const response = await api.post('/chat', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  // 文字轉語音
  async textToSpeech(data) {
    const response = await api.post('/tts', data, {
      responseType: 'blob'
    })
    return response.data
  },

  // 完整對話流程
  async fullConversation(audioFile, conversationId = null) {
    const formData = new FormData()
    formData.append('audio_file', audioFile, 'recording.wav')
    if (conversationId) {
      formData.append('conversation_id', conversationId)
    }

    const response = await api.post('/conversation', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  // 獲取語者資訊
  async getSpeakerInfo() {
    const response = await api.get('/speaker_info')
    return response.data
  },

  // 獲取音檔
  async getAudioFile(filename) {
    const response = await api.get(`/audio/${filename}`, {
      responseType: 'blob'
    })
    return response.data
  }
}

export default apiService

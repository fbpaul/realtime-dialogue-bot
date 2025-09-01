import { defineStore } from 'pinia'
import { ref } from 'vue'
import apiService from '../services/api'

export const useSystemStore = defineStore('system', () => {
  // 狀態
  const healthStatus = ref({
    status: 'unknown',
    stt_ready: false,
    tts_ready: false,
    llm_ready: false,
    timestamp: null
  })

  const isLoading = ref(false)
  const lastHealthCheck = ref(null)

  // 動作
  const checkHealth = async () => {
    isLoading.value = true
    try {
      const response = await apiService.checkHealth()
      healthStatus.value = {
        ...response,
        status: response.status || 'unknown'
      }
      lastHealthCheck.value = Date.now()
      return response
    } catch (error) {
      console.error('健康檢查失敗:', error)
      healthStatus.value = {
        status: 'error',
        stt_ready: false,
        tts_ready: false,
        llm_ready: false,
        timestamp: null
      }
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const getSpeakerInfo = async () => {
    try {
      return await apiService.getSpeakerInfo()
    } catch (error) {
      console.error('獲取語者資訊失敗:', error)
      throw error
    }
  }

  return {
    healthStatus,
    isLoading,
    lastHealthCheck,
    checkHealth,
    getSpeakerInfo
  }
})

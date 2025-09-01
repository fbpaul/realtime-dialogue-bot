import { ref, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

export function useAudioRecorder() {
  const isRecording = ref(false)
  const audioBlob = ref(null)
  const mediaRecorder = ref(null)
  const audioChunks = ref([])

  const startRecording = async () => {
    try {
      // 請求麥克風權限
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        }
      })

      // 創建 MediaRecorder
      const options = {
        mimeType: 'audio/webm;codecs=opus'
      }
      
      if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        options.mimeType = 'audio/webm'
      }
      
      if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        options.mimeType = 'audio/mp4'
      }

      mediaRecorder.value = new MediaRecorder(stream, options)
      audioChunks.value = []

      // 監聽數據事件
      mediaRecorder.value.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.value.push(event.data)
        }
      }

      // 監聽停止事件
      mediaRecorder.value.onstop = () => {
        const blob = new Blob(audioChunks.value, { type: 'audio/wav' })
        audioBlob.value = blob
        
        // 停止麥克風串流
        stream.getTracks().forEach(track => track.stop())
      }

      // 開始錄音
      mediaRecorder.value.start(100) // 每100ms收集一次數據
      isRecording.value = true
      
      ElMessage.success('開始錄音')

    } catch (error) {
      console.error('錄音啟動失敗:', error)
      ElMessage.error('無法存取麥克風，請檢查權限設定')
    }
  }

  const stopRecording = async () => {
    if (mediaRecorder.value && isRecording.value) {
      mediaRecorder.value.stop()
      isRecording.value = false
      ElMessage.success('錄音結束')
    }
  }

  const clearRecording = () => {
    audioBlob.value = null
    audioChunks.value = []
  }

  // 清理資源
  onUnmounted(() => {
    if (mediaRecorder.value && isRecording.value) {
      stopRecording()
    }
  })

  return {
    isRecording,
    audioBlob,
    startRecording,
    stopRecording,
    clearRecording
  }
}

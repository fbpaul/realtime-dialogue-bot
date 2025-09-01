<template>
  <div class="chat-container">
    <!-- 頂部標題 -->
    <div class="header">
      <h1 class="title">
        🎙️ 即時語音對話系統
      </h1>
      <div class="status-indicator">
        <el-tag :type="systemStatus.type" :icon="systemStatus.icon">
          {{ systemStatus.text }}
        </el-tag>
      </div>
    </div>

    <!-- 對話區域 -->
    <div class="chat-area" ref="chatArea">
      <div class="message-list">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['message', message.type]"
        >
          <div class="message-content">
            <div class="message-text">{{ message.text }}</div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            <div v-if="message.audioUrl" class="message-audio">
              <audio controls :src="message.audioUrl"></audio>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 輸入區域 -->
    <div class="input-area">
      <!-- 語音錄音按鈕 -->
      <div class="voice-controls">
        <el-button
          :type="isRecording ? 'danger' : 'primary'"
          :icon="isRecording ? 'VideoPlay' : 'Microphone'"
          size="large"
          circle
          @click="toggleRecording"
          :loading="isProcessing"
          :disabled="!systemReady"
        >
        </el-button>
        <div class="recording-hint">
          {{ isRecording ? '🔴 錄音中... 點擊停止' : '🎤 點擊開始錄音' }}
        </div>
      </div>

      <!-- 文字輸入 -->
      <div class="text-input">
        <el-input
          v-model="textInput"
          type="textarea"
          :rows="3"
          placeholder="或者在此輸入文字訊息..."
          @keydown.ctrl.enter="sendTextMessage"
          :disabled="isProcessing"
        />
        <div class="input-actions">
          <el-button 
            type="primary" 
            @click="sendTextMessage"
            :loading="isProcessing"
            :disabled="!textInput.trim() || !systemReady"
          >
            發送訊息
          </el-button>
        </div>
      </div>
    </div>

    <!-- 系統狀態對話框 -->
    <el-dialog v-model="showStatusDialog" title="系統狀態" width="500px">
      <div class="status-details">
        <div class="status-item">
          <span class="status-label">STT (語音轉文字):</span>
          <el-tag :type="healthStatus.stt_ready ? 'success' : 'danger'">
            {{ healthStatus.stt_ready ? '✅ 就緒' : '❌ 未就緒' }}
          </el-tag>
        </div>
        <div class="status-item">
          <span class="status-label">TTS (文字轉語音):</span>
          <el-tag :type="healthStatus.tts_ready ? 'success' : 'danger'">
            {{ healthStatus.tts_ready ? '✅ 就緒' : '❌ 未就緒' }}
          </el-tag>
        </div>
        <div class="status-item">
          <span class="status-label">LLM (對話模型):</span>
          <el-tag :type="healthStatus.llm_ready ? 'success' : 'danger'">
            {{ healthStatus.llm_ready ? '✅ 就緒' : '❌ 未就緒' }}
          </el-tag>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { useSystemStore } from '../stores/system'
import { useAudioRecorder } from '../composables/useAudioRecorder'
import apiService from '../services/api'

// 系統狀態
const systemStore = useSystemStore()
const { healthStatus, checkHealth } = systemStore

// 對話訊息
const messages = ref([
  {
    id: 1,
    type: 'assistant',
    text: '你好！我是語音助理，可以幫你回答問題、聊天對話。你可以點擊麥克風按鈕錄音，或直接輸入文字。',
    timestamp: Date.now()
  }
])

// 輸入狀態
const textInput = ref('')
const isProcessing = ref(false)
const showStatusDialog = ref(false)
const chatArea = ref(null)

// 語音錄音
const { isRecording, startRecording, stopRecording, audioBlob } = useAudioRecorder()

// 計算屬性
const systemReady = computed(() => 
  healthStatus.value.stt_ready && 
  healthStatus.value.tts_ready && 
  healthStatus.value.llm_ready
)

const systemStatus = computed(() => {
  if (systemReady.value) {
    return { type: 'success', icon: 'CircleCheck', text: '系統就緒' }
  }
  return { type: 'danger', icon: 'CircleClose', text: '系統未就緒' }
})

// 方法
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('zh-TW', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatArea.value) {
      chatArea.value.scrollTop = chatArea.value.scrollHeight
    }
  })
}

const addMessage = (type, text, audioUrl = null) => {
  const message = {
    id: Date.now() + Math.random(),
    type,
    text,
    timestamp: Date.now(),
    audioUrl
  }
  messages.value.push(message)
  scrollToBottom()
  return message
}

const toggleRecording = async () => {
  if (isRecording.value) {
    await stopRecording()
    await processVoiceMessage()
  } else {
    await startRecording()
  }
}

const processVoiceMessage = async () => {
  if (!audioBlob.value) return

  isProcessing.value = true
  addMessage('user', '🎤 語音訊息處理中...', null)

  try {
    // 語音轉文字
    const formData = new FormData()
    formData.append('file', audioBlob.value, 'recording.wav')
    
    const sttResponse = await apiService.speechToText(formData)
    const userText = sttResponse.text

    // 更新用戶訊息
    messages.value[messages.value.length - 1].text = userText

    // 獲取 LLM 回應
    const chatResponse = await apiService.chat(userText)
    const assistantText = chatResponse.response

    // 文字轉語音
    const ttsResponse = await apiService.textToSpeech({
      text: assistantText,
      cfg_scale: 1.0
    })

    // 創建音檔 URL
    const audioUrl = URL.createObjectURL(ttsResponse)

    // 添加助理回應
    addMessage('assistant', assistantText, audioUrl)

    ElMessage.success('語音對話完成！')

  } catch (error) {
    console.error('語音處理錯誤:', error)
    ElMessage.error('語音處理失敗: ' + error.message)
    // 移除處理中的訊息
    messages.value.pop()
  } finally {
    isProcessing.value = false
  }
}

const sendTextMessage = async () => {
  if (!textInput.value.trim()) return

  const userText = textInput.value.trim()
  textInput.value = ''
  isProcessing.value = true

  // 添加用戶訊息
  addMessage('user', userText)

  try {
    // 獲取 LLM 回應
    const chatResponse = await apiService.chat(userText)
    const assistantText = chatResponse.response

    // 文字轉語音
    const ttsResponse = await apiService.textToSpeech({
      text: assistantText,
      cfg_scale: 1.0
    })

    // 創建音檔 URL
    const audioUrl = URL.createObjectURL(ttsResponse)

    // 添加助理回應
    addMessage('assistant', assistantText, audioUrl)

    ElMessage.success('訊息發送成功！')

  } catch (error) {
    console.error('文字處理錯誤:', error)
    ElMessage.error('訊息處理失敗: ' + error.message)
  } finally {
    isProcessing.value = false
  }
}

// 生命週期
onMounted(async () => {
  await checkHealth()
  if (!systemReady.value) {
    ElNotification({
      title: '系統狀態警告',
      message: '部分系統模組未就緒，請檢查後端服務',
      type: 'warning',
      duration: 5000
    })
  }
})
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header {
  padding: 1rem 2rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.status-indicator {
  cursor: pointer;
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 2rem;
}

.message-list {
  max-width: 800px;
  margin: 0 auto;
}

.message {
  margin-bottom: 1rem;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 70%;
  padding: 1rem;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.message.user .message-content {
  background: rgba(255, 255, 255, 0.2);
}

.message-text {
  margin-bottom: 0.5rem;
  line-height: 1.5;
}

.message-time {
  font-size: 0.8rem;
  opacity: 0.7;
  text-align: right;
}

.message-audio {
  margin-top: 0.5rem;
}

.message-audio audio {
  width: 100%;
  height: 40px;
}

.input-area {
  padding: 1rem 2rem 2rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.voice-controls {
  text-align: center;
  margin-bottom: 1rem;
}

.voice-controls .el-button {
  width: 60px;
  height: 60px;
  font-size: 1.5rem;
}

.recording-hint {
  margin-top: 0.5rem;
  font-size: 0.9rem;
  opacity: 0.8;
}

.text-input {
  max-width: 800px;
  margin: 0 auto;
}

.text-input :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #333;
}

.input-actions {
  margin-top: 1rem;
  text-align: right;
}

.status-details {
  space-y: 1rem;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #eee;
}

.status-item:last-child {
  border-bottom: none;
}

.status-label {
  font-weight: 600;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .header {
    padding: 1rem;
    flex-direction: column;
    gap: 0.5rem;
  }

  .title {
    font-size: 1.2rem;
  }

  .chat-area {
    padding: 1rem;
  }

  .input-area {
    padding: 1rem;
  }

  .message-content {
    max-width: 90%;
  }
}
</style>

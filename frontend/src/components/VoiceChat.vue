<template>
  <div class="chat-app">
    <!-- 頂部標題欄 -->
    <div class="app-header">
      <div class="user-info">
        <div class="avatar">
          <User :size="24" />
        </div>
        <div class="user-details">
          <div class="user-name">智慧語音助手</div>
          <div class="user-status">
            <div class="status-dot" :class="{ 'online': allServicesOnline }"></div>
            {{ allServicesOnline ? '已連線到後端 API' : '連線中...' }}
          </div>
        </div>
      </div>
      <div class="header-tabs">
        <div class="tab active">語音對話體驗</div>
        <div class="tab">引導對話</div>
        <div class="tab">進出端資方案</div>
      </div>
      <div class="header-actions">
        <button 
          class="new-chat-btn"
          @click="startNewConversation"
          :disabled="isProcessing"
        >
          <MessageCircle :size="16" />
          新對話
        </button>
      </div>
    </div>

    <!-- 聊天區域 -->
    <div class="chat-container">
      <div class="chat-messages" ref="chatMessagesRef">
        <div v-if="chatHistory.length === 0" class="welcome-message">
          <MessageCircle :size="48" class="welcome-icon" />
          <p>開始對話吧！</p>
        </div>
        
        <div 
          v-for="(message, index) in chatHistory" 
          :key="index" 
          :class="['message-bubble', message.type === 'user' ? 'user-bubble' : 'assistant-bubble']"
        >
          <div class="bubble-content">
            <div class="message-text">
              {{ message.text }}
              <div v-if="message.isProcessing" class="processing-indicator">
                <Loader2 :size="14" class="spinning" />
              </div>
            </div>
            
            <!-- 處理時間顯示 -->
            <div v-if="message.processingTimes && !message.isProcessing" class="processing-times">
              <div v-if="message.processingTimes.stt_time" class="time-item stt-time">
                <Headphones :size="12" />
                <span>STT: {{ message.processingTimes.stt_time }}ms</span>
              </div>
              <div v-if="message.processingTimes.llm_time" class="time-item llm-time">
                <Brain :size="12" />
                <span>LLM: {{ message.processingTimes.llm_time }}ms</span>
              </div>
              <div v-if="message.processingTimes.tts_time" class="time-item tts-time">
                <Volume2 :size="12" />
                <span>TTS: {{ message.processingTimes.tts_time }}ms</span>
              </div>
              <div v-if="message.processingTimes.total_time" class="time-item total-time">
                <Timer :size="12" />
                <span>總計: {{ message.processingTimes.total_time }}ms</span>
              </div>
            </div>
            
            <div class="message-time">
              <Clock :size="12" />
              {{ formatTime(message.timestamp) }}
            </div>
          </div>
          
          <div v-if="message.audioUrl && !message.isProcessing" class="audio-attachment">
            <div class="audio-player">
              <button class="play-btn" @click="playAudio(message.audioUrl)">
                <Play :size="16" />
              </button>
              <div class="audio-info">語音訊息</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 底部輸入區域 -->
      <div class="input-area">
        <div class="input-container">
          <div class="text-input">
            <textarea 
              v-model="inputText"
              placeholder="請輸入您的問題..."
              @keydown.enter.prevent="sendTextMessage"
              :disabled="isProcessing"
            ></textarea>
          </div>
          <div class="action-buttons">
            <button 
              class="send-btn"
              @click="sendTextMessage"
              :disabled="!inputText.trim() || isProcessing"
            >
              <Send :size="20" />
            </button>
            <button 
              :class="['mic-btn', { 'recording': isRecording }]"
              @click="toggleRecording"
              :disabled="isProcessing && !isRecording"
            >
              <Mic v-if="!isRecording" :size="24" />
              <Square v-else :size="24" />
            </button>
          </div>
        </div>
        
        <!-- 錄音狀態顯示 -->
        <div v-if="isRecording" class="recording-status">
          <div class="recording-indicator">
            <div class="pulse-dot"></div>
            <span>正在錄音... {{ formatDuration(recordingDuration) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, computed } from 'vue'
import { 
  Mic, 
  Square, 
  Send, 
  User, 
  Bot, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Timer, 
  MessageCircle,
  Play, 
  Loader2,
  Headphones,
  Brain,
  Volume2
} from 'lucide-vue-next'

// 響應式數據
const sttStatus = ref(false)
const llmStatus = ref(false)
const ttsStatus = ref(false)
const isRecording = ref(false)
const isProcessing = ref(false)
const recordingDuration = ref(0)
const inputText = ref('')
const processingStatus = ref('')
const chatHistory = reactive([])
const chatMessagesRef = ref(null)

// 計算屬性
const allServicesOnline = computed(() => {
  return sttStatus.value && llmStatus.value && ttsStatus.value
})

// 媒體相關
let mediaRecorder = null
let audioChunks = []
let recordingTimer = null

// API 基礎 URL
const API_BASE_URL = 'http://10.204.245.170:8945'

// 初始化
onMounted(async () => {
  await checkBackendStatus()
})

// 檢查後端狀態
const checkBackendStatus = async () => {
  try {
    // 檢查 STT
    const sttResponse = await fetch(`${API_BASE_URL}/health/stt`)
    sttStatus.value = sttResponse.ok

    // 檢查 LLM
    const llmResponse = await fetch(`${API_BASE_URL}/health/llm`)  
    llmStatus.value = llmResponse.ok

    // 檢查 TTS
    const ttsResponse = await fetch(`${API_BASE_URL}/health/tts`)
    ttsStatus.value = ttsResponse.ok
  } catch (error) {
    console.error('檢查服務狀態失敗:', error)
    sttStatus.value = false
    llmStatus.value = false
    ttsStatus.value = false
  }
}

// 切換錄音狀態
const toggleRecording = async () => {
  if (isRecording.value) {
    await stopRecording()
  } else {
    await startRecording()
  }
}

// 開始錄音
const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(stream)
    audioChunks = []

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data)
      }
    }

    mediaRecorder.onstop = async () => {
      await processRecording()
    }

    mediaRecorder.start()
    isRecording.value = true
    recordingDuration.value = 0

    // 開始計時
    recordingTimer = setInterval(() => {
      recordingDuration.value += 1
    }, 1000)

  } catch (error) {
    console.error('開始錄音失敗:', error)
    alert('無法存取麥克風，請檢查權限設定')
  }
}

// 停止錄音
const stopRecording = () => {
  if (mediaRecorder && isRecording.value) {
    mediaRecorder.stop()
    mediaRecorder.stream.getTracks().forEach(track => track.stop())
    isRecording.value = false

    if (recordingTimer) {
      clearInterval(recordingTimer)
      recordingTimer = null
    }
  }
}

// 處理錄音
const processRecording = async () => {
  if (audioChunks.length === 0) return

  isProcessing.value = true
  processingStatus.value = '正在轉換語音...'

  try {
    // 創建音頻 blob
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' })
    const formData = new FormData()
    formData.append('file', audioBlob, 'recording.wav')  // 修改字段名為 'file'

    // 添加處理中的用戶訊息佔位符
    const userMessageId = Date.now()
    chatHistory.push({
      id: userMessageId,
      type: 'user',
      text: '正在轉換語音...',
      timestamp: new Date(),
      audioUrl: URL.createObjectURL(audioBlob),
      isProcessing: true
    })

    await nextTick()
    scrollToBottom()

    // 第一階段：語音轉文字 (STT)
    const sttResponse = await fetch(`${API_BASE_URL}/stt`, {
      method: 'POST',
      body: formData
    })

    if (!sttResponse.ok) {
      throw new Error('語音轉文字失敗')
    }

    const sttResult = await sttResponse.json()
    
    // 立即更新用戶訊息顯示轉錄結果
    const userMessage = chatHistory.find(msg => msg.id === userMessageId)
    if (userMessage) {
      userMessage.text = sttResult.transcription
      userMessage.isProcessing = false
      userMessage.processingTimes = {
        stt_time: sttResult.processing_time
      }
    }

    await nextTick()
    scrollToBottom()

    // 第二階段：文字對話 (LLM + TTS)
    processingStatus.value = '正在生成回應...'
    
    // 添加助理回應的佔位符
    const assistantMessageId = Date.now() + 1
    chatHistory.push({
      id: assistantMessageId,
      type: 'assistant',
      text: '正在思考回應...',
      timestamp: new Date(),
      isProcessing: true
    })

    await nextTick()
    scrollToBottom()

    // 調用文字對話 API
    const chatResponse = await fetch(`${API_BASE_URL}/text_chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message: sttResult.transcription })
    })

    if (!chatResponse.ok) {
      throw new Error('生成回應失敗')
    }

    const chatResult = await chatResponse.json()
    
    // 更新助理訊息
    const assistantMessage = chatHistory.find(msg => msg.id === assistantMessageId)
    if (assistantMessage) {
      assistantMessage.text = chatResult.response
      assistantMessage.audioUrl = chatResult.audio_url ? `${API_BASE_URL}${chatResult.audio_url}` : null
      assistantMessage.isProcessing = false
      assistantMessage.processingTimes = {
        llm_time: chatResult.processing_times.llm_time,
        tts_time: chatResult.processing_times.tts_time,
        total_time: chatResult.processing_times.total_time
      }
    }

    // 滾動到底部
    await nextTick()
    scrollToBottom()

  } catch (error) {
    console.error('處理語音失敗:', error)
    alert('語音處理失敗，請重試')
    // 移除處理失敗的訊息
    const failedIndex = chatHistory.findIndex(msg => msg.isProcessing)
    if (failedIndex !== -1) {
      chatHistory.splice(failedIndex, 1)
    }
  } finally {
    isProcessing.value = false
    processingStatus.value = ''
  }
}

// 發送文字訊息
const sendTextMessage = async () => {
  if (!inputText.value.trim() || isProcessing.value) return

  const userMessage = inputText.value.trim()
  inputText.value = ''
  isProcessing.value = true

  // 添加用戶訊息
  chatHistory.push({
    id: Date.now(),
    type: 'user',
    text: userMessage,
    timestamp: new Date()
  })

  // 添加助理回應的佔位符
  const assistantMessageId = Date.now() + 1
  chatHistory.push({
    id: assistantMessageId,
    type: 'assistant',
    text: '正在思考回應...',
    timestamp: new Date(),
    isProcessing: true
  })

  await nextTick()
  scrollToBottom()

  try {
    const response = await fetch(`${API_BASE_URL}/text_chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message: userMessage })
    })

    if (response.ok) {
      const result = await response.json()
      
      // 更新助理訊息
      const assistantMessage = chatHistory.find(msg => msg.id === assistantMessageId)
      if (assistantMessage) {
        assistantMessage.text = result.response
        assistantMessage.audioUrl = result.audio_url ? `${API_BASE_URL}${result.audio_url}` : null
        assistantMessage.isProcessing = false
        assistantMessage.processingTimes = {
          llm_time: result.processing_times.llm_time,
          tts_time: result.processing_times.tts_time,
          total_time: result.processing_times.total_time
        }
      }

      // 滾動到底部
      await nextTick()
      scrollToBottom()

    } else {
      throw new Error('發送訊息失敗')
    }

  } catch (error) {
    console.error('發送訊息失敗:', error)
    alert('發送訊息失敗，請重試')
    // 移除處理失敗的訊息
    const failedIndex = chatHistory.findIndex(msg => msg.id === assistantMessageId)
    if (failedIndex !== -1) {
      chatHistory.splice(failedIndex, 1)
    }
  } finally {
    isProcessing.value = false
  }
}

// 開始新對話
const startNewConversation = async () => {
  if (isProcessing.value) return
  
  try {
    // 清空聊天歷史
    chatHistory.splice(0, chatHistory.length)
    
    // 調用後端 API 重置對話歷史
    const response = await fetch(`${API_BASE_URL}/reset_conversation`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      console.log('對話歷史已重置')
    } else {
      console.warn('重置對話歷史失敗，但前端已清空')
    }
    
  } catch (error) {
    console.error('重置對話失敗:', error)
    // 即使後端失敗，前端也已經清空了
  }
}

// 播放音頻
const playAudio = (audioUrl) => {
  const audio = new Audio(audioUrl)
  audio.play()
}

// 滾動到底部
const scrollToBottom = () => {
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  }
}

// 格式化時間
const formatTime = (date) => {
  return date.toLocaleTimeString('zh-TW', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

// 格式化持續時間
const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
/* 整體應用樣式 */
.chat-app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #f0f0f1 0%, #c0bcf5 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow: hidden;
}

/* 頂部標題欄 */
.app-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 16px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  height: 80px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(79, 172, 254, 0.3);
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-name {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.user-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #7f8c8d;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e74c3c;
  transition: background-color 0.3s;
}

.status-dot.online {
  background: #27ae60;
}

.header-tabs {
  display: flex;
  gap: 8px;
}

.tab {
  padding: 8px 16px;
  font-size: 14px;
  color: #7f8c8d;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s;
}

.tab.active {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
  font-weight: 500;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background: white;
  color: #495057;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.new-chat-btn:hover:not(:disabled) {
  background: #f8f9fa;
  border-color: #adb5bd;
  transform: translateY(-1px);
}

.new-chat-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 聊天容器 */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f8f9fa;
  margin: 16px;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  min-height: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}

.welcome-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #d7dadd;
}

.welcome-icon {
  margin-bottom: 16px;
  opacity: 0.5;
}

/* 訊息氣泡 */
.message-bubble {
  max-width: 70%;
  margin-bottom: 16px;
}

.user-bubble {
  align-self: flex-end;
  margin-left: auto;
}

.assistant-bubble {
  align-self: flex-start;
}

.bubble-content {
  background: white;
  border-radius: 16px;
  padding: 14px 18px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
  position: relative;
}

.user-bubble .bubble-content {
  background: #e3f2fd;
  color: #1565c0;
  border: 1px solid #bbdefb;
  border-bottom-right-radius: 4px;
}

.user-bubble .bubble-content::after {
  content: '';
  position: absolute;
  bottom: 0;
  right: -8px;
  width: 0;
  height: 0;
  border-left: 8px solid #e3f2fd;
  border-bottom: 8px solid transparent;
}

.assistant-bubble .bubble-content {
  background: #f5f5f5;
  color: #424242;
  border: 1px solid #e0e0e0;
  border-bottom-left-radius: 4px;
}

.assistant-bubble .bubble-content::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: -8px;
  width: 0;
  height: 0;
  border-right: 8px solid #f5f5f5;
  border-bottom: 8px solid transparent;
}

.message-text {
  font-size: 16px;
  line-height: 1.5;
  margin: 0;
  position: relative;
}

.processing-indicator {
  display: inline-flex;
  align-items: center;
  margin-left: 8px;
  color: #6c757d;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.processing-times {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.time-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}

.stt-time {
  background: #e8f5e8;
  color: #2e7d32;
}

.llm-time {
  background: #fff3e0;
  color: #f57c00;
}

.tts-time {
  background: #e3f2fd;
  color: #1976d2;
}

.total-time {
  background: #f3e5f5;
  color: #2c1fa2;
  font-weight: 600;
}

.user-bubble .processing-times .time-item {
  background: rgba(255, 255, 255, 0.7);
  color: #1565c0;
}

.message-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  opacity: 0.7;
  margin-top: 6px;
}

/* 音頻附件 */
.audio-attachment {
  margin-top: 8px;
}

.audio-player {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  font-size: 14px;
}

.play-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: #6c757d;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.3s;
}

.play-btn:hover {
  background: #5a6268;
}

/* 底部輸入區域 */
.input-area {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 16px 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 0 0 16px 16px;
  flex-shrink: 0;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  max-width: 1200px;
  margin: 0 auto;
}

.text-input {
  flex: 1;
}

.text-input textarea {
  width: 100%;
  min-height: 48px;
  max-height: 120px;
  border: 2px solid #e9ecef;
  border-radius: 24px;
  padding: 12px 16px;
  font-size: 16px;
  resize: none;
  outline: none;
  transition: border-color 0.3s;
  font-family: inherit;
}

.text-input textarea:focus {
  border-color: #4facfe;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.send-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: none;
  background: #4facfe;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.send-btn:hover:not(:disabled) {
  background: #3b8bfe;
  transform: scale(1.05);
}

.send-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.mic-btn {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: none;
  background: #4facfe;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.mic-btn:hover:not(:disabled) {
  background: #3b8bfe;
  transform: scale(1.05);
}

.mic-btn.recording {
  background: #e74c3c;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.7);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 0 10px rgba(231, 76, 60, 0);
  }
}

/* 錄音狀態 */
.recording-status {
  margin-top: 12px;
  display: flex;
  justify-content: center;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(231, 76, 60, 0.1);
  border-radius: 20px;
  font-size: 14px;
  color: #e74c3c;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e74c3c;
  animation: pulse-dot 1s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* 響應式設計 */
@media (max-width: 768px) {
  .app-header {
    padding: 12px 16px;
    flex-direction: column;
    gap: 12px;
  }
  
  .header-tabs {
    order: -1;
    width: 100%;
    justify-content: center;
  }
  
  .tab {
    flex: 1;
    text-align: center;
    font-size: 12px;
    padding: 6px 8px;
  }
  
  .chat-container {
    margin: 0 8px;
  }
  
  .input-area {
    padding: 12px 16px;
  }
  
  .message-bubble {
    max-width: 85%;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 8px;
  }
}
</style>

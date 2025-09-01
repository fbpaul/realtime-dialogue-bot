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
            {{ allServicesOnline ? '已連線到資料庫' : '連線中...' }}
          </div>
        </div>
      </div>
      <div class="header-tabs">
        <div class="tab active">語音對話體驗</div>
        <div class="tab">引導對話</div>
        <div class="tab">進出端資方案</div>
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
            <div class="message-text">{{ message.text }}</div>
            <div class="message-time">
              <Clock :size="12" />
              {{ formatTime(message.timestamp) }}
            </div>
          </div>
          
          <div v-if="message.audioUrl" class="audio-attachment">
            <div class="audio-player">
              <button class="play-btn" @click="playAudio(message.audioUrl)">
                <Play :size="16" />
              </button>
              <div class="audio-info">語音訊息</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部控制區域 -->
    <!-- 底部控制區域 -->
    <div class="bottom-controls">
      <div class="control-container">
        <!-- 錄音區域 -->
        <div class="recording-section">
          <button 
            :class="['record-btn', { 'recording': isRecording, 'processing': isProcessing }]"
            @click="toggleRecording"
            :disabled="isProcessing"
          >
            <Mic v-if="!isRecording && !isProcessing" :size="24" />
            <Square v-else-if="isRecording" :size="24" />
            <Loader2 v-else :size="24" class="spinning" />
          </button>
          <span class="record-label">
            {{ isRecording ? '停止錄音' : isProcessing ? '處理中...' : '語音輸入' }}
          </span>
          <div v-if="isRecording" class="recording-timer">
            <Timer :size="16" />
            {{ formatDuration(recordingDuration) }}
          </div>
        </div>

        <!-- 分隔線 -->
        <div class="divider">或</div>

        <!-- 文字輸入區域 -->
        <div class="text-input-section">
          <div class="input-group">
            <textarea
              v-model="textInput"
              placeholder="輸入訊息..."
              :disabled="isProcessing"
              @keydown.ctrl.enter="sendTextMessage"
              rows="2"
            ></textarea>
            <button 
              @click="sendTextMessage" 
              :disabled="isProcessing || !textInput.trim()"
              class="send-btn"
            >
              <Send :size="20" />
            </button>
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
            class="send-btn-new"
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
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, computed } from 'vue'
import { 
  Mic, 
  Square, 
  Send, 
  User, 
  Bot, 
  Headphones, 
  Brain, 
  Volume2, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Timer, 
  MessageSquare, 
  MessageCircle,
  Play, 
  Loader2 
} from 'lucide-vue-next'

// 響應式數據
const sttStatus = ref(false)
const llmStatus = ref(false)
const ttsStatus = ref(false)
const isRecording = ref(false)
const isProcessing = ref(false)
const recordingDuration = ref(0)
const textInput = ref('')
const inputText = ref('')
const processingStatus = ref('')
const chatHistory = reactive([])
const chatHistoryRef = ref(null)

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
  
  // 添加歡迎消息
  addMessage('bot', '你好！我是你的語音助理。你可以點擊麥克風按鈕開始錄音，或直接輸入文字與我對話。', new Date(), null)
})

// 檢查後端狀態
const checkBackendStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`)
    if (response.ok) {
      const data = await response.json()
      sttStatus.value = data.stt_ready || false
      llmStatus.value = data.llm_ready || false
      ttsStatus.value = data.tts_ready || false
    }
  } catch (error) {
    console.error('檢查後端狀態失敗:', error)
  }
}

// 切換錄音狀態
const toggleRecording = async () => {
  if (isRecording.value) {
    stopRecording()
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
    
    mediaRecorder.onstop = handleRecordingStop
    
    mediaRecorder.start()
    isRecording.value = true
    recordingDuration.value = 0
    
    // 開始計時
    recordingTimer = setInterval(() => {
      recordingDuration.value++
    }, 1000)
    
  } catch (error) {
    console.error('無法開始錄音:', error)
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

// 處理錄音結束
const handleRecordingStop = async () => {
  const audioBlob = new Blob(audioChunks, { type: 'audio/wav' })
  await processAudioMessage(audioBlob)
}

// 處理音頻消息
const processAudioMessage = async (audioBlob) => {
  isProcessing.value = true
  processingStatus.value = '正在轉錄語音...'
  
  try {
    // Step 1: STT - 語音轉文字
    const formData = new FormData()
    formData.append('file', audioBlob, 'recording.wav')
    
    const sttResponse = await fetch(`${API_BASE_URL}/stt`, {
      method: 'POST',
      body: formData
    })
    
    if (!sttResponse.ok) {
      throw new Error('STT 轉錄失敗')
    }
    
    const sttData = await sttResponse.json()
    const userText = sttData.text
    
    if (!userText.trim()) {
      throw new Error('未識別到語音內容')
    }
    
    // 添加用戶消息
    addMessage('user', userText, new Date(), null)
    
    // Step 2: LLM - 獲取回應
    processingStatus.value = '正在生成回應...'
    
    const chatFormData = new FormData()
    chatFormData.append('text', userText)
    
    const chatResponse = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      body: chatFormData
    })
    
    if (!chatResponse.ok) {
      throw new Error('獲取 AI 回應失敗')
    }
    
    const chatData = await chatResponse.json()
    const botResponse = chatData.response
    
    // Step 3: TTS - 文字轉語音
    processingStatus.value = '正在合成語音...'
    
    const ttsResponse = await fetch(`${API_BASE_URL}/tts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: botResponse,
        cfg_scale: 1.0
      })
    })
    
    if (!ttsResponse.ok) {
      throw new Error('語音合成失敗')
    }
    
    // 創建音頻 URL
    const audioData = await ttsResponse.blob()
    const audioUrl = URL.createObjectURL(audioData)
    
    // 添加機器人消息
    addMessage('bot', botResponse, new Date(), audioUrl)
    
    // 自動播放語音
    const audio = new Audio(audioUrl)
    audio.play().catch(console.error)
    
  } catch (error) {
    console.error('處理語音消息失敗:', error)
    addMessage('bot', `抱歉，處理時發生錯誤：${error.message}`, new Date(), null)
  } finally {
    isProcessing.value = false
    processingStatus.value = ''
  }
}

// 發送文字消息
const sendTextMessage = async () => {
  if (!textInput.value.trim()) return
  
  const message = textInput.value.trim()
  textInput.value = ''
  
  isProcessing.value = true
  processingStatus.value = '正在處理消息...'
  
  try {
    // 添加用戶消息
    addMessage('user', message, new Date(), null)
    
    // 獲取 AI 回應
    const formData = new FormData()
    formData.append('text', message)
    
    const chatResponse = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      body: formData
    })
    
    if (!chatResponse.ok) {
      throw new Error('獲取 AI 回應失敗')
    }
    
    const chatData = await chatResponse.json()
    const botResponse = chatData.response
    
    // 添加機器人消息（不進行 TTS）
    addMessage('bot', botResponse, new Date(), null)
    
  } catch (error) {
    console.error('發送文字消息失敗:', error)
    addMessage('bot', `抱歉，處理時發生錯誤：${error.message}`, new Date(), null)
  } finally {
    isProcessing.value = false
    processingStatus.value = ''
  }
}

// 添加消息到聊天歷史
const addMessage = (type, text, timestamp, audioUrl) => {
  chatHistory.push({
    type,
    text,
    timestamp,
    audioUrl
  })
  
  // 滾動到底部
  nextTick(() => {
    if (chatHistoryRef.value) {
      chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
    }
  })
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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

/* 聊天容器 */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.1);
  margin: 16px;
  border-radius: 16px;
  backdrop-filter: blur(10px);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: rgba(255, 255, 255, 0.8);
}

.welcome-icon {
  margin-bottom: 16px;
  opacity: 0.6;
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
  border-radius: 18px;
  padding: 12px 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  position: relative;
}

.user-bubble .bubble-content {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.user-bubble .bubble-content::after {
  content: '';
  position: absolute;
  bottom: 0;
  right: -8px;
  width: 0;
  height: 0;
  border-left: 8px solid #00f2fe;
  border-bottom: 8px solid transparent;
}

.assistant-bubble .bubble-content {
  border-bottom-left-radius: 4px;
}

.assistant-bubble .bubble-content::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: -8px;
  width: 0;
  height: 0;
  border-right: 8px solid white;
  border-bottom: 8px solid transparent;
}

.message-text {
  font-size: 16px;
  line-height: 1.5;
  margin: 0;
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
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  font-size: 14px;
}

.play-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: #4facfe;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.3s;
}

.play-btn:hover {
  background: #3b8bfe;
}

/* 底部輸入區域 */
.input-area {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 16px 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
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

.send-btn-new {
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

.send-btn-new:hover:not(:disabled) {
  background: #3b8bfe;
  transform: scale(1.05);
}

.send-btn-new:disabled {
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
    margin: 8px;
  }
  
  .message-bubble {
    max-width: 85%;
  }
  
  .input-area {
    padding: 12px 16px;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 8px;
  }
}

/* 隱藏舊元素 */
.voice-chat-app, .status-panel, .chat-area, .bottom-controls {
  display: none !important;
}
</style>
/* 主容器 */
.voice-chat-app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-height: 100vh;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
}

/* 頂部狀態面板 */
.status-panel {
  padding: 16px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  flex-shrink: 0;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: white;
  border-radius: 8px;
  border: 1px solid #dee2e6;
  font-size: 0.9rem;
}

.status-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.online {
  color: #28a745;
}

.offline {
  color: #dc3545;
}

/* 聊天區域 */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgba(248, 249, 250, 0.3);
}

.chat-history {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  scroll-behavior: smooth;
}

.chat-empty {
  text-align: center;
  color: #6c757d;
  font-style: italic;
  padding: 80px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: #adb5bd;
}

.chat-message {
  margin-bottom: 30px;
  display: flex;
  align-items: flex-start;
  max-width: 100%;
}

/* 使用者訊息靠右對齊 */
.user-message {
  justify-content: flex-end;
  margin-left: 15%;
}

/* AI 助理訊息靠左對齊 */
.assistant-message {
  justify-content: flex-start;
  margin-right: 15%;
}

.message-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  max-width: 85%;
}

/* 使用者訊息的頭像在右邊 */
.user-message .message-wrapper {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.avatar-icon {
  width: 22px;
  height: 22px;
}

.user-message .message-avatar {
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
}

.assistant-message .message-avatar {
  background: linear-gradient(135deg, #28a745, #1e7e34);
  color: white;
}

.message-content {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  padding: 18px 20px;
  border-radius: 18px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
}

.user-message .message-content {
  background: rgba(227, 242, 253, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 18px;
  border-bottom-right-radius: 6px;
}

.user-message .message-content::after {
  content: '';
  position: absolute;
  bottom: 0;
  right: -8px;
  width: 0;
  height: 0;
  border-left: 8px solid rgba(227, 242, 253, 0.9);
  border-bottom: 8px solid transparent;
}

.assistant-message .message-content {
  border-bottom-left-radius: 6px;
}

.assistant-message .message-content::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: -8px;
  width: 0;
  height: 0;
  border-right: 8px solid rgba(255, 255, 255, 0.9);
  border-bottom: 8px solid transparent;
}

.message-text {
  margin: 0;
  line-height: 1.6;
  color: #2c3e50;
  font-size: 1rem;
}

.message-meta {
  margin-top: 10px;
  font-size: 0.85rem;
  color: #6c757d;
  display: flex;
  align-items: center;
  gap: 6px;
  opacity: 0.8;
}

.meta-icon {
  width: 12px;
  height: 12px;
}

/* Audio Player */
.message-audio {
  margin-top: 12px;
}

.audio-player {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: rgba(248, 249, 250, 0.8);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.audio-icon {
  color: #007bff;
}

.audio-player audio {
  flex: 1;
  height: 32px;
}

/* 底部控制區域 */
.bottom-controls {
  flex-shrink: 0;
  background: white;
  border-top: 1px solid #e9ecef;
  padding: 20px;
}

.control-container {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 30px;
}

/* 錄音區域 */
.recording-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.record-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(0, 123, 255, 0.3);
}

.record-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 123, 255, 0.4);
}

.record-btn.recording {
  background: linear-gradient(135deg, #dc3545, #c82333);
  box-shadow: 0 4px 16px rgba(220, 53, 69, 0.3);
  animation: recording-pulse 2s infinite;
}

.record-btn.processing {
  background: linear-gradient(135deg, #6c757d, #5a6268);
  cursor: not-allowed;
}

.record-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.record-label {
  font-size: 0.9rem;
  color: #6c757d;
  text-align: center;
}

.recording-timer {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.9rem;
  color: #dc3545;
  font-weight: 500;
}

/* 分隔線 */
.divider {
  color: #adb5bd;
  font-size: 0.9rem;
  padding: 0 10px;
}

/* 文字輸入區域 */
.text-input-section {
  flex: 1;
}

.input-group {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-group textarea {
  flex: 1;
  min-height: 60px;
  padding: 12px 16px;
  border: 1px solid #ced4da;
  border-radius: 12px;
  resize: vertical;
  font-family: inherit;
  font-size: 1rem;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.input-group textarea:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.send-btn {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #28a745, #1e7e34);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
}

.send-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(40, 167, 69, 0.4);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .status-panel {
    grid-template-columns: 1fr;
    padding: 12px 16px;
  }
  
  .chat-history {
    padding: 16px;
  }
  
  .control-container {
    flex-direction: column;
    gap: 20px;
  }
  
  .input-group {
    width: 100%;
  }
  
  .user-message,
  .assistant-message {
    margin-left: 0;
    margin-right: 0;
  }
  
  .message-wrapper {
    max-width: 100%;
  }
}

/* 動畫效果 */
@keyframes recording-pulse {
  0%, 100% {
    box-shadow: 0 4px 16px rgba(220, 53, 69, 0.3);
  }
  50% {
    box-shadow: 0 4px 20px rgba(220, 53, 69, 0.6);
  }
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>

/* Status Panel */
.status-panel {
  padding: 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: white;
  border-radius: 8px;
  border: 1px solid #dee2e6;
  font-size: 0.9rem;
}

.status-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.status-connected {
  color: #28a745;
}

.status-disconnected {
  color: #dc3545;
}

.status-checking {
  color: #ffc107;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Control Panel */
.control-panel {
  padding: 30px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-top: 1px solid #dee2e6;
}

.main-controls {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 30px;
}

/* Recording Section */
.recording-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.main-record-button {
  width: 180px;
  height: 180px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
  box-shadow: 0 8px 32px rgba(0, 123, 255, 0.3);
  position: relative;
  overflow: hidden;
}

.main-record-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.2), rgba(255,255,255,0));
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.main-record-button:hover::before {
  opacity: 1;
}

.main-record-button:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 48px rgba(0, 123, 255, 0.4);
}

.main-record-button.recording {
  background: linear-gradient(135deg, #dc3545, #c82333);
  box-shadow: 0 8px 32px rgba(220, 53, 69, 0.3);
  animation: recording-pulse 2s infinite;
}

.main-record-button.processing {
  background: linear-gradient(135deg, #ffc107, #e0a800);
  box-shadow: 0 8px 32px rgba(255, 193, 7, 0.3);
}

.button-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.main-button-icon {
  width: 32px;
  height: 32px;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}

.main-button-text {
  font-size: 1.1rem;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

.recording-timer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: rgba(220, 53, 69, 0.1);
  border-radius: 25px;
  color: #dc3545;
  font-weight: 600;
  font-size: 1.1rem;
  backdrop-filter: blur(10px);
  border: 2px solid rgba(220, 53, 69, 0.2);
}

.timer-icon {
  animation: pulse 2s infinite;
}

.timer-text {
  font-family: 'Courier New', monospace;
  letter-spacing: 1px;
}

/* Divider */
.divider {
  position: relative;
  width: 100%;
  max-width: 300px;
  height: 1px;
  background: linear-gradient(to right, transparent, #dee2e6, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
}

.divider-text {
  position: absolute;
  background: #f8f9fa;
  padding: 0 20px;
  color: #6c757d;
  font-weight: 500;
  font-size: 1rem;
}

/* Text Input Section */
.text-input-section {
  width: 100%;
  max-width: 600px;
}

.input-container {
  display: flex;
  gap: 15px;
  align-items: flex-end;
}

.input-wrapper {
  flex: 1;
  position: relative;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 2px solid #e9ecef;
  transition: all 0.3s ease;
}

.input-wrapper:focus-within {
  border-color: #007bff;
  box-shadow: 0 4px 20px rgba(0, 123, 255, 0.2);
}

.input-icon {
  position: absolute;
  top: 16px;
  left: 16px;
  color: #6c757d;
  z-index: 1;
}

.input-wrapper textarea {
  width: 100%;
  min-height: 100px;
  padding: 16px 16px 16px 50px;
  border: none;
  border-radius: 14px;
  resize: vertical;
  font-family: inherit;
  font-size: 1.1rem;
  background: transparent;
  outline: none;
  line-height: 1.5;
}

.input-wrapper textarea::placeholder {
  color: #adb5bd;
}

.main-send-button {
  width: 120px;
  height: 100px;
  border: none;
  border-radius: 16px;
  background: linear-gradient(135deg, #28a745, #1e7e34);
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 4px 20px rgba(40, 167, 69, 0.3);
  font-weight: 600;
}

.main-send-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(40, 167, 69, 0.4);
}

.main-send-button:active {
  transform: translateY(0);
}

.main-send-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.send-icon {
  filter: drop-shadow(0 1px 2px rgba(0,0,0,0.2));
}

.send-text {
  font-size: 0.9rem;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

/* Spinning Animation */
.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes recording-pulse {
  0%, 100% {
    box-shadow: 0 8px 32px rgba(220, 53, 69, 0.3), 0 0 0 0 rgba(220, 53, 69, 0.4);
  }
  50% {
    box-shadow: 0 8px 32px rgba(220, 53, 69, 0.5), 0 0 0 20px rgba(220, 53, 69, 0);
  }
}

/* Responsive */
@media (max-width: 768px) {
  .control-panel {
    padding: 20px;
  }
  
  .main-record-button {
    width: 150px;
    height: 150px;
  }
  
  .main-button-icon {
    width: 28px;
    height: 28px;
  }
  
  .main-button-text {
    font-size: 1rem;
  }
  
  .input-container {
    flex-direction: column;
    align-items: stretch;
  }
  
  .main-send-button {
    width: 100%;
    height: 60px;
    flex-direction: row;
    justify-content: center;
  }
}

/* Chat History */
.chat-history {
  padding: 30px;
  background: rgba(248, 249, 250, 0.3);
  min-height: 500px;
  max-height: 700px;
  overflow-y: auto;
}

.chat-empty {
  text-align: center;
  color: #6c757d;
  font-style: italic;
  padding: 80px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: #adb5bd;
}

.chat-message {
  margin-bottom: 30px;
  display: flex;
  align-items: flex-start;
  max-width: 100%;
}

/* 使用者訊息靠右對齊 */
.user-message {
  justify-content: flex-end;
  margin-left: 15%;
}

/* AI 助理訊息靠左對齊 */
.assistant-message {
  justify-content: flex-start;
  margin-right: 15%;
}

.message-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  max-width: 85%;
}

/* 使用者訊息的頭像在右邊 */
.user-message .message-wrapper {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.avatar-icon {
  width: 22px;
  height: 22px;
}

.user-message .message-avatar {
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
}

.assistant-message .message-avatar {
  background: linear-gradient(135deg, #28a745, #1e7e34);
  color: white;
}

.message-content {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  padding: 18px 20px;
  border-radius: 18px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
}

.user-message .message-content {
  background: rgba(227, 242, 253, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 18px;
  border-bottom-right-radius: 6px;
}

.user-message .message-content::after {
  content: '';
  position: absolute;
  bottom: 0;
  right: -8px;
  width: 0;
  height: 0;
  border-left: 8px solid rgba(227, 242, 253, 0.9);
  border-bottom: 8px solid transparent;
}

.assistant-message .message-content {
  border-bottom-left-radius: 6px;
}

.assistant-message .message-content::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: -8px;
  width: 0;
  height: 0;
  border-right: 8px solid rgba(255, 255, 255, 0.9);
  border-bottom: 8px solid transparent;
}

.message-text {
  margin: 0;
  line-height: 1.6;
  color: #2c3e50;
  font-size: 1rem;
}

.message-meta {
  margin-top: 10px;
  font-size: 0.85rem;
  color: #6c757d;
  display: flex;
  align-items: center;
  gap: 6px;
  opacity: 0.8;
}

.meta-icon {
  width: 12px;
  height: 12px;
}

/* Audio Player */
.message-audio {
  margin-top: 12px;
  padding: 0 20px;
}

.user-message .message-audio {
  margin-right: 54px;
}

.assistant-message .message-audio {
  margin-left: 54px;
}

.audio-player {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: rgba(248, 249, 250, 0.8);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.audio-icon {
  color: #007bff;
}

.audio-player audio {
  flex: 1;
  height: 32px;
}

/* Input Area */
.input-area {
  padding: 20px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.input-group {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.input-control {
  flex: 1;
}

.input-control textarea {
  width: 100%;
  min-height: 120px;
  padding: 16px;
  border: 1px solid #ced4da;
  border-radius: 12px;
  resize: vertical;
  font-family: inherit;
  font-size: 1.1rem;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.input-control textarea:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

/* Responsive */
@media (max-width: 768px) {
  .status-panel {
    grid-template-columns: 1fr;
  }
  
  .controls {
    flex-direction: column;
    align-items: center;
  }
  
  .input-group {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
    justify-content: center;
  }
}

/* Recording Animation */
@keyframes recording-pulse {
  0%, 100% {
    background: #dc3545;
    box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7);
  }
  50% {
    background: #c82333;
    box-shadow: 0 0 0 10px rgba(220, 53, 69, 0);


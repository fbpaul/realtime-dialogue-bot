<template>
  <div class="chat-app">
    <!-- 側邊欄 -->
    <div class="sidebar" :class="{ 'collapsed': sidebarCollapsed }">
      <div class="sidebar-header">
        <button 
          class="sidebar-toggle"
          @click="toggleSidebar"
        >
          <Menu :size="20" />
        </button>
        <div v-if="!sidebarCollapsed" class="logo">
          <MessageCircle :size="24" />
          <span>智慧語音助手</span>
        </div>
      </div>

      <div v-if="!sidebarCollapsed" class="sidebar-content">
        <button 
          class="new-chat-btn"
          @click="startNewConversation"
          :disabled="isProcessing"
        >
          <Plus :size="16" />
          新對話
        </button>

        <div class="chat-history">
          <div class="history-section">
            <h3>今日</h3>
            <div class="history-item active">
              <MessageCircle :size="16" />
              <span>語音對話體驗</span>
            </div>
          </div>
        </div>

        <div class="sidebar-footer">
          <div class="status-section">
            <h4>服務狀態</h4>
            <div class="status-item">
              <div class="status-dot" :class="{ 'online': sttStatus }"></div>
              <span>語音轉文字 (STT)</span>
            </div>
            <div class="status-item">
              <div class="status-dot" :class="{ 'online': llmStatus }"></div>
              <span>語言模型 (LLM)</span>
            </div>
            <div class="status-item">
              <div class="status-dot" :class="{ 'online': ttsStatus }"></div>
              <span>文字轉語音 (TTS)</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主內容區域 -->
    <div class="main-content" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <!-- 聊天訊息區域 -->
      <div class="chat-messages" ref="chatMessagesRef">
        <div v-if="chatHistory.length === 0" class="welcome-message">
          <div class="welcome-content">
            <MessageCircle :size="64" class="welcome-icon" />
            <h2>歡迎使用智慧語音助手</h2>
            <div class="feature-cards">
              <div class="feature-card">
                <Headphones :size="20" />
                <span>語音識別</span>
              </div>
              <div class="feature-card">
                <Brain :size="20" />
                <span>智能對話</span>
              </div>
              <div class="feature-card">
                <Volume2 :size="20" />
                <span>語音回應</span>
              </div>
            </div>
          </div>
        </div>
        
        <div 
          v-for="(message, index) in chatHistory" 
          :key="index" 
          class="message-wrapper"
        >
          <div :class="['message', message.type]">
            <div v-if="message.type === 'assistant'" class="message-avatar">
              <Bot :size="20" />
            </div>
            <div class="message-content">
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
                {{ formatTime(message.timestamp) }}
              </div>
            </div>
          </div>
          
          <div v-if="message.audioUrl && !message.isProcessing" class="audio-attachment">
            <button class="play-btn" @click="playAudio(message.audioUrl)">
              <Play :size="16" />
              <span>播放語音回應</span>
            </button>
          </div>
        </div>

        <!-- 底部間距 -->
        <div class="chat-bottom-spacer"></div>
      </div>
    </div>

    <!-- 懸浮輸入區域 -->
    <div class="floating-input" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <div class="input-container">
        <div class="input-wrapper">
          <textarea 
            v-model="inputText"
            placeholder="輸入訊息..."
            @keydown.enter.prevent="sendTextMessage"
            :disabled="isProcessing"
            rows="1"
            @input="adjustTextareaHeight"
            ref="textareaRef"
          ></textarea>
          <div class="input-actions">
            <button 
              :class="['mic-btn', { 'recording': isRecording }]"
              @click="toggleRecording"
              :disabled="isProcessing && !isRecording"
              :title="isRecording ? '停止錄音' : '開始語音輸入'"
            >
              <Mic v-if="!isRecording" :size="20" />
              <Square v-else :size="20" />
            </button>
            <button 
              class="send-btn"
              @click="sendTextMessage"
              :disabled="!inputText.trim() || isProcessing"
              title="發送訊息"
            >
              <Send :size="20" />
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
  Volume2,
  Menu,
  Plus
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
const textareaRef = ref(null)
const sidebarCollapsed = ref(false)

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

// 側邊欄控制
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 自動調整textarea高度
const adjustTextareaHeight = () => {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 120) + 'px'
  }
}

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
  
  // 重置textarea高度
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }
  
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
/* 全局樣式 */
.chat-app {
  height: 100vh;
  display: flex;
  background: #f7f7f8;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow: hidden;
}

/* 側邊欄樣式 */
.sidebar {
  width: 260px;
  background: #171717;
  border-right: 1px solid #404040;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #404040;
  display: flex;
  align-items: center;
  gap: 12px;
}

.sidebar-toggle {
  background: none;
  border: none;
  color: #e5e5e5;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: background-color 0.2s;
  flex-shrink: 0;
}

.sidebar-toggle:hover {
  background: #404040;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e5e5e5;
  font-weight: 600;
  font-size: 14px;
}

.sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 16px;
  overflow-y: auto;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: none;
  border: 1px solid #404040;
  border-radius: 8px;
  color: #e5e5e5;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  width: 100%;
}

.new-chat-btn:hover:not(:disabled) {
  background: #262626;
  border-color: #525252;
}

.new-chat-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-history {
  flex: 1;
}

.history-section h3 {
  color: #a3a3a3;
  font-size: 12px;
  font-weight: 500;
  margin: 0 0 8px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  color: #e5e5e5;
  font-size: 14px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.history-item:hover {
  background: #262626;
}

.history-item.active {
  background: #404040;
}

.sidebar-footer {
  border-top: 1px solid #404040;
  padding-top: 16px;
}

.status-section h4 {
  color: #a3a3a3;
  font-size: 12px;
  font-weight: 500;
  margin: 0 0 8px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  color: #e5e5e5;
  font-size: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #dc2626;
  transition: background-color 0.3s;
}

.status-dot.online {
  background: #16a34a;
}

/* 主內容區域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  min-height: 0;
}

.main-content.sidebar-collapsed {
  margin-left: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.chat-bottom-spacer {
  height: 120px;
  flex-shrink: 0;
}

/* 歡迎消息 */
.welcome-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  text-align: center;
}

.welcome-content {
  max-width: 480px;
}

.welcome-icon {
  color: #6b7280;
  margin-bottom: 24px;
}

.welcome-content h2 {
  color: #111827;
  font-size: 32px;
  font-weight: 600;
  margin: 0 0 32px 0;
}

.feature-cards {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.feature-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  color: #374151;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  cursor: pointer;
}

.feature-card:hover {
  border-color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* 訊息樣式 */
.message-wrapper {
  margin-bottom: 24px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 100%;
}

.message.user {
  flex-direction: row-reverse;
}

.message.user .message-content {
  background: #3b82f6;
  color: white;
  border-radius: 18px 18px 4px 18px;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #111827;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.message-content {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 18px 18px 18px 4px;
  padding: 12px 16px;
  max-width: 70%;
  position: relative;
}

.message-text {
  color: #111827;
  font-size: 15px;
  line-height: 1.5;
  margin: 0;
  word-wrap: break-word;
}

.message.user .message-text {
  color: white;
}

.processing-indicator {
  display: inline-flex;
  align-items: center;
  margin-left: 8px;
  color: #6b7280;
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
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.time-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 500;
}

.stt-time { background: #dcfce7; color: #166534; }
.llm-time { background: #fef3c7; color: #92400e; }
.tts-time { background: #dbeafe; color: #1e40af; }
.total-time { background: #f3e8ff; color: #7c3aed; font-weight: 600; }

.message-time {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

.audio-attachment {
  margin-top: 8px;
  margin-left: 44px;
}

.play-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #374151;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.play-btn:hover {
  background: #e5e7eb;
}

/* 懸浮輸入框 */
.floating-input {
  position: fixed;
  bottom: 0;
  left: 260px;
  right: 0;
  background: linear-gradient(transparent, #f7f7f8 20%);
  padding: 0 24px 24px;
  transition: left 0.3s ease;
  z-index: 100;
}

.floating-input.sidebar-collapsed {
  left: 60px;
}

.input-container {
  max-width: 800px;
  margin: 0 auto;
}

.input-wrapper {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 12px 16px;
  display: flex;
  align-items: flex-end;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: border-color 0.2s;
}

.input-wrapper:focus-within {
  border-color: #3b82f6;
}

.input-wrapper textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 15px;
  line-height: 1.5;
  color: #111827;
  background: transparent;
  font-family: inherit;
  min-height: 24px;
  max-height: 120px;
}

.input-wrapper textarea::placeholder {
  color: #9ca3af;
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.mic-btn, .send-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.mic-btn {
  background: #f3f4f6;
  color: #6b7280;
}

.mic-btn:hover:not(:disabled) {
  background: #e5e7eb;
  color: #374151;
}

.mic-btn.recording {
  background: #dc2626;
  color: white;
  animation: pulse 1.5s infinite;
}

.send-btn {
  background: #3b82f6;
  color: white;
}

.send-btn:hover:not(:disabled) {
  background: #2563eb;
}

.send-btn:disabled, .mic-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* 錄音狀態 */
.recording-status {
  margin-top: 8px;
  display: flex;
  justify-content: center;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(220, 38, 38, 0.1);
  border-radius: 20px;
  font-size: 13px;
  color: #dc2626;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #dc2626;
  animation: pulse-dot 1s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* 響應式設計 */
@media (max-width: 768px) {
  .sidebar {
    width: 280px;
    position: fixed;
    left: -280px;
    z-index: 200;
  }
  
  .sidebar.collapsed {
    left: -280px;
  }
  
  .floating-input {
    left: 0;
    padding: 0 16px 16px;
  }
  
  .floating-input.sidebar-collapsed {
    left: 0;
  }
  
  .chat-messages {
    padding: 16px;
  }
  
  .message-content {
    max-width: 85%;
  }
}
</style>

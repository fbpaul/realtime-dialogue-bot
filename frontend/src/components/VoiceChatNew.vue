<template>
  <div class="voice-chat-app">
    <!-- 聊天頭部 -->
    <div class="chat-header">
      <div class="header-left">
        <MessageCircle :size="24" />
        <div>
          <h1>智慧語音助手</h1>
          <p>支援語音對話、文字輸入，享受地端LLM、STT、TTS交互體驗</p>
        </div>
      </div>
      
      <div class="header-controls">
        <!-- TTS 控制開關 -->
        <button 
          :class="['tts-toggle-btn', { 'enabled': ttsEnabled }]"
          @click="toggleTTS"
          :title="ttsEnabled ? '關閉TTS' : '開啟TTS'"
        >
          <Volume2 v-if="ttsEnabled" :size="16" />
          <VolumeX v-else :size="16" />
          {{ ttsEnabled ? 'TTS開啟' : 'TTS關閉' }}
        </button>
        
        <button 
          class="new-chat-btn"
          @click="startNewConversation"
          :disabled="isProcessing"
        >
          <Plus :size="16" />
          新對話
        </button>
      </div>
    </div>

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
              <!-- TTS處理中指示器 -->
              <div v-if="message.showTtsProgress" class="tts-progress-indicator">
                <Volume2 :size="14" class="spinning" />
                <span>正在生成語音...</span>
              </div>
            </div>
            
            <!-- 處理時間顯示 -->
            <div v-if="message.processingTimes && !message.isProcessing" class="processing-times">
              <div v-if="message.processingTimes.stt_time" class="time-item stt-time">
                <Headphones :size="12" />
                <span>STT: {{ message.processingTimes.stt_time }}</span>
              </div>
              <div v-if="message.processingTimes.llm_time" class="time-item llm-time">
                <Brain :size="12" />
                <span>LLM: {{ message.processingTimes.llm_time }}</span>
              </div>
              <div v-if="message.processingTimes.tts_time" class="time-item tts-time">
                <Volume2 :size="12" />
                <span>TTS: {{ message.processingTimes.tts_time }}</span>
              </div>
              <div v-if="message.processingTimes.total_time" class="time-item total-time">
                <Timer :size="12" />
                <span>總計: {{ message.processingTimes.total_time }}</span>
              </div>
            </div>
            
            <div class="message-time">
              {{ formatTime(message.timestamp) }}
            </div>
          </div>
        </div>
        
        <div v-if="message.audioUrl && !message.isProcessing && !message.showTtsProgress" 
             :class="['audio-attachment', { 'user-audio': message.type === 'user' }]">
          <button class="play-btn" @click="playAudio(message.audioUrl)">
            <Play :size="16" />
            <span v-if="message.type === 'user'">播放原始錄音</span>
            <span v-else>播放語音回應</span>
          </button>
        </div>
      </div>

      <!-- 底部間距 -->
      <div class="chat-bottom-spacer"></div>
    </div>

    <!-- 懸浮輸入區域 -->
    <div class="floating-input">
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
  VolumeX,
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
const ttsEnabled = ref(true) // 控制是否啟用TTS

// 計算屬性
const allServicesOnline = computed(() => {
  return sttStatus.value && llmStatus.value && ttsStatus.value
})

// 媒體相關
let mediaRecorder = null
let audioChunks = []
let recordingTimer = null

// API 基礎 URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://10.204.245.170:8945'

// 切換TTS功能
const toggleTTS = () => {
  ttsEnabled.value = !ttsEnabled.value
}

// 自動調整textarea高度
const adjustTextareaHeight = () => {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 120) + 'px'
  }
}

// 滾動到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
    }
  })
}

// 格式化時間
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('zh-TW', {
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

// 播放音頻
const playAudio = (audioUrl) => {
  const audio = new Audio(audioUrl)
  audio.play()
}

// 開始新對話
const startNewConversation = () => {
  chatHistory.length = 0
  inputText.value = ''
}

// 開始/停止錄音
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
    recordingDuration.value = 0
    
    mediaRecorder.ondataavailable = (event) => {
      audioChunks.push(event.data)
    }
    
    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/wav' })
      handleAudioInput(audioBlob)
      
      // 停止所有音軌
      stream.getTracks().forEach(track => track.stop())
    }
    
    mediaRecorder.start()
    isRecording.value = true
    
    // 開始計時
    recordingTimer = setInterval(() => {
      recordingDuration.value++
    }, 1000)
    
  } catch (error) {
    console.error('無法獲取麥克風權限:', error)
    alert('無法獲取麥克風權限，請確認已允許網站使用麥克風')
  }
}

// 停止錄音
const stopRecording = () => {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop()
  }
  
  isRecording.value = false
  
  if (recordingTimer) {
    clearInterval(recordingTimer)
    recordingTimer = null
  }
}

// 處理音頻輸入
const handleAudioInput = async (audioBlob) => {
  const audioUrl = URL.createObjectURL(audioBlob)
  
  // 添加用戶音頻消息
  const userMessage = {
    type: 'user',
    text: '🎤 語音訊息',
    timestamp: Date.now(),
    audioUrl: audioUrl,
    isProcessing: true
  }
  
  chatHistory.push(userMessage)
  scrollToBottom()
  
  try {
    isProcessing.value = true
    
    // 調用STT API 並計算前端時間
    const sttStartTime = performance.now()
    const sttResult = await callSTTAPI(audioBlob)
    const sttEndTime = performance.now()
    const sttFrontendTime = Math.round(sttEndTime - sttStartTime)
    
    // 更新用戶消息為轉錄文本
    userMessage.text = sttResult.transcription
    userMessage.isProcessing = false
    userMessage.processingTimes = {
      stt_time: `${sttFrontendTime}ms`
    }
    
    // 調用LLM和TTS
    await processLLMAndTTS(sttResult.transcription, sttFrontendTime)
    
  } catch (error) {
    console.error('處理音頻失敗:', error)
    userMessage.text = '語音處理失敗'
    userMessage.isProcessing = false
  } finally {
    isProcessing.value = false
  }
}

// 發送文字消息
const sendTextMessage = async () => {
  if (!inputText.value.trim() || isProcessing.value) return
  
  const messageText = inputText.value.trim()
  inputText.value = ''
  
  // 重置textarea高度
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }
  
  // 添加用戶消息
  const userMessage = {
    type: 'user',
    text: messageText,
    timestamp: Date.now()
  }
  
  chatHistory.push(userMessage)
  scrollToBottom()
  
  try {
    isProcessing.value = true
    
    // 直接調用LLM和TTS（文字輸入沒有STT時間）
    await processLLMAndTTS(messageText, 0)
    
  } catch (error) {
    console.error('處理文字失敗:', error)
  } finally {
    isProcessing.value = false
  }
}

// 處理LLM和TTS
const processLLMAndTTS = async (userText, sttTime = 0) => {
  const assistantMessage = {
    type: 'assistant',
    text: '',
    timestamp: Date.now(),
    isProcessing: true,
    showTtsProgress: false,
    processingTimes: {}
  }
  
  chatHistory.push(assistantMessage)
  scrollToBottom()
  
  try {
    // 調用LLM API 並計算前端時間
    const llmStartTime = performance.now()
    const llmResult = await callLLMAPI(userText)
    const llmEndTime = performance.now()
    const llmFrontendTime = Math.round(llmEndTime - llmStartTime)
    
    assistantMessage.text = llmResult.response
    assistantMessage.processingTimes.llm_time = `${llmFrontendTime}ms`
    
    scrollToBottom()
    
    let ttsFrontendTime = 0
    // 如果啟用TTS，則生成語音
    if (ttsEnabled.value) {
      assistantMessage.showTtsProgress = true
      scrollToBottom()
      
      const ttsStartTime = performance.now()
      const ttsResult = await generateTTS(llmResult.response)
      const ttsEndTime = performance.now()
      ttsFrontendTime = Math.round(ttsEndTime - ttsStartTime)
      
      assistantMessage.audioUrl = ttsResult.audioUrl
      assistantMessage.processingTimes.tts_time = `${ttsFrontendTime}ms`
      assistantMessage.showTtsProgress = false
    }
    
    // 計算總時間
    const totalTime = sttTime + llmFrontendTime + ttsFrontendTime
    assistantMessage.processingTimes.total_time = `${totalTime}ms`
    
    assistantMessage.isProcessing = false
    scrollToBottom()
    
  } catch (error) {
    console.error('LLM/TTS處理失敗:', error)
    assistantMessage.text = '抱歉，我現在無法回應您的問題。'
    assistantMessage.isProcessing = false
    assistantMessage.showTtsProgress = false
  }
}

// 調用STT API
const callSTTAPI = async (audioBlob) => {
  const formData = new FormData()
  formData.append('file', audioBlob, 'audio.wav')
  
  const response = await fetch(`${API_BASE_URL}/stt`, {
    method: 'POST',
    body: formData
  })
  
  if (!response.ok) {
    throw new Error(`STT API 錯誤: ${response.status}`)
  }
  
  return await response.json()
}

// 調用LLM API
const callLLMAPI = async (text) => {
  const formData = new FormData()
  formData.append('text', text)
  
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    body: formData
  })
  
  if (!response.ok) {
    throw new Error(`LLM API 錯誤: ${response.status}`)
  }
  
  return await response.json()
}

// 生成TTS
const generateTTS = async (text) => {
  const response = await fetch(`${API_BASE_URL}/tts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      text: text,
      speaker_voice_path: null,
      cfg_scale: 1.0
    })
  })
  
  if (!response.ok) {
    throw new Error(`TTS API 錯誤: ${response.status}`)
  }
  
  const audioBlob = await response.blob()
  const audioUrl = URL.createObjectURL(audioBlob)
  
  return {
    audioUrl
  }
}

// 檢查服務狀態
const checkServiceStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`)
    if (response.ok) {
      sttStatus.value = true
      llmStatus.value = true
      ttsStatus.value = true
    }
  } catch (error) {
    console.error('服務狀態檢查失敗:', error)
  }
}

// 組件掛載時初始化
onMounted(async () => {
  await checkServiceStatus()
})
</script>

<style scoped>
.voice-chat-app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f7f7f8;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h1 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 600;
  color: #111827;
}

.header-left p {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

.header-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.tts-toggle-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  color: #374151;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.tts-toggle-btn.enabled {
  background: #dcfdf4;
  border-color: #10b981;
  color: #065f46;
}

.tts-toggle-btn:not(.enabled) {
  background: #fef2f2;
  border-color: #ef4444;
  color: #991b1b;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.new-chat-btn:hover:not(:disabled) {
  background: #2563eb;
}

.new-chat-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  padding-bottom: 100px;
  margin-bottom: 100px;
}

.welcome-message {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 50vh;
  text-align: center;
}

.welcome-content h2 {
  margin: 16px 0 24px 0;
  color: #374151;
  font-size: 28px;
  font-weight: 600;
}

.welcome-icon {
  color: #9ca3af;
}

.feature-cards {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 32px;
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

.message-wrapper {
  margin-bottom: 16px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  flex-shrink: 0;
}

.message.assistant .message-avatar {
  background: #dbeafe;
  color: #1e40af;
}

.message-content {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 12px 16px;
  position: relative;
}

.message.user .message-content {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.message-text {
  font-size: 15px;
  line-height: 1.5;
  word-wrap: break-word;
}

.processing-indicator, .tts-progress-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 12px;
  color: #6b7280;
}

.spinning {
  animation: spin 1s linear infinite;
}

.processing-times {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.time-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.time-item.stt-time { background: #fef3c7; color: #92400e; }
.time-item.llm-time { background: #dbeafe; color: #1e40af; }
.time-item.tts-time { background: #dcfce7; color: #166534; }
.time-item.total-time { background: #f3e8ff; color: #7c3aed; }

.message-time {
  font-size: 11px;
  color: #d3d3dd;
  margin-top: 4px;
}

.audio-attachment {
  margin-top: 8px;
}

.audio-attachment.user-audio {
  display: flex;
  justify-content: flex-end;
}

.play-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #374151;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.play-btn:hover {
  background: #e5e7eb;
}

.chat-bottom-spacer {
  height: 20px;
}

.floating-input {
  position: fixed;
  bottom: 0;
  left: 280px;
  right: 0;
  background: white;
  border-top: 1px solid #e5e7eb;
  padding: 16px 24px;
}

.input-container {
  max-width: 800px;
  margin: 0 auto;
}

.input-wrapper {
  display: flex;
  gap: 8px;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 8px;
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
  padding: 8px;
  font-size: 15px;
  line-height: 1.5;
  min-height: 20px;
  max-height: 120px;
  background: transparent;
}

.input-actions {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.mic-btn, .send-btn {
  padding: 10px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.mic-btn {
  background: #f3f4f6;
  color: #374151;
}

.mic-btn:hover:not(:disabled) {
  background: #e5e7eb;
}

.mic-btn.recording {
  background: #fee2e2;
  color: #dc2626;
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

.recording-status {
  margin-top: 12px;
  text-align: center;
}

.recording-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  color: #dc2626;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #dc2626;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* 響應式設計 */
@media (max-width: 768px) {
  .floating-input {
    left: 0;
  }
  
  .feature-cards {
    flex-direction: column;
    align-items: center;
  }
  
  .header-controls {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
  
  .tts-toggle-btn, .new-chat-btn {
    justify-content: center;
  }
}
</style>

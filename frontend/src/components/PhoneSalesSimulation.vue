<template>
  <div class="simulation-app">
    <div class="simulation-header">
      <div class="header-left">
        <CircleFadingArrowUp :size="24" />
        <div>
          <h1>電話銷售對話模擬</h1>
          <p class="subtitle">模擬真實電話銷售場景，測試 LLM、TTS、STT 完整流程</p>
        </div>
      </div>
    </div>

    <!-- 控制面板 -->
    <div class="control-panel">
      <div class="panel-row">
        <div class="input-group">
          <label>對話輪次:</label>
          <input 
            type="number" 
            v-model="rounds" 
            min="1" 
            max="10" 
            :disabled="isRunning"
          />
        </div>
        <div class="input-group">
          <label>API地址:</label>
          <input 
            type="text" 
            v-model="apiHost" 
            :disabled="isRunning"
            placeholder="http://localhost:8945"
          />
        </div>
        <button 
          :class="['start-btn', { 'running': isRunning }]"
          @click="isRunning ? stopSimulation() : startSimulation()"
          :disabled="!apiHost"
        >
          <Play v-if="!isRunning" :size="16" />
          <Square v-else :size="16" />
          {{ isRunning ? '停止模擬' : '開始模擬' }}
        </button>
      </div>
    </div>

    <!-- 狀態顯示 -->
    <div v-if="simulationStatus" class="status-panel">
      <div class="status-content">
        <Loader2 v-if="isRunning" :size="16" class="spinning" />
        <CheckCircle v-else-if="simulationComplete" :size="16" class="success" />
        <AlertCircle v-else-if="hasError" :size="16" class="error" />
        <Clock v-else :size="16" />
        <span>{{ simulationStatus }}</span>
      </div>
      <div v-if="currentProgress" class="progress-bar">
        <div 
          class="progress-fill" 
          :style="{ width: `${(currentProgress.current / currentProgress.total) * 100}%` }"
        ></div>
      </div>
    </div>

    <!-- 對話顯示區域 -->
    <div class="conversation-area" ref="conversationRef">
      <div v-if="conversationHistory.length === 0 && !isRunning" class="empty-state">
        <MessageCircle :size="64" class="empty-icon" />
        <h3>準備開始模擬</h3>
        <p>點擊「開始模擬」按鈕開始電話銷售對話模擬</p>
      </div>

      <!-- 對話記錄 -->
      <div 
        v-for="(message, index) in conversationHistory" 
        :key="index"
        class="conversation-round"
      >
        <div class="round-header">
          <div class="round-number">第 {{ message.round }} 輪</div>
          <div class="round-role">
            <User v-if="message.role === 'customer'" :size="16" />
            <Headphones v-else :size="16" />
            {{ message.role === 'customer' ? '客戶' : '銷售員小王' }}
          </div>
          <div v-if="message.isProcessing" class="processing-indicator">
            <Loader2 :size="14" class="spinning" />
            處理中...
          </div>
        </div>

        <!-- LLM 回應 -->
        <div class="message-content">
          <div class="message-text">{{ message.llmResponse || '正在生成回應...' }}</div>
          
          <!-- 處理時間指標 -->
          <div v-if="message.metrics && !message.isProcessing" class="metrics-row">
            <div v-if="message.metrics.llmTime" class="metric-item llm">
              <Brain :size="12" />
              <span>LLM: {{ message.metrics.llmTime }}ms</span>
            </div>
            <div v-if="message.metrics.ttsTime" class="metric-item tts">
              <Volume2 :size="12" />
              <span>TTS: {{ message.metrics.ttsTime }}ms</span>
            </div>
            <div v-if="message.metrics.sttTime" class="metric-item stt">
              <Mic :size="12" />
              <span>STT: {{ message.metrics.sttTime }}ms</span>
            </div>
            <div v-if="message.metrics.accuracy !== undefined" class="metric-item accuracy">
              <Target :size="12" />
              <span>準確度: {{ message.metrics.accuracy }}%</span>
            </div>
          </div>

          <!-- 音檔播放 -->
          <div v-if="message.audioUrl && !message.isProcessing" class="audio-player">
            <button class="play-audio-btn" @click="playAudio(message.audioUrl)">
              <Play :size="14" />
              播放語音
            </button>
          </div>

          <!-- STT 結果對比 -->
          <div v-if="message.sttResult && !message.isProcessing" class="stt-comparison">
            <div class="comparison-label">STT 轉譯結果:</div>
            <div class="stt-text">{{ message.sttResult }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 統計報告 -->
    <div v-if="simulationComplete && finalReport" class="report-section">
      <h2>模擬報告</h2>
      
      <div class="report-grid">
        <!-- 基本統計 -->
        <div class="report-card">
          <h3>基本統計</h3>
          <div class="stat-row">
            <span>完成輪次:</span>
            <span>{{ finalReport.completedRounds }}</span>
          </div>
          <div class="stat-row">
            <span>總耗時:</span>
            <span>{{ finalReport.totalTime }}s</span>
          </div>
          <div class="stat-row">
            <span>平均每輪:</span>
            <span>{{ finalReport.avgTimePerRound }}s</span>
          </div>
        </div>

        <!-- LLM 性能 -->
        <div class="report-card">
          <h3>LLM 性能</h3>
          <div class="stat-row">
            <span>平均響應時間:</span>
            <span>{{ finalReport.llm.avgTime }}ms</span>
          </div>
          <div class="stat-row">
            <span>平均生成速度:</span>
            <span>{{ finalReport.llm.avgSpeed }} 字/秒</span>
          </div>
        </div>

        <!-- TTS 性能 -->
        <div class="report-card">
          <h3>TTS 性能</h3>
          <div class="stat-row">
            <span>平均轉換時間:</span>
            <span>{{ finalReport.tts.avgTime }}ms</span>
          </div>
          <div class="stat-row">
            <span>平均轉換速度:</span>
            <span>{{ finalReport.tts.avgSpeed }} 字/秒</span>
          </div>
        </div>

        <!-- STT 性能 -->
        <div class="report-card">
          <h3>STT 性能</h3>
          <div class="stat-row">
            <span>平均識別時間:</span>
            <span>{{ finalReport.stt.avgTime }}ms</span>
          </div>
          <div class="stat-row">
            <span>平均轉譯速度:</span>
            <span>{{ finalReport.stt.avgSpeed }} 字/秒</span>
          </div>
          <div class="stat-row">
            <span>平均準確度:</span>
            <span>{{ finalReport.stt.avgAccuracy }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { 
  Play, 
  Square, 
  MessageCircle, 
  User, 
  Headphones, 
  Brain, 
  Volume2, 
  Mic, 
  Target,
  Loader2,
  CheckCircle,
  AlertCircle,
  Clock,
  CircleFadingArrowUp
} from 'lucide-vue-next'

// 定義 emit
const emit = defineEmits(['simulation-status-change'])

// 響應式數據
const rounds = ref(10)
const apiHost = ref('http://10.204.245.170:8945')
const isRunning = ref(false)
const simulationComplete = ref(false)
const hasError = ref(false)
const simulationStatus = ref('')
const currentProgress = ref(null)
const conversationHistory = reactive([])
const conversationRef = ref(null)
const finalReport = ref(null)

// 監聽 isRunning 狀態變化，發送事件給父組件
watch(isRunning, (newValue) => {
  emit('simulation-status-change', {
    isRunning: newValue,
    isComplete: simulationComplete.value,
    hasError: hasError.value
  })
})

// 銷售對話提示詞
const salesDialoguePrompts = [
  {
    role: "salesperson",
    prompt: "你是一位專業的台北富邦銀行電銷專員，名叫小王，正在進行電話銷售。請用友善但專業的語調打電話給客戶，介紹你們公司的信貸產品。記住這是對話的開始，要自然、簡潔地開場。"
  },
  {
    role: "customer",
    prompt: "你是一位30歲的上班族李先生，剛接到信貸銷售電話。你對信貸產品有些基本了解，但對電話銷售有些戒心。請根據銷售員的介紹給出自然的回應，可以表現出一些興趣但也有疑慮。回覆要簡潔。"
  },
  {
    role: "salesperson", 
    prompt: "根據客戶的回應，請介紹你們信貸產品的主要優勢，如利率優惠、審核快速、彈性還款等。要針對客戶的疑慮給出回應，語調要有說服力但不強硬。回覆要簡潔。"
  },
  {
    role: "customer",
    prompt: "你對產品有些興趣，但作為謹慎的消費者，想了解更多具體細節，如每月還款多少、利率、手續費等。請根據之前的對話內容提出具體問題。回覆要簡潔。"
  },
  {
    role: "salesperson",
    prompt: "客戶詢問了具體的產品細節，請提供專業的還款資訊和利率說明。要針對客戶提出的具體問題給出回答，展現專業知識並建立信任。回覆要簡潔。"
  },
  {
    role: "customer", 
    prompt: "聽了銷售員的詳細介紹，你覺得產品還不錯，但需要時間考慮，想跟家人討論一下。請根據前面的對話表現出認真考慮但不急於決定的態度。回覆要簡潔。"
  },
  {
    role: "salesperson",
    prompt: "客戶需要考慮時間，這很正常。請提供一些促進成交的誘因，如本月限時優惠、手續費折抵等額外服務，但要保持專業不能太推銷。要尊重客戶需要討論的想法。回覆要簡潔。"
  },
  {
    role: "customer",
    prompt: "你對優惠有興趣，但還是有些擔心，想比較其他銀行的類似產品，或者想了解是否有更便宜的方案。表現出精明消費者的態度，根據對話內容提出合理疑問。回覆要簡潔。"
  },
  {
    role: "salesperson",
    prompt: "客戶想比較其他產品這很正常，請專業地強調你們公司的獨特優勢和競爭力，比如服務品質、撥款速度、後續客服等。要尊重客戶的決定過程，不要過於強勢。回覆要簡潔。"
  },
  {
    role: "customer",
    prompt: "經過這次詳細的對話，你決定先不立即購買，但對銷售員小王的專業態度印象很好。你願意留下聯絡方式，表示可能會在未來一周內給出最終決定。回覆要簡潔。"
  }
]

// API 調用函數
const callLLMAPI = async (prompt, role, conversationHistory) => {
  const startTime = performance.now()
  
  try {
    // 構建包含歷史的完整提示
    const fullPrompt = buildPromptWithHistory(prompt, role, conversationHistory)
    
    const formData = new FormData()
    formData.append('text', fullPrompt)
    
    const response = await fetch(`${apiHost.value}/chat`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error(`LLM API 錯誤: ${response.status}`)
    }
    
    const result = await response.json()
    const llmTime = performance.now() - startTime
    
    return {
      response: result.response,
      time: llmTime,
      charCount: result.response.length
    }
  } catch (error) {
    console.error('LLM API 調用失敗:', error)
    throw error
  }
}

const callTTSAPI = async (text) => {
  const startTime = performance.now()
  
  try {
    const response = await fetch(`${apiHost.value}/tts`, {
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
    const ttsTime = performance.now() - startTime
    
    return {
      audioUrl,
      time: ttsTime
    }
  } catch (error) {
    console.error('TTS API 調用失敗:', error)
    throw error
  }
}

const callSTTAPI = async (audioBlob) => {
  const startTime = performance.now()
  
  try {
    const formData = new FormData()
    formData.append('file', audioBlob, 'audio.wav')
    
    const response = await fetch(`${apiHost.value}/stt`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error(`STT API 錯誤: ${response.status}`)
    }
    
    const result = await response.json()
    const sttTime = performance.now() - startTime
    
    return {
      transcription: result.transcription,
      time: sttTime
    }
  } catch (error) {
    console.error('STT API 調用失敗:', error)
    throw error
  }
}

// 輔助函數
const buildPromptWithHistory = (currentPrompt, currentRole, history) => {
  if (history.length === 0) {
    return `角色設定：${currentPrompt}\n\n請直接開始對話，不要說「作為...」這樣的開場白。`
  }
  
  let historyText = "對話歷史記錄：\n"
  history.forEach((msg, index) => {
    const roleName = msg.role === "salesperson" ? "銷售員" : "客戶"
    historyText += `${index + 1}. ${roleName}：${msg.llmResponse}\n`
  })
  
  const currentRoleName = currentRole === "salesperson" ? "銷售員" : "客戶"
  
  return `${historyText}

角色指示：
你現在是${currentRoleName}，請根據以上對話歷史和以下角色設定進行回應：

${currentPrompt}

請確保回應：
1. 與之前的對話內容保持連貫
2. 符合角色設定
3. 自然流暢，不要重複之前說過的話
4. 直接回應，不要說「作為...」這樣的開場白

請直接開始你的回應：`
}

// 移除文字中的所有標點符號（全型和半型）
const removePunctuation = (text) => {
  if (!text) return ''
  
  // 移除全型和半型標點符號，保留中文字符、英文字母、數字和空白
  return text
    .replace(/[\u3000-\u303F\uFF00-\uFFEF]/g, '') // 移除全型標點符號
    .replace(/[^\w\s\u4e00-\u9fff]/g, '') // 移除半型標點符號，保留中文字符
    .replace(/\s+/g, ' ') // 將多個空白合併為單個空白
    .trim()
    .toLowerCase()
}

// 計算 Levenshtein 距離（編輯距離）
const calculateLevenshteinDistance = (str1, str2) => {
  const len1 = str1.length
  const len2 = str2.length
  
  // 創建二維數組來存儲距離
  const matrix = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(null))
  
  // 初始化第一行和第一列
  for (let i = 0; i <= len1; i++) {
    matrix[i][0] = i
  }
  for (let j = 0; j <= len2; j++) {
    matrix[0][j] = j
  }
  
  // 填充矩陣
  for (let i = 1; i <= len1; i++) {
    for (let j = 1; j <= len2; j++) {
      const cost = str1[i - 1] === str2[j - 1] ? 0 : 1
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,     // 刪除
        matrix[i][j - 1] + 1,     // 插入
        matrix[i - 1][j - 1] + cost // 替換
      )
    }
  }
  
  return matrix[len1][len2]
}

// 使用 Levenshtein 距離計算 STT 準確度
const calculateAccuracy = (original, transcribed) => {
  if (!original || !transcribed) return 0
  
  // 清理文字，移除標點符號
  const cleanOriginal = removePunctuation(original)
  const cleanTranscribed = removePunctuation(transcribed)
  
  // 如果清理後的文字完全相同，準確度為 100%
  if (cleanOriginal === cleanTranscribed) return 100
  
  // 如果其中一個為空，準確度為 0%
  if (cleanOriginal.length === 0 || cleanTranscribed.length === 0) return 0
  
  // 計算編輯距離
  const editDistance = calculateLevenshteinDistance(cleanOriginal, cleanTranscribed)
  
  // 計算準確度：1 - (編輯距離 / 較長字串的長度)
  const maxLength = Math.max(cleanOriginal.length, cleanTranscribed.length)
  const accuracy = Math.max(0, (1 - editDistance / maxLength) * 100)
  
  return Math.round(accuracy)
}

// 主要模擬函數
const startSimulation = async () => {
  if (isRunning.value) return
  
  isRunning.value = true
  simulationComplete.value = false
  hasError.value = false
  conversationHistory.length = 0
  finalReport.value = null
  
  simulationStatus.value = '正在初始化模擬...'
  currentProgress.value = { current: 0, total: rounds.value }
  
  try {
    // 測試 API 連接
    simulationStatus.value = '測試 API 連接...'
    const healthResponse = await fetch(`${apiHost.value}/health`)
    if (!healthResponse.ok) {
      throw new Error('API 連接失敗')
    }
    
    simulationStatus.value = '開始對話模擬...'
    
    const metrics = {
      llmTimes: [],
      ttsTimes: [],
      sttTimes: [],
      accuracies: [],
      charCounts: []
    }
    
    const simulationStartTime = performance.now()
    
    // 執行每一輪對話
    for (let i = 0; i < Math.min(rounds.value, salesDialoguePrompts.length); i++) {
      if (!isRunning.value) break // 檢查是否被停止
      
      const promptData = salesDialoguePrompts[i]
      currentProgress.value.current = i + 1
      
      simulationStatus.value = `第 ${i + 1} 輪對話 - ${promptData.role === 'salesperson' ? '銷售員' : '客戶'}`
      
      // 創建對話輪次記錄
      const roundRecord = {
        round: i + 1,
        role: promptData.role,
        prompt: promptData.prompt,
        isProcessing: true,
        llmResponse: '',
        audioUrl: '',
        sttResult: '',
        metrics: {}
      }
      
      conversationHistory.push(roundRecord)
      await nextTick()
      scrollToBottom()
      
      try {
        // Step 1: LLM 生成
        const llmResult = await callLLMAPI(promptData.prompt, promptData.role, conversationHistory.slice(0, -1))
        roundRecord.llmResponse = llmResult.response
        roundRecord.metrics.llmTime = Math.round(llmResult.time)
        
        await nextTick()
        scrollToBottom()
        
        // Step 2: TTS 轉換
        const ttsResult = await callTTSAPI(llmResult.response)
        roundRecord.audioUrl = ttsResult.audioUrl
        roundRecord.metrics.ttsTime = Math.round(ttsResult.time)
        
        // Step 3: STT 轉換
        const audioResponse = await fetch(ttsResult.audioUrl)
        const audioBlob = await audioResponse.blob()
        const sttResult = await callSTTAPI(audioBlob)
        
        roundRecord.sttResult = sttResult.transcription
        roundRecord.metrics.sttTime = Math.round(sttResult.time)
        roundRecord.metrics.accuracy = calculateAccuracy(llmResult.response, sttResult.transcription)
        
        // 完成處理
        roundRecord.isProcessing = false
        
        // 記錄指標
        metrics.llmTimes.push(llmResult.time)
        metrics.ttsTimes.push(ttsResult.time)
        metrics.sttTimes.push(sttResult.time)
        metrics.accuracies.push(roundRecord.metrics.accuracy)
        metrics.charCounts.push(llmResult.charCount)
        
      } catch (error) {
        console.error(`第 ${i + 1} 輪對話失敗:`, error)
        roundRecord.isProcessing = false
        roundRecord.llmResponse = '處理失敗'
        hasError.value = true
      }
      
      await nextTick()
      scrollToBottom()
    }
    
    const totalTime = (performance.now() - simulationStartTime) / 1000
    
    // 生成最終報告
    generateFinalReport(metrics, totalTime)
    
    simulationComplete.value = true
    simulationStatus.value = `模擬完成！共完成 ${conversationHistory.length} 輪對話`
    
  } catch (error) {
    console.error('模擬失敗:', error)
    simulationStatus.value = `模擬失敗: ${error.message}`
    hasError.value = true
  } finally {
    isRunning.value = false
    currentProgress.value = null
  }
}

const stopSimulation = () => {
  isRunning.value = false
  simulationStatus.value = '模擬已停止'
}

const generateFinalReport = (metrics, totalTime) => {
  const avgLLMTime = metrics.llmTimes.length > 0 ? 
    Math.round(metrics.llmTimes.reduce((a, b) => a + b, 0) / metrics.llmTimes.length) : 0
  
  const avgTTSTime = metrics.ttsTimes.length > 0 ? 
    Math.round(metrics.ttsTimes.reduce((a, b) => a + b, 0) / metrics.ttsTimes.length) : 0
    
  const avgSTTTime = metrics.sttTimes.length > 0 ? 
    Math.round(metrics.sttTimes.reduce((a, b) => a + b, 0) / metrics.sttTimes.length) : 0
    
  const avgAccuracy = metrics.accuracies.length > 0 ? 
    Math.round(metrics.accuracies.reduce((a, b) => a + b, 0) / metrics.accuracies.length) : 0
  
  const totalChars = metrics.charCounts.reduce((a, b) => a + b, 0)
  const totalLLMTime = metrics.llmTimes.reduce((a, b) => a + b, 0) / 1000
  const totalTTSTime = metrics.ttsTimes.reduce((a, b) => a + b, 0) / 1000
  const totalSTTTime = metrics.sttTimes.reduce((a, b) => a + b, 0) / 1000
  
  const llmSpeed = totalLLMTime > 0 ? Math.round(totalChars / totalLLMTime) : 0
  const ttsSpeed = totalTTSTime > 0 ? Math.round(totalChars / totalTTSTime) : 0
  const sttSpeed = totalSTTTime > 0 ? Math.round(totalChars / totalSTTTime) : 0
  
  finalReport.value = {
    completedRounds: conversationHistory.length,
    totalTime: totalTime.toFixed(2),
    avgTimePerRound: (totalTime / conversationHistory.length).toFixed(2),
    llm: {
      avgTime: avgLLMTime,
      avgSpeed: llmSpeed
    },
    tts: {
      avgTime: avgTTSTime,
      avgSpeed: ttsSpeed
    },
    stt: {
      avgTime: avgSTTTime,
      avgAccuracy: avgAccuracy,
      avgSpeed: sttSpeed
    }
  }
}

const playAudio = (audioUrl) => {
  const audio = new Audio(audioUrl)
  audio.play()
}

const scrollToBottom = () => {
  if (conversationRef.value) {
    conversationRef.value.scrollTop = conversationRef.value.scrollHeight
  }
}

// 生命週期
onMounted(() => {
  // 初始化
})
</script>

<style scoped>
.simulation-app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f7f7f8;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.simulation-header {
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

.simulation-header h1 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 600;
  color: #111827;
}

.subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 16px;
}

.control-panel {
  padding: 20px 24px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.panel-row {
  display: flex;
  align-items: center;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-group label {
  font-weight: 500;
  color: #374151;
  white-space: nowrap;
}

.input-group input {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.input-group input[type="number"] {
  width: 80px;
}

.input-group input[type="text"] {
  width: 300px;
}

.start-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.start-btn:hover:not(:disabled) {
  background: #2563eb;
}

.start-btn.running {
  background: #dc2626;
}

.start-btn.running:hover {
  background: #b91c1c;
}

.start-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.status-panel {
  padding: 16px 24px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.status-content {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #374151;
  font-weight: 500;
  max-width: 1200px;
  margin: 0 auto;
}

.spinning {
  animation: spin 1s linear infinite;
}

.success {
  color: #16a34a;
}

.error {
  color: #dc2626;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  margin-top: 8px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #3b82f6;
  transition: width 0.3s ease;
}

.conversation-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 50vh;
  text-align: center;
}

.empty-icon {
  color: #9ca3af;
  margin-bottom: 16px;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  color: #374151;
  font-size: 20px;
}

.empty-state p {
  margin: 0;
  color: #6b7280;
}

.conversation-round {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  margin-bottom: 16px;
  overflow: hidden;
}

.round-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.round-number {
  background: #3b82f6;
  color: white;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.round-role {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  color: #374151;
}

.processing-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #6b7280;
  font-size: 14px;
  margin-left: auto;
}

.message-content {
  padding: 16px;
}

.message-text {
  color: #111827;
  font-size: 15px;
  line-height: 1.6;
  margin-bottom: 12px;
}

.metrics-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.metric-item.llm { background: #fef3c7; color: #92400e; }
.metric-item.tts { background: #dbeafe; color: #1e40af; }
.metric-item.stt { background: #dcfce7; color: #166534; }
.metric-item.accuracy { background: #f3e8ff; color: #7c3aed; }

.audio-player {
  margin-bottom: 12px;
}

.play-audio-btn {
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

.play-audio-btn:hover {
  background: #e5e7eb;
}

.stt-comparison {
  padding: 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.comparison-label {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 4px;
}

.stt-text {
  color: #374151;
  font-size: 14px;
}

.report-section {
  padding: 24px;
  background: white;
  border-top: 1px solid #e5e7eb;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.report-section h2 {
  margin: 0 0 20px 0;
  color: #111827;
  font-size: 24px;
  font-weight: 600;
}

.report-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.report-card {
  padding: 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.report-card h3 {
  margin: 0 0 12px 0;
  color: #374151;
  font-size: 16px;
  font-weight: 600;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  color: #6b7280;
  font-size: 14px;
  border-bottom: 1px solid #e5e7eb;
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-row span:last-child {
  font-weight: 600;
  color: #111827;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 響應式設計 */
@media (max-width: 768px) {
  .panel-row {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .input-group {
    justify-content: space-between;
  }
  
  .input-group input[type="text"] {
    width: 200px;
  }
  
  .conversation-area {
    padding: 16px;
  }
  
  .report-grid {
    grid-template-columns: 1fr;
  }
}
</style>

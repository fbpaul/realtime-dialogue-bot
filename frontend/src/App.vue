<template>
  <div id="app">
    <div class="app-layout">
      <!-- Sidebar -->
      <div class="sidebar">
        <div class="sidebar-header">
          <h2>金控數科 語音對話機器人</h2>
        </div>
        
        <nav class="sidebar-nav">
          <div 
            :class="['nav-item', { 
              active: currentView === 'voice-chat', 
              disabled: isSimulationRunning 
            }]"
            @click="switchView('voice-chat')"
            :title="isSimulationRunning ? '電話銷售模擬進行中，無法切換到語音對話' : ''"
          >
            <MessageCircle :size="20" />
            <span>智慧語音助手</span>
          </div>
          
          <div 
            :class="['nav-item', { active: currentView === 'sales-simulation' }]"
            @click="switchView('sales-simulation')"
          >
            <Phone :size="20" />
            <span>電話銷售模擬</span>
          </div>
        </nav>
        
        <!-- 操作教學 -->
        <div class="help-section">
          <div class="help-title">
            <span>操作教學</span>
          </div>
          <div class="help-content">
            <p class="help-subtitle">若要在Google Chrome啟用語音服務，請新增信任網站：</p>
            <ol class="help-steps">
              <li>
                前往 <code>chrome://flags/</code><br>
                搜尋 "Insecure origins treated as secure" 改成 <strong>Enable</strong>
              </li>
              <li>
                前往 <code>chrome://flags/#unsafely-treat-insecure-origin-as-secure</code><br>
                輸入本網址 (若有多網址則用逗號隔開)
              </li>
            </ol>
          </div>
        </div>
        
        <!-- 後端狀態檢查 -->
        <div class="status-section">
          <div class="status-title">
            <span>後端服務狀態</span>
            <button class="refresh-btn" @click="checkBackendStatus" :disabled="isCheckingStatus">
              <RotateCcw :size="12" :class="{ spinning: isCheckingStatus }" />
            </button>
          </div>
          <div class="status-list">
            <div class="status-item">
              <div class="status-indicator" :class="{ online: sttStatus, offline: !sttStatus }"></div>
              <span class="status-label">STT 語音識別</span>
            </div>
            <div class="status-item">
              <div class="status-indicator" :class="{ online: llmStatus, offline: !llmStatus }"></div>
              <span class="status-label">LLM 對話模型</span>
            </div>
            <div class="status-item">
              <div class="status-indicator" :class="{ online: ttsStatus, offline: !ttsStatus }"></div>
              <span class="status-label">TTS 語音合成</span>
            </div>
          </div>
        </div>
        
        <div class="sidebar-footer">
          <div class="version-info">
            <span>v2.0</span>
          </div>
        </div>
      </div>
      
      <!-- Main Content -->
      <div class="main-content">
        <VoiceChatNew v-if="currentView === 'voice-chat'" />
        <PhoneSalesSimulation 
          v-if="currentView === 'sales-simulation'" 
          @simulation-status-change="handleSimulationStatusChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { MessageCircle, Phone, RotateCcw } from 'lucide-vue-next'
import VoiceChatNew from './components/VoiceChatNew.vue'
import PhoneSalesSimulation from './components/PhoneSalesSimulation.vue'

// API 基礎地址
const API_BASE_URL = 'http://10.204.245.170:8945'

const currentView = ref('voice-chat')
const isSimulationRunning = ref(false)

// 後端狀態
const sttStatus = ref(false)
const llmStatus = ref(false)
const ttsStatus = ref(false)
const isCheckingStatus = ref(false)

const switchView = (view) => {
  // 如果模擬正在運行且試圖切換到語音對話，則阻止切換
  if (view === 'voice-chat' && isSimulationRunning.value) {
    return
  }
  currentView.value = view
}

const handleSimulationStatusChange = (status) => {
  isSimulationRunning.value = status.isRunning
}

// 檢查後端狀態
const checkBackendStatus = async () => {
  isCheckingStatus.value = true
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
  } finally {
    isCheckingStatus.value = false
  }
}

// 初始化
onMounted(async () => {
  await checkBackendStatus()
})
</script>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

#app {
  min-height: 100vh;
  background: #ffffff;
  color: #333333;
}

.app-layout {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 280px;
  background: #1e293b;
  color: white;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #334155;
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid #334155;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #f1f5f9;
}

.sidebar-nav {
  flex: 1;
  padding: 20px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.2s;
  color: #cbd5e1;
}

.nav-item:hover {
  background: #334155;
  color: #f1f5f9;
}

.nav-item.active {
  background: #3b82f6;
  color: white;
  border-right: 3px solid #60a5fa;
}

.nav-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.nav-item.disabled:hover {
  background: transparent;
  color: #cbd5e1;
}

.nav-item span {
  font-weight: 500;
}

.help-section {
  padding: 16px 20px;
  border-top: 1px solid #334155;
  border-bottom: 1px solid #334155;
  background: #0f172a;
}

.help-title {
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 12px;
}

.help-content {
  font-size: 12px;
  color: #cbd5e1;
  line-height: 1.4;
}

.help-subtitle {
  margin: 0 0 8px 0;
  font-weight: 500;
  color: #e2e8f0;
}

.help-steps {
  margin: 0;
  padding-left: 16px;
}

.help-steps li {
  margin-bottom: 8px;
  color: #94a3b8;
}

.help-steps code {
  background: #1e293b;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: #60a5fa;
}

.help-steps strong {
  color: #10b981;
  font-weight: 600;
}

.status-section {
  padding: 16px 20px;
  border-top: 1px solid #334155;
  border-bottom: 1px solid #334155;
  background: #0f172a;
}

.status-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 12px;
}

.refresh-btn {
  background: none;
  border: 1px solid #334155;
  color: #cbd5e1;
  padding: 4px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.refresh-btn:hover:not(:disabled) {
  background: #334155;
  color: #f1f5f9;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinning {
  animation: spin 1s linear infinite;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #cbd5e1;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #64748b;
  transition: all 0.2s;
}

.status-indicator.online {
  background: #10b981;
  box-shadow: 0 0 4px rgba(16, 185, 129, 0.4);
}

.status-indicator.offline {
  background: #ef4444;
  box-shadow: 0 0 4px rgba(239, 68, 68, 0.4);
}

.status-label {
  font-weight: 500;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid #334155;
  text-align: center;
}

.version-info {
  color: #64748b;
  font-size: 12px;
}

.main-content {
  flex: 1;
  overflow: hidden;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .app-layout {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    height: auto;
    flex-direction: row;
    align-items: center;
    padding: 0;
  }
  
  .sidebar-header {
    flex: 1;
    padding: 16px;
    border-bottom: none;
    border-right: 1px solid #334155;
  }
  
  .sidebar-header h2 {
    font-size: 16px;
  }
  
  .sidebar-nav {
    flex: none;
    padding: 0;
    display: flex;
  }
  
  .nav-item {
    padding: 16px;
    border-right: none;
    border-bottom: 3px solid transparent;
  }
  
  .nav-item.active {
    border-right: none;
    border-bottom: 3px solid #60a5fa;
  }
  
  .nav-item span {
    display: none;
  }
  
  .help-section {
    display: none;
  }
  
  .status-section {
    display: none;
  }
  
  .sidebar-footer {
    display: none;
  }
  
  .main-content {
    height: calc(100vh - 70px);
  }
}
</style>

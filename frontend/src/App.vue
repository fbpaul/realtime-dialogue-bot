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
import { ref } from 'vue'
import { MessageCircle, Phone } from 'lucide-vue-next'
import VoiceChatNew from './components/VoiceChatNew.vue'
import PhoneSalesSimulation from './components/PhoneSalesSimulation.vue'

const currentView = ref('voice-chat')
const isSimulationRunning = ref(false)

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
  
  .sidebar-footer {
    display: none;
  }
  
  .main-content {
    height: calc(100vh - 70px);
  }
}
</style>

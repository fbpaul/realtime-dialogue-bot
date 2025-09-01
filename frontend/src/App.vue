<template>
  <div id="app">
    <div class="header">
      <h1>
        <MessageCircle :size="32" class="header-icon" />
        即時語音對話系統
      </h1>
      <p>
        <Zap :size="16" />
        支援語音輸入、智能對話和語音輸出
      </p>
    </div>
    <VoiceChat />
  </div>
</template>

<script setup>
import VoiceChat from './components/VoiceChat.vue'
import { MessageCircle, Zap } from 'lucide-vue-next'
</script>

<style>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  color: #333333;
}

.header {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  margin-bottom: 20px;
}

.header h1 {
  margin: 0 0 10px 0;
  font-size: 2.5rem;
  font-weight: 300;
  color: #2c3e50;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.header-icon {
  color: #007bff;
}

.header p {
  margin: 0;
  color: #6c757d;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
</style>

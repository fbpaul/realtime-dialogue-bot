#!/bin/bash

# 前端啟動腳本

echo "🚀 啟動即時語音對話前端服務..."

# 檢查是否在正確的目錄
if [ ! -f "package.json" ]; then
    echo "❌ 請在前端專案根目錄執行此腳本"
    exit 1
fi

# 檢查 Node.js 和 npm
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安裝，請先安裝 Node.js"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安裝，請先安裝 npm"
    exit 1
fi

# 安裝依賴套件
echo "📦 安裝依賴套件..."
npm install

# 檢查後端服務狀態
echo "🔍 檢查後端服務狀態..."
BACKEND_URL="http://10.204.245.170:8945"

if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo "✅ 後端服務運行正常"
else
    echo "⚠️  警告: 後端服務似乎未運行，請先啟動後端服務"
fi

# 啟動開發服務器
echo "🌐 啟動前端開發服務器..."
echo "📡 前端地址: http://10.204.245.170:8946"
echo "🔗 後端代理: $BACKEND_URL"

npm run dev

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import tempfile
import os
import uuid
import time
from datetime import datetime
from typing import Optional, List

from app.stt import STTService
from app.tts_vibe import TTSVibeService  # 改用 VibeVoice
from app.chat import ChatService

# Pydantic 模型定義
class TTSRequest(BaseModel):
    text: str = Field(..., description="要合成的文字")
    speaker_voice_path: Optional[str] = Field(None, description="語者音檔路徑")
    cfg_scale: Optional[float] = Field(1.0, description="CFG 尺度參數（0.5-2.0）")

app = FastAPI(title="Realtime Dialogue API", version="1.0.0")

# CORS 設定（允許前端呼叫）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境請改成具體的前端網址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服務
stt_service = STTService()
tts_service = TTSVibeService()  # 改用 VibeVoice
chat_service = ChatService()

@app.on_event("startup")
async def startup_event():
    """啟動時初始化模型"""
    print("正在初始化 STT、TTS (VibeVoice) 和 LLM 模型...")
    await stt_service.initialize()
    # TTS 初始化，使用 VibeVoice
    await tts_service.initialize(model_name="microsoft/VibeVoice-1.5B")
    await chat_service.initialize_llm()
    print("所有模型初始化完成!")

@app.get("/")
async def root():
    return {"message": "Realtime Dialogue API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "stt_ready": stt_service.is_ready(),
        "tts_ready": tts_service.is_ready(),
        "llm_ready": chat_service.llm_chat is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health/stt")
async def health_check_stt():
    """STT 服務健康檢查"""
    is_ready = stt_service.is_ready()
    return {
        "service": "STT",
        "status": "healthy" if is_ready else "not ready",
        "ready": is_ready,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health/llm")
async def health_check_llm():
    """LLM 服務健康檢查"""
    is_ready = chat_service.llm_chat is not None
    return {
        "service": "LLM", 
        "status": "healthy" if is_ready else "not ready",
        "ready": is_ready,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health/tts")
async def health_check_tts():
    """TTS 服務健康檢查"""
    is_ready = tts_service.is_ready()
    return {
        "service": "TTS",
        "status": "healthy" if is_ready else "not ready", 
        "ready": is_ready,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    """語音轉文字 API"""
    try:
        if not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="請上傳音檔")
        
        start_time = time.time()
        
        # 讀取音檔
        audio_data = await file.read()
        
        # 使用 STT 服務轉換
        text = await stt_service.transcribe(audio_data)
        
        processing_time = int((time.time() - start_time) * 1000)  # 轉換為毫秒
        
        return {
            "success": True,
            "transcription": text,  # 修改為前端期望的字段名
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"STT 錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"STT 處理錯誤: {str(e)}")

@app.post("/set_speakers")
async def set_speakers(
    speaker_names: str = Form(...),  # 逗號分隔的語者名稱
    speaker_audio_files: List[UploadFile] = File(...)
):
    """設定 TTS 系統的語者音檔"""
    try:
        names = [name.strip() for name in speaker_names.split(',')]
        
        if len(names) != len(speaker_audio_files):
            raise HTTPException(status_code=400, detail="語者名稱數量與音檔數量不符")
        
        # 儲存上傳的語者音檔
        speaker_paths = []
        for i, audio_file in enumerate(speaker_audio_files):
            if not audio_file.content_type.startswith("audio/"):
                raise HTTPException(status_code=400, detail=f"檔案 {i+1} 不是音頻檔案")
            
            speaker_data = await audio_file.read()
            speaker_path = await tts_service.save_temp_audio(speaker_data, f"speaker_{names[i]}")
            speaker_paths.append(speaker_path)
        
        # 設定語者音檔
        await tts_service.set_speaker_voices(speaker_paths, names)
        
        return {
            "message": "語者音檔設定成功",
            "speakers": tts_service.get_speaker_info()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"語者設定錯誤: {str(e)}")

@app.get("/speaker_info")
async def get_speaker_info():
    """取得目前使用的語者資訊"""
    return tts_service.get_speaker_info()

@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    """文字轉語音"""
    try:
        # 使用 TTS 服務合成語音
        audio_data = await tts_service.synthesize(
            text=request.text,
            speaker_voice_path=request.speaker_voice_path,
            cfg_scale=getattr(request, 'cfg_scale', 1.0)
        )
        
        # 回傳音檔流
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=tts_output.wav"
            }
        )
        
    except Exception as e:
        print(f"TTS API 錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS 失敗: {str(e)}")
        
        # 回傳音檔
        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename=f"tts_output_{uuid.uuid4().hex[:8]}.wav"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 處理錯誤: {str(e)}")

@app.post("/tts_conversation")
async def text_to_speech_conversation(
    conversation_text: str = Form(...),
    cfg_scale: float = Form(1.0)
):
    """對話格式文字轉語音 API - 支援多語者對話"""
    try:
        if not conversation_text.strip():
            raise HTTPException(status_code=400, detail="對話內容不能為空")
        
        # 使用 VibeVoice 進行對話 TTS 合成
        output_path = await tts_service.synthesize_conversation(conversation_text, cfg_scale=cfg_scale)
        
        # 回傳音檔
        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename=f"conversation_{uuid.uuid4().hex[:8]}.wav"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"對話 TTS 處理錯誤: {str(e)}")

@app.post("/chat")
async def chat_with_bot(
    text: str = Form(...),
    conversation_id: str = Form(None)
):
    """與機器人對話 API"""
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="訊息內容不能為空")
        
        # 使用聊天服務取得回覆
        response = await chat_service.get_response(text, conversation_id)
        
        return {
            "success": True,
            "response": response["message"],
            "conversation_id": response["conversation_id"],
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聊天處理錯誤: {str(e)}")

@app.post("/voice_chat")
async def voice_chat(audio: UploadFile = File(...)):
    """語音對話 API - 前端使用"""
    try:
        if not audio.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="請上傳音檔")
        
        start_time = time.time()
        
        # Step 1: STT - 語音轉文字
        stt_start = time.time()
        audio_data = await audio.read()
        user_text = await stt_service.transcribe(audio_data)
        stt_time = time.time() - stt_start
        
        # Step 2: Chat - 取得回應
        llm_start = time.time()
        chat_response = await chat_service.get_response(user_text)
        bot_message = chat_response["message"]
        llm_time = time.time() - llm_start
        
        # Step 3: TTS - 文字轉語音
        tts_start = time.time()
        audio_bytes = await tts_service.synthesize(bot_message)
        tts_time = time.time() - tts_start
        
        # 保存音檔到 outputs 目錄
        audio_filename = f"voice_chat_{uuid.uuid4().hex[:8]}.wav"
        audio_filepath = os.path.join("./outputs", audio_filename)
        
        with open(audio_filepath, 'wb') as f:
            f.write(audio_bytes)
        
        total_time = time.time() - start_time
        
        return {
            "success": True,
            "transcription": user_text,
            "response": bot_message,
            "audio_url": f"/audio/{audio_filename}",
            "processing_times": {
                "stt_time": round(stt_time * 1000),  # 轉換為毫秒
                "llm_time": round(llm_time * 1000),
                "tts_time": round(tts_time * 1000),
                "total_time": round(total_time * 1000)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"語音對話錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"語音對話處理錯誤: {str(e)}")

class TextChatRequest(BaseModel):
    message: str

@app.post("/text_chat")
async def text_chat(request: TextChatRequest):
    """文字對話 API - 前端使用"""
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="訊息內容不能為空")
        
        start_time = time.time()
        
        # Step 1: Chat - 取得回應
        llm_start = time.time()
        chat_response = await chat_service.get_response(request.message)
        bot_message = chat_response["message"]
        llm_time = time.time() - llm_start
        
        # Step 2: TTS - 文字轉語音
        tts_start = time.time()
        audio_bytes = await tts_service.synthesize(bot_message)
        tts_time = time.time() - tts_start
        
        # 保存音檔到 outputs 目錄
        audio_filename = f"text_chat_{uuid.uuid4().hex[:8]}.wav"
        audio_filepath = os.path.join("./outputs", audio_filename)
        
        with open(audio_filepath, 'wb') as f:
            f.write(audio_bytes)
        
        total_time = time.time() - start_time
        
        return {
            "success": True,
            "response": bot_message,
            "audio_url": f"/audio/{audio_filename}",
            "processing_times": {
                "llm_time": round(llm_time * 1000),  # 轉換為毫秒
                "tts_time": round(tts_time * 1000),
                "total_time": round(total_time * 1000)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"文字對話錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文字對話處理錯誤: {str(e)}")

@app.post("/conversation")
async def full_conversation(
    audio_file: UploadFile = File(...),
    conversation_id: str = Form(None)
):
    """完整對話流程：語音 -> 文字 -> 聊天 -> 語音（使用固定參考音檔）"""
    try:
        # Step 1: STT
        if not audio_file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="請上傳音檔")
        
        audio_data = await audio_file.read()
        user_text = await stt_service.transcribe(audio_data)
        
        # Step 2: Chat
        chat_response = await chat_service.get_response(user_text, conversation_id)
        bot_message = chat_response["message"]
        
        # Step 3: TTS (使用 VibeVoice，預設語者索引 0)
        output_audio_path = await tts_service.synthesize(bot_message, speaker_index=0)
        
        return {
            "success": True,
            "user_text": user_text,
            "bot_message": bot_message,
            "conversation_id": chat_response["conversation_id"],
            "audio_url": f"/audio/{os.path.basename(output_audio_path)}",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"完整對話處理錯誤: {str(e)}")

@app.post("/reset_conversation")
async def reset_conversation():
    """重置對話歷史"""
    try:
        # 使用默認的對話 ID 或清空所有對話
        # 這裡我們清空所有對話，因為前端只有一個聊天界面
        conversation_ids = chat_service.get_active_conversations()
        
        if conversation_ids:
            # 清空所有活躍對話
            for conversation_id in conversation_ids:
                chat_service.clear_conversation(conversation_id)
            cleared_count = len(conversation_ids)
        else:
            cleared_count = 0
            
        return {
            "success": True,
            "message": "對話歷史已重置",
            "cleared_conversations": cleared_count
        }
        
    except Exception as e:
        print(f"重置對話錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重置對話錯誤: {str(e)}")

@app.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """取得生成的音檔"""
    # 更新路徑以配合實際的輸出目錄
    file_path = os.path.join("./outputs", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="音檔不存在")
    
    return FileResponse(
        file_path,
        media_type="audio/wav",
        filename=filename
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# podman exec -it realtime-dialogue-backend bash
# python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
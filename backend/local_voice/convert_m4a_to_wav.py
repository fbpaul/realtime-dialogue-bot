#!/usr/bin/env python3
"""
M4A 轉 WAV 轉換工具
將 local_voice 資料夾中的 m4a 檔案轉換為 wav 格式
"""

import os
import sys
from pathlib import Path

try:
    from pydub import AudioSegment
    from pydub.utils import which
except ImportError:
    print("❌ 缺少必要的依賴套件！")
    print("請安裝 pydub:")
    print("pip install pydub")
    print("\n如果是在 Ubuntu/Debian 系統，還需要安裝 ffmpeg:")
    print("sudo apt update && sudo apt install ffmpeg")
    print("\n如果是在 macOS，可以使用 Homebrew:")
    print("brew install ffmpeg")
    print("\n如果是在 Windows，請下載 ffmpeg 並加入 PATH")
    sys.exit(1)

def check_ffmpeg():
    """檢查 ffmpeg 是否可用"""
    if which("ffmpeg") is None:
        print("❌ 未找到 ffmpeg！")
        print("pydub 需要 ffmpeg 來處理 m4a 檔案")
        print("\n安裝方法:")
        print("Ubuntu/Debian: sudo apt install ffmpeg")
        print("macOS: brew install ffmpeg")
        print("Windows: 下載 ffmpeg 並加入 PATH")
        return False
    return True

def convert_m4a_to_wav(input_path, output_path=None, sample_rate=16000):
    """
    將 m4a 檔案轉換為 wav 格式
    
    Args:
        input_path (str): 輸入 m4a 檔案路徑
        output_path (str, optional): 輸出 wav 檔案路徑
        sample_rate (int): 採樣率，預設 16000 Hz
    
    Returns:
        str: 輸出檔案路徑
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"找不到檔案: {input_path}")
    
    if not input_path.suffix.lower() == '.m4a':
        raise ValueError("輸入檔案必須是 .m4a 格式")
    
    # 如果沒有指定輸出路徑，則使用相同目錄和檔名，但改為 .wav
    if output_path is None:
        output_path = input_path.with_suffix('.wav')
    else:
        output_path = Path(output_path)
    
    print(f"🔄 開始轉換: {input_path.name} -> {output_path.name}")
    
    try:
        # 載入 m4a 檔案
        print("📂 載入音頻檔案...")
        audio = AudioSegment.from_file(str(input_path), format="m4a")
        
        # 顯示原始檔案資訊
        print(f"📊 原始檔案資訊:")
        print(f"   - 長度: {len(audio) / 1000:.2f} 秒")
        print(f"   - 採樣率: {audio.frame_rate} Hz")
        print(f"   - 聲道數: {audio.channels}")
        print(f"   - 位元深度: {audio.sample_width * 8} bit")
        
        # 轉換為單聲道（如果是立體聲）
        if audio.channels > 1:
            print("🔧 轉換為單聲道...")
            audio = audio.set_channels(1)
        
        # 調整採樣率
        if audio.frame_rate != sample_rate:
            print(f"🔧 調整採樣率: {audio.frame_rate} Hz -> {sample_rate} Hz")
            audio = audio.set_frame_rate(sample_rate)
        
        # 確保輸出目錄存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 匯出為 WAV 格式
        print("💾 匯出為 WAV 格式...")
        audio.export(str(output_path), format="wav")
        
        print(f"✅ 轉換完成！")
        print(f"📁 輸出檔案: {output_path}")
        print(f"📊 輸出檔案資訊:")
        print(f"   - 大小: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        return str(output_path)
        
    except Exception as e:
        print(f"❌ 轉換失敗: {e}")
        raise

def convert_all_m4a_in_directory(directory_path):
    """轉換指定目錄中的所有 m4a 檔案"""
    directory_path = Path(directory_path)
    
    if not directory_path.exists():
        print(f"❌ 目錄不存在: {directory_path}")
        return
    
    # 找到所有 m4a 檔案
    m4a_files = list(directory_path.glob("*.m4a"))
    
    if not m4a_files:
        print("❌ 在指定目錄中沒有找到 .m4a 檔案")
        return
    
    print(f"📁 找到 {len(m4a_files)} 個 m4a 檔案")
    
    success_count = 0
    for m4a_file in m4a_files:
        try:
            convert_m4a_to_wav(m4a_file)
            success_count += 1
        except Exception as e:
            print(f"❌ 轉換 {m4a_file.name} 失敗: {e}")
    
    print(f"\n🎉 總共成功轉換 {success_count}/{len(m4a_files)} 個檔案")

def main():
    """主函數"""
    print("=" * 60)
    print("🎵 M4A 轉 WAV 轉換工具")
    print("=" * 60)
    
    # 檢查 ffmpeg
    if not check_ffmpeg():
        return
    
    # 預設處理 local_voice 目錄
    local_voice_dir = Path("local_voice")
    
    if len(sys.argv) > 1:
        # 如果有命令列參數，使用指定的目錄或檔案
        input_path = Path(sys.argv[1])
        
        if input_path.is_file():
            # 處理單個檔案
            try:
                convert_m4a_to_wav(input_path)
            except Exception as e:
                print(f"❌ 處理失敗: {e}")
        elif input_path.is_dir():
            # 處理整個目錄
            convert_all_m4a_in_directory(input_path)
        else:
            print(f"❌ 路徑不存在: {input_path}")
    else:
        # 預設處理 local_voice 目錄
        if local_voice_dir.exists():
            convert_all_m4a_in_directory(local_voice_dir)
        else:
            print(f"❌ 預設目錄 {local_voice_dir} 不存在")
            print("使用方法:")
            print("python convert_m4a_to_wav.py [檔案路徑或目錄路徑]")

if __name__ == "__main__":
    main()

import os
import time
import subprocess
import argparse
import pandas as pd
from datasets import Dataset
from single_inference import single_inference, CustomCosyVoice
from g2pw import G2PWConverter


def process_batch(csv_file, speaker_prompt_audio_folder, output_audio_folder, model):
    # Load CSV with pandas
    data = pd.read_csv(csv_file)

    # Transform pandas DataFrame to HuggingFace Dataset
    dataset = Dataset.from_pandas(data)
    dataset = dataset.shuffle(seed = int(time.time()*1000))

    cosyvoice, bopomofo_converter = model

    def gen_audio(row):
        speaker_prompt_audio_path = os.path.join(speaker_prompt_audio_folder, f"{row['speaker_prompt_audio_filename']}.wav")
        speaker_prompt_text_transcription = row['speaker_prompt_text_transcription']
        content_to_synthesize = row['content_to_synthesize']
        output_audio_path = os.path.join(output_audio_folder, f"{row['output_audio_filename']}.wav")

        if not os.path.exists(speaker_prompt_audio_path):
            print(f"File {speaker_prompt_audio_path} does not exist")
            return row #{"status": "failed", "reason": "file not found"}
        if not os.path.exists(output_audio_path):
            single_inference(speaker_prompt_audio_path, content_to_synthesize, output_audio_path, cosyvoice, bopomofo_converter, speaker_prompt_text_transcription)
        else:
            pass
        # command = [
        #     "python", "single_inference.py",
        #     "--speaker_prompt_audio_path", speaker_prompt_audio_path,
        #     "--speaker_prompt_text_transcription", speaker_prompt_text_transcription,
        #     "--content_to_synthesize", content_to_synthesize,
        #     "--output_path", output_audio_path
        # ]

        # try:
        #     print(f"Processing: {speaker_prompt_audio_path}")
        #     subprocess.run(command, check=True)
        #     print(f"Generated: {output_audio_path}")
        #     return row #{"status": "success", "output": gen_voice_file_name}
        # except subprocess.CalledProcessError as e:
        #     print(f"Failed to generate {speaker_prompt_audio_path}, error: {e}")
        #     return row #{"status": "failed", "reason": str(e)}

    dataset = dataset.map(gen_audio, num_proc = 1)

def main():
    parser = argparse.ArgumentParser(description="Batch process audio generation.")
    parser.add_argument("--csv_file", required=True, help="Path to the CSV file containing input data.")
    parser.add_argument("--speaker_prompt_audio_folder", required=True, help="Path to the folder containing speaker prompt audio files.")
    parser.add_argument("--output_audio_folder", required=True, help="Path to the folder where results will be stored.")
    parser.add_argument("--model_path", type=str, required=False, default = "MediaTek-Research/BreezyVoice-300M",help="Specifies the model used for speech synthesis.")

    args = parser.parse_args()

    cosyvoice = CustomCosyVoice(args.model_path)
    bopomofo_converter = G2PWConverter()

    os.makedirs(args.output_audio_folder, exist_ok=True)

    process_batch(
        csv_file=args.csv_file,
        speaker_prompt_audio_folder=args.speaker_prompt_audio_folder,
        output_audio_folder=args.output_audio_folder,
        model = (cosyvoice, bopomofo_converter),

    )

if __name__ == "__main__":
    main()


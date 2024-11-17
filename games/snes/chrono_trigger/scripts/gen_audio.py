import pandas as pd
from TTS.api import TTS
import librosa
import os

def extract_japanese_text(df):
    japanese_list = []
    
    valid_rows = df[df['japanese'].notna()]
        
    for _, row in valid_rows.iterrows():
        text = row['japanese']
        row_num = row['row']
        
        text = text.split('「', 1)[1] if '「' in text else text
        text = text.replace('[END]', '').strip()
        if text:
            japanese_list.append({
                'text': text,
                'row': row_num
            })
    
    return japanese_list


def generate_audio(full_script_path: str, output_path: str):
    df = pd.read_csv(full_script_path)
    japanese_texts = extract_japanese_text(df)

    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

    for text in japanese_texts:
        if not os.path.exists(f"{output_path}/{text['row']}.wav"):
            tts.tts_to_file(text['text'],
                speaker="Kazuhiko Atallah",
                language="ja", file_path=f"{output_path}/{text['row']}.wav")

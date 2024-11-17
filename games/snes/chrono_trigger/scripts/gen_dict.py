import pandas as pd
import json
from openai import OpenAI
import time
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_japanese_words(text):
    
    prompt = f"""
    Analyze this Japanese text: {text}
    Return a JSON array where each element contains:
    - word: the original word
    - hiragana: hiragana reading
    - romaji: romaji reading
    - meaning: English meaning
    Only return the JSON array, no other text.
    Example format:
    [
        {{"word": "森", "hiragana": "もり", "romaji": "mor", "meaning": "forest"}},
        {{"word": "川", "hiragana": "かわ", "romaji": "kawa", "meaning": "river"}}
    ]
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error processing text '{text}': {str(e)}")
        return None

def generate_dict(full_script_path: str, dict_path: str):
    # Read both CSV files
    processed_df = pd.read_csv(full_script_path)
    
    # Combine Japanese text and row numbers from both files
    texts_to_process = []
    
    for df in [processed_df]:
        mask = df['japanese'].notna()
        texts = df[mask][['japanese', 'row']].to_dict('records')
        texts_to_process.extend(texts)
    
    # Initialize or load existing results
    results = {}
    if os.path.exists(dict_path):
        with open(dict_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
    
    # Process each text
    for i, item in enumerate(texts_to_process):
        row_num = str(item['row'])  # Convert to string for JSON key
        text = item['japanese']
        original_text = item['japanese']
        
        # Skip if row already processed
        if row_num in results:
            print(f"Skipping already processed row {row_num}")
            continue
            
        if isinstance(text, str) and text.strip():
            print(f"Processing {i}/{len(texts_to_process)}: Row {row_num}")
            
            # Clean the text
            text = text.split('「', 1)[1] if '「' in text else text
            text = text.replace('[END]', '').strip()
            
            analysis = analyze_japanese_words(text)
            if analysis:
                results[row_num] = {
                    'text': text,
                    'analysis': analysis
                }
                # Save after each successful analysis
                with open(dict_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            
            time.sleep(1)  # Rate limiting


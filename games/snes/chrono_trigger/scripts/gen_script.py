import pandas as pd

df = pd.read_excel('ct.xls')

def process_data(categories_file_path: str, init_row: int, end_row: int):
    df_categories = pd.read_csv(categories_file_path)
    chapters = df_categories[df_categories.category == 'Chapter Titles']['english'].unique()

    current_chapter = None
    current_location = None
    processed_data = []

    current_japanese = []
    current_english = []

    for index, row in df.iterrows():
        if init_row <= index <= end_row:
            col_a = str(row.iloc[0]).strip()
            col_c = str(row.iloc[2]).strip()
            col_e = str(row.iloc[4]).strip()
                    
            chapter_name = col_e
            if chapter_name in chapters and chapter_name != current_chapter:
                current_chapter = chapter_name
                processed_data.append({
                    'type': 'chapter',
                    'chapter': current_chapter,
                    'row': index
                })
                continue

            if (col_a.startswith('[') and col_a.endswith(']') and 
                col_c.strip() == 'nan' and col_e.strip() == 'nan'):
                current_location = col_a[1:-1]
                processed_data.append({
                    'type': 'location',
                    'chapter': current_chapter,
                    'location': current_location,
                    'row': index
                })
                continue
            
            if (isinstance(col_c, str) and col_c != 'nan' and col_c.strip() != '') or (isinstance(col_e, str) and col_e != 'nan' and col_e.strip() != ''):  # If either column has content
                if isinstance(col_c, str) and col_c != 'nan' and col_c.strip() != '':
                    current_japanese.append(col_c.strip())
                if isinstance(col_e, str) and col_e != 'nan' and col_e.strip() != '':
                    current_english.append(col_e.strip())
                
            else:
                if current_japanese and current_english:  # Changed from 'or' to 'and'
                    processed_data.append({
                        'type': 'text',
                        'chapter': current_chapter,
                        'location': current_location,
                        'japanese': ' '.join(current_japanese),
                        'english': ' '.join(current_english),
                        'row': index
                    })
                    current_japanese = []
                    current_english = []


    return processed_data
    

def save_category(category: str, init_row: int, end_row: int):
    data = []
    for index, row in df.iterrows():
        if index >= init_row and index <= end_row:
            japanese_text = str(row.iloc[2])
            english_text = str(row.iloc[4])
            if isinstance(japanese_text, str) and japanese_text.strip() != '':
                entry = {"category": category, "japanese": japanese_text, "english": english_text, "row": index}
                data.append(entry)
    
    return data

def save_categories(categories_file_path: str):
    categories = [('Location Names', 18917, 18988), ('Years Text', 19010, 19016), ('Item Names', 19021, 19253), ('Tech Names', 19267, 19383), ('Item Descriptions', 19388, 19492), ('Tech Descriptions', 19498, 19618), ('Enemy Names', 19622, 19874), ('Battle Messages', 19878, 20104), ('Battle Party Messages', 20111, 20125), ('Treasure Chest Text', 20129, 20134), ('Menu Text', 20139, 20151), ('Chapter Titles', 20156, 20182), ('Age Names', 20186, 20194), ('Settings Text', 20199, 20234)]
    data = []
    for category in categories:
        data.extend(save_category(category[0], category[1], category[2]))
    
    df = pd.DataFrame(data)
    df.drop_duplicates(keep='first', inplace=True)
    df.to_csv(categories_file_path, index=False, encoding='utf-8-sig')


def generate_full_script(categories_file_path: str, full_script_path: str):
    save_categories(categories_file_path)
    data_1 = process_data(categories_file_path, 91, 17527) # Main game script
    data_2 = process_data(categories_file_path, 17529, 18759) # Endings script
    
    columns = ['type', 'chapter', 'location', 'japanese', 'english', 'row']
    df1 = pd.DataFrame(data_1, columns=columns)
    df2 = pd.DataFrame(data_2, columns=columns)
    
    output_df = pd.concat([df1, df2])

    output_df.to_csv(full_script_path, index=False, encoding='utf-8-sig')


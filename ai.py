from manga_ocr import MangaOcr
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import pandas as pd
import json

class FuzzyMatch:
    def __init__(self, platform: str, game: str):
        self.df = pd.read_csv(f'./games/{platform}/{game}/full_script.csv')
        self.dict = json.load(open(f'./games/{platform}/{game}/dict.json'))
        self.database = self.df['japanese'].tolist()
        self.ids = self.df['row'].tolist()
        
    def fuzzy_match(self, query, n_results=3):
        best_match = process.extractOne(query, self.database, scorer=fuzz.token_sort_ratio)[0]
        best_match_index = self.database.index(best_match)
        best_match_id = self.ids[best_match_index]
        best_match_row = self.df[self.df['row'] == best_match_id]
        best_match_dict = self.dict[str(best_match_id)]
        return best_match_row.to_dict(orient='records')[0], best_match_dict

class AnalyzeImage:
    def __init__(self, platform: str, game: str):
        self.mocr = MangaOcr()
        self.fuzzy_match = FuzzyMatch(platform=platform, game=game)
    def ocr(self, img_path: str):
        return self.mocr(img_path)
    
    def analyze(self, img_path):
        text = self.ocr(img_path)
        best_match, best_match_dict = self.fuzzy_match.fuzzy_match(text)
        return best_match, best_match_dict

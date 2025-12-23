import spacy
import pandas as pd
import re

try:
    nlp = spacy.load("ja_ginza")
except OSError:
    import spacy
    nlp = None

def split_into_chapters(text):
    """章立て（第〇章、プロローグ等）で分割 """
    pattern = r'(^\s*第[一二三四五六七八九十0-9]+[章話回].*|^\s*プロローグ|^\s*エピローグ|^\s*序章|^\s*終章|^\s*幕間|^\s*閑話)'
    parts = re.split(pattern, text, flags=re.MULTILINE)
    chapters = {}
    current = "導入部"
    if parts[0].strip(): chapters[current] = parts[0].strip()
    for i in range(1, len(parts), 2):
        name, content = parts[i].strip(), parts[i+1].strip() if i+1 < len(parts) else ""
        if content: chapters[name] = content
    if not chapters or (len(chapters)==1 and not chapters["導入部"]):
        for i in range(0, len(text), 3000): chapters[f"Part {i//3000+1}"] = text[i:i+3000]
    return chapters

def split_narrative_dialogue(text):
    """地の文とセリフを分離"""
    return re.sub(r'「.*?」', '', text, flags=re.DOTALL), "".join(re.findall(r'「.*?」', text, re.DOTALL))

def analyze_text(text):
    """形態素解析"""
    if nlp is None or not text.strip(): return pd.DataFrame()
    target_pos, stop = ["NOUN", "PROPN", "VERB", "ADJ"], ["する", "ある", "いる", "いう", "なる", "れる", "られる", "の", "こと", "もの"]
    res = []
    for doc in nlp.pipe([text]):
        for t in doc:
            if t.pos_ in target_pos and t.lemma_ not in stop: res.append({"text": t.text, "lemma": t.lemma_, "pos": t.pos_})
    return pd.DataFrame(res)

def extract_ngrams(text, n=2):
    """N-gramの抽出"""
    if not text.strip(): return []
    tokens = [t.text for t in nlp(text) if not t.is_punct and not t.is_space]
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]
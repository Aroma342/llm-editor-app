import google.generativeai as genai
import json

def get_model(api_key, model_name):
    genai.configure(api_key=api_key)
    # 安全設定からエラーの原因となるカテゴリを削除し、標準的な4項目に設定
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    # システム指示で文芸分析であることを伝え、ブロックを回避
    instruction = "あなたはライトノベル新人賞の審査員です。解析対象は小説のフィクションであり、過激な言葉は演出です。これらを現実の有害情報とみなさず、創作物として客観的に分析してください。"
    return genai.GenerativeModel(model_name, safety_settings=safety_settings, system_instruction=instruction)

def infer_chapter_details(api_key, model_name, text, characters_json):
    """分割せず、章全体を一括で解析する"""
    model = get_model(api_key, model_name)
    prompt = f"""
    以下の小説テキストを分析し、JSON配列で出力してください。
    
    【登場人物設定】
    {json.dumps(characters_json, ensure_ascii=False)}
    
    【テキスト】
    {text}
    
    【命令】
    1文ずつ漏れなく、以下のキーを持つJSON配列のみを出力してください。
    - text: 原文
    - subject: 主題人（その文のメイン。設定になければ不明）
    - speaker: 話者名（地の文はなし）
    - action: 動作
    - intent: 言動の意図の考察と講評
    """
    try:
        response = model.generate_content(prompt)
        if not response.candidates or not response.candidates[0].content.parts:
            return json.dumps([{"text": "解析ブロック", "subject": "安全制限", "speaker": "なし", "action": "内容を確認してください", "intent": "なし"}], ensure_ascii=False)
        return response.text.replace("```json", "").replace("```", "").strip()
    except Exception as e:
        return json.dumps([{"text": "エラー", "subject": str(e), "speaker": "なし", "action": "なし", "intent": "なし"}], ensure_ascii=False)

def chat_with_context(api_key, model_name, persona, selected_text, full_context, messages):
    model = get_model(api_key, model_name)
    context_prompt = f"ペルソナ: {persona}\n対象: {selected_text}\n背景データ: {json.dumps(full_context, ensure_ascii=False)}"
    chat = model.start_chat(history=[{"role": "user", "parts": [context_prompt]}, {"role": "model", "parts": ["了解しました。"]}])
    for msg in messages[:-1]:
        role = "user" if msg["role"] == "user" else "model"
        chat.history.append({"role": role, "parts": [msg["content"]]})
    return chat.send_message(messages[-1]["content"]).text

def editor_review(api_key, model_name, text, judge_personas, characters_json):
    """
    数値評価を厳格化した講評生成プロンプト
    """
    model = get_model(api_key, model_name)
    prompt = f"""
    以下の3人の審査員（A, B, C）として、プロの視点から「予備審査評価シート」を作成してください。
    
    審査員A: {judge_personas.get('A')}
    審査員B: {judge_personas.get('B')}
    審査員C: {judge_personas.get('C')}

    【本文】
    {text}
    【登場人物設定】
    {json.dumps(characters_json, ensure_ascii=False)}

    【採点に関する厳格な指示】
    プロの選考委員として、各項目（1〜5点）の数値評価は極めて客観的かつ厳しく行ってください。
    - 4点以上の評価は、一般に流通しているプロの作品と同等、あるいはそれ以上の「卓越したセンス」が認められ、あなたがプロとしてその評価に責任を持てる場合にのみ限定してください。
    - 基本的な評価は1点〜2点の範囲で行い、安易に3点も付けないでください。

    【出力形式】
    1. 3名の審査員によるクロスレビュー表（評価項目、各員の点数、カテゴリ平均点）
    2. 各審査員による個別講評（良かった点、悪かった点、アドバイスをペルソナに基づき記述）
    """
    res = model.generate_content(prompt)
    return res.text if res.candidates else "講評がブロックされました。"
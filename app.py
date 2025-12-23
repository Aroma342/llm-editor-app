import streamlit as st
import pandas as pd
import json
import os
from modules import text_processor, visualizer, llm_handler

st.set_page_config(page_title="AI Editor Interface", layout="wide")
PROJECT_DIR = "projects"
if not os.path.exists(PROJECT_DIR): os.makedirs(PROJECT_DIR)

# --- ユーティリティ ---
def save_project_data(p_name, char_data):
    path = os.path.join(PROJECT_DIR, p_name)
    if not os.path.exists(path): os.makedirs(path)
    with open(os.path.join(path, "characters.json"), "w", encoding="utf-8") as f:
        json.dump(char_data, f, ensure_ascii=False, indent=2)

def load_project_data(p_name):
    path = os.path.join(PROJECT_DIR, p_name, "characters.json")
    return json.load(open(path, "r", encoding="utf-8")) if os.path.exists(path) else []

def save_txt(p_name, text):
    path = os.path.join(PROJECT_DIR, p_name)
    if not os.path.exists(path): os.makedirs(path)
    with open(os.path.join(path, "source.txt"), "w", encoding="utf-8") as f: f.write(text)

# --- サイドバー ---
st.sidebar.header(" API & Settings")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")
model_choice = st.sidebar.selectbox("Model", ["gemini-3-flash-preview","gemini-2.5-flash"])

st.sidebar.divider()
st.sidebar.header(" Project")
existing = [d for d in os.listdir(PROJECT_DIR) if os.path.isdir(os.path.join(PROJECT_DIR, d))]
sel_p = st.sidebar.selectbox("選択", ["新規作成"] + existing)

if sel_p == "新規作成":
    n_name = st.sidebar.text_input("新規名")
    if st.sidebar.button("作成"):
        st.session_state['current_p'], st.session_state['char_data'] = n_name, []
        save_project_data(n_name, []); st.rerun()
else:
    if st.session_state.get('current_p') != sel_p:
        st.session_state['current_p'] = sel_p
        st.session_state['char_data'] = load_project_data(sel_p)

current_p = st.session_state.get('current_p', "未選択")
st.sidebar.info(f"Project: {current_p}")

st.sidebar.divider()
st.sidebar.header(" 審査員ペルソナ")
j_personas = {
    "A": st.sidebar.text_area("審査員A", "数々のヒット作品を手掛けた実績のある編集長", key="j_a"),
    "B": st.sidebar.text_area("審査員B", "ライトノベルが好きな新人編集", key="j_b"),
    "C": st.sidebar.text_area("審査員C", "長年ライトノベルを書き続けたベテラン作家", key="j_c")
}

if current_p == "未選択":
    st.title("AI Editor")
    st.info("プロジェクトを選択してください。")
    st.stop()

st.title(f" Project: {current_p}")

# --- 登場人物設定 ---
st.header(" 登場人物の設定")
with st.expander(" 新規登録", expanded=not st.session_state.get('char_data')):
    with st.form("add_char", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 1, 2])
        name = c1.text_input("名前")
        post = c1.text_input("役職 (例: 高校1年生)")
        role, gender = c1.text_input("役割"), c2.selectbox("性別", ["男", "女", "その他", "不明"])
        fp, tone = c3.text_input("一人称"), c3.text_input("口調")
        traits = st.text_area("性格")
        if st.form_submit_button("登録"):
            if name:
                st.session_state['char_data'].append({"名前":name,"役職":post,"性別":gender,"役割":role,"一人称":fp,"口調":tone,"性格":traits})
                save_project_data(current_p, st.session_state['char_data']); st.rerun()

# 既存キャラクターの編集・削除
if st.session_state.get('char_data'):
    delete_idx = -1
    for i, char in enumerate(st.session_state['char_data']):
        with st.expander(f"👤 {char['名前']} ({char.get('役職','')})"):
            # 3列構成で編集フィールドを配置
            ce1, ce2, ce3 = st.columns([2, 1, 2])
            
            # 基本情報
            st.session_state['char_data'][i]['名前'] = ce1.text_input(f"名前##edit_{i}", char['名前'])
            st.session_state['char_data'][i]['役職'] = ce1.text_input(f"役職##edit_{i}", char.get('役職',''))
            st.session_state['char_data'][i]['役割'] = ce1.text_input(f"役割##edit_{i}", char.get('役割',''))
            
            # 性別選択
            g_list = ["男", "女", "その他", "不明"]
            current_g = char.get('性別', "不明")
            g_idx = g_list.index(current_g) if current_g in g_list else 3
            st.session_state['char_data'][i]['性別'] = ce2.selectbox(f"性別##edit_{i}", g_list, index=g_idx)
            
            # 口調・一人称
            st.session_state['char_data'][i]['一人称'] = ce3.text_input(f"一人称##edit_{i}", char.get('一人称',''))
            st.session_state['char_data'][i]['口調'] = ce3.text_input(f"口調##edit_{i}", char.get('口調',''))
            
            # 性格（広めに確保）
            st.session_state['char_data'][i]['性格'] = st.text_area(f"性格##edit_{i}", char.get('性格',''))
            
            # 操作ボタン
            col_save, col_del = st.columns(2)
            if col_save.button(f"変更を保存##{i}", key=f"btn_save_{i}"):
                save_project_data(current_p, st.session_state['char_data'])
                st.success(f"{char['名前']} の情報を更新しました")
                st.rerun()
                
            if col_del.button(f"削除##{i}", key=f"btn_del_{i}"):
                delete_idx = i

    # 削除処理の実行（ループ外で行うことで安全にリスト操作を行う）
    if delete_idx != -1:
        removed_char = st.session_state['char_data'].pop(delete_idx)
        save_project_data(current_p, st.session_state['char_data'])
        st.warning(f"{removed_char['名前']} を削除しました")
        st.rerun()

st.divider()

# --- 本文処理 ---
up_file = st.sidebar.file_uploader("小説ファイル(.txt)", type="txt", key="txt_up")
if up_file and gemini_key:
    raw_t = up_file.read().decode("utf-8")
    save_txt(current_p, raw_t)
    chaps = text_processor.split_into_chapters(raw_t)
    sel_ch = st.selectbox("章を選択", list(chaps.keys()))
    ch_text = chaps[sel_ch]

    t1, t2, t3, t4 = st.tabs(["📊 分析", "🤖 解析", "💬 チャット", "📝 講評"])

    with t1:
        cat = st.radio("範囲", ["全文", "地の文", "セリフ"], horizontal=True)
        if st.button("マイニング実行"):
            with st.spinner("解析中..."):
                nar, dia = text_processor.split_narrative_dialogue(ch_text)
                target = ch_text if cat == "全文" else (nar if cat == "地の文" else dia)
                st.session_state['df_m'] = text_processor.analyze_text(target)
                st.session_state['ng'] = text_processor.extract_ngrams(target)
        if 'df_m' in st.session_state:
            cl, cr = st.columns(2)
            cl.image(visualizer.create_wordcloud(st.session_state['df_m']).to_array(), use_container_width=True)
            cl.pyplot(visualizer.create_network_graph(st.session_state['df_m']))
            cr.pyplot(visualizer.create_frequency_chart(st.session_state['df_m']))
            cr.pyplot(visualizer.create_ngram_chart(st.session_state['ng']))

    with t2:
        if st.button("解析開始"):
            with st.spinner("解析中..."):
                res_j = llm_handler.infer_chapter_details(gemini_key, model_choice, ch_text, st.session_state['char_data'])
                try:
                    st.session_state['inf_d'] = json.loads(res_j)
                except Exception as e:
                    st.error(f"解析結果の読み込みに失敗しました: {e}")
        
        if 'inf_d' in st.session_state:
            for i, item in enumerate(st.session_state['inf_d']):
                with st.container(border=True):
                    st.write(f"**{i+1}:** {item['text']}")
                    h1, h2, h3, h4 = st.columns(4)
                    st.session_state['inf_d'][i]['subject'] = h1.text_input(f"主題##{i}", item['subject'])
                    st.session_state['inf_d'][i]['speaker'] = h2.text_input(f"話者##{i}", item['speaker'])
                    st.session_state['inf_d'][i]['action'] = h3.text_input(f"動作##{i}", item['action'])
                    st.session_state['inf_d'][i]['intent'] = h4.text_area(f"講評##{i}", item['intent'], height=68)

    with t3:
        if 'inf_d' in st.session_state:
            s_list = [f"{i+1}: {r['text']}" for i, r in enumerate(st.session_state['inf_d'])]
            idxs = st.multiselect("選択", range(len(s_list)), format_func=lambda x: s_list[x])
            sel_t = "\n".join([st.session_state['inf_d'][i]['text'] for i in idxs])
            if "msgs" not in st.session_state: st.session_state.msgs = []
            for m in st.session_state.msgs:
                with st.chat_message(m["role"]): st.markdown(m["content"])
            if p := st.chat_input("質問"):
                st.session_state.msgs.append({"role":"user","content":p})
                with st.chat_message("user"): st.markdown(p)
                with st.chat_message("assistant"):
                    ans = llm_handler.chat_with_context(gemini_key, model_choice, j_personas["A"], sel_t, st.session_state['inf_d'], st.session_state.msgs)
                    st.markdown(ans); st.session_state.msgs.append({"role":"assistant","content":ans})

    with t4:
        if st.button("講評生成"):
            st.markdown(llm_handler.editor_review(gemini_key, model_choice, ch_text, j_personas, st.session_state['char_data']))
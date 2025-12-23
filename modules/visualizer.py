import os
import pandas as pd
from wordcloud import WordCloud
import networkx as nx
import matplotlib.pyplot as plt

def get_font_path():
    candidates = ["C:/Windows/Fonts/msgothic.ttc", "C:/Windows/Fonts/meiryo.ttc"]
    for path in candidates:
        if os.path.exists(path): return path
    return None

def create_wordcloud(word_df):
    if word_df.empty: return None
    text = " ".join(word_df['lemma'].tolist())
    font_path = get_font_path()
    wc = WordCloud(width=600, height=400, background_color='white', font_path=font_path).generate(text)
    return wc

def create_frequency_chart(word_df, title="頻出単語"):
    if word_df.empty: return None
    counts = word_df['lemma'].value_counts().head(15)
    fig, ax = plt.subplots(figsize=(5, 4))
    plt.rcParams['font.family'] = 'MS Gothic'
    counts.plot(kind='barh', ax=ax, color='skyblue')
    ax.invert_yaxis()
    ax.set_title(title)
    plt.tight_layout()
    return fig

def create_ngram_chart(ngrams, title="N-gramランキング"):
    if not ngrams: return None
    from collections import Counter
    counts = pd.Series(Counter(ngrams)).sort_values(ascending=False).head(15)
    fig, ax = plt.subplots(figsize=(5, 4))
    plt.rcParams['font.family'] = 'MS Gothic'
    counts.plot(kind='barh', ax=ax, color='salmon')
    ax.invert_yaxis()
    ax.set_title(title)
    plt.tight_layout()
    return fig

def create_network_graph(word_df, title="共起ネットワーク"):
    if word_df.empty: return None
    G = nx.Graph()
    words = word_df['lemma'].tolist()
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i+1]
        if w1 != w2:
            if G.has_edge(w1, w2): G[w1][w2]['weight'] += 1
            else: G.add_edge(w1, w2, weight=1)

    d = dict(G.degree)
    top_nodes = sorted(d, key=d.get, reverse=True)[:25]
    G_sub = G.subgraph(top_nodes)

    fig, ax = plt.subplots(figsize=(6, 5))
    plt.rcParams['font.family'] = 'MS Gothic'
    pos = nx.spring_layout(G_sub, k=0.8, seed=42)
    nx.draw_networkx_nodes(G_sub, pos, node_size=800, node_color='lightgreen', alpha=0.8)
    nx.draw_networkx_edges(G_sub, pos, edge_color='gray', alpha=0.5)
    nx.draw_networkx_labels(G_sub, pos, font_family='MS Gothic', font_size=9)
    ax.set_title(title)
    ax.set_axis_off()
    plt.tight_layout()
    return fig
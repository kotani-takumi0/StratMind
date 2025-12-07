import json
import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# --- 設定 ---
# 分析したいJSONファイルのパス（ファイル名は適宜変更してください）
# ※ backend/app/logs/logs/ 以下のファイルを指定
JSON_FILE_PATH = "backend/app/logs/logs/session_26636b0c-a1fc-47a7-9655-d29d21149069.json"

# 日本語フォントの設定（OSに合わせてコメントアウトを外してください）
# Macの場合
# plt.rcParams['font.family'] = 'Hiragino Sans'
# Windowsの場合
#plt.rcParams['font.family'] = 'MS Gothic'
# Linux/Colabなどの場合 (IPAexGothicなどがインストールされている必要あり)
#plt.rcParams['font.family'] = 'IPAexGothic'

def get_embeddings(texts):
    """OpenAI APIを使ってテキストをベクトル化する"""
    client = OpenAI() # 環境変数 OPENAI_API_KEY を使用
    
    # 空文字列対策
    clean_texts = [t if t.strip() else " " for t in texts]
    
    print("OpenAI APIで埋め込みを計算中...")
    resp = client.embeddings.create(
        input=clean_texts,
        model="text-embedding-3-small"
    )
    return np.array([d.embedding for d in resp.data])

def visualize_trajectory(json_path):
    # 1. JSONの読み込み
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    history = data.get("idea_history", [])
    if not history:
        print("エラー: idea_history が見つかりません。")
        return

    print(f"セッションID: {data.get('session_id')}")
    print(f"ステップ数: {len(history)}")

    # 2. テキストの抽出
    # step順に並べる
    history.sort(key=lambda x: x['step'])
    titles = [f"Step {h['step']}" for h in history]
    summaries = [h['summary'] for h in history]

    # 3. ベクトル化 (Embedding)
    vecs = get_embeddings(summaries)

    # 4. 変化量の計算（コサイン類似度）
    print("\n--- 思考の変化量分析 ---")
    distances = []
    for i in range(len(vecs) - 1):
        sim = cosine_similarity([vecs[i]], [vecs[i+1]])[0][0]
        dist = 1.0 - sim
        distances.append(dist)
        print(f"Step {i+1} -> {i+2}: 距離 {dist:.4f}")
    
    avg_change = np.mean(distances) if distances else 0
    print(f"\n平均変化量: {avg_change:.4f}")

    # 5. 次元圧縮 (PCA) で2次元化
    # ※ 点が少なすぎる(2点未満)とPCAできないので注意
    if len(vecs) < 2:
        print("データ点が少なすぎるためグラフを描画できません。")
        return

    pca = PCA(n_components=2)
    vecs_2d = pca.fit_transform(vecs)

    # 6. 可視化 (プロット)
    plt.figure(figsize=(10, 8))
    
    # 軌跡を描画
    plt.plot(vecs_2d[:, 0], vecs_2d[:, 1], color='gray', linestyle='--', alpha=0.5)
    
    # 矢印を描画
    for i in range(len(vecs_2d) - 1):
        start = vecs_2d[i]
        end = vecs_2d[i+1]
        plt.arrow(
            start[0], start[1], 
            end[0] - start[0], end[1] - start[1],
            head_width=0.02, head_length=0.03, fc='blue', ec='blue', alpha=0.6,
            length_includes_head=True
        )

    # 点をプロット
    # Start (Step1) は緑、End は赤、途中は青
    colors = ['blue'] * len(vecs_2d)
    colors[0] = 'green'
    colors[-1] = 'red'
    
    plt.scatter(vecs_2d[:, 0], vecs_2d[:, 1], c=colors, s=100, zorder=5)

    # ラベルを表示
    for i, (x, y) in enumerate(vecs_2d):
        label = f"Step {i+1}"
        plt.text(x + 0.02, y + 0.02, label, fontsize=12)

    plt.title(f"Trajectory of Thought (Avg Shift: {avg_change:.3f})\nGreen:Start -> Red:End", fontsize=14)
    plt.xlabel("PCA Component 1")
    plt.ylabel("PCA Component 2")
    plt.grid(True)
    
    # 保存
    output_filename = "trajectory_plot.png"
    plt.savefig(output_filename)
    print(f"\nグラフを保存しました: {output_filename}")
    plt.show()

if __name__ == "__main__":
    visualize_trajectory(JSON_FILE_PATH)
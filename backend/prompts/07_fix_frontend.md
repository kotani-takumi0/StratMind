# Role
あなたは熟練したフロントエンドエンジニア兼UIデザイナーです。
現在開発中のMVPアプリ「StratMind（新規事業企画の自己レビューツール）」のUI/UXを大幅に刷新するコードを書いてください。

# Context
- 現在のスタック: FastAPI (Backend), Jinja2, Vanilla JS, CSS
- 現状: 3カラムの単純なレイアウトだが、UXが洗練されていない。
- ゴール: ユーザーが「企画案の修正」と「AIレビュー」を往復しやすい「デュアルペイン・ワークショップ形式」のUIに変更する。

# Requirements (UI/UX Specification)

## 1. Overall Layout (CSS Grid)
- 画面全体を左右2分割（Dual Pane）にする。
- **Left Pane (Editor):** 画面幅の40%。ユーザーが企画を練り上げる場所。
- **Right Pane (Review Assistant):** 画面幅の60%。AIからの問いと参考資料を表示する場所。
- 画面全体で `100vh` を使い、各ペイン内部でスクロールさせる（Windowスクロールはさせない）。

## 2. Left Pane: Editor Area
- 常に編集可能な「タイトル入力欄」と「本文テキストエリア」を配置。
- テキストエリアはペインの高さいっぱいに広げ、ドキュメントエディタのような集中できる見た目にする。
- ヘッダー部分に「AIレビュー実行（Update Review）」ボタンを配置。

## 3. Right Pane: Tab Interface
- 上部にタブ切り替えを配置:
  1. **"Review Questions" (Main)**: AI生成された問いのリスト。
  2. **"Reference Cases" (Sub)**: 類似した過去の意思決定ケース一覧。
- 初期表示は "Review Questions"。

## 4. Component Details
- **Question Card (問いカード):**
  - 問いのテキストを大きく表示。
  - 「反映ボタン（←企画書に追記）」を配置。これを押すと、左側のテキストエリアの末尾にメモが追記される挙動（JS）を実装する。
  - ステータス管理（未検討/修正済）のチェックボックス。
- **Case Card (類似ケースカード):**
  - コンパクトに表示。
  - `status` (rejected/adopted) に応じて色分けしたバッジを表示。
  - `summary` と `main_reason` を表示。

# Deliverables
以下のファイルの更新版コードを出力してください。
1. `index.html`: 新しいDOM構造（セマンティックなタグ使用）
2. `style.css`: CSS Gridを用いたレイアウト、モダンなカードデザイン、見やすいタイポグラフィ
3. `app.js`: タブ切り替えロジック、"反映ボタン"のイベントハンドラ、ダミーデータを用いたレンダリング関数

# Design Tone
- B2B SaaSのような清潔感のあるデザイン。
- 白ベース、アクセントカラーは落ち着いた青(#2563eb)。
- 境界線は薄いグレー(#e5e7eb)を使用。
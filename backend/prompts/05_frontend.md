# Prompt 05: templates/index.html ＆ static/js/app.js

## 【目的】
FastAPI バックエンドと連携する、自己レビュー用フロントエンド（HTML＋バニラJS）を実装するためのプロンプトです。

## 【役割】
- ユーザーが新規事業案（NewIdea）をフォーム入力する
- 類似する過去の意思決定ケース（DecisionCase）の一覧を閲覧する
- 生成された「問い（Question）」に対して評価・フィードバックを送る
という一連の流れを 1 ページで実現する UI を定義します。

このプロンプトで実装してほしいファイルは次の2つです：
1. backend/app/templates/index.html
2. backend/app/static/js/app.js

[前提コンテキスト]

- プロダクトは「新規事業の企画ドラフトを自己レビューするためのツール」です。
- 想定ユーザーは、新規事業担当・PdM・DX室メンバーなどです。
- ユーザーは次のフローで利用します：
  1. 自分の新しい企画案（NewIdea）をフォームで入力する
  2. 類似する過去の意思決定ケース（DecisionCase）のサマリを閲覧する
  3. それらから生成された「問い（Question）」を見て、企画を見直し、問いの有用性を評価する

バックエンドは FastAPI を想定し、以下の API がすでに用意されている前提とします。

1. POST /api/review_sessions
   入力:
   {
     "new_idea": {
       "title":   string,
       "purpose": string,
       "target":  string,
       "value":   string,
       "model":   string,
       "memo":    string
     },
     "tags": [string, ...]
   }

   出力例:
   {
     "session_id": "xxxx-uuid",
     "new_idea": { ... },
     "questions": [
       {
         "id": "q1",
         "layer": 1,
         "theme": "purpose_kpi",
         "question": "この企画の最終的な目的と成功指標（KPI）を一文で…",
         "based_on_case_ids": ["DC-001", "DC-003"],
         "risk_type": "generic_check",
         "priority": 3,
         "note_for_admin": "..."
       },
       ...
     ],
     "similar_cases": [
       {
         "id": "DC-001",
         "title": "...",
         "summary": "...",
         "status": "rejected",
         "main_reason": "...",
         "tags": ["B2B", "SaaS", ...]
       },
       ...
     ]
   }

2. POST /api/review_sessions/{session_id}/feedback
   入力:
   {
     "feedbacks": [
       {
         "question_id": "q1",
         "usefulness_score": 1〜5 の整数,
         "applied": true/false,
         "note": "この問いをきっかけに〇〇を書き直した、など任意メモ"
       },
       ...
     ]
   }

   出力:
   { "ok": true } 程度を想定。

3. （任意）GET /api/decision_cases/{id}
   入力: なし
   出力:
   {
     "id": string,
     "title": string,
     "summary": string,
     "status": "adopted" | "rejected" | "pending",
     "main_reason": string,
     "tags": [string, ...],
     "decision_date": string,
     "decision_level": string
   }

テンプレート構成:
- backend/app/templates/index.html
- backend/app/static/js/app.js

FastAPI 側では Jinja2Templates を使って index.html を返す前提です。

## [実装してほしいファイル 1] backend/app/templates/index.html

■ 要件（HTML構造・UX）

1. シンプルなシングルページ構成
   - ページ全体は次の 3 カラム構成を基本としてください（画面幅が狭い場合は縦並びで良いです）:
     - 左：新規企画入力フォーム（NewIdea フォーム）
     - 中央：生成された「問い」リスト
     - 右：類似 DecisionCase のリスト

2. NewIdea 入力フォーム
   - form#new-idea-form を用意し、以下の入力欄を持たせてください:
     - input#idea-title      : 企画名
     - textarea#idea-purpose : 目的・課題
     - textarea#idea-target  : 対象ユーザー
     - textarea#idea-value   : 提供価値・ユースケース
     - textarea#idea-model   : 収益モデル・ビジネスモデルのメモ
     - textarea#idea-memo    : その他メモ・前提
     - input#idea-tags       : カンマ区切りタグ（例: "B2B,SaaS,製造業"）
   - 送信ボタン:
     - button#start-review-btn
     - ボタンラベル: 「この企画で自己レビューを始める」
   - 送信中はボタンを disabled にし、「送信中…」とわかる表示にしてください。

3. 問いリスト表示エリア
   - div#questions-section を用意してください。
   - 初期状態では「まだ自己レビューは開始されていません」といったプレースホルダーテキストを表示してください。
   - POST /api/review_sessions のレスポンスを受け取ったら、questions 配列をカード形式で表示する想定です。
   - 各問いカードの構造（例）:
     - div.question-card (data-question-id 属性に question.id をセット)
       - 上部: レイヤー・テーマ
         - span.question-layer   : 例 "L1" / "L2" / "L3"
         - span.question-theme   : 例 "purpose_kpi"
       - 本文: p.question-text    : 問いの本文
       - 類似 DecisionCase へのリンク:
         - div.related-cases
         - 中に button.view-case-btn を、data-case-id にケースIDを入れて配置
       - フィードバック入力エリア:
         - 「この問いは役に立ちましたか？」5段階評価
           → select.usefulness-score（option: 1〜5）
         - 「この問いによって企画内容を修正・追記しましたか？」
           → input.applied-checkbox (type=checkbox)
         - 「どんな修正をしたか？」任意メモ
           → textarea.feedback-note
   - 問い全体のフィードバック送信用ボタン:
     - button#submit-feedback-btn
     - ページ下部に設置し、「評価を送信」といったラベルにしてください。

4. 類似 DecisionCase リストエリア
   - div#cases-section を用意してください。
   - POST /api/review_sessions の similar_cases を表示します。
   - 1件あたりのカード構造（例）:
     - h3.case-title   : タイトル
     - span.case-status: ステータス（採用 / 不採用 / 保留 等）
     - div.case-tags   : タグ一覧
     - p.case-summary  : 概要サマリ（数行程度）
     - button.case-detail-btn（data-case-id をセット）
       - ラベル: 「詳細を見る」
   - 「詳細を見る」クリック時にモーダルか右側エリア内で詳細を展開するスペースを確保してください:
     - 例: div#case-detail-modal
       - 中に title, main_reason, summary 等を表示できるようにします。

5. ステータス表示領域
   - ページ上部に div#global-message を用意し、
     - 成功メッセージ
     - エラーメッセージ
     - ローディング中インジケータ
     などを表示できるようにしてください。

6. スタイル
   - CSS フレームワークは使わず、テンプレート内の <style> タグで最低限のレイアウトと装飾を定義してください。
   - 必須:
     - 全体の余白
     - 3 カラムレイアウト（狭い画面では 1 カラムに落ちる）
     - カードの枠線・余白・影などの最低限の装飾
     - ボタンの基本スタイル

7. JS 読み込み
   - ページ末尾で次のように JS を読み込んでください:
     <script src="{{ url_for('static', path='/js/app.js') }}" defer></script>
   - defer を付けて、DOM 構築後に実行されるようにしてください。


## [実装してほしいファイル 2] backend/app/static/js/app.js

■ 要件（ロジック）

1. 初期化とイベント登録
   - document.addEventListener('DOMContentLoaded', ...) 内で初期化処理を行ってください。
   - 次の要素を取得してください:
     - フォーム:           #new-idea-form
     - 送信ボタン:         #start-review-btn
     - 問い表示エリア:     #questions-section
     - 類似ケース表示エリア:#cases-section
     - フィードバック送信: #submit-feedback-btn
     - グローバルメッセージ: #global-message
   - フォーム送信時のイベントハンドラでは:
     - event.preventDefault() でページ遷移を防止
     - 入力値を取得して payload オブジェクトを構築:
       const payload = {
         new_idea: {
           title,
           purpose,
           target,
           value,
           model,
           memo,
         },
         tags: parsedTagsArray, // カンマ区切り文字列を配列に変換
       };
     - fetch('/api/review_sessions', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(payload),
       }) を実行してください。
     - ローディング中は送信ボタンを disabled にし、ラベルを「送信中…」に変更します。

2. レビューセッション開始レスポンスの処理
   - 成功時:
     - レスポンスJSONから session_id を取り出し、モジュール内変数 let currentSessionId に保存してください。
     - questions を元に renderQuestions(questions) を呼び、問いカードを生成・表示します。
     - similar_cases を元に renderCases(cases) を呼び、類似ケースカードを生成・表示します。
     - showMessage('success', '自己レビュー用の問いを生成しました。') のような形で成功メッセージを表示してください。
   - エラー時:
     - エラー内容を showMessage('error', '自己レビューの開始に失敗しました') などで表示してください。
   - finally:
     - ボタンの disabled を解除し、ラベルを元に戻してください。

3. 問いカードのレンダリング
   - 関数 renderQuestions(questions) を実装してください。
     - questions-section の中身を一度クリアし、
     - questions 配列に対して createQuestionCard(question) を呼び出し、生成された DOM 要素を append します。
   - 関数 createQuestionCard(question) の要件:
     - div.question-card 要素を作成し、data-question-id 属性に question.id をセットします。
     - 子要素として:
       - レイヤー表示 span.question-layer （例: "L1"）
       - テーマ表示 span.question-theme （例: "purpose_kpi"）
       - p.question-text （問い本文）
       - div.related-cases 内に、based_on_case_ids ごとに button.view-case-btn を配置し、
         data-case-id 属性にケースIDをセットします。
       - 5段階評価 select.usefulness-score（option value: 1〜5）
       - applied 用 input.applied-checkbox (type='checkbox')
       - メモ用 textarea.feedback-note
     - 「関連ケースを見る」ボタンはクリック時に handleCaseDetailClick(caseId) を呼ぶようにしてください（関数は後述）。

4. 類似ケースカードのレンダリング
   - 関数 renderCases(cases) を実装してください。
     - cases-section の中身をクリアし、
     - cases 配列の各要素に対してカードDOMを作成して append します。
     - カード内容:
       - h3.case-title
       - span.case-status
       - div.case-tags
       - p.case-summary
       - button.case-detail-btn（data-case-id を設定。ラベルは「詳細を見る」）
   - 「詳細を見る」ボタンのクリック時:
     - handleCaseDetailClick(caseId) を呼び出します。
   - 関数 handleCaseDetailClick(caseId):
     - fetch('/api/decision_cases/' + encodeURIComponent(caseId)) を実行し、
     - 取得したケース詳細を、モーダル div#case-detail-modal に描画します。
     - 失敗時には showMessage('error', 'ケース詳細の取得に失敗しました') を呼びます。

5. フィードバック送信ロジック
   - #submit-feedback-btn クリック時の処理:
     - currentSessionId が未設定の場合は showMessage('error', '先に自己レビューを開始してください') を表示し、処理を中断します。
     - document.querySelectorAll('.question-card') で全カードを取得し、各カードからフィードバック情報を集めて配列を作成します:
       const feedbacks = Array.from(document.querySelectorAll('.question-card')).map(card => {
         const questionId = card.dataset.questionId;
         const scoreSelect = card.querySelector('.usefulness-score');
         const appliedCheckbox = card.querySelector('.applied-checkbox');
         const noteTextarea = card.querySelector('.feedback-note');
         return {
           question_id: questionId,
           usefulness_score: scoreSelect.value ? Number(scoreSelect.value) : null,
           applied: appliedCheckbox.checked,
           note: noteTextarea.value || "",
         };
       });
     - fetch(`/api/review_sessions/${encodeURIComponent(currentSessionId)}/feedback`, {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ feedbacks }),
       }) を実行してください。
     - 送信中はボタンを disabled にし、ラベルを「送信中…」に変更します。
   - 成功時:
     - showMessage('success', 'フィードバックを保存しました。ありがとうございました。') を表示してください。
   - エラー時:
     - showMessage('error', 'フィードバックの送信に失敗しました') を表示してください。
   - finally でボタンを元に戻します。

6. ヘルパー関数
   - showMessage(type, text) を実装してください。
     - type は 'success' | 'error' | 'info' を想定し、
       - success: 緑系
       - error: 赤系
       - info: 青系
       のように CSS クラスを切り替えて global-message にテキストを表示します。
   - parseTags(raw) を実装してください。
     - raw.split(',') で分割し、trim() 済みの文字列のうち空でないものだけを配列で返します。

7. エラーハンドリング
   - fetch の Promise チェーンまたは async/await を使い、try/catch でネットワークエラーを捕捉してください。
   - レスポンスステータスが 200 以外の場合は、可能であればレスポンス本文の message 等を表示し、それがない場合は汎用的なエラーメッセージを表示してください。




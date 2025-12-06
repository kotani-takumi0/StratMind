# プロンプト
## 目的
- フロントエンドで生成された問いがどのレイヤーに属するかを明示し、レイヤー別の確認をしやすくする。

## 変更点
- 問題カードヘッダーにレイヤー番号のバッジを追加し、Theme名とセットで表示するようにした。
- APIレスポンスの`similar_cases`を正しく受け取り、ケース表示が機能するようにフロント側のデータ受け取りを修正した。
- 入力タイトルのIDを実際のDOMと合わせた（`idea-title`）。
- レイヤー別のバッジスタイル（Layer1/2/3/unknown）をCSSに追加。

## 対象ファイル
- backend/statics/js/app.js
- backend/statics/css/style.css
- backend/prompts/layer_prompt.md

# StratMind

StratMindは、過去の意思決定事例に基づき、AIが新規企画への「問い」を自動生成することで、アイデアのレビューを加速させる意思決定支援ツールです。

---
## 環境
- Python3.10以降
- OpenAI APIキー（もしくはGemini APIに対応(予定)）

## 環境設定と実行
1. ライブラリのインストール
   ```[bash]
   pip install -r requirements.txt
   ```
   
2. **環境変数の設定**  
   環境変数`OPENAI_API_KEY`にAPIキーをセット 
   （Geminiの場合は`GEMINI_API_KEY`）
   
4. 実行・サーバー起動
   ```[bash]
   uvicorn app.main:app --reload
   ```


### 主な使用技術
**バックエンド :**
- [FastAPI](https://fastapi.tiangolo.com/) - Webフレームワーク
- [Uvicorn](https://www.uvicorn.org/) - ASGIサーバー
- [Pydantic](https://docs.pydantic.dev/) - データ検証
- [OpenAI API](https://platform.openai.com/)

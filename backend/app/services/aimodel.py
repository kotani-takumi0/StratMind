import os
from openai import OpenAI
from google import genai

# 2025/11/20 add ---
def get_ai_client() -> OpenAI | genai.Client:
    """
    FastAPI起動時に、APIキーの有無に基づいて使用するAIクライアントを選択する関数
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    # デフォルトはOpenAI
    if openai_key:
        return OpenAI()
    
    # OpenAIキーがない場合、Geminiキーの有無を確認
    elif gemini_key:
        print("OpenAI APIキーがないため、Gemini API (2.5 Flash) を使用します。")
        return genai.Client()
    
    # どちらのキーもない場合
    else:
        raise ValueError("AIサービスのAPIキーが設定されていません。")
# ---
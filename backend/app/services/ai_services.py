from __future__ import annotations

import os
import numpy as np
from openai import OpenAI
from google import genai
from google.genai import types

from app.models import LLMQuestionsPayload

# 11/27 add: AIを使うサービスはここに集約
class AI_Services:
    def __init__(self):
        self.client = self.get_ai_client()

    def get_ai_client(self) -> OpenAI | genai.Client:
        """
        初回で呼ばれた際にAPIキーの有無に基づいて使用するAIクライアントを選択する関数
        """
        openai_key = os.getenv("OPENAI_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        # デフォルトはOpenAI
        if openai_key:
            print("OpenAI APIを使用します。")
            return OpenAI()
        
        # OpenAIキーがない場合、Geminiキーの有無を確認
        elif gemini_key:
            print("OpenAI APIキーがないため、Gemini API (2.5 Flash) を使用します。")
            return genai.Client()
        
        # どちらのキーもない場合
        else:
            raise ValueError("AIサービスのAPIキーが設定されていません。")
    
    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """
        与えられたテキスト群に対して OpenAI の埋め込みを計算し、
        shape = (len(texts), D) の numpy.ndarray を返す。

        - モデル: text-embedding-3-small
        - .env の OPENAI_API_KEY を利用する
        """
        if not texts:
            return np.zeros((0, 0), dtype="float32")
        
        vectors = []
        
        # OpenAIクライアントの場合
        if isinstance(self.client, OpenAI):
            # モデル名: text-embedding-3-small (OpenAI)
            res = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
            )
            vectors = [item.embedding for item in res.data]

        # Geminiクライアントの場合
        elif isinstance(self.client, genai.Client):
            # モデル名: gemini-embedding-001 (Google)
            res = self.client.models.embed_content(
                model="gemini-embedding-001", 
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type="SEMANTIC_SIMILARITY" # 例: 意味的類似性のタスク
                )
            )
            if res.embeddings is None:
                raise ValueError()
            # Geminiのレスポンスは .embeddings プロパティを持ち、要素ごとに値が格納されている
            # 11/27 add: e.valuesがNoneの場合list()がエラーを吐くのでそれ防止
            vectors = [list(e.values or []) for e in res.embeddings]

        arr = np.array(vectors, dtype="float32")
        return arr
    
    def call_llm(self, system_prompt: str, user_message: str) -> LLMQuestionsPayload:
        """
        services/question_generator.pyで使用
        
        OpenAI Responses API を呼び出し、JSON をパースして内部モデルに変換する。
        """
        if isinstance(self.client, OpenAI):
            # res = _client.responses.create(
            #     model="gpt-4.1-mini",
            #     input=[
            #         {"role": "system", "content": system_prompt},
            #         {"role": "user", "content": user_message},
            #     ],
            #     response_format={"type": "json_object"},
            # )
            # content = res.output_text

            # 11/27 add: 未確認！
            # OpenAI SDK v1.40.0以降ならこれでも動くらしい (Pydanticモデルで返してくれる)
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                response_format=LLMQuestionsPayload, # ここにPydanticクラスを渡せる
            )
            parsed_data = completion.choices[0].message.parsed

            # None防止
            if parsed_data is None:
                raise ValueError(f"[OpenAI API] refused of failed to parse: {completion.choices[0].message.refusal}")

            return parsed_data

        elif isinstance(self.client, genai.Client):

            # Gemini (gemini-2.5-flash) の処理
            res = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[types.Content(role="user", parts=[types.Part.from_text(text=user_message)])],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=LLMQuestionsPayload,
                ),
            )

            # None防止
            if res.text is None:
                raise ValueError("[Gemini API] failed generate content")
            
            return LLMQuestionsPayload.model_validate_json(res.text)
        else:
            raise ValueError("Unknown API client")

ai_service = AI_Services()
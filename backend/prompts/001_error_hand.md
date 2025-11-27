# Error Log / トラブルシューティングメモ

このプロジェクトでこれまでに発生した主なエラーと、その原因・対応内容をまとめます。

---

## 1. PydanticImportError: `BaseSettings` has been moved to the `pydantic-settings` package

### 症状

FastAPI を起動した際に、次のようなエラーが発生した。

```text
pydantic.errors.PydanticImportError: `BaseSettings` has been moved to the `pydantic-settings` package.
```

スタックトレース上では `backend/app/config.py` の

```python
from pydantic import BaseSettings
```

を起点としてエラーになっていた。

### 原因

環境で利用している Pydantic が v2 系であり、`BaseSettings` が `pydantic-settings` パッケージに分離されたのに、v1 スタイルの `from pydantic import BaseSettings` を使っていたため。

### 対応

当初は `pydantic-settings` を導入する方向も検討したが、現状の `Settings` クラスは単純な設定値コンテナとしてしか使っておらず、`.env` などからの自動読み込み機能は不要だったため、よりシンプルな対応を採用した。

- `backend/app/config.py` を修正し、`BaseSettings` への依存をやめて `BaseModel` ベースに変更。

修正前:

```python
from pydantic import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Decision Question Helper"
    ...
```

修正後:

```python
from pydantic import BaseModel


class Settings(BaseModel):
    APP_NAME: str = "Decision Question Helper"
    ...
```

`BaseSettings` 固有の機能を使っていなかったため、この変更で互換性を保ったままエラーを解消できた。

---

## 2. ModuleNotFoundError: No module named `pydantic_settings`

### 症状

1 のエラー対応として一度 `pydantic_settings.BaseSettings` を使うように書き換えたところ、FastAPI 起動時に次のエラーが発生した。

```text
ModuleNotFoundError: No module named 'pydantic_settings'
```

### 原因

`from pydantic_settings import BaseSettings` と書き換えたが、開発環境の仮想環境に `pydantic-settings` パッケージがインストールされていなかったため。

### 対応

最終的には「そもそも `BaseSettings` を使わない」方針に切り替えたため、この依存自体を撤去した。

- `backend/app/config.py` から `from pydantic_settings import BaseSettings` を削除。
- `Settings` を `BaseModel` 継承に変更（上記 1 の「修正後」を参照）。

これにより、追加パッケージのインストールなしでアプリ全体が起動するようになった。

---

## 今後の方針メモ

- 本番運用や環境変数ベースの設定管理が必要になった場合は、改めて `pydantic-settings` の導入を検討し、`Settings` を `BaseSettings` 継承に戻すことを想定。
- その際は `requirements.txt` に `pydantic-settings` を追加し、インストール漏れによる `ModuleNotFoundError` を防ぐ。

---

## 3. AssertionError: `jinja2 must be installed to use Jinja2Templates`

### 症状

FastAPI を `uvicorn app.main:app --reload` で起動した際、次のエラーが発生した。

```text
AssertionError: jinja2 must be installed to use Jinja2Templates
```

スタックトレース上では `backend/app/main.py` の

```python
templates = Jinja2Templates(directory=str(BASE_DIR.parent / "templates"))
```

の呼び出しから、`starlette.templating.Jinja2Templates` 内部のアサーションで停止していた。

### 原因

FastAPI/Starlette のテンプレート機能 (`Jinja2Templates`) を使用しているが、仮想環境に `jinja2` パッケージがインストールされていなかったため。

### 対応

テンプレート描画に必要な依存パッケージを追加した。

- `requirements.txt` に `jinja2` を追加。

修正前:

```text
python-dotenv==1.2.1
sniffio==1.3.1
starlette==0.49.3
```

修正後（抜粋）:

```text
python-dotenv==1.2.1
jinja2==3.1.4
sniffio==1.3.1
starlette==0.49.3
```

そのうえで仮想環境内で:

```bash
pip install -r requirements.txt
```

を実行し、`jinja2` をインストールすることでエラーが解消された。

---

## 4. FileNotFoundError: `decision_case.json` が見つからない

### 症状

アプリ起動時の startup フックで次のエラーが発生した。

```text
FileNotFoundError: [Errno 2] No such file or directory: '/home/takumi/StratMind/backend/app/data/decision_case.json'
```

スタックトレース上では `backend/app/services/loader.py` の `load_decision_cases()` 内で
`decision_case.json` を開こうとして失敗していた。

### 原因

実際の JSON ファイルの位置は `backend/data/decision_case.json` であり、
`services/loader.py` のデフォルトパスが 1階層だけしか上に遡っていなかったため、
`backend/app/data/decision_case.json` を参照してしまっていた。

当初の実装では次のようになっていた:

```python
services_dir = Path(__file__).resolve().parent
path = services_dir.parent / "data" / "decision_case.json"
```

このため、`services_dir` (= backend/app/services) から 1階層しか戻らず、
`backend/app/data/decision_case.json` を探しに行っていた。

### 対応

`decision_case.json` の検索位置を正しくするために 2 点修正した。

1. `services/loader.py` のデフォルトパス解決を修正

修正前:

```python
services_dir = Path(__file__).resolve().parent
path = services_dir.parent / "data" / "decision_case.json"
```

修正後:

```python
services_dir = Path(__file__).resolve().parent
path = services_dir.parent.parent / "data" / "decision_case.json"
```

これにより、`backend/app/services/` から 2階層上の `backend/` を起点として
`backend/data/decision_case.json` を参照するようになった。

2. `app/main.py` の `on_startup()` から誤ったパス指定を削除

`BASE_DIR / "data" / "decision_case.json"` という別の誤ったパス組み立てを行っていたため、
これを削除し、`loader.load_decision_cases()` を引数なしで呼ぶように変更した。

この 2つの修正により、起動時に `decision_case.json` が正しい場所から読み込まれ、
`FileNotFoundError` が解消された。

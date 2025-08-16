# 緊急避難場所API (Python)

> このファイルは、「セットアップ手順・使い方・エンドポイント」を説明します。

Python/Flask で実装した API 版です。既存のフロントエンド (`index.html` + `script.js`) と同等の機能をサーバー側で提供します。

## セットアップ

```bash
# PowerShell 例
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r emgcy_API_py/requirements.txt
$env:GOOGLE_MAPS_API_KEY="<あなたのAPIキー>"
python emgcy_API_py/app.py
```

ブラウザでアクセス:
- `http://127.0.0.1:8000/` （簡易ビューア UI。Google Maps 表示は `GOOGLE_MAPS_API_KEY` がある場合のみ）
- API は以下を利用可能（CORS許可済み）

サブパス配下（例: `https://www.hungryclimber.com/emgcy_API_py/`）でも動作するよう相対パス対応済みです。Nginxなどのリバースプロキシ設定で `/emgcy_API_py/` へプロキシしてください。

## エンドポイント

- GET /health ヘルスチェック
- GET /shelters 避難場所一覧
- GET /shelters?limit=100&offset=0&q=綾瀬&bbox=minLon,minLat,maxLon,maxLat でフィルタ/ページング
- GET /nearest?lat=<lat>&lon=<lon>&limit=5 現在地（緯度経度）から近い順（`n` も可）
- GET /nearest/by-zip?zip=1234567&limit=5 郵便番号から近い順（Google Geocoding API 使用）

## データ

リポジトリ直下の CSV を自動検出します。
優先: `mergeFromCity_2.csv` → 次点: `13121_2.csv`

CSV 例 (`13121_2.csv`):
- 施設・場所名（`施設・場所名`）
- 住所（`住所`）
- 緯度（`緯度`）
- 経度（`経度`）

## 注意

- ZIP 検索には環境変数 `GOOGLE_MAPS_API_KEY` が必要です。
- レスポンスは JSON。距離は `distance_km`（km、少数3桁丸め）。
- CORS: 簡易に `*` を許可。GET用途での利用を想定。

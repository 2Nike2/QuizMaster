# 軽量版Python 3.10イメージをベースにする
FROM python:3.10-slim

# 作業フォルダをappに指定
WORKDIR /app

# ホストのrequirements.txtをコンテナの作業フォルダにコピー
COPY requirements.txt .

# pipでrequirements.txtに記載されたパッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# ホストのファイルをコンテナの作業フォルダにコピー
COPY . .

# ポート番号を指定
EXPOSE 80

# コンテナが起動したときにstremlitをポート番号80で実行
CMD ["streamlit", "run", "app.py", "--server.port", "80"]

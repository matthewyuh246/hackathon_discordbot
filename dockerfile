# ベースイメージとしてUbuntuを使用
FROM ubuntu:latest

# 必要なツールのインストール
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Golangをインストール
RUN curl -OL https://golang.org/dl/go1.18.3.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.18.3.linux-amd64.tar.gz && \
    rm go1.18.3.linux-amd64.tar.gz

# PATHにGolangのパスを追加
ENV PATH="/usr/local/go/bin:${PATH}"

# ワーキングディレクトリを設定
WORKDIR /app

# Goモジュールを有効にする
ENV GO111MODULE=on

# ローカルのコードをコンテナにコピー
COPY . .

# Google APIとDiscordの依存パッケージを取得
RUN go mod download

# 環境変数の設定 (.envファイルや credentials.jsonが必要)
COPY .env .env
COPY credentials.json credentials.json

# アプリケーションのビルド
RUN go build -o discordbot main.go

# コンテナ起動時に実行されるコマンド
CMD ["./discordbot"]

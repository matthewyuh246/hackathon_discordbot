# Golangの公式イメージを使用（バージョンは必要に応じて変更）
FROM golang:1.22

# ワーキングディレクトリを設定
WORKDIR /app

# プロジェクトのファイルをコンテナにコピー
COPY . .

# Goモジュールの依存関係をインストール
RUN go mod download

# アプリケーションのビルド
RUN go build -o discordbot main.go

# コンテナ起動時に実行されるコマンド
CMD ["./discordbot"]

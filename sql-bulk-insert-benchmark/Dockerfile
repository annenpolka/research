FROM ubuntu:22.04

# 非対話モードでパッケージインストール
ENV DEBIAN_FRONTEND=noninteractive

# 基本パッケージとPython、Rubyをインストール
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ruby \
    ruby-dev \
    build-essential \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Bundlerをインストール
RUN gem install bundler

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係ファイルをコピー
COPY requirements.txt Gemfile ./

# Python依存関係をインストール
RUN pip3 install --no-cache-dir -r requirements.txt

# Ruby依存関係をインストール
RUN bundle install

# ソースコードをコピー
COPY . .

# スクリプトに実行権限を付与
RUN chmod +x python_benchmark.py ruby_benchmark.rb run_benchmarks.sh

# デフォルトコマンド
CMD ["/bin/bash"]

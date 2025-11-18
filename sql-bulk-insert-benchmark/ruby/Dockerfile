FROM ruby:3.3-slim

WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    libpq-dev \
    default-mysql-client \
    default-libmysqlclient-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Bundlerのインストール
RUN gem install bundler

# Gemfileのコピーと依存関係のインストール
COPY Gemfile Gemfile.lock* ./
RUN bundle install

CMD ["tail", "-f", "/dev/null"]

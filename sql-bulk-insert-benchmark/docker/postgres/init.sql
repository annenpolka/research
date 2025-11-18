-- PostgreSQL初期化スクリプト

-- シンプルなテストテーブル
CREATE TABLE IF NOT EXISTS simple_records (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    age INTEGER NOT NULL,
    score DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 複雑なテストテーブル
CREATE TABLE IF NOT EXISTS complex_records (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    age INTEGER NOT NULL,
    score DECIMAL(10, 2) NOT NULL,
    balance DECIMAL(15, 2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    category VARCHAR(50),
    description TEXT,
    metadata JSONB,
    tags VARCHAR(100)[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    ip_address INET
);

-- インデックス付きテーブル
CREATE TABLE IF NOT EXISTS indexed_records (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    age INTEGER NOT NULL,
    score DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_indexed_records_email ON indexed_records(email);
CREATE INDEX idx_indexed_records_age ON indexed_records(age);
CREATE INDEX idx_indexed_records_score ON indexed_records(score);

-- 権限設定
GRANT ALL PRIVILEGES ON DATABASE benchmark TO benchmark;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO benchmark;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO benchmark;

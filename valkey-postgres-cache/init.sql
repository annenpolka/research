-- パラメータ管理テーブル
CREATE TABLE IF NOT EXISTS parameters (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    category VARCHAR(100),
    data_type VARCHAR(50) DEFAULT 'string',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 更新日時を自動更新するトリガー
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_parameters_updated_at
    BEFORE UPDATE ON parameters
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- サンプルデータの挿入
INSERT INTO parameters (key, value, description, category, data_type) VALUES
    ('app.max_connections', '100', 'アプリケーションの最大同時接続数', 'system', 'integer'),
    ('app.timeout_seconds', '30', 'リクエストタイムアウト時間（秒）', 'system', 'integer'),
    ('app.enable_debug', 'false', 'デバッグモードの有効化', 'system', 'boolean'),
    ('api.rate_limit', '1000', '1時間あたりのAPIリクエスト上限', 'api', 'integer'),
    ('api.version', 'v2.1.0', 'APIバージョン', 'api', 'string'),
    ('cache.default_ttl', '3600', 'デフォルトキャッシュTTL（秒）', 'cache', 'integer'),
    ('cache.max_size_mb', '512', 'キャッシュの最大サイズ（MB）', 'cache', 'integer'),
    ('feature.new_ui_enabled', 'true', '新UIの有効化フラグ', 'feature', 'boolean'),
    ('feature.maintenance_mode', 'false', 'メンテナンスモード', 'feature', 'boolean'),
    ('db.pool_size', '20', 'データベース接続プールサイズ', 'database', 'integer')
ON CONFLICT (key) DO NOTHING;

-- インデックスの作成
CREATE INDEX IF NOT EXISTS idx_parameters_category ON parameters(category);
CREATE INDEX IF NOT EXISTS idx_parameters_key ON parameters(key);

-- パラメータ統計ビュー
CREATE OR REPLACE VIEW parameter_stats AS
SELECT
    category,
    COUNT(*) as param_count,
    MAX(updated_at) as last_updated
FROM parameters
GROUP BY category;

-- Database initialization script

-- Create indexes for better query performance
-- These will be created by Alembic, but listed here for reference

-- Posts indexes
CREATE INDEX IF NOT EXISTS idx_posts_created_utc ON posts(created_utc);
CREATE INDEX IF NOT EXISTS idx_posts_subreddit ON posts(subreddit);
CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author);
CREATE INDEX IF NOT EXISTS idx_posts_entities_gin ON posts USING GIN(entities);
CREATE INDEX IF NOT EXISTS idx_posts_sentiment ON posts(sentiment);

-- Comments indexes
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_created_utc ON comments(created_utc);
CREATE INDEX IF NOT EXISTS idx_comments_author ON comments(author);

-- Entity daily indexes
CREATE INDEX IF NOT EXISTS idx_entities_daily_entity ON entities_daily(entity);
CREATE INDEX IF NOT EXISTS idx_entities_daily_dt ON entities_daily(dt);

-- Prices indexes
CREATE INDEX IF NOT EXISTS idx_prices_symbol ON prices(symbol);
CREATE INDEX IF NOT EXISTS idx_prices_timestamp ON prices(timestamp);

-- Snapshots indexes
CREATE INDEX IF NOT EXISTS idx_snapshots_key ON snapshots(key);

-- Admin blocklist indexes
CREATE INDEX IF NOT EXISTS idx_blocklist_type ON admin_blocklist(type);
CREATE INDEX IF NOT EXISTS idx_blocklist_value ON admin_blocklist(value);

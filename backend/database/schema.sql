-- ProxyAssessmentTool PostgreSQL Schema
-- Production-grade database design with proper normalization

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis"; -- For geolocation features
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- For query performance monitoring

-- Create custom types
CREATE TYPE proxy_protocol AS ENUM ('http', 'https', 'socks4', 'socks5');
CREATE TYPE proxy_anonymity AS ENUM ('transparent', 'anonymous', 'elite');
CREATE TYPE test_status AS ENUM ('pending', 'testing', 'completed', 'failed');

-- ASN (Autonomous System Number) information
CREATE TABLE asn_info (
    asn VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    organization VARCHAR(255),
    country_code CHAR(2),
    is_hosting BOOLEAN DEFAULT FALSE,
    is_vpn_provider BOOLEAN DEFAULT FALSE,
    reputation_score DECIMAL(3,2) CHECK (reputation_score >= 0 AND reputation_score <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_asn_reputation ON asn_info(reputation_score);
CREATE INDEX idx_asn_type ON asn_info(is_hosting, is_vpn_provider);

-- Proxy providers/sources
CREATE TABLE proxy_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    success_rate DECIMAL(5,2) DEFAULT 0.00,
    last_fetch_at TIMESTAMP WITH TIME ZONE,
    last_success_at TIMESTAMP WITH TIME ZONE,
    total_fetches INTEGER DEFAULT 0,
    successful_fetches INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_source_active ON proxy_sources(is_active, last_fetch_at);

-- Main proxies table
CREATE TABLE proxies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ip INET NOT NULL,
    port INTEGER NOT NULL CHECK (port > 0 AND port <= 65535),
    protocol proxy_protocol NOT NULL,
    anonymity_level proxy_anonymity,
    asn VARCHAR(20) REFERENCES asn_info(asn),
    source_id UUID REFERENCES proxy_sources(id),
    
    -- Geolocation
    country_code CHAR(2),
    city VARCHAR(100),
    region VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    location GEOGRAPHY(POINT, 4326), -- PostGIS point
    
    -- Network info
    isp VARCHAR(255),
    organization VARCHAR(255),
    is_mobile BOOLEAN DEFAULT FALSE,
    is_hosting BOOLEAN DEFAULT FALSE,
    is_residential BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_tested_at TIMESTAMP WITH TIME ZONE,
    times_seen INTEGER DEFAULT 1,
    times_tested INTEGER DEFAULT 0,
    times_working INTEGER DEFAULT 0,
    
    -- Constraints
    CONSTRAINT unique_proxy UNIQUE(ip, port, protocol)
);

-- Indexes for performance
CREATE INDEX idx_proxy_location ON proxies USING GIST(location);
CREATE INDEX idx_proxy_working ON proxies(times_working, times_tested);
CREATE INDEX idx_proxy_last_tested ON proxies(last_tested_at);
CREATE INDEX idx_proxy_country ON proxies(country_code);
CREATE INDEX idx_proxy_protocol ON proxies(protocol);
CREATE INDEX idx_proxy_composite ON proxies(protocol, country_code, is_mobile);

-- Proxy test results
CREATE TABLE proxy_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    proxy_id UUID NOT NULL REFERENCES proxies(id) ON DELETE CASCADE,
    test_id UUID NOT NULL, -- Groups tests in same batch
    status test_status NOT NULL DEFAULT 'pending',
    
    -- Basic test results
    is_working BOOLEAN DEFAULT FALSE,
    response_time_ms INTEGER,
    exit_ip INET,
    detected_protocol proxy_protocol,
    anonymity_level proxy_anonymity,
    
    -- Speed test results
    download_speed_mbps DECIMAL(10,2),
    upload_speed_mbps DECIMAL(10,2),
    
    -- Stability metrics
    avg_latency_ms DECIMAL(10,2),
    min_latency_ms DECIMAL(10,2),
    max_latency_ms DECIMAL(10,2),
    jitter_ms DECIMAL(10,2),
    packet_loss_percent DECIMAL(5,2),
    stability_score DECIMAL(3,2),
    
    -- Security tests
    dns_leak_detected BOOLEAN DEFAULT FALSE,
    ip_leak_detected BOOLEAN DEFAULT FALSE,
    ssl_intercepted BOOLEAN DEFAULT FALSE,
    webrtc_leak_detected BOOLEAN DEFAULT FALSE,
    
    -- Advanced results
    ja3_fingerprint VARCHAR(32),
    ja3s_fingerprint VARCHAR(32),
    tls_version VARCHAR(10),
    cipher_suite VARCHAR(100),
    
    -- Fraud/risk assessment
    fraud_score DECIMAL(3,2) CHECK (fraud_score >= 0 AND fraud_score <= 1),
    risk_level VARCHAR(20),
    risk_factors JSONB,
    
    -- Test metadata
    error_message TEXT,
    test_duration_ms INTEGER,
    tested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional data
    raw_results JSONB
);

-- Indexes for test results
CREATE INDEX idx_test_proxy ON proxy_tests(proxy_id, tested_at DESC);
CREATE INDEX idx_test_batch ON proxy_tests(test_id);
CREATE INDEX idx_test_working ON proxy_tests(is_working, tested_at DESC);
CREATE INDEX idx_test_timestamp ON proxy_tests(tested_at DESC);

-- Proxy blacklist
CREATE TABLE proxy_blacklist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ip INET NOT NULL,
    port INTEGER,
    reason VARCHAR(255) NOT NULL,
    source VARCHAR(100),
    severity VARCHAR(20) DEFAULT 'medium',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT unique_blacklist UNIQUE(ip, port)
);

CREATE INDEX idx_blacklist_ip ON proxy_blacklist(ip);
CREATE INDEX idx_blacklist_expires ON proxy_blacklist(expires_at) WHERE expires_at IS NOT NULL;

-- User favorites/saved proxies
CREATE TABLE user_proxy_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL, -- External user ID
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_list UNIQUE(user_id, name)
);

CREATE TABLE user_proxy_list_items (
    list_id UUID NOT NULL REFERENCES user_proxy_lists(id) ON DELETE CASCADE,
    proxy_id UUID NOT NULL REFERENCES proxies(id) ON DELETE CASCADE,
    notes TEXT,
    tags TEXT[],
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (list_id, proxy_id)
);

-- API usage tracking
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_key VARCHAR(255) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    request_body JSONB,
    response_status INTEGER,
    response_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_key ON api_usage(api_key, created_at DESC);
CREATE INDEX idx_api_endpoint ON api_usage(endpoint, created_at DESC);
CREATE INDEX idx_api_timestamp ON api_usage(created_at DESC);

-- Scanning history and statistics
CREATE TABLE scan_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_type VARCHAR(50) NOT NULL, -- 'discovery', 'active_scan', 'scheduled'
    targets_scanned INTEGER DEFAULT 0,
    proxies_found INTEGER DEFAULT 0,
    duration_seconds INTEGER,
    configuration JSONB,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_by VARCHAR(100)
);

CREATE INDEX idx_scan_type ON scan_history(scan_type, started_at DESC);

-- Performance metrics table for monitoring
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20,4) NOT NULL,
    metric_unit VARCHAR(20),
    tags JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_name ON performance_metrics(metric_name, recorded_at DESC);
CREATE INDEX idx_metrics_time ON performance_metrics(recorded_at DESC);

-- Materialized view for proxy statistics
CREATE MATERIALIZED VIEW proxy_stats AS
SELECT 
    p.id,
    p.ip,
    p.port,
    p.protocol,
    p.country_code,
    p.is_mobile,
    COUNT(pt.id) as total_tests,
    COUNT(CASE WHEN pt.is_working = true THEN 1 END) as successful_tests,
    AVG(pt.response_time_ms) as avg_response_time,
    AVG(pt.download_speed_mbps) as avg_download_speed,
    AVG(pt.stability_score) as avg_stability_score,
    MAX(pt.tested_at) as last_test_date,
    CASE 
        WHEN COUNT(pt.id) > 0 THEN 
            ROUND(COUNT(CASE WHEN pt.is_working = true THEN 1 END)::DECIMAL / COUNT(pt.id) * 100, 2)
        ELSE 0 
    END as success_rate
FROM proxies p
LEFT JOIN proxy_tests pt ON p.id = pt.proxy_id
GROUP BY p.id;

CREATE INDEX idx_proxy_stats_success ON proxy_stats(success_rate DESC);
CREATE INDEX idx_proxy_stats_country ON proxy_stats(country_code, success_rate DESC);

-- Functions and triggers
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_asn_updated_at BEFORE UPDATE ON asn_info
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_user_lists_updated_at BEFORE UPDATE ON user_proxy_lists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Function to update proxy location geography
CREATE OR REPLACE FUNCTION update_proxy_location()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.location = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_proxy_location_trigger BEFORE INSERT OR UPDATE ON proxies
    FOR EACH ROW EXECUTE FUNCTION update_proxy_location();

-- Function to calculate proxy health score
CREATE OR REPLACE FUNCTION calculate_proxy_health(proxy_id UUID)
RETURNS TABLE(
    health_score DECIMAL,
    reliability DECIMAL,
    performance DECIMAL,
    security DECIMAL
) AS $$
DECLARE
    stats RECORD;
BEGIN
    SELECT 
        COUNT(*) as total_tests,
        COUNT(CASE WHEN is_working = true THEN 1 END) as working_tests,
        AVG(response_time_ms) as avg_response,
        AVG(stability_score) as avg_stability,
        AVG(download_speed_mbps) as avg_speed,
        BOOL_OR(dns_leak_detected OR ip_leak_detected OR ssl_intercepted) as has_security_issues
    INTO stats
    FROM proxy_tests
    WHERE proxy_id = $1
    AND tested_at > CURRENT_TIMESTAMP - INTERVAL '7 days';
    
    -- Calculate component scores
    reliability := CASE 
        WHEN stats.total_tests > 0 THEN 
            (stats.working_tests::DECIMAL / stats.total_tests) 
        ELSE 0 
    END;
    
    performance := CASE
        WHEN stats.avg_response IS NOT NULL THEN
            LEAST(1.0, GREATEST(0, 1 - (stats.avg_response / 5000.0)))
        ELSE 0
    END;
    
    security := CASE
        WHEN stats.has_security_issues THEN 0.5
        ELSE 1.0
    END;
    
    -- Overall health score
    health_score := (reliability * 0.4 + performance * 0.3 + 
                    COALESCE(stats.avg_stability, 0.5) * 0.2 + security * 0.1);
    
    RETURN QUERY SELECT health_score, reliability, performance, security;
END;
$$ LANGUAGE plpgsql;

-- Partitioning for large tables (proxy_tests by month)
CREATE TABLE proxy_tests_2024_01 PARTITION OF proxy_tests
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE proxy_tests_2024_02 PARTITION OF proxy_tests
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Add more partitions as needed...

-- Grants for application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO proxyapp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO proxyapp;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO proxyapp;
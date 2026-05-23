-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table 1: Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Table 2: User Profiles (Targeting Criteria & Settings)
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    target_titles JSONB NOT NULL DEFAULT '[]'::jsonb,
    target_locations JSONB NOT NULL DEFAULT '[]'::jsonb,
    salary_min INTEGER CHECK (salary_min >= 0),
    experience_level VARCHAR(50) NOT NULL DEFAULT 'mid',
    job_types JSONB NOT NULL DEFAULT '[]'::jsonb,
    keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
    excluded_keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
    resume_url VARCHAR(512),
    consent_given BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_experience ON user_profiles(experience_level);

-- Table 3: Jobs (Normalized Jobs crawled from various sources)
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source VARCHAR(100) NOT NULL,
    original_id VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    is_remote BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT NOT NULL,
    salary_min INTEGER CHECK (salary_min >= 0),
    salary_max INTEGER CHECK (salary_max >= 0),
    salary_currency VARCHAR(10) DEFAULT 'USD',
    url VARCHAR(1024) UNIQUE NOT NULL,
    posted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    raw_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    hash_key VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_salary_range CHECK (salary_max IS NULL OR salary_min IS NULL OR salary_max >= salary_min)
);

CREATE INDEX IF NOT EXISTS idx_jobs_source_original ON jobs(source, original_id);
CREATE INDEX IF NOT EXISTS idx_jobs_posted_at ON jobs(posted_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_hash_key ON jobs(hash_key);
CREATE INDEX IF NOT EXISTS idx_jobs_title_company ON jobs(title, company);

-- Table 4: Job Matches (Matches calculated by the matching engine)
CREATE TABLE IF NOT EXISTS job_matches (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    match_score DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (match_score >= 0.0 AND match_score <= 1.0),
    matching_details JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'viewed', 'saved', 'applied', 'dismissed')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, job_id)
);

CREATE INDEX IF NOT EXISTS idx_job_matches_user_status ON job_matches(user_id, status);
CREATE INDEX IF NOT EXISTS idx_job_matches_score ON job_matches(match_score DESC);

-- Table 5: Social Credentials (Secure encrypted tokens for notifications/monitoring)
CREATE TABLE IF NOT EXISTS social_credentials (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    twitter_token TEXT, -- Encrypted AES-256
    telegram_chat_id VARCHAR(255), -- Encrypted AES-256
    whatsapp_phone VARCHAR(255), -- Encrypted AES-256
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table 6: Audit Logs (For compliance, GDPR, CCPA audit tracking)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(512),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action ON audit_logs(user_id, action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

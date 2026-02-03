-- ============================================================================
-- SEC 10-K Analysis Platform - Database Schema
-- ============================================================================
-- Platform: Supabase (PostgreSQL)
-- Version: 1.0
-- ============================================================================

-- ============================================================================
-- USERS & AUTH
-- ============================================================================
-- Note: Supabase handles auth.users table automatically
-- We extend it with a profiles table

CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    
    -- Subscription & Billing
    subscription_tier TEXT DEFAULT 'free', -- 'free', 'beta', 'pro'
    subscription_status TEXT DEFAULT 'active', -- 'active', 'cancelled', 'expired'
    tokens_remaining INTEGER DEFAULT 0,
    tokens_purchased INTEGER DEFAULT 0, -- Lifetime total
    
    -- Stripe
    stripe_customer_id TEXT UNIQUE,
    stripe_subscription_id TEXT,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    
    -- Settings
    email_notifications BOOLEAN DEFAULT true,
    beta_access BOOLEAN DEFAULT false
);

-- RLS (Row Level Security)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- ============================================================================
-- COMPANIES
-- ============================================================================
-- Store company metadata and extraction status

CREATE TABLE public.companies (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- Company Info
    ticker TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    cik TEXT NOT NULL,
    
    -- Extraction Status
    extraction_status TEXT DEFAULT 'unknown', -- 'working', 'broken', 'unknown'
    last_successful_extraction TIMESTAMPTZ,
    failure_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Search
    tsv_search TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('english', company_name || ' ' || ticker)
    ) STORED
);

CREATE INDEX companies_ticker_idx ON public.companies(ticker);
CREATE INDEX companies_search_idx ON public.companies USING GIN(tsv_search);

-- RLS: Everyone can read companies
ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Companies are viewable by everyone"
    ON public.companies FOR SELECT
    USING (true);

-- ============================================================================
-- REPORTS
-- ============================================================================
-- Store generated 10-K analysis reports

CREATE TABLE public.reports (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- Relationships
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    company_name TEXT NOT NULL,
    
    -- Filing Info
    newer_filing_date DATE NOT NULL,
    older_filing_date DATE NOT NULL,
    newer_accession TEXT NOT NULL,
    older_accession TEXT NOT NULL,
    
    -- Extraction Status
    extraction_success BOOLEAN NOT NULL,
    sections_extracted TEXT[], -- ['Item 1', 'Item 1A', 'Item 7', 'Item 8']
    extraction_issues TEXT[], -- ['Item 7: too short', etc.]
    
    -- AI Analysis
    ai_summaries JSONB, -- { "Item 1": "summary...", "Item 1A": "...", ... }
    
    -- Costs & Tokens
    tokens_used INTEGER NOT NULL DEFAULT 1,
    refunded BOOLEAN DEFAULT false,
    ai_cost_usd DECIMAL(10, 4),
    total_tokens_consumed INTEGER, -- Claude API tokens
    
    -- File Storage
    report_url TEXT, -- URL to full report in Supabase Storage
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    generation_time_seconds INTEGER,
    
    -- Search
    tsv_search TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('english', company_name || ' ' || ticker)
    ) STORED
);

CREATE INDEX reports_user_id_idx ON public.reports(user_id);
CREATE INDEX reports_ticker_idx ON public.reports(ticker);
CREATE INDEX reports_created_at_idx ON public.reports(created_at DESC);
CREATE INDEX reports_search_idx ON public.reports USING GIN(tsv_search);

-- RLS: Users can only see their own reports
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own reports"
    ON public.reports FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own reports"
    ON public.reports FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- ERROR LOGS
-- ============================================================================
-- Track extraction failures for debugging

CREATE TABLE public.error_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- Context
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    ticker TEXT NOT NULL,
    company_name TEXT,
    
    -- Error Details
    error_type TEXT NOT NULL, -- 'extraction_failed', 'api_error', 'timeout', etc.
    error_message TEXT,
    stack_trace TEXT,
    
    -- Extraction Details
    sections_attempted TEXT[],
    sections_succeeded TEXT[],
    sections_failed TEXT[],
    word_counts JSONB, -- { "Item 1": 1234, "Item 1A": 5432, ... }
    
    -- Filing Info
    filing_url TEXT,
    newer_filing_date DATE,
    older_filing_date DATE,
    
    -- Resolution
    status TEXT DEFAULT 'open', -- 'open', 'investigating', 'resolved', 'wontfix'
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX error_logs_ticker_idx ON public.error_logs(ticker);
CREATE INDEX error_logs_status_idx ON public.error_logs(status);
CREATE INDEX error_logs_created_at_idx ON public.error_logs(created_at DESC);

-- RLS: Only admins can view error logs (we'll set this up later)
ALTER TABLE public.error_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- TOKEN TRANSACTIONS
-- ============================================================================
-- Track all token purchases and usage

CREATE TABLE public.token_transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- Relationships
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    report_id UUID REFERENCES public.reports(id) ON DELETE SET NULL,
    
    -- Transaction Details
    transaction_type TEXT NOT NULL, -- 'purchase', 'usage', 'refund', 'grant'
    tokens_amount INTEGER NOT NULL, -- Positive for credits, negative for usage
    
    -- Purchase Details (if applicable)
    stripe_payment_intent_id TEXT,
    amount_gbp DECIMAL(10, 2),
    
    -- Description
    description TEXT,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX token_transactions_user_id_idx ON public.token_transactions(user_id);
CREATE INDEX token_transactions_created_at_idx ON public.token_transactions(created_at DESC);

-- RLS: Users can view their own transactions
ALTER TABLE public.token_transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own transactions"
    ON public.token_transactions FOR SELECT
    USING (auth.uid() = user_id);

-- ============================================================================
-- ADMIN NOTES
-- ============================================================================
-- For tracking issues, user feedback, etc.

CREATE TABLE public.admin_notes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    -- Context
    entity_type TEXT NOT NULL, -- 'user', 'company', 'error_log', 'report'
    entity_id UUID NOT NULL,
    
    -- Note
    note TEXT NOT NULL,
    priority TEXT DEFAULT 'normal', -- 'low', 'normal', 'high', 'urgent'
    
    -- Admin
    admin_user_id UUID REFERENCES public.profiles(id),
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX admin_notes_entity_idx ON public.admin_notes(entity_type, entity_id);
CREATE INDEX admin_notes_created_at_idx ON public.admin_notes(created_at DESC);

-- RLS: Only admins (we'll define this later)
ALTER TABLE public.admin_notes ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_companies_updated_at
    BEFORE UPDATE ON public.companies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- User stats view
CREATE VIEW public.user_stats AS
SELECT 
    p.id,
    p.email,
    p.subscription_tier,
    p.tokens_remaining,
    COUNT(DISTINCT r.id) as total_reports,
    COUNT(DISTINCT r.id) FILTER (WHERE r.refunded = false) as successful_reports,
    COUNT(DISTINCT r.id) FILTER (WHERE r.refunded = true) as refunded_reports,
    SUM(r.ai_cost_usd) as total_spent_usd,
    MAX(r.created_at) as last_report_date
FROM public.profiles p
LEFT JOIN public.reports r ON r.user_id = p.id
GROUP BY p.id, p.email, p.subscription_tier, p.tokens_remaining;

-- Company reliability view
CREATE VIEW public.company_reliability AS
SELECT 
    c.ticker,
    c.company_name,
    c.extraction_status,
    COUNT(r.id) as total_attempts,
    COUNT(r.id) FILTER (WHERE r.extraction_success = true) as successful_extractions,
    COUNT(r.id) FILTER (WHERE r.extraction_success = false) as failed_extractions,
    ROUND(
        COUNT(r.id) FILTER (WHERE r.extraction_success = true)::NUMERIC / 
        NULLIF(COUNT(r.id), 0) * 100, 
        2
    ) as success_rate_pct,
    MAX(r.created_at) as last_attempt
FROM public.companies c
LEFT JOIN public.reports r ON r.ticker = c.ticker
GROUP BY c.ticker, c.company_name, c.extraction_status;

-- ============================================================================
-- SAMPLE DATA (for development)
-- ============================================================================

-- Insert some test companies
INSERT INTO public.companies (ticker, company_name, cik, extraction_status) VALUES
('AAPL', 'Apple Inc.', '0000320193', 'working'),
('TSLA', 'Tesla, Inc.', '0001318605', 'working'),
('NVDA', 'NVIDIA CORP', '0001045810', 'working'),
('DIS', 'Walt Disney Co', '0001744489', 'working');

-- ============================================================================
-- NOTES
-- ============================================================================
/*
Key Design Decisions:

1. **Profiles separate from auth.users**
   - Supabase owns auth.users, we own profiles
   - Easier to extend with custom fields
   
2. **Reports store everything**
   - Full report content in JSONB
   - File URL for formatted version
   - Self-contained for easy debugging
   
3. **Companies table for reliability tracking**
   - Know which companies work/don't work
   - Update extraction_status as we learn
   
4. **Error logs for debugging**
   - Critical for Beta phase
   - Track patterns in failures
   
5. **Token transactions for audit trail**
   - Every token movement tracked
   - Refunds are separate transactions
   
6. **RLS enabled everywhere**
   - Security by default
   - Users can't see others' data
*/

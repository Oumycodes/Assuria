-- Assura Database Schema for Supabase Postgres
-- Run this in your Supabase SQL editor

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector"; -- For pgvector (embeddings/RAG)

-- ============================================================================
-- USERS TABLE
-- ============================================================================
-- Note: Supabase Auth handles user authentication, but we may need a profiles table
-- This is optional if you only use Supabase Auth's built-in users table

CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    full_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INCIDENTS TABLE
-- ============================================================================
-- Main table for storing incident claims

CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Encrypted story text (PII redacted before encryption)
    story_text TEXT NOT NULL, -- Encrypted with Fernet
    
    -- Structured extraction (JSON, with encrypted PII fields)
    extracted_data JSONB NOT NULL DEFAULT '{}',
    
    -- PII mapping for restoration (encrypted)
    pii_mapping JSONB, -- Stores pseudonym -> original mapping
    
    -- Status tracking
    status TEXT NOT NULL DEFAULT 'pending',
    -- Values: pending, processing, extracted, verified, escalated, closed
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT status_check CHECK (status IN ('pending', 'processing', 'extracted', 'verified', 'escalated', 'closed'))
);

-- Indexes for incidents
CREATE INDEX IF NOT EXISTS idx_incidents_user_id ON incidents(user_id);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at DESC);

-- ============================================================================
-- CLAIM EVENTS TABLE (Timeline)
-- ============================================================================
-- Stores timeline events for each incident

CREATE TABLE IF NOT EXISTS claim_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    
    event_type TEXT NOT NULL,
    -- Examples: incident_created, processing_started, coverage_verified, 
    --           escalated, follow_up_triggered, etc.
    
    description TEXT NOT NULL,
    metadata JSONB, -- Additional event data
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for claim_events
CREATE INDEX IF NOT EXISTS idx_claim_events_incident_id ON claim_events(incident_id);
CREATE INDEX IF NOT EXISTS idx_claim_events_created_at ON claim_events(created_at DESC);

-- ============================================================================
-- DOCUMENTS TABLE
-- ============================================================================
-- Stores metadata for uploaded documents (images, PDFs, videos)
-- Actual files stored in Supabase Storage (encrypted)

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    file_size BIGINT,
    
    -- Storage path (Supabase Storage)
    storage_path TEXT, -- Path in Supabase Storage bucket
    
    -- CV extraction results
    cv_metadata JSONB, -- OCR text, detected objects, etc.
    
    -- Encryption
    is_encrypted BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for documents
CREATE INDEX IF NOT EXISTS idx_documents_incident_id ON documents(incident_id);

-- ============================================================================
-- EMBEDDINGS TABLE (for RAG/learning)
-- ============================================================================
-- Stores vector embeddings for incidents and corrections
-- Used for few-shot learning and RAG improvements

CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    
    -- Embedding vector (pgvector)
    embedding vector(1536), -- Adjust dimension based on your embedding model
    
    -- Content that was embedded
    content_type TEXT NOT NULL, -- 'incident_story', 'extraction', 'correction'
    content_text TEXT,
    
    -- Metadata
    metadata JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for vector similarity search
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================================================
-- HUMAN CORRECTIONS TABLE (for safe learning)
-- ============================================================================
-- Stores human corrections to improve prompts and RAG

CREATE TABLE IF NOT EXISTS human_corrections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    
    -- Field that was corrected
    field_name TEXT NOT NULL,
    
    -- Original and corrected values
    original_value JSONB,
    corrected_value JSONB NOT NULL,
    
    -- Who made the correction
    corrected_by UUID REFERENCES auth.users(id),
    
    -- Final status after correction
    final_status TEXT, -- 'approved', 'rejected', 'modified'
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for human_corrections
CREATE INDEX IF NOT EXISTS idx_human_corrections_incident_id ON human_corrections(incident_id);
CREATE INDEX IF NOT EXISTS idx_human_corrections_field_name ON human_corrections(field_name);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================
-- Ensure users can only access their own data

-- Enable RLS on all tables
ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE claim_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE human_corrections ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Incidents: Users can only see their own incidents
CREATE POLICY "Users can view own incidents"
    ON incidents FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own incidents"
    ON incidents FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own incidents"
    ON incidents FOR UPDATE
    USING (auth.uid() = user_id);

-- Claim Events: Users can only see events for their incidents
CREATE POLICY "Users can view own claim events"
    ON claim_events FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM incidents 
            WHERE incidents.id = claim_events.incident_id 
            AND incidents.user_id = auth.uid()
        )
    );

-- Documents: Users can only see documents for their incidents
CREATE POLICY "Users can view own documents"
    ON documents FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM incidents 
            WHERE incidents.id = documents.incident_id 
            AND incidents.user_id = auth.uid()
        )
    );

-- Embeddings: Users can only see embeddings for their incidents
CREATE POLICY "Users can view own embeddings"
    ON embeddings FOR SELECT
    USING (
        incident_id IS NULL OR
        EXISTS (
            SELECT 1 FROM incidents 
            WHERE incidents.id = embeddings.incident_id 
            AND incidents.user_id = auth.uid()
        )
    );

-- Human Corrections: Users can only see corrections for their incidents
CREATE POLICY "Users can view own corrections"
    ON human_corrections FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM incidents 
            WHERE incidents.id = human_corrections.incident_id 
            AND incidents.user_id = auth.uid()
        )
    );

-- User Profiles: Users can only see their own profile
CREATE POLICY "Users can view own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON user_profiles FOR UPDATE
    USING (auth.uid() = id);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for incidents
CREATE TRIGGER update_incidents_updated_at
    BEFORE UPDATE ON incidents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for user_profiles
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- STORAGE BUCKET (for file uploads)
-- ============================================================================
-- Note: Create this bucket in Supabase Dashboard > Storage
-- Or use SQL:
-- INSERT INTO storage.buckets (id, name, public) 
-- VALUES ('incident-attachments', 'incident-attachments', false);

-- Storage policy: Users can upload to their own folder
-- CREATE POLICY "Users can upload own files"
--     ON storage.objects FOR INSERT
--     WITH CHECK (
--         bucket_id = 'incident-attachments' AND
--         (storage.foldername(name))[1] = auth.uid()::text
--     );

-- Storage policy: Users can read their own files
-- CREATE POLICY "Users can read own files"
--     ON storage.objects FOR SELECT
--     USING (
--         bucket_id = 'incident-attachments' AND
--         (storage.foldername(name))[1] = auth.uid()::text
--     );

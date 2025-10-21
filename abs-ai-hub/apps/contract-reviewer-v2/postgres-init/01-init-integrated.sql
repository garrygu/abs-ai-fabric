-- PostgreSQL initialization script for Contract Reviewer v2 - Integrated
-- This script creates the necessary database schema for the integrated application

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    mime_type VARCHAR(100),
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    analysis_timestamp TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'uploaded',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create analysis_results table
CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,
    analysis_data JSONB NOT NULL,
    analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    model_used VARCHAR(100),
    processing_time_ms INTEGER,
    status VARCHAR(20) DEFAULT 'completed',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create document_chunks table for vector storage references
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_metadata JSONB,
    vector_id VARCHAR(255), -- Reference to Qdrant vector ID
    embedding_model VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create user_sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_documents_upload_timestamp ON documents(upload_timestamp);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN(metadata);

CREATE INDEX IF NOT EXISTS idx_analysis_results_document_id ON analysis_results(document_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_analysis_type ON analysis_results(analysis_type);
CREATE INDEX IF NOT EXISTS idx_analysis_results_status ON analysis_results(status);
CREATE INDEX IF NOT EXISTS idx_analysis_results_analysis_timestamp ON analysis_results(analysis_timestamp);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_vector_id ON document_chunks(vector_id);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- Create views for common queries
CREATE OR REPLACE VIEW document_summary AS
SELECT 
    d.id,
    d.original_filename,
    d.file_size,
    d.file_type,
    d.upload_timestamp,
    d.status,
    d.metadata->>'client_id' as client_id,
    d.metadata->>'document_type' as document_type,
    COUNT(ar.id) as analysis_count,
    MAX(ar.analysis_timestamp) as last_analysis_timestamp
FROM documents d
LEFT JOIN analysis_results ar ON d.id = ar.document_id
GROUP BY d.id, d.original_filename, d.file_size, d.file_type, d.upload_timestamp, d.status, d.metadata;

CREATE OR REPLACE VIEW analysis_summary AS
SELECT 
    ar.id,
    ar.document_id,
    d.original_filename,
    ar.analysis_type,
    ar.model_used,
    ar.processing_time_ms,
    ar.status,
    ar.analysis_timestamp,
    ar.analysis_data->'summary'->>'summary' as summary_text,
    jsonb_array_length(ar.analysis_data->'risks') as risk_count,
    jsonb_array_length(ar.analysis_data->'recommendations') as recommendation_count
FROM analysis_results ar
JOIN documents d ON ar.document_id = d.id;

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, full_name, role) 
VALUES (
    'admin', 
    'admin@contract-reviewer.local', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8X8K2K', -- admin123
    'System Administrator', 
    'admin'
) ON CONFLICT (username) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions to hub_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hub_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hub_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO hub_user;

-- Insert sample data for testing (optional)
INSERT INTO documents (original_filename, filename, file_path, file_size, file_type, status, metadata) 
VALUES (
    'sample_contract.pdf',
    'sample_contract.pdf',
    '/data/file_storage/documents/sample_contract.pdf',
    102400,
    '.pdf',
    'uploaded',
    '{"client_id": "Sample_Client", "document_type": "contract", "upload_source": "contract-reviewer-v2-integrated"}'
) ON CONFLICT DO NOTHING;

-- Log initialization completion
INSERT INTO audit_logs (action, resource_type, details) 
VALUES (
    'database_initialized',
    'system',
    '{"message": "Contract Reviewer v2 - Integrated database schema initialized successfully", "version": "2.0.0"}'
);

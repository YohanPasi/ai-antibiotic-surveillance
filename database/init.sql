-- Database Initialization Script
-- Executed automatically when PostgreSQL container starts

\c ast_db;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE ast_db TO ast_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ast_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ast_user;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Log initialization
SELECT 'AST Database initialized successfully' AS status;

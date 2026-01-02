CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user', -- 'admin', 'user', 'viewer'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed default admin user (password: admin123) - ONLY IF NOT EXISTS
INSERT INTO users (username, email, password_hash, role)
SELECT 'admin', 'admin@hospital.lk', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6q.1/6.1/6.1/6.1/6.1', 'admin'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');
-- Note: The hash above is a dummy placeholder. I will use a Python script to generate a real bcrypt hash for 'admin123' separately or during app startup if preferred. 
-- Actually, let's just create the table first. Managing seed data via API startup is safer for hash compatibility.

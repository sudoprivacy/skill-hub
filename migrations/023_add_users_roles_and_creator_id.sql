-- 023: Add users/roles tables and creator_id ownership columns.
-- Idempotent and additive — safe to run multiple times; existing data untouched.
-- (The application also applies this automatically on startup via
--  skill_hub/db/bootstrap.py; this file documents the schema change.)

-- Roles
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_roles_name ON roles (name);

-- Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    role_id UUID NOT NULL REFERENCES roles(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_users_username ON users (username);
CREATE INDEX IF NOT EXISTS ix_users_role_id ON users (role_id);

-- Ownership columns on existing tables
ALTER TABLE skills ADD COLUMN IF NOT EXISTS creator_id UUID REFERENCES users(id);
ALTER TABLE assistants ADD COLUMN IF NOT EXISTS creator_id UUID REFERENCES users(id);
CREATE INDEX IF NOT EXISTS ix_skills_creator_id ON skills (creator_id);
CREATE INDEX IF NOT EXISTS ix_assistants_creator_id ON assistants (creator_id);

-- Seed roles
INSERT INTO roles (name, description)
VALUES ('admin', 'Administrator with full access')
ON CONFLICT (name) DO NOTHING;
INSERT INTO roles (name, description)
VALUES ('user', 'Regular user')
ON CONFLICT (name) DO NOTHING;

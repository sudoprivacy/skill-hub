-- Migration: Add tenant_id to assistants table
-- Description: Add tenant_id column to support multi-tenant filtering

ALTER TABLE assistants ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(255);

CREATE INDEX IF NOT EXISTS idx_assistants_tenant_id ON assistants(tenant_id);

COMMENT ON COLUMN assistants.tenant_id IS 'Tenant ID for multi-tenant isolation';

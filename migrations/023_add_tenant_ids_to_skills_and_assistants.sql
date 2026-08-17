-- Add plural tenant ownership while retaining tenant_id for old clients.

ALTER TABLE skills
    ADD COLUMN IF NOT EXISTS tenant_ids VARCHAR(255)[];

ALTER TABLE assistants
    ADD COLUMN IF NOT EXISTS tenant_ids VARCHAR(255)[];

-- Backfill legacy single-tenant rows. Public rows remain NULL.
UPDATE skills
SET tenant_ids = ARRAY[tenant_id]
WHERE tenant_id IS NOT NULL
  AND (tenant_ids IS NULL OR cardinality(tenant_ids) = 0);

UPDATE assistants
SET tenant_ids = ARRAY[tenant_id]
WHERE tenant_id IS NOT NULL
  AND (tenant_ids IS NULL OR cardinality(tenant_ids) = 0);

CREATE INDEX IF NOT EXISTS idx_skills_tenant_ids
    ON skills USING GIN (tenant_ids);

CREATE INDEX IF NOT EXISTS idx_assistants_tenant_ids
    ON assistants USING GIN (tenant_ids);

COMMENT ON COLUMN skills.tenant_ids IS
    'Tenant IDs; tenant_id retains the first value for backward compatibility';

COMMENT ON COLUMN assistants.tenant_ids IS
    'Tenant IDs; tenant_id retains the first value for backward compatibility';

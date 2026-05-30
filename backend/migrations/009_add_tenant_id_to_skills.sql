-- 1. 添加 tenant_id 字段
ALTER TABLE skills ADD COLUMN tenant_id VARCHAR(255);

-- 2. 为该字段添加注释
COMMENT ON COLUMN skills.tenant_id IS 'Tenant ID';

-- 3. 创建索引（根据模型中的 index=True）
CREATE INDEX ix_skills_tenant_id ON skills (tenant_id);

-- 4. （可选）如果你希望同一个 name 在不同租户下可以重复，
--    可能需要删除原有的 name 唯一约束并替换为 (name, tenant_id) 的联合唯一约束
-- ALTER TABLE skills DROP CONSTRAINT skills_name_key;
-- ALTER TABLE skills ADD CONSTRAINT skills_name_tenant_id_key UNIQUE (name, tenant_id);

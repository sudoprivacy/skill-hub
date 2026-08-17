import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from skill_hub.models.assistant import Assistant
from skill_hub.models.skill import Skill
from skill_hub.schemas.assistant_schemas import (
    AssistantCreateRequest,
    AssistantUpdateRequest,
)
from skill_hub.schemas.skill_schemas import SkillCreateRequest, SkillUpdateRequest
from skill_hub.utils.tenant_utils import (
    effective_tenant_ids,
    normalize_tenant_ids,
    tenant_filter,
    tenants_filter,
)


def test_normalize_tenant_ids_supports_legacy_and_plural_values():
    assert normalize_tenant_ids(None, "tenant-a") == ["tenant-a"]
    assert normalize_tenant_ids('["tenant-a", "tenant-b"]') == [
        "tenant-a",
        "tenant-b",
    ]
    assert normalize_tenant_ids("tenant-a, tenant-b,tenant-a") == [
        "tenant-a",
        "tenant-b",
    ]
    assert normalize_tenant_ids([], "legacy-is-ignored") == []


def test_skill_schemas_synchronize_legacy_and_plural_fields():
    legacy = SkillCreateRequest(
        name="legacy",
        display_name="Legacy",
        version="1.0.0",
        tenant_id="tenant-a",
    ).to_skill_data(str(uuid.uuid4()))
    assert legacy["tenant_id"] == "tenant-a"
    assert legacy["tenant_ids"] == ["tenant-a"]

    plural = SkillUpdateRequest.from_dict(
        {"tenantId": "stale", "tenantIds": ["tenant-b", "tenant-c"]}
    ).to_update_data()
    assert plural["tenant_id"] == "tenant-b"
    assert plural["tenant_ids"] == ["tenant-b", "tenant-c"]


def test_assistant_schemas_accept_json_csv_and_clear_ownership():
    created = AssistantCreateRequest.from_dict(
        {
            "name": "assistant",
            "profession": "tester",
            "tenantIds": '["tenant-a", "tenant-b"]',
        }
    ).to_assistant_data()
    assert created["tenant_id"] == "tenant-a"
    assert created["tenant_ids"] == ["tenant-a", "tenant-b"]

    updated = AssistantUpdateRequest.from_dict(
        {"tenant_ids": "tenant-c,tenant-d"}
    ).to_update_data()
    assert updated["tenant_ids"] == ["tenant-c", "tenant-d"]

    cleared = AssistantUpdateRequest.from_dict({"tenantIds": []})
    assert cleared.validate() == (True, None)
    assert cleared.to_update_data() == {"tenant_ids": [], "tenant_id": None}


def test_models_serialize_plural_and_legacy_tenant_fields():
    now = datetime.utcnow()
    skill = Skill(
        id=uuid.uuid4(),
        name="skill",
        display_name="Skill",
        author_id=uuid.uuid4(),
        tenant_id="tenant-a",
        tenant_ids=["tenant-a", "tenant-b"],
        created_at=now,
        updated_at=now,
    )
    skill_data = skill.to_dict()
    assert skill_data["tenant_id"] == "tenant-a"
    assert skill_data["tenant_ids"] == ["tenant-a", "tenant-b"]

    assistant = Assistant(
        id=uuid.uuid4(),
        name="assistant",
        profession="tester",
        tenant_id="tenant-a",
        tenant_ids=["tenant-a", "tenant-b"],
        created_at=now,
        updated_at=now,
    )
    assistant_data = assistant.to_dict()
    assert assistant_data["tenantId"] == "tenant-a"
    assert assistant_data["tenantIds"] == ["tenant-a", "tenant-b"]

    legacy_only = Skill(tenant_id="tenant-old", tenant_ids=None)
    assert effective_tenant_ids(legacy_only) == ["tenant-old"]


def test_tenant_filters_cover_array_legacy_and_public_records():
    member_query = select(Skill).where(tenant_filter(Skill, "tenant-b"))
    member_sql = str(member_query.compile(dialect=postgresql.dialect()))
    assert "skills.tenant_id =" in member_sql
    assert "ANY (skills.tenant_ids)" in member_sql

    overlap_query = select(Assistant).where(
        tenants_filter(Assistant, ["tenant-a", "tenant-b"])
    )
    overlap_sql = str(overlap_query.compile(dialect=postgresql.dialect()))
    assert "assistants.tenant_id IN" in overlap_sql
    assert "assistants.tenant_ids &&" in overlap_sql

    public_query = select(Skill).where(tenant_filter(Skill, None))
    public_sql = str(public_query.compile(dialect=postgresql.dialect()))
    assert "skills.tenant_id IS NULL" in public_sql
    assert "cardinality(skills.tenant_ids)" in public_sql

"""Helpers for backward-compatible tenant ownership."""

import json
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_


def parse_tenant_ids(value: Any) -> Optional[List[str]]:
    """Parse an optional tenant list from JSON, CSV, or a Python sequence."""
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            decoded = value.split(",")
        value = decoded if isinstance(decoded, list) else [decoded]
    elif isinstance(value, (tuple, set)):
        value = list(value)
    elif not isinstance(value, list):
        value = [value]

    result = []
    seen = set()
    for tenant_id in value:
        if tenant_id is None:
            continue
        tenant_id = str(tenant_id).strip()
        if tenant_id and tenant_id not in seen:
            seen.add(tenant_id)
            result.append(tenant_id)
    return result


def normalize_tenant_ids(
    tenant_ids: Any = None, tenant_id: Optional[str] = None
) -> List[str]:
    """Return canonical tenant IDs, preferring the new plural field."""
    parsed = parse_tenant_ids(tenant_ids)
    if parsed is not None:
        return parsed
    return parse_tenant_ids(tenant_id) or []


def synchronize_tenant_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronize plural ownership with the legacy scalar field in-place."""
    if "tenant_ids" not in data and "tenant_id" not in data:
        return data

    tenant_ids = normalize_tenant_ids(data.get("tenant_ids"), data.get("tenant_id"))
    data["tenant_ids"] = tenant_ids
    data["tenant_id"] = tenant_ids[0] if tenant_ids else None
    return data


def effective_tenant_ids(entity: Any) -> List[str]:
    """Read ownership from new records or legacy scalar-only records."""
    return normalize_tenant_ids(
        getattr(entity, "tenant_ids", None), getattr(entity, "tenant_id", None)
    )


def tenant_filter(model: Any, tenant_id: Optional[str]):
    """Build a filter that matches both plural and legacy tenant storage."""
    if tenant_id is not None:
        return or_(
            model.tenant_id == tenant_id,
            model.tenant_ids.any(tenant_id),
        )

    return and_(
        model.tenant_id.is_(None),
        or_(model.tenant_ids.is_(None), func.cardinality(model.tenant_ids) == 0),
    )


def tenants_filter(model: Any, tenant_ids: Any = None, tenant_id: Optional[str] = None):
    """Build an ownership filter for a plural create/update lookup."""
    normalized = normalize_tenant_ids(tenant_ids, tenant_id)
    if not normalized:
        return tenant_filter(model, None)
    return or_(
        model.tenant_id.in_(normalized),
        model.tenant_ids.overlap(normalized),
    )

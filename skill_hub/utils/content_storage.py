"""Local-filesystem content storage for skill packages and icons.

When the hub is configured for local content mode (SKILL_HUB_CONTENT_BASE_URL
set), skill `.zip` packages and icons are written under
`<SKILL_HUB_DATA_DIR>/content/<object_key>` and served back by the
`GET /api/skills/content/<key>` route, instead of being uploaded to Tencent
COS. This keeps the on-prem deployment fully self-contained (no external
object storage), while leaving the public/COS deployment behaviour unchanged
when SKILL_HUB_CONTENT_BASE_URL is empty.

The functions here read configuration straight from the environment so they
can be used both from request handlers and from model `to_dict()` methods
(which don't have the app config injected).
"""

import os
import shutil
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Legacy default kept for backwards compatibility: when neither local content
# mode nor an explicit COS base URL is configured, source_url values are
# prefixed with this (matches the historical hard-coded value).
_DEFAULT_COS_BASE_URL = "https://sudowork-hub-1309794936.cos.ap-beijing.myqcloud.com"


def _data_dir() -> str:
    return os.getenv("SKILL_HUB_DATA_DIR", "./data")


def content_base_url() -> str:
    """Public base URL for locally-served content, or '' if not in local mode."""
    return (os.getenv("SKILL_HUB_CONTENT_BASE_URL", "") or "").strip().rstrip("/")


def cos_base_url() -> str:
    """Tencent COS base URL, read from SKILL_HUB_COS_BASE_URL.

    Falls back to the legacy hard-coded value only when the env var is unset.
    """
    return (os.getenv("SKILL_HUB_COS_BASE_URL", "") or "").strip().rstrip("/") or _DEFAULT_COS_BASE_URL


def cos_bucket_name() -> str:
    """Bucket name derived from the COS base URL host (its first label).

    e.g. ``https://my-bucket-123.cos.ap-beijing.myqcloud.com`` -> ``my-bucket-123``.
    """
    host = urlparse(cos_base_url()).hostname or ""
    return host.split(".")[0]


def is_local_mode() -> bool:
    """True when skill content is stored on local FS and served by this hub."""
    return bool(content_base_url())


def api_prefix() -> str:
    return (os.getenv("SKILL_HUB_API_PREFIX", "/api") or "/api").rstrip("/")


def content_root() -> str:
    """Local directory under which content objects are stored."""
    return os.path.join(_data_dir(), "content")


def local_path_for(object_key: str) -> str:
    """Absolute on-disk path for an object key, guarded against traversal."""
    root = os.path.abspath(content_root())
    # Normalize and ensure the resolved path stays within content_root.
    target = os.path.abspath(os.path.join(root, object_key))
    if target != root and not target.startswith(root + os.sep):
        raise ValueError(f"Illegal content object key: {object_key!r}")
    return target


def store_object(local_file_path: str, object_key: str) -> None:
    """Copy a freshly-uploaded file into local content storage."""
    dest = local_path_for(object_key)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copyfile(local_file_path, dest)
    logger.info("Stored content object locally: %s", object_key)


def resolve_source_url(source_url: str) -> str:
    """Build the client-facing download URL for a stored source_url value.

    `source_url` as persisted in the DB is an object key (e.g.
    `skill-hub/<id>/pkg.zip`). Absolute URLs (already-resolved or external
    git/http sources) are returned unchanged.
    """
    if not source_url:
        return source_url
    if source_url.startswith(("http://", "https://")):
        return source_url
    key = source_url.lstrip("/")
    base = content_base_url()
    if base:
        # Served by this hub's download route.
        return f"{base}{api_prefix()}/skills/content/{key}"
    # Legacy COS behaviour.
    return f"{cos_base_url()}/{key}"


def resolve_version_download_url(version_id: str) -> str:
    """Build the countable package download URL for a skill version."""
    if not version_id:
        return version_id
    base = content_base_url()
    return f"{base}{api_prefix()}/skill-versions/{version_id}/download"


def resolve_local_only(object_key: str) -> str:
    """Resolve an object key to a local content URL, but ONLY in local mode.

    Used for fields (assistant promptFile / avatar / sourceUrl) that the model
    historically returned as raw object keys, with URL resolution done client
    side. In local mode we must return an absolute URL the client can fetch
    from this hub; in COS/default mode we return the value unchanged so
    behavior is identical to before (no COS prefixing here — the client does
    that, as it always has).
    """
    if not object_key:
        return object_key
    if object_key.startswith(("http://", "https://")):
        return object_key
    base = content_base_url()
    if not base:
        return object_key  # COS/default mode: unchanged (client resolves)
    return f"{base}{api_prefix()}/skills/content/{object_key.lstrip('/')}"

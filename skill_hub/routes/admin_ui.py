"""Static delivery for the admin web console (Single Page Application).

Registered at ``/admin`` (outside AuthMiddleware's ``/api`` scope so the
HTML/JS/CSS load without a bearer token — the SPA itself attaches the token
to its ``/api`` XHR calls). Serves the built frontend from
``skill_hub/static/admin`` produced by ``sudo-skill-frontend`` (``pnpm build``).

Behaviour:
- An existing file under the build dir is served as-is (assets, favicon...).
- Any other path falls back to ``index.html`` so client-side routes
  (``/admin/skills``, ``/admin/login`` ...) resolve on full-page loads/refresh.

No business logic, database, or auth is touched here.
"""

import os
from pathlib import Path

from quart import Blueprint, send_file

admin_ui_router = Blueprint("admin_ui", __name__)

# Build output directory: skill_hub/static/admin
_STATIC_ADMIN_DIR = (Path(__file__).resolve().parent.parent / "static" / "admin")
_INDEX_FILE = _STATIC_ADMIN_DIR / "index.html"


def _safe_resolve(relative_path: str) -> Path | None:
    """Resolve ``relative_path`` inside the build dir, guarding traversal.

    Returns the absolute path if it stays within the build dir, else None.
    """
    candidate = (_STATIC_ADMIN_DIR / relative_path).resolve()
    try:
        candidate.relative_to(_STATIC_ADMIN_DIR.resolve())
    except ValueError:
        return None
    return candidate


async def _serve_index():
    """Serve the SPA entry, or a friendly hint if not built yet."""
    if not _INDEX_FILE.is_file():
        return (
            "Admin UI is not built yet. Run `pnpm build` in "
            "sudo-skill-frontend to generate skill_hub/static/admin.",
            503,
        )
    return await send_file(str(_INDEX_FILE))


@admin_ui_router.route("", methods=["GET"])
@admin_ui_router.route("/", methods=["GET"])
async def admin_root():
    """Serve the admin console entry page."""
    return await _serve_index()


@admin_ui_router.route("/<path:path>", methods=["GET"])
async def admin_assets(path: str):
    """Serve a built asset if it exists, else fall back to index.html (SPA)."""
    resolved = _safe_resolve(path)
    if resolved is not None and resolved.is_file():
        return await send_file(str(resolved))
    return await _serve_index()

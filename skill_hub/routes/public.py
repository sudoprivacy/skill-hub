"""Unauthenticated public file delivery for local content mode.

Registered at ``/public`` (outside AuthMiddleware's `/api` scope), this
blueprint serves locally-stored content (skill icons/zips and assistant
avatar/prompt/source) without requiring an Authorization header — necessary
because browsers cannot attach bearer tokens to ``<img>`` loads or direct
download links.

COS mode requests are rejected with 404 (no business logic touched).
No download counting here; the counted endpoint remains
``/api/skill-versions/<id>/download``.
"""

import os
from quart import Blueprint, send_file

from skill_hub.utils.content_storage import (
    is_local_mode,
    local_path_for,
)
from skill_hub.api.exceptions import BadRequestException, NotFoundException

public_router = Blueprint("public", __name__)


@public_router.route("/<path:object_key>", methods=["GET"])
async def serve_public_content(object_key: str):
    """Serve a locally-stored content object without authentication.

    Only active when SKILL_HUB_CONTENT_BASE_URL is configured; otherwise
    returns 404. `object_key` is the stored key, e.g.
    ``skill-hub/<id>/pkg.zip`` or ``assistant-hub/<id>/avatar.png``.
    """
    if not is_local_mode():
        raise NotFoundException(message="Local content storage is not enabled")

    try:
        abs_path = local_path_for(object_key)
    except ValueError:
        raise BadRequestException(message="Invalid content path")

    if not os.path.isfile(abs_path):
        raise NotFoundException(message=f"Content not found: {object_key}")

    return await send_file(abs_path, as_attachment=False)

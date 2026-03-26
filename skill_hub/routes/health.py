"""Health check routes"""

from quart import Blueprint, jsonify

health_router = Blueprint("health", __name__)


@health_router.route("/health")
async def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "skill-hub",
        "timestamp": "2026-03-17T14:00:00Z"
    })


@health_router.route("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return jsonify({
        "status": "ready",
        "service": "skill-hub",
        "timestamp": "2026-03-17T14:00:00Z"
    })


@health_router.route("/live")
async def liveness_check():
    """Liveness check endpoint"""
    return jsonify({
        "status": "alive",
        "service": "skill-hub",
        "timestamp": "2026-03-17T14:00:00Z"
    })

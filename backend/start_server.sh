#!/bin/bash
# Start Skill Hub Server

echo "Starting Skill Hub Server..."

# Check if auth token is provided
if [ -z "$SKILL_HUB_AUTH_TOKEN" ]; then
    echo "Error: SKILL_HUB_AUTH_TOKEN environment variable is not set"
    echo "Please set it with: export SKILL_HUB_AUTH_TOKEN=your-secret-token"
    echo "Or provide it as an argument: --auth-token your-secret-token"
    echo ""
    echo "Starting with default token (for testing only)..."
    export SKILL_HUB_AUTH_TOKEN="default-test-token-12345"
fi

# Start the server
python main.py \
    --host "${SKILL_HUB_HOST:-0.0.0.0}" \
    --port "${SKILL_HUB_PORT:-8080}" \
    --auth-token "$SKILL_HUB_AUTH_TOKEN" \
    --data-dir "${SKILL_HUB_DATA_DIR:-./data}" \
    --log-level "${SKILL_HUB_LOG_LEVEL:-INFO}" \
    --api-prefix "${SKILL_HUB_API_PREFIX:-/api}" \
    $([ "${SKILL_HUB_DEBUG:-false}" = "true" ] && echo "--debug")

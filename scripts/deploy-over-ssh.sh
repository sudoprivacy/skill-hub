#!/usr/bin/env bash
# Bound SSH connection, transfer, and activation separately so stalled transfers
# fail with a useful diagnostic before the workflow's overall time limit.
set -euo pipefail
umask 077

revision="${1:?The source commit is required}"
[[ "$revision" =~ ^[0-9a-f]{40}$ ]]
: "${SSH_HOST:?The deployment host is required}"
: "${SSH_USERNAME:?The deployment user is required}"
: "${SSH_PRIVATE_KEY:?The deployment key is required}"
: "${DEPLOY_PATH:?The deployment directory is required}"
: "${GITHUB_REPOSITORY:?The image repository is required}"
: "${RUNNER_TEMP:?The runner temporary directory is required}"
[[ "$SSH_HOST" =~ ^[A-Za-z0-9][A-Za-z0-9.-]*$ ]]
[[ "$SSH_USERNAME" =~ ^[A-Za-z_][A-Za-z0-9_-]*$ ]]
[[ "$DEPLOY_PATH" =~ ^/[A-Za-z0-9._/-]+$ && "$DEPLOY_PATH" != / ]]
[[ ! "/${DEPLOY_PATH#/}/" =~ /\.\.?/ ]]
[[ "$GITHUB_REPOSITORY" =~ ^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$ ]]

archive="skill-hub-image-${revision}.tar.gz"
test -f "$archive"
sha256sum --check "$archive.sha256"
ssh_dir="$(mktemp -d "${RUNNER_TEMP}/skill-hub-ssh.XXXXXX")"
trap 'rm -f -- "$ssh_dir/key" "$ssh_dir/known_hosts"; rmdir -- "$ssh_dir"' EXIT
printf '%s\n' "$SSH_PRIVATE_KEY" > "$ssh_dir/key"
unset SSH_PRIVATE_KEY
chmod 600 "$ssh_dir/key"

printf 'Collecting the deployment host key (30 second limit).\n'
timeout 30s ssh-keyscan -T 15 -H "$SSH_HOST" > "$ssh_dir/known_hosts" 2>/dev/null
test -s "$ssh_dir/known_hosts"
options=(
  -i "$ssh_dir/key"
  -o BatchMode=yes
  -o IdentitiesOnly=yes
  -o ConnectTimeout=20
  -o ConnectionAttempts=1
  -o ServerAliveInterval=15
  -o ServerAliveCountMax=4
  -o StrictHostKeyChecking=yes
  -o "UserKnownHostsFile=$ssh_dir/known_hosts"
)
destination="${SSH_USERNAME}@${SSH_HOST}"

printf 'Checking SSH authentication and Docker access (60 second limit).\n'
timeout 60s ssh "${options[@]}" "$destination" \
  "test -d '$DEPLOY_PATH' && docker info --format '{{.ServerVersion}}' >/dev/null && mkdir -p '$DEPLOY_PATH/scripts'"

printf 'Transferring deployment metadata (2 minute limit per operation).\n'
timeout 120s scp -O "${options[@]}" docker-compose.prod.yml "$archive.sha256" \
  "${destination}:${DEPLOY_PATH}/"
timeout 120s scp -O "${options[@]}" scripts/deploy-image.sh \
  "${destination}:${DEPLOY_PATH}/scripts/"

printf 'Transferring the verified image (15 minute limit).\n'
timeout 900s scp -O "${options[@]}" "$archive" "${destination}:${DEPLOY_PATH}/"

printf 'Activating and checking the verified image (10 minute limit).\n'
timeout 600s ssh "${options[@]}" "$destination" \
  "cd '$DEPLOY_PATH' && GITHUB_REPOSITORY='$GITHUB_REPOSITORY' bash scripts/deploy-image.sh '$revision'"

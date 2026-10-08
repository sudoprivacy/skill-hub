#!/usr/bin/env bash
# Load the CI image without requiring the production host to reach GHCR.
set -euo pipefail
umask 077

revision="${1:?The source commit is required}"
[[ "$revision" =~ ^[0-9a-f]{40}$ ]]
: "${GITHUB_REPOSITORY:?The image repository is required}"
[[ "$GITHUB_REPOSITORY" =~ ^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$ ]]
export IMAGE_TAG="sha-${revision:0:7}"
archive="skill-hub-image-${revision}.tar.gz"
image="ghcr.io/${GITHUB_REPOSITORY}:${IMAGE_TAG}"

test -f docker-compose.prod.yml
test "$(cat "$archive.sha256")" = "$(sha256sum "$archive")"
sha256sum --check "$archive.sha256"

release_backup="backups/release-${revision}"
mkdir -p "$release_backup"
chmod 700 "$release_backup"
previous_image=''
if [ -f "$release_backup/previous-image-id" ]; then
  previous_image="$(cat "$release_backup/previous-image-id")"
elif docker inspect skill-hub >/dev/null 2>&1; then
  previous_image="$(docker inspect --format '{{.Image}}' skill-hub)"
  printf '%s\n' "$previous_image" > "$release_backup/previous-image-id"
  docker inspect --format '{{.Config.Image}}' skill-hub > "$release_backup/previous-image-tag"
fi
if [ -f .env ] && [ ! -f "$release_backup/.env" ]; then
  cp .env "$release_backup/.env"
  chmod 600 "$release_backup/.env"
fi
if [ ! -f "$release_backup/docker-compose.prod.yml" ]; then
  cp docker-compose.prod.yml "$release_backup/docker-compose.prod.yml"
fi

gzip -dc "$archive" | docker load
test "$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$image")" = "$revision"
expected_image="$(docker image inspect --format '{{.Id}}' "$image")"

is_ready() {
  for _ in {1..60}; do
    if [ "$(docker inspect --format '{{.State.Health.Status}}' skill-hub 2>/dev/null || true)" = healthy ] &&
       [ "$(docker inspect --format '{{.Image}}' skill-hub)" = "$expected_image" ]; then
      return 0
    fi
    sleep 5
  done
  return 1
}

if docker compose -f docker-compose.prod.yml up -d --pull never && is_ready; then
  printf 'Healthy deployment: %s\n' "$revision"
  rm -f -- "$archive" "$archive.sha256"
else
  printf 'Deployment failed health verification: %s\n' "$revision" >&2
  if [ -n "$previous_image" ]; then
    export IMAGE_TAG="rollback-${revision}"
    docker tag "$previous_image" "ghcr.io/${GITHUB_REPOSITORY}:${IMAGE_TAG}"
    docker compose -f docker-compose.prod.yml up -d --pull never
    expected_image="$previous_image"
    is_ready
    printf 'Previous image restored: %s\n' "$previous_image"
  fi
  exit 1
fi

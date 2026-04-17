#!/usr/bin/env sh
set -eu

COMPOSE_FILE="${COMPOSE_FILE:-compose/docker-compose.yml}"
ENV_FILE="${ENV_FILE:-compose/.env}"
PROJECT="${PROJECT:-zabbix}"
BACKUP_DIR="${BACKUP_DIR:-backups}"

mkdir -p "${BACKUP_DIR}"

if [ ! -f "${ENV_FILE}" ]; then
  echo "Missing env file: ${ENV_FILE}" >&2
  exit 1
fi

set -a
. "${ENV_FILE}"
set +a

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output="${BACKUP_DIR}/zabbix-postgres-${timestamp}.dump"

docker compose -p "${PROJECT}" --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" exec -T postgres-server \
  pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -F c > "${output}"

echo "${output}"

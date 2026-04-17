#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 path/to/backup.dump" >&2
  exit 1
fi

COMPOSE_FILE="${COMPOSE_FILE:-compose/docker-compose.yml}"
ENV_FILE="${ENV_FILE:-compose/.env}"
PROJECT="${PROJECT:-zabbix}"
BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "Backup file not found: ${BACKUP_FILE}" >&2
  exit 1
fi

set -a
. "${ENV_FILE}"
set +a

docker compose -p "${PROJECT}" --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" exec -T postgres-server \
  pg_restore -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --clean --if-exists < "${BACKUP_FILE}"

#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"

if [ -z "${ZABBIX_URL:-}" ]; then
  echo "error: ZABBIX_URL is required" >&2
  exit 1
fi

if [ -z "${ZABBIX_API_TOKEN:-}" ] && { [ -z "${ZABBIX_USER:-}" ] || [ -z "${ZABBIX_PASSWORD:-}" ]; }; then
  echo "error: set ZABBIX_API_TOKEN or ZABBIX_USER/ZABBIX_PASSWORD" >&2
  exit 1
fi

"${PYTHON_BIN}" scripts/zabbix-config.py validate zabbix-config/config.yml
"${PYTHON_BIN}" scripts/zabbix-config.py apply zabbix-config/config.yml

while IFS= read -r file; do
  "${PYTHON_BIN}" scripts/zabbix-native-yaml.py validate "${file}"
  "${PYTHON_BIN}" scripts/zabbix-native-yaml.py import "${file}" --rules zabbix-native/rules-safe.yml
done < <(find zabbix-native/exports -type f \( -name '*.yaml' -o -name '*.yml' \) ! -name '*.example.yaml' ! -name '*.example.yml' | sort)

#!/usr/bin/env sh
set -eu

HOST="${1:-zabbix}"
WEB_PORT="${WEB_PORT:-8443}"
WEB_SCHEME="${WEB_SCHEME:-https}"
CURL_TLS_ARGS="${CURL_TLS_ARGS:--k}"

ssh "root@${HOST}" docker ps
ssh "root@${HOST}" curl ${CURL_TLS_ARGS} -I "${WEB_SCHEME}://127.0.0.1:${WEB_PORT}/"

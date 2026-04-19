COMPOSE_FILE ?= compose/docker-compose.yml
ENV_FILE ?= compose/.env
PROJECT ?= zabbix
ZABBIX_CONFIG ?= zabbix-config/config.yml
ZABBIX_NATIVE_FILE ?= $(FILE)
ZABBIX_NATIVE_RULES ?= zabbix-native/rules-safe.yml
HOST ?=
PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)

COMPOSE = docker compose -p $(PROJECT) --env-file $(ENV_FILE) -f $(COMPOSE_FILE)

.PHONY: config up down ps logs pull restart backup check agent-up zabbix-config-validate zabbix-config-dry-run zabbix-config-apply zabbix-config-export zabbix-native-validate zabbix-native-import zabbix-native-export-host

config:
	$(COMPOSE) config

up:
	$(COMPOSE) up -d

agent-up:
	$(COMPOSE) --profile agent up -d

down:
	$(COMPOSE) down

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs --tail=200 -f

pull:
	$(COMPOSE) pull

restart:
	$(COMPOSE) up -d --force-recreate

backup:
	./scripts/backup-postgres.sh

check:
	./scripts/check-remote.sh

zabbix-config-validate:
	$(PYTHON) scripts/zabbix-config.py validate $(ZABBIX_CONFIG)

zabbix-config-dry-run:
	$(PYTHON) scripts/zabbix-config.py apply --dry-run $(ZABBIX_CONFIG)

zabbix-config-apply:
	$(PYTHON) scripts/zabbix-config.py apply $(ZABBIX_CONFIG)

zabbix-config-export:
	$(PYTHON) scripts/zabbix-config.py export --tag managed_by=git

zabbix-native-validate:
	$(PYTHON) scripts/zabbix-native-yaml.py validate $(ZABBIX_NATIVE_FILE)

zabbix-native-import:
	$(PYTHON) scripts/zabbix-native-yaml.py import $(ZABBIX_NATIVE_FILE) --rules $(ZABBIX_NATIVE_RULES)

zabbix-native-export-host:
	$(PYTHON) scripts/zabbix-native-yaml.py export --host "$(HOST)"

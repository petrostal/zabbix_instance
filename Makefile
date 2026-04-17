COMPOSE_FILE ?= compose/docker-compose.yml
ENV_FILE ?= compose/.env
PROJECT ?= zabbix

COMPOSE = docker compose -p $(PROJECT) --env-file $(ENV_FILE) -f $(COMPOSE_FILE)

.PHONY: config up down ps logs pull restart backup check agent-up

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

# Zabbix Docker Deployment

Repository scaffold for deploying a Zabbix server with Docker Compose.

Current audited server:

- SSH host: `root@zabbix`
- Active compose path: `/opt/zabbix/docker-compose.yml`
- Web UI: `https://zabbix:8443/` or `https://172.30.193.75:8443/`
- HTTP fallback: `http://zabbix:8080/` or `http://172.30.193.75:8080/`
- Default Zabbix login for a fresh install is usually `Admin` / `zabbix`; change it immediately after login.

## Local Compose

1. Copy the environment template:

   ```bash
   cp compose/.env.example compose/.env
   ```

2. Edit `compose/.env` and set a strong `POSTGRES_PASSWORD`.

   For HTTPS, place certificate files at `compose/ssl/ssl.crt` and `compose/ssl/ssl.key`, or set `ZABBIX_SSL_DIR` to another directory containing those files.

3. Validate the final Compose config:

   ```bash
   make config
   ```

4. Start the stack:

   ```bash
   make up
   make ps
   ```

The containerized agent is optional. Start it only when you intentionally want an agent inside Docker:

```bash
make agent-up
```

## Operations

Create a PostgreSQL backup:

```bash
make backup
```

Check the audited remote server:

```bash
make check
```

## Layout

- `compose/` - Docker Compose deployment for Zabbix, PostgreSQL, web UI, and optional agent.
- `ansible/` - future host provisioning and deployment automation.
- `terraform/` - future infrastructure definitions.
- `docs/` - operational notes and server audit results.
- `scripts/` - helper scripts for deployment and checks.

## Next Steps

Use `docs/server-audit.md` for current server state and remaining production hardening notes.

## Ansible

The Ansible playbook can provision a fresh Ubuntu server and deploy the same stack to `/opt/zabbix`.

Read [ansible/README.md](ansible/README.md) before running it because `zabbix_postgres_password`, `zabbix_trusted_cidr`, and `zabbix_public_iface` must match the target environment.

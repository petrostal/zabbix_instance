# Server Audit

Date: 2026-04-17

Host: `root@zabbix`

## Current State

- Docker is installed and working.
- Zabbix Agent 2 is also installed directly on the host through `apt` and is running as `zabbix_agent2`.
- Existing Docker containers were stopped for 8 days and were started during this audit.
- The stack was migrated to `/opt/zabbix/docker-compose.yml` with project name `zabbix-server`.
- Zabbix web UI is reachable locally and from the current client on ports `8080` and `8443`.
- HTTPS uses a self-signed certificate. Replace it with a trusted certificate when DNS is available.
- UFW is enabled. Published Docker ports are additionally restricted through persistent `DOCKER-USER` iptables rules.

Current UI links:

- `https://zabbix:8443/`
- `https://172.30.193.75:8443/`
- `http://zabbix:8080/`
- `http://172.30.193.75:8080/`

Current running containers:

- `zabbix-postgres`
- `zabbix-server`
- `zabbix-web`

The containerized `zabbix-agent` is no longer part of the running compose stack. Host-level `zabbix-agent2.service` remains active.

## Compose Files Found

Two compose files exist:

- `/home/zabbix/zabbix-server/docker-compose.yaml`
- `/home/zabbix/docker-compose.yaml`

The active containers were created from `/home/zabbix/zabbix-server/docker-compose.yaml`. Docker labels show project name `zabbix-server`, config file `/home/zabbix/zabbix-server/docker-compose.yaml`, and volume `zabbix-server_postgres_data`.

The newer top-level `/home/zabbix/docker-compose.yaml` is syntactically valid and uses `/home/zabbix/.env`, but it cannot be applied cleanly while the old containers exist because both compose files hard-code the same container names.

The active deployment is now:

- `/opt/zabbix/docker-compose.yml`
- `/opt/zabbix/.env`
- `/opt/zabbix/ssl/ssl.crt`
- `/opt/zabbix/ssl/ssl.key`
- `/opt/zabbix/ssl/dhparam.pem`

The old compose file was copied to `/root/zabbix-old-compose/` before migration.

## Issues

- Old compose files use obsolete top-level `version`; Docker Compose now ignores it.
- Old compose files hard-code `container_name`, which prevents parallel projects, clean migrations, and predictable compose ownership.
- Old active compose stored database credentials inline and used weak sample password `zabbix_password`.
- Zabbix images are now pinned to `ubuntu-7.4.8`.
- The active DB password was changed and is stored in root-only files on the server.
- Host-level `zabbix-agent2.service` is the selected agent. The containerized agent is optional in the repository and is not running on the server.
- The containerized agent previously logged `host [docker-zabbix-server] not found`; the host must exist in Zabbix frontend with the same agent hostname or the hostname must be changed.
- Port `8080` is still available as HTTP fallback. Prefer `8443` and replace the self-signed cert with a trusted certificate.

## Recommended Migration Path

1. Replace the self-signed certificate with a trusted certificate after DNS is assigned.
2. Decide whether HTTP `8080` should remain enabled or be removed after HTTPS is trusted.
3. Configure scheduled off-host backups.
4. Create or fix the Zabbix frontend host so it matches host-level `zabbix_agent2` hostname.
5. Automate deployment through Ansible after the compose file is finalized.
6. Add Terraform only when server/network/DNS resources need to be provisioned declaratively.

## Safe Changes Already Done

- The existing stack from `/home/zabbix/zabbix-server/docker-compose.yaml` was started.
- The web UI responded with HTTP `200` on `127.0.0.1:8080`.
- A PostgreSQL custom-format backup was created and verified with `pg_restore -l`: `/root/zabbix-backups/zabbix-20260417T133051Z.dump`.
- A repository scaffold was created locally with Compose, Ansible, Terraform, operational scripts, and this audit note.
- The local Compose template avoids fixed `container_name`, uses `.env`, includes Docker log rotation, and makes the containerized agent optional.
- The running stack was migrated to `/opt/zabbix`.
- PostgreSQL password was changed.
- Zabbix image tags were pinned to `ubuntu-7.4.8`.
- Self-signed HTTPS was enabled on `8443`.
- UFW was enabled and Docker published ports `8080`, `8443`, and `10051` were restricted to `172.30.0.0/16` through `DOCKER-USER`.

## Proxmox Test Deployment

Date: 2026-04-17

A fresh Ubuntu 24.04 cloud-init VM was created on Proxmox and deployed through Ansible:

- Proxmox host: `root@proxmox`
- VMID: `101`
- VM name: `zabbix-test`
- IP: `172.30.193.76/24`
- Gateway: `172.30.193.1`
- Bridge: `vmbr193`
- Storage: `local-lvm`
- Disk: `64G`
- CPU/RAM: `4 cores`, `8192 MB`
- SSH user: `ubuntu`

The VLAN did not have direct internet egress, so deployment used a temporary local HTTP proxy exposed to the VM through SSH reverse forwarding. The Ansible role now supports `zabbix_proxy_env` and configures both apt tasks and Docker daemon proxy settings.

Validation results:

- Ansible playbook completed with `failed=0`.
- Docker service is active.
- `zabbix-docker-firewall.service` is active.
- `zabbix-server-postgres-server-1` is healthy.
- `zabbix-server-zabbix-server-1` is healthy.
- `zabbix-server-zabbix-web-1` is healthy.
- `https://172.30.193.76:8443/` returned HTTP `200`.
- `http://172.30.193.76:8080/` returned HTTP `200`.

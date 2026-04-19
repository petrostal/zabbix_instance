# Zabbix Docker Deployment

Repository scaffold for deploying a Zabbix server with Docker Compose and managing selected Zabbix objects as code.

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
- `ansible/` - host provisioning and deployment automation.
- `terraform/` - Proxmox VM infrastructure definitions.
- `zabbix-config/` - host/group/template-link configuration applied through the Zabbix API.
- `zabbix-native/` - Zabbix-native YAML exports applied through `configuration.import`.
- `docs/` - operational notes and server audit results.
- `scripts/` - helper scripts for deployment and checks.

## Next Steps

Use `docs/server-audit.md` for current server state and remaining production hardening notes.

## Ansible

The Ansible playbook can provision a fresh Ubuntu server and deploy the same stack to `/opt/zabbix`.

Read [ansible/README.md](ansible/README.md) before running it because `zabbix_postgres_password`, `zabbix_trusted_cidr`, and `zabbix_public_iface` must match the target environment.

## Terraform

Terraform can create the Proxmox VM, then Ansible deploys Zabbix into it. The tested path is:

```bash
cd terraform/envs/prod
terraform init
terraform apply
cd ../../..
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-zabbix.yml
```

Read [terraform/README.md](terraform/README.md) and [terraform/envs/prod/README.md](terraform/envs/prod/README.md) before applying; Proxmox API token and SSH key settings are required.

## Zabbix Config as Code

After Zabbix is running, apply selected Zabbix objects from Git:

```bash
python3 -m pip install -r zabbix-config/requirements.txt
export ZABBIX_URL="https://172.30.193.75:8443"
export ZABBIX_API_TOKEN="..."
export ZABBIX_VERIFY_TLS=false
make zabbix-config-dry-run
make zabbix-config-apply
```

The default config is [zabbix-config/config.yml](zabbix-config/config.yml). It manages declared host groups and hosts, including interfaces, tags, macros, and template links. It does not delete missing Zabbix objects.

For a full fresh deployment on Proxmox, the order is:

```bash
cd terraform/envs/prod
terraform apply
cd ../../..
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-zabbix.yml
make zabbix-config-apply
```

Read [zabbix-config/README.md](zabbix-config/README.md) for API authentication and export examples.

## Native Zabbix YAML

For templates, maps, media types, and larger host exports, use Zabbix's native YAML format:

```bash
export ZABBIX_URL="https://172.30.193.75:8443"
export ZABBIX_API_TOKEN="..."
export ZABBIX_VERIFY_TLS=false

make zabbix-native-export-host HOST=zabbix-test > zabbix-native/exports/zabbix-test.yaml
make zabbix-native-validate FILE=zabbix-native/exports/zabbix-test.yaml
make zabbix-native-import FILE=zabbix-native/exports/zabbix-test.yaml
```

The default import rules are [zabbix-native/rules-safe.yml](zabbix-native/rules-safe.yml). They create and update objects but do not delete missing objects. Read [zabbix-native/README.md](zabbix-native/README.md) before enabling any `deleteMissing` rule.

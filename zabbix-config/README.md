# Zabbix Configuration as Code

This directory stores Zabbix configuration that should be reproducible after the server is deployed.

The intended workflow is:

1. Terraform creates the VM.
2. Ansible installs Docker and starts Zabbix.
3. `scripts/zabbix-config.py apply` creates or updates Zabbix groups and hosts through the Zabbix API.

Use this layer for objects that are intentionally managed from Git:

- host groups;
- hosts;
- host interfaces;
- template links;
- tags;
- non-secret macros;
- inventory fields.

Avoid storing passwords, PSKs, SNMP secrets, or API tokens in this directory. Use environment variables for secrets.

## Install Local Dependency

The script uses PyYAML for config files:

```bash
python3 -m pip install -r zabbix-config/requirements.txt
```

If you use the repository virtualenv:

```bash
. .venv/bin/activate
python -m pip install -r zabbix-config/requirements.txt
```

## Authentication

Preferred: create a Zabbix API token in the UI and export it locally:

```bash
export ZABBIX_URL="https://172.30.193.75:8443"
export ZABBIX_API_TOKEN="..."
```

For a fresh lab install, login/password can also be used:

```bash
export ZABBIX_URL="https://172.30.193.75:8443"
export ZABBIX_USER="Admin"
export ZABBIX_PASSWORD="zabbix"
```

Self-signed TLS is accepted only when `ZABBIX_VERIFY_TLS=false` is set:

```bash
export ZABBIX_VERIFY_TLS=false
```

## Validate

```bash
scripts/zabbix-config.py validate zabbix-config/config.yml
```

## Dry Run

```bash
scripts/zabbix-config.py apply --dry-run zabbix-config/config.yml
```

## Apply

```bash
scripts/zabbix-config.py apply zabbix-config/config.yml
```

By default the script only creates or updates declared objects. It does not delete objects missing from Git.

## Export

Export hosts marked with `managed_by=git`:

```bash
scripts/zabbix-config.py export --tag managed_by=git > zabbix-config/exported.yml
```

Review exported files before committing them.

## Example Host

```yaml
hosts:
  - host: zabbix-test
    name: Zabbix Test
    status: enabled
    groups:
      - Linux servers
    templates:
      - Linux by Zabbix agent
    interfaces:
      - type: agent
        ip: 172.30.193.76
        port: 10050
    tags:
      - tag: managed_by
        value: git
      - tag: environment
        value: lab
```

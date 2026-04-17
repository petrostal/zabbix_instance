# Ansible Deployment

This playbook provisions a fresh Ubuntu server and deploys the Zabbix Docker Compose stack to `/opt/zabbix`.

It installs Docker from the official Docker apt repository, creates a self-signed TLS certificate, starts Zabbix with Docker Compose, enables UFW, and installs persistent `DOCKER-USER` rules for published Docker ports.

## Prepare Control Machine

Install collections:

```bash
ansible-galaxy collection install -r ansible/requirements.yml
```

## Configure Inventory

Edit `ansible/inventory/hosts.yml`:

```yaml
all:
  children:
    zabbix_servers:
      hosts:
        zabbix-new:
          ansible_host: 172.30.193.75
          ansible_user: root
```

Create group vars from the example:

```bash
cp ansible/inventory/group_vars/zabbix_servers.yml.example ansible/inventory/group_vars/zabbix_servers.yml
```

Set at least `zabbix_postgres_password` to a long random value. Prefer Ansible Vault:

```bash
ansible-vault encrypt ansible/inventory/group_vars/zabbix_servers.yml
```

Important variables:

- `zabbix_trusted_cidr` - network allowed to reach `8080`, `8443`, `10051`, and `10050`.
- `zabbix_public_iface` - external interface used by Docker firewall rules, for example `ens18`.
- `zabbix_tls_common_name` - DNS name for the self-signed certificate.
- `zabbix_agent_hostname` - hostname used by the optional/container agent settings and documentation.

## Deploy

Run:

```bash
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-zabbix.yml
```

With Vault:

```bash
ansible-playbook --ask-vault-pass -i ansible/inventory/hosts.yml ansible/playbooks/deploy-zabbix.yml
```

## Networks Without Internet Egress

If the target server cannot reach Ubuntu/Docker registries directly, provide an HTTP proxy and pass it as `zabbix_proxy_env`:

```yaml
zabbix_proxy_env:
  http_proxy: "http://127.0.0.1:3128"
  https_proxy: "http://127.0.0.1:3128"
  HTTP_PROXY: "http://127.0.0.1:3128"
  HTTPS_PROXY: "http://127.0.0.1:3128"
```

The role uses this proxy for apt tasks and configures Docker daemon proxy settings before pulling images. For one-off testing, `scripts/simple-http-proxy.py` can be run locally and exposed to the target with SSH reverse forwarding:

```bash
scripts/simple-http-proxy.py 127.0.0.1 3128
ssh -N -R 127.0.0.1:3128:127.0.0.1:3128 ubuntu@<target>
```

For production, prefer real internet egress, an internal HTTP proxy, or a local Docker registry/cache.

## Result

The deployed service listens on:

- `https://<server>:8443/` - preferred UI, self-signed certificate by default.
- `http://<server>:8080/` - HTTP fallback.
- `<server>:10051` - Zabbix server trapper/listener.

On the server:

```bash
cd /opt/zabbix
docker compose -p zabbix-server --env-file .env -f docker-compose.yml ps
systemctl status zabbix-docker-firewall.service --no-pager
ufw status verbose
```

## Production Notes

Replace the self-signed certificate in `/opt/zabbix/ssl` with a trusted certificate when DNS is available. Keep the filenames `ssl.crt`, `ssl.key`, and `dhparam.pem`.

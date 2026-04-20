# CI/CD Strategy

This repository supports direct-push deployment for Zabbix configuration.

The low-downtime path for normal monitoring changes is:

1. Edit `zabbix-config/config.yml` to add or update hosts, groups, interfaces, tags, macros, or template links.
2. Commit and push.
3. CI validates YAML and script syntax.
4. On the default branch, CI applies the configuration through the Zabbix API.

This does not restart Zabbix containers. Adding hosts is an API-only update, so monitoring remains available while the config is applied.

## Deployment Boundaries

Use separate deployment paths for different blast radius:

- `zabbix-config/config.yml`: automatic apply on the default branch. Best for adding hosts and changing template links.
- `zabbix-native/exports/*.yaml`: automatic native import on the default branch, excluding `*.example.yaml`. Best for templates and larger Zabbix-native objects.
- Terraform: manual apply. VM changes can affect availability and should not run automatically on every push.
- Ansible: manual apply. Runtime server changes can restart containers and should be planned.

## GitHub Actions

Workflow: `.github/workflows/zabbix-config.yml`

Behavior:

- every push to any branch runs validation;
- push to `main` deploys after validation;
- deployment jobs are serialized with `concurrency: zabbix-production`.

Required repository or environment secrets:

- `ZABBIX_URL`: for example `https://172.30.193.75:8443`
- `ZABBIX_API_TOKEN`: Zabbix API token with enough rights to manage imported objects

Optional repository/environment variable:

- `ZABBIX_VERIFY_TLS`: set to `false` only for self-signed lab certificates

If GitHub-hosted runners cannot reach the private Zabbix IP, use a self-hosted runner inside the same network or expose the API through a controlled VPN/proxy.

## GitLab CI

Pipeline: `.gitlab-ci.yml`

Behavior:

- every push validates;
- push to the default branch deploys after validation;
- deployment jobs are serialized with `resource_group: zabbix-production`.

Required CI/CD variables:

- `ZABBIX_URL`
- `ZABBIX_API_TOKEN`

Optional variable:

- `ZABBIX_VERIFY_TLS=false` for self-signed lab certificates

For your current private network, a GitLab Runner inside the Proxmox/Zabbix network is the cleanest option.

## Native YAML Safety

CI imports native YAML files from `zabbix-native/exports/`, but ignores files ending in:

- `.example.yaml`
- `.example.yml`

The default import rules are `zabbix-native/rules-safe.yml`. Validation fails if this file contains `deleteMissing: true`.

Keep destructive import rules in a separate file and run them manually only after reviewing the export scope.

## Adding A New Host

Example change:

```yaml
hosts:
  - host: app-01
    name: App 01
    status: enabled
    groups:
      - Linux servers
    templates:
      - Linux by Zabbix agent
    interfaces:
      - type: agent
        ip: 172.30.193.101
        port: 10050
    tags:
      - tag: managed_by
        value: git
      - tag: environment
        value: prod
```

Then:

```bash
make zabbix-config-validate
git add zabbix-config/config.yml
git commit -m "Add app-01 monitoring"
git push
```

On the default branch, the CI deploy job applies the change without restarting Zabbix.

## Rollback

For a bad host change:

1. Revert the Git commit.
2. Push to the default branch.
3. CI applies the previous desired state.

The default scripts update and create objects; they do not delete missing hosts. If a rollback must remove a host, disable it in Git first or remove it manually after confirming it is safe.

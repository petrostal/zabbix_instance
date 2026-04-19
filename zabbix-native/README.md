# Zabbix Native YAML Export/Import

This directory is for files exported by Zabbix itself through `configuration.export` and imported back through `configuration.import`.

Use this option when you want Zabbix to own the file format exactly as the UI/API exports it. It is useful for templates, maps, media types, and larger host definitions where preserving Zabbix-native structure matters more than keeping a compact hand-written config.

## Files

- `exports/` - committed Zabbix-native `.yaml` exports.
- `rules-safe.yml` - default import rules. They create/update objects but do not delete missing objects.

## Authentication

Use the same environment variables as the declarative config tool:

```bash
export ZABBIX_URL="https://172.30.193.75:8443"
export ZABBIX_API_TOKEN="..."
export ZABBIX_VERIFY_TLS=false
```

Login/password also works for a fresh lab instance:

```bash
export ZABBIX_USER="Admin"
export ZABBIX_PASSWORD="zabbix"
```

## Export

Export host `zabbix-test` in native Zabbix YAML format:

```bash
make zabbix-native-export-host HOST=zabbix-test > zabbix-native/exports/zabbix-test.yaml
```

Export a template:

```bash
scripts/zabbix-native-yaml.py export --template "Linux by Zabbix agent" > zabbix-native/exports/linux-by-zabbix-agent.yaml
```

The script resolves names to IDs before calling `configuration.export`.

## Validate Local YAML

```bash
make zabbix-native-validate FILE=zabbix-native/exports/zabbix-test.yaml
```

This checks only file shape and YAML syntax. Zabbix has no no-change dry-run import API.

## Import

```bash
make zabbix-native-import FILE=zabbix-native/exports/zabbix-test.yaml
```

By default this uses `zabbix-native/rules-safe.yml`. To use another rules file:

```bash
scripts/zabbix-native-yaml.py import zabbix-native/exports/zabbix-test.yaml --rules zabbix-native/rules-strict.yml
```

Do not enable `deleteMissing` until the export file is known to be complete for the objects it owns.

## When To Use This Instead Of `zabbix-config/config.yml`

Use native YAML for:

- templates with many items/triggers/discovery rules;
- maps;
- media types;
- files exported from another Zabbix instance;
- preserving Zabbix's exact export format.

Use `zabbix-config/config.yml` for:

- compact Git-managed host inventory;
- simple host groups, host interfaces, tags, macros, and template links;
- cases where reviewing small human-written changes matters.

Official API methods used here:

- `configuration.export`: exports serialized YAML/XML/JSON configuration.
- `configuration.import`: imports a serialized configuration string with explicit import rules.

#!/usr/bin/env python3
"""Apply and export a small declarative Zabbix configuration."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from typing import Any


INTERFACE_TYPES = {
    "agent": 1,
    "snmp": 2,
    "ipmi": 3,
    "jmx": 4,
}

STATUS = {
    "enabled": 0,
    "disabled": 1,
}

INVENTORY_MODE = {
    "disabled": -1,
    "manual": 0,
    "automatic": 1,
}


class ZabbixError(RuntimeError):
    pass


class ZabbixAPI:
    def __init__(
        self,
        url: str,
        token: str | None = None,
        username: str | None = None,
        password: str | None = None,
        verify_tls: bool = True,
    ) -> None:
        self.url = url.rstrip("/") + "/api_jsonrpc.php"
        self.token = token
        self.username = username
        self.password = password
        self.request_id = 0
        self.context = None if verify_tls else ssl._create_unverified_context()

    def login(self) -> None:
        if self.token:
            return
        if not self.username or not self.password:
            raise ZabbixError("Set ZABBIX_API_TOKEN or ZABBIX_USER/ZABBIX_PASSWORD.")
        result = self.call(
            "user.login",
            {"username": self.username, "password": self.password},
            authenticated=False,
        )
        if isinstance(result, dict) and "sessionid" in result:
            self.token = result["sessionid"]
        elif isinstance(result, str):
            self.token = result
        else:
            raise ZabbixError("Unexpected user.login response.")

    def call(self, method: str, params: Any, authenticated: bool = True) -> Any:
        self.request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.request_id,
        }
        headers = {"Content-Type": "application/json-rpc"}
        if authenticated and self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        request = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, context=self.context, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ZabbixError(f"HTTP {exc.code} from Zabbix API: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ZabbixError(f"Cannot reach Zabbix API at {self.url}: {exc.reason}") from exc

        if "error" in body:
            error = body["error"]
            message = error.get("message", "API error")
            data = error.get("data", "")
            raise ZabbixError(f"{method}: {message}: {data}")
        return body.get("result")


def load_yaml(path: str) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise ZabbixError(
            "PyYAML is required. Run: python3 -m pip install -r zabbix-config/requirements.txt"
        ) from exc

    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ZabbixError("Config root must be a YAML mapping.")
    return data


def dump_yaml(data: dict[str, Any]) -> str:
    try:
        import yaml
    except ImportError as exc:
        raise ZabbixError(
            "PyYAML is required. Run: python3 -m pip install -r zabbix-config/requirements.txt"
        ) from exc
    return yaml.safe_dump(data, allow_unicode=False, sort_keys=False)


def as_list(value: Any, field: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ZabbixError(f"{field} must be a list.")
    return value


def normalize_groups(config: dict[str, Any]) -> list[str]:
    groups = []
    for group in as_list(config.get("host_groups"), "host_groups"):
        if isinstance(group, str):
            groups.append(group)
        elif isinstance(group, dict) and isinstance(group.get("name"), str):
            groups.append(group["name"])
        else:
            raise ZabbixError("Each host group must be a string or {name: ...}.")
    for host in as_list(config.get("hosts"), "hosts"):
        for group in as_list(host.get("groups"), f"hosts[{host.get('host')}].groups"):
            if group not in groups:
                groups.append(group)
    return groups


def normalize_tags(tags: list[Any]) -> list[dict[str, str]]:
    normalized = []
    for tag in tags:
        if isinstance(tag, dict):
            normalized.append({"tag": str(tag["tag"]), "value": str(tag.get("value", ""))})
        else:
            raise ZabbixError("Tags must be objects with tag/value.")
    return normalized


def normalize_macros(macros: list[Any]) -> list[dict[str, str]]:
    normalized = []
    for macro in macros:
        if not isinstance(macro, dict) or "macro" not in macro:
            raise ZabbixError("Macros must be objects with at least macro.")
        item = {"macro": str(macro["macro"])}
        if "value_env" in macro:
            env_name = str(macro["value_env"])
            if env_name not in os.environ:
                raise ZabbixError(f"Environment variable {env_name} is required for {item['macro']}.")
            item["value"] = os.environ[env_name]
        else:
            item["value"] = str(macro.get("value", ""))
        if "description" in macro:
            item["description"] = str(macro["description"])
        if "type" in macro:
            item["type"] = str(macro["type"])
        normalized.append(item)
    return normalized


def normalize_interfaces(interfaces: list[Any], existing: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    existing = existing or []
    used_existing_ids = set()
    normalized = []

    for index, interface in enumerate(interfaces):
        if not isinstance(interface, dict):
            raise ZabbixError("Interfaces must be objects.")
        interface_type = interface.get("type", "agent")
        type_id = INTERFACE_TYPES.get(str(interface_type), interface_type)
        item = {
            "type": int(type_id),
            "main": int(interface.get("main", 1 if index == 0 else 0)),
            "useip": int(interface.get("useip", 1 if interface.get("ip") else 0)),
            "ip": str(interface.get("ip", "")),
            "dns": str(interface.get("dns", "")),
            "port": str(interface.get("port", "10050")),
        }
        if "details" in interface:
            item["details"] = interface["details"]

        for current in existing:
            interfaceid = current.get("interfaceid")
            if interfaceid in used_existing_ids:
                continue
            if int(current.get("type", 0)) == item["type"] and int(current.get("main", 0)) == item["main"]:
                item["interfaceid"] = interfaceid
                used_existing_ids.add(interfaceid)
                break
        normalized.append(item)

    return normalized


def validate_config(config: dict[str, Any]) -> None:
    normalize_groups(config)
    hosts = as_list(config.get("hosts"), "hosts")
    for host in hosts:
        if not isinstance(host, dict):
            raise ZabbixError("Each host must be a mapping.")
        if not host.get("host"):
            raise ZabbixError("Each host must define host.")
        if not host.get("groups"):
            raise ZabbixError(f"Host {host['host']} must define at least one group.")
        normalize_interfaces(as_list(host.get("interfaces"), f"hosts[{host['host']}].interfaces"))
        normalize_tags(as_list(host.get("tags"), f"hosts[{host['host']}].tags"))
        normalize_macros(as_list(host.get("macros"), f"hosts[{host['host']}].macros"))
        if "status" in host and host["status"] not in STATUS and host["status"] not in (0, 1):
            raise ZabbixError(f"Host {host['host']} has unsupported status {host['status']!r}.")
        if "inventory_mode" in host and host["inventory_mode"] not in INVENTORY_MODE and host["inventory_mode"] not in (-1, 0, 1):
            raise ZabbixError(f"Host {host['host']} has unsupported inventory_mode.")


def get_group_map(api: ZabbixAPI) -> dict[str, str]:
    groups = api.call("hostgroup.get", {"output": ["groupid", "name"]})
    return {group["name"]: group["groupid"] for group in groups}


def ensure_groups(api: ZabbixAPI, names: list[str], dry_run: bool) -> dict[str, str]:
    group_map = get_group_map(api)
    missing = [name for name in names if name not in group_map]
    if missing:
        if dry_run:
            print(f"would create host groups: {', '.join(missing)}")
        else:
            api.call("hostgroup.create", [{"name": name} for name in missing])
            print(f"created host groups: {', '.join(missing)}")
            group_map = get_group_map(api)
    return group_map


def get_template_map(api: ZabbixAPI, names: list[str]) -> dict[str, str]:
    if not names:
        return {}
    templates = api.call(
        "template.get",
        {
            "output": ["templateid", "host", "name"],
            "filter": {"host": names},
        },
    )
    template_map = {template["host"]: template["templateid"] for template in templates}
    missing = [name for name in names if name not in template_map]
    if missing:
        templates = api.call(
            "template.get",
            {
                "output": ["templateid", "host", "name"],
                "filter": {"name": missing},
            },
        )
        template_map.update({template["name"]: template["templateid"] for template in templates})
    return template_map


def get_host(api: ZabbixAPI, host_name: str) -> dict[str, Any] | None:
    hosts = api.call(
        "host.get",
        {
            "output": ["hostid", "host", "name", "status"],
            "filter": {"host": [host_name]},
            "selectInterfaces": "extend",
            "selectHostGroups": ["groupid", "name"],
            "selectParentTemplates": ["templateid", "host", "name"],
            "selectTags": "extend",
            "selectMacros": "extend",
            "selectInventory": "extend",
        },
    )
    return hosts[0] if hosts else None


def host_params(host: dict[str, Any], group_map: dict[str, str], template_map: dict[str, str], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    groups = [{"groupid": group_map[group]} for group in host["groups"]]
    templates = []
    for template in as_list(host.get("templates"), f"hosts[{host['host']}].templates"):
        if template not in template_map:
            raise ZabbixError(f"Template {template!r} was not found in Zabbix.")
        templates.append({"templateid": template_map[template]})

    status = host.get("status", "enabled")
    inventory_mode = host.get("inventory_mode")
    params: dict[str, Any] = {
        "host": str(host["host"]),
        "name": str(host.get("name", host["host"])),
        "status": int(STATUS.get(status, status)),
        "groups": groups,
        "interfaces": normalize_interfaces(
            as_list(host.get("interfaces"), f"hosts[{host['host']}].interfaces"),
            existing.get("interfaces", []) if existing else None,
        ),
        "templates": templates,
        "tags": normalize_tags(as_list(host.get("tags"), f"hosts[{host['host']}].tags")),
        "macros": normalize_macros(as_list(host.get("macros"), f"hosts[{host['host']}].macros")),
    }

    if inventory_mode is not None:
        params["inventory_mode"] = int(INVENTORY_MODE.get(inventory_mode, inventory_mode))
    if "inventory" in host:
        params["inventory"] = host["inventory"]
    return params


def apply_config(api: ZabbixAPI, config: dict[str, Any], dry_run: bool) -> None:
    validate_config(config)
    api.login()

    group_map = ensure_groups(api, normalize_groups(config), dry_run)
    template_names = []
    for host in as_list(config.get("hosts"), "hosts"):
        for template in as_list(host.get("templates"), f"hosts[{host['host']}].templates"):
            if template not in template_names:
                template_names.append(template)
    template_map = get_template_map(api, template_names)

    for host in as_list(config.get("hosts"), "hosts"):
        existing = get_host(api, host["host"])
        params = host_params(host, group_map, template_map, existing)
        if existing:
            params["hostid"] = existing["hostid"]
            if dry_run:
                print(f"would update host: {host['host']}")
            else:
                api.call("host.update", params)
                print(f"updated host: {host['host']}")
        else:
            if dry_run:
                print(f"would create host: {host['host']}")
            else:
                api.call("host.create", params)
                print(f"created host: {host['host']}")


def export_config(api: ZabbixAPI, tag: str | None) -> dict[str, Any]:
    api.login()
    params: dict[str, Any] = {
        "output": ["hostid", "host", "name", "status"],
        "selectInterfaces": "extend",
        "selectHostGroups": ["name"],
        "selectParentTemplates": ["host", "name"],
        "selectTags": "extend",
        "selectMacros": "extend",
        "selectInventory": "extend",
    }
    if tag:
        key, _, value = tag.partition("=")
        params["evaltype"] = 0
        params["tags"] = [{"tag": key, "value": value, "operator": 1}]
    hosts = api.call("host.get", params)

    group_names: list[str] = []
    exported_hosts = []
    for host in sorted(hosts, key=lambda item: item["host"]):
        groups = sorted(group["name"] for group in host.get("hostgroups", []))
        for group in groups:
            if group not in group_names:
                group_names.append(group)
        exported_hosts.append(
            {
                "host": host["host"],
                "name": host.get("name") or host["host"],
                "status": "disabled" if str(host.get("status")) == "1" else "enabled",
                "groups": groups,
                "templates": [
                    template.get("host") or template.get("name")
                    for template in host.get("parentTemplates", [])
                ],
                "interfaces": [
                    {
                        "type": next((name for name, number in INTERFACE_TYPES.items() if number == int(interface["type"])), interface["type"]),
                        "main": int(interface.get("main", 0)),
                        "useip": int(interface.get("useip", 0)),
                        "ip": interface.get("ip", ""),
                        "dns": interface.get("dns", ""),
                        "port": interface.get("port", ""),
                    }
                    for interface in host.get("interfaces", [])
                ],
                "tags": [
                    {"tag": item["tag"], "value": item.get("value", "")}
                    for item in host.get("tags", [])
                ],
                "macros": [
                    {
                        "macro": macro["macro"],
                        "value": macro.get("value", ""),
                        **({"description": macro["description"]} if macro.get("description") else {}),
                    }
                    for macro in host.get("macros", [])
                ],
            }
        )
    return {"host_groups": sorted(group_names), "hosts": exported_hosts}


def build_api_from_env() -> ZabbixAPI:
    url = os.environ.get("ZABBIX_URL")
    if not url:
        raise ZabbixError("Set ZABBIX_URL, for example https://172.30.193.75:8443")
    verify_tls = os.environ.get("ZABBIX_VERIFY_TLS", "true").lower() not in {"0", "false", "no"}
    return ZabbixAPI(
        url=url,
        token=os.environ.get("ZABBIX_API_TOKEN"),
        username=os.environ.get("ZABBIX_USER"),
        password=os.environ.get("ZABBIX_PASSWORD"),
        verify_tls=verify_tls,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("config")

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("config")
    apply_parser.add_argument("--dry-run", action="store_true")

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--tag", help="Export only hosts with tag=value.")

    args = parser.parse_args()

    try:
        if args.command == "validate":
            validate_config(load_yaml(args.config))
            print(f"valid: {args.config}")
            return 0

        api = build_api_from_env()
        if args.command == "apply":
            apply_config(api, load_yaml(args.config), args.dry_run)
            return 0
        if args.command == "export":
            sys.stdout.write(dump_yaml(export_config(api, args.tag)))
            return 0
    except ZabbixError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

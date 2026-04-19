#!/usr/bin/env python3
"""Import and export Zabbix native YAML configuration files."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


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
            with urllib.request.urlopen(request, context=self.context, timeout=60) as response:
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


def load_yaml(path: str | Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise ZabbixError(
            "PyYAML is required. Run: python3 -m pip install -r zabbix-config/requirements.txt"
        ) from exc

    with open(path, "r", encoding="utf-8-sig") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ZabbixError(f"{path} must contain a YAML mapping.")
    return data


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


def validate_native_yaml(path: str | Path) -> None:
    data = load_yaml(path)
    root = data.get("zabbix_export")
    if not isinstance(root, dict):
        raise ZabbixError(f"{path} is not a Zabbix native export: missing zabbix_export.")
    if "version" not in root:
        raise ZabbixError(f"{path} is not a Zabbix native export: missing zabbix_export.version.")


def load_rules(path: str | Path) -> dict[str, Any]:
    data = load_yaml(path)
    rules = data.get("rules", data)
    if not isinstance(rules, dict) or not rules:
        raise ZabbixError(f"{path} does not contain import rules.")
    return rules


def read_source(path: str | Path) -> str:
    validate_native_yaml(path)
    return Path(path).read_text(encoding="utf-8")


def first_id(api: ZabbixAPI, method: str, params: dict[str, Any], id_field: str, name: str) -> str:
    result = api.call(method, params)
    if not result:
        raise ZabbixError(f"Cannot find {name!r} through {method}.")
    return str(result[0][id_field])


def resolve_export_options(api: ZabbixAPI, args: argparse.Namespace) -> dict[str, list[str]]:
    options: dict[str, list[str]] = {}

    if args.host_group:
        options["host_groups"] = [
            first_id(
                api,
                "hostgroup.get",
                {"output": ["groupid", "name"], "filter": {"name": [name]}},
                "groupid",
                name,
            )
            for name in args.host_group
        ]
    if args.template_group:
        options["template_groups"] = [
            first_id(
                api,
                "templategroup.get",
                {"output": ["groupid", "name"], "filter": {"name": [name]}},
                "groupid",
                name,
            )
            for name in args.template_group
        ]
    if args.host:
        options["hosts"] = [
            first_id(
                api,
                "host.get",
                {"output": ["hostid", "host", "name"], "filter": {"host": [name]}},
                "hostid",
                name,
            )
            for name in args.host
        ]
    if args.template:
        options["templates"] = [
            first_id(
                api,
                "template.get",
                {"output": ["templateid", "host", "name"], "filter": {"host": [name]}},
                "templateid",
                name,
            )
            for name in args.template
        ]

    if not options:
        raise ZabbixError("Select at least one object to export.")
    return options


def import_file(api: ZabbixAPI, source_path: str, rules_path: str) -> None:
    api.login()
    result = api.call(
        "configuration.import",
        {
            "format": "yaml",
            "source": read_source(source_path),
            "rules": load_rules(rules_path),
        },
    )
    if result is not True:
        raise ZabbixError(f"Unexpected import result: {result!r}")
    print(f"imported: {source_path}")


def export_yaml(api: ZabbixAPI, args: argparse.Namespace) -> str:
    api.login()
    return str(
        api.call(
            "configuration.export",
            {
                "format": "yaml",
                "prettyprint": True,
                "options": resolve_export_options(api, args),
            },
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("file")

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("file")
    import_parser.add_argument("--rules", default="zabbix-native/rules-safe.yml")

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--host", action="append", default=[])
    export_parser.add_argument("--template", action="append", default=[])
    export_parser.add_argument("--host-group", action="append", default=[])
    export_parser.add_argument("--template-group", action="append", default=[])

    args = parser.parse_args()

    try:
        if args.command == "validate":
            validate_native_yaml(args.file)
            print(f"valid native Zabbix YAML: {args.file}")
            return 0

        api = build_api_from_env()
        if args.command == "import":
            import_file(api, args.file, args.rules)
            return 0
        if args.command == "export":
            sys.stdout.write(export_yaml(api, args))
            return 0
    except ZabbixError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

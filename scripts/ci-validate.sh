#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"

"${PYTHON_BIN}" -m py_compile scripts/zabbix-config.py scripts/zabbix-native-yaml.py
"${PYTHON_BIN}" scripts/zabbix-config.py validate zabbix-config/config.yml

if [ -f zabbix-native/rules-safe.yml ]; then
  "${PYTHON_BIN}" - <<'PY'
from pathlib import Path
import sys
import yaml

rules_path = Path("zabbix-native/rules-safe.yml")
rules = yaml.safe_load(rules_path.read_text()) or {}
rules = rules.get("rules", rules)

bad = []
for section, section_rules in rules.items():
    if isinstance(section_rules, dict) and section_rules.get("deleteMissing") is True:
        bad.append(section)

if bad:
    print(f"error: deleteMissing=true is not allowed in {rules_path}: {', '.join(bad)}", file=sys.stderr)
    sys.exit(1)
PY
fi

while IFS= read -r file; do
  "${PYTHON_BIN}" scripts/zabbix-native-yaml.py validate "${file}"
done < <(find zabbix-native/exports -type f \( -name '*.yaml' -o -name '*.yml' \) ! -name '*.example.yaml' ! -name '*.example.yml' | sort)

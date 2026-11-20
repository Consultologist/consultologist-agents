#!/usr/bin/env python3
"""Check the specVersion 31 catalogue in agents/v31/ and the judgement agent.

Run from anywhere: python3 scripts/check-v31.py. Exits 0 when every check holds.
"""
import json
import pathlib
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
V31 = ROOT / "agents" / "v31"
BUILT_IN = {"string", "number", "boolean", "date", "plaintext",
            "markdown_block", "markdown_inline", "check_result", "judgement"}
PLAINTEXT_DESCRIPTION = "Plain text, with no markup."
DIALECT = "urn:consultologist:spec:31:dialect"
THIRTY_FILES = ["agents/formats.json", "agents/formats", "agents/output-contracts.json",
                "agents/schemas", "agents/classification.yaml", "agents/concept-extraction.yaml",
                "agents/custom-json.yaml", "agents/test-json.yaml"]

errors = []


def check(ok, message):
    if not ok:
        errors.append(message)


def check_closed(schema, where):
    """Every object level lists exactly its properties in required and is closed."""
    if isinstance(schema, dict):
        if schema.get("type") == "object":
            check(schema.get("additionalProperties") is False, f"{where}: additionalProperties is not false")
            check(sorted(schema.get("required", [])) == sorted(schema.get("properties", {})),
                  f"{where}: required does not list exactly the properties")
        for key, value in schema.items():
            check_closed(value, f"{where}/{key}")
    elif isinstance(schema, list):
        for i, value in enumerate(schema):
            check_closed(value, f"{where}/{i}")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


bindings = load(V31 / "bindings.json")
agents = load(V31 / "agents.json")
index = load(V31 / "formats" / "index.json")
version = bindings["version"]

# Format files: listed once in the index, each carrying $schema and its own $id.
files = sorted(p.stem for p in (V31 / "formats").glob("*.json") if p.name != "index.json")
check(sorted(index["items"]) == files and len(set(index["items"])) == len(index["items"]),
      f"formats/index.json items {index['items']} are not each format file once: {files}")
for name in files:
    fmt = load(V31 / "formats" / f"{name}.json")
    check_closed(fmt, f"{name}.json")
    check(fmt.get("$schema") == DIALECT, f"{name}.json: $schema is not {DIALECT}")
    check(fmt.get("$id") == f"urn:consultologist:format:{name}@{version}",
          f"{name}.json: $id is {fmt.get('$id')}")

# Bindings: every bound format exists; every bound agent exists at the bound version.
bound = {}
for fmt_name, entry in bindings["formats"].items():
    check(fmt_name in files or fmt_name in BUILT_IN, f"bound format {fmt_name} has no file and is not built in")
    bound[(entry["generated"]["agentName"], entry["generated"]["agentVersion"])] = fmt_name
bound[(bindings["custom"]["generated"]["agentName"], bindings["custom"]["generated"]["agentVersion"])] = "custom"
check(agents["version"] == version, "agents.json version differs from bindings.json")
for (name, ver), fmt_name in bound.items():
    path = ROOT / "agents" / f"{name}.yaml"
    check(path.exists(), f"{fmt_name}: agent {name} has no agents/{name}.yaml")
    if path.exists():
        check(str(yaml.safe_load(path.read_text(encoding="utf-8"))["version"]) == str(ver),
              f"{fmt_name}: agents/{name}.yaml version is not {ver}")
    check(str(ver) in agents["agents"].get(name, {}), f"agents.json has no entry for {name}@{ver}")
for name, versions in agents["agents"].items():
    for ver in versions:
        check((name, int(ver)) in bound, f"agents.json entry {name}@{ver} is bound by nothing")

# judgement.yaml's embedded schema.
judgement = yaml.safe_load((ROOT / "agents" / "judgement.yaml").read_text(encoding="utf-8"))
response_format = judgement["definition"]["text"]["format"]
check(response_format["name"] == "judgement" and response_format["strict"] is True,
      "judgement.yaml's response format is not the strict format named judgement")
schema = json.loads(response_format["schema"])
check_closed(schema, "judgement.yaml schema")
check(schema["properties"]["reason"]["description"].startswith(PLAINTEXT_DESCRIPTION),
      "judgement.yaml's reason description does not begin with the plaintext format's description")
check(list(schema["properties"]) == ["answer", "reason"], "judgement schema properties are not answer, reason")

# Nothing the engine at 30 reads has changed.
unchanged = subprocess.run(["git", "diff", "--quiet", "origin/main", "--", *THIRTY_FILES], cwd=ROOT)
check(unchanged.returncode == 0, "a file the engine at 30 reads differs from origin/main")
stray = subprocess.run(["git", "status", "--porcelain", "--", *THIRTY_FILES], cwd=ROOT,
                       capture_output=True, text=True).stdout
check(not stray, f"a path the engine at 30 reads has untracked or changed files:\n{stray}")

for message in errors:
    print("FAIL:", message)
if not errors:
    print("agents/v31: OK")
sys.exit(1 if errors else 0)

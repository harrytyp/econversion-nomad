#!/usr/bin/env python3
"""Patch nomad-distro-template files for elabFTW integration."""
import os, sys, re, yaml

DISTRO = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("NOMAD_DISTRO_DIR", os.path.expanduser("~/nomad-distro-template"))
IMAGE = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("NOMAD_IMAGE", "nomad-distro-template:with-elabftw")

changes = []

# 1. Patch pyproject.toml
pp_path = os.path.join(DISTRO, "pyproject.toml")
with open(pp_path) as f:
    content = f.read()

if "nomad-external-eln-integrations" not in content:
    old = 'plugins = [
 "nomad-north-jupyter>=0.2.5"
]'
    new = 'plugins = [
 "nomad-north-jupyter>=0.2.5",
 "nomad-external-eln-integrations @ git+https://github.com/FAIRmat-NFDI/nomad-external-eln-integrations.git",
]'
    if old in content:
        content = content.replace(old, new)
        with open(pp_path, "w") as f:
            f.write(content)
        changes.append("pyproject.toml: added elabFTW plugin")
    else:
        changes.append("pyproject.toml: SKIP - pattern not found")

# 2. Patch docker-compose.yaml
dc_path = os.path.join(DISTRO, "docker-compose.yaml")
with open(dc_path) as f:
    data = yaml.safe_load(f)

for svc in ["app", "north", "worker"]:
    s = data["services"].get(svc)
    if s and s.get("image") != IMAGE:
        s["image"] = IMAGE
        changes.append(f"{svc}: image -> {IMAGE}")

app = data["services"].get("app", {})
vol_path = "./plugins:/app/plugins"
if vol_path not in app.get("volumes", []):
    app.setdefault("volumes", []).append(vol_path)
    changes.append("app: added plugins volume")

env = app.setdefault("environment", {})
if env.get("PYTHONPATH") != "/app/plugins":
    env["PYTHONPATH"] = "/app/plugins"
    changes.append("app: added PYTHONPATH")

with open(dc_path, "w") as f:
    yaml.dump(data, f, default_flow_style=False, width=200, sort_keys=False)
changes.append("docker-compose.yaml saved")

for c in changes:
    print(f"  {c}")

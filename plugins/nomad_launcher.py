#!/usr/bin/env python3
"""
NOMAD launcher with _plugins cleanup.

Works around NOMAD v1.4.2 shared-state bug in _plugins that causes
load_plugins() to fail. Cleans stale defaults, then runs NOMAD CLI
without interfering with NOMAD's own initialization order.
"""
import os
import sys

sys.path.insert(0, "/app/plugins")

# ---- Clean stale _plugins entries ----
# This prevents the ValueError from load_plugins() when it encounters
# example_uploads/apps entries with residual 'id' fields from defaults.yaml
from nomad.config import _plugins
if _plugins:
    opts = _plugins.get("entry_points", {}).get("options", {})
    for k in list(opts.keys()):
        if k.startswith("example_uploads/"):
            del opts[k]

# ---- Ensure .nomad_pat exists ----
if not os.path.exists("/app/.nomad_pat"):
    for src in ["/app/plugins/.nomad_pat"]:
        if os.path.exists(src):
            import shutil
            shutil.copy(src, "/app/.nomad_pat")
            os.chmod("/app/.nomad_pat", 0o600)

# ---- Run NOMAD CLI ----
from nomad.cli.cli import run_cli
run_cli()

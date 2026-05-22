#!/bin/bash
# =============================================================================
# NOMAD Bridge Plugin Startup Hook
# =============================================================================
# Runs every time the container starts. Installs the elabFTW bridge plugin
# and instrument data schemas. Uses the OFFICIAL NOMAD image — no custom build.
# =============================================================================

set -e

echo "[startup] Installing elabFTW bridge plugin..."

# Ensure pip is available
python3 -m ensurepip --upgrade 2>/dev/null || true

# Install the FAIRmat elabFTW base plugin from local archive (no git needed)
if [ ! -d /opt/venv/lib/python3.12/site-packages/nomad_external_eln_integrations ]; then
    if [ -f /app/plugins/nomad-external-eln-integrations.tar.gz ]; then
        echo "[startup] Installing FAIRmat elabFTW plugin from local archive..."
        python3 -m pip install --quiet --no-cache-dir \
            /app/plugins/nomad-external-eln-integrations.tar.gz 2>&1 | grep -v "^$" | sed 's/^/[startup]   /'
        echo "[startup] FAIRmat elabFTW plugin installed"
    else
        echo "[startup] WARNING: FAIRmat plugin archive not found at /app/plugins/nomad-external-eln-integrations.tar.gz"
    fi
else
    echo "[startup] FAIRmat plugin already installed"
fi

# Copy our bridge plugin egg-info so NOMAD discovers it
if [ -d /app/plugins/three_way_nomad_bridge.egg-info ]; then
    cp -r /app/plugins/three_way_nomad_bridge.egg-info /opt/venv/lib/python3.12/site-packages/ 2>/dev/null
    echo "[startup] Bridge egg-info installed"
fi

# Install instrument data plugin (TGA, DMA, FTIR, MS schemas)
if [ -d /app/plugins/instrument_data ]; then
    cd /app/plugins
    python3 << 'PYEOF'
import os
name = "instrument_data"
egg_dir = name + ".egg-info"
os.makedirs(egg_dir, exist_ok=True)
with open(os.path.join(egg_dir, "PKG-INFO"), "w") as f:
    f.write("Metadata-Version: 2.1\nName: instrument-data\nVersion: 0.1.0\nSummary: Instrument measurement schemas for NOMAD Oasis (TGA, DMA, FTIR, MS)\n")
with open(os.path.join(egg_dir, "entry_points.txt"), "w") as f:
    f.write("[nomad.plugin]\ninstrument-schema = instrument_data.entrypoint:instrument_schema\n")
with open(os.path.join(egg_dir, "top_level.txt"), "w") as f:
    f.write("instrument_data\n")
for fn in ["dependency_links.txt", "requires.txt", "SOURCES.txt"]:
    with open(os.path.join(egg_dir, fn), "w") as f:
        f.write("")
PYEOF
    cp -r /app/plugins/instrument_data.egg-info /opt/venv/lib/python3.12/site-packages/ 2>/dev/null
    echo "[startup] Instrument data plugin installed (TGA, DMA, FTIR, MS schemas)"
fi

# Create .pth file for the plugins directory
echo "/app/plugins" > /opt/venv/lib/python3.12/site-packages/_bridge_plugins.pth 2>/dev/null
echo "[startup] Bridge plugins path registered"

# Deploy user guide to NOMAD static docs
if [ -f /app/plugins/three_way_sync/user-guide.html ]; then
    mkdir -p /opt/venv/lib/python3.12/site-packages/nomad/app/static/docs/elabftw/
    cp /app/plugins/three_way_sync/user-guide.html /opt/venv/lib/python3.12/site-packages/nomad/app/static/docs/elabftw/
    echo "[startup] User guide deployed"
fi

echo "[startup] Starting NOMAD..."
exec python -m nomad.cli "$@"

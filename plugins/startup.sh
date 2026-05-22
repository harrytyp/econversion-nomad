#!/bin/bash
# =============================================================================
# NOMAD Bridge Plugin Startup Hook
# =============================================================================
# Runs every time the container starts. Installs the elabFTW bridge plugin.
# Uses the OFFICIAL NOMAD image — no custom build needed.
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

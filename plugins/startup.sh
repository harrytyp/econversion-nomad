#!/bin/bash
# NOMAD Bridge Plugin Startup Hook
# Copy the bridge plugin egg-info to site-packages so NOMAD discovers it.
# Mount this as /app/startup.sh and set command to run it.
if [ -d /app/plugins/three_way_nomad_bridge.egg-info ]; then
    cp -r /app/plugins/three_way_nomad_bridge.egg-info /opt/venv/lib/python3.12/site-packages/ 2>/dev/null
fi
exec python -m nomad.cli "$@"

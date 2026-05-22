#!/bin/bash
# =============================================================================
# econversion-NOMAD: One-click Setup
# =============================================================================
# Run this on a fresh NOMAD Oasis server to install:
#   1. nomad-external-eln-integrations (FAIRmat elabFTW parser)
#   2. three_way_sync bridge (bidirectional elabFTW-NOMAD linking)
#   3. ElabftwSettings + ElabftwLinkedEntry schemas
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/harrytyp/econversion-nomad/main/setup.sh | bash
#
# Or:
#   git clone https://github.com/harrytyp/econversion-nomad.git
#   cd econversion-nomad && bash setup.sh
# =============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[✗]${NC} $1"; }

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
DISTRO_DIR="${NOMAD_DISTRO_DIR:-$HOME/nomad-distro-template}"
BRIDGE_IMAGE="${NOMAD_IMAGE:-nomad-distro-template:with-elabftw}"

# ---- Step 0: Prerequisites ------------------------------------------------
echo "=== econversion-NOMAD Setup ==="
echo ""

# Check dependencies
for cmd in docker git python3; do
    if ! command -v $cmd &>/dev/null; then
        err "$cmd is required but not installed."
        exit 1
    fi
done
info "All prerequisites found"

# ---- Step 1: Clone/Update nomad-distro-template ---------------------------
if [ ! -d "$DISTRO_DIR" ]; then
    echo "Cloning nomad-distro-template..."
    git clone https://github.com/FAIRmat-NFDI/nomad-distro-template.git "$DISTRO_DIR"
    info "nomad-distro-template cloned"
else
    info "nomad-distro-template already exists at $DISTRO_DIR"
fi

cd "$DISTRO_DIR"

# ---- Step 2: Patch pyproject.toml with elabFTW plugin ---------------------
# Only add if not already present
if grep -q "nomad-external-eln-integrations" pyproject.toml 2>/dev/null; then
    info "elabFTW plugin already in pyproject.toml"
else
    warn "Adding elabFTW plugin to pyproject.toml..."
    # Add the git dependency to the plugins list
    python3 -c "
import re
with open('pyproject.toml') as f: c = f.read()
c = c.replace(
    'plugins = [\n \"nomad-north-jupyter>=0.2.5\"\n]',
    'plugins = [\n \"nomad-north-jupyter>=0.2.5\",\n \"nomad-external-eln-integrations @ git+https://github.com/FAIRmat-NFDI/nomad-external-eln-integrations.git\",\n]'
)
with open('pyproject.toml', 'w') as f: f.write(c)
"
    info "pyproject.toml patched"
fi

# ---- Step 3: Update uv.lock ------------------------------------------------
warn "Regenerating uv.lock (this may take a minute)..."
python3 -m venv /tmp/uv_venv
/tmp/uv_venv/bin/pip install uv -q
/tmp/uv_venv/bin/uv lock 2>&1 | tail -3
info "uv.lock updated"

# ---- Step 4: Build custom Docker image ------------------------------------
warn "Building Docker image (this may take 3-5 minutes)..."
DOCKER_BUILDKIT=1 docker build --target final -t "$BRIDGE_IMAGE" . 2>&1 | tail -5
info "Docker image built: $BRIDGE_IMAGE"

# ---- Step 5: Copy bridge plugin into distro -------------------------------
mkdir -p "$DISTRO_DIR/plugins"
cp -r "$REPO_DIR/plugins/three_way_sync" "$DISTRO_DIR/plugins/"
cp -r "$REPO_DIR/plugins/three_way_nomad_bridge.egg-info" "$DISTRO_DIR/plugins/" 2>/dev/null || true
cp "$REPO_DIR/plugins/startup.sh" "$DISTRO_DIR/plugins/" 2>/dev/null || true
chmod +x "$DISTRO_DIR/plugins/startup.sh"
info "Bridge plugin files copied"

# ---- Step 6: Patch docker-compose.yaml ------------------------------------
warn "Patching docker-compose.yaml..."
python3 -c "
import yaml
path = 'docker-compose.yaml'
with open(path) as f: data = yaml.safe_load(f)

changes = 0
for svc in ['app', 'north', 'worker']:
    s = data['services'].get(svc)
    if not s: continue
    if 'nomad-distro-template:with-elabftw' not in str(s.get('image', '')):
        s['image'] = '$BRIDGE_IMAGE'
        changes += 1

# Add volumes and PYTHONPATH to app service
app = data['services'].get('app', {})
vols = app.get('volumes', [])
vol_path = './plugins:/app/plugins'
if vol_path not in vols:
    vols.append(vol_path)
    changes += 1
env = app.get('environment', {})
env['PYTHONPATH'] = '/app/plugins'
changes += 1

with open(path, 'w') as f: yaml.dump(data, f, default_flow_style=False, width=200, sort_keys=False)
print(f'Made {changes} changes to docker-compose.yaml')
"
info "docker-compose.yaml patched"

# ---- Step 7: Restart services ---------------------------------------------
warn "Restarting NOMAD services..."
docker compose up -d app north worker 2>&1 | tail -3
info "Services restarted"

# ---- Step 8: Wait for healthy and set up entry points ---------------------
warn "Waiting for app to start (up to 3 minutes)..."
sleep 10
CONTAINER=""
for i in $(seq 1 18); do
    CONTAINER=$(docker ps --filter name=app --format '{{.ID}}' | head -1)
    STATUS=$(docker inspect "$CONTAINER" --format '{{.State.Health.Status}}' 2>/dev/null || echo "starting")
    [ "$STATUS" = "healthy" ] && break
    sleep 10
done

if [ -n "$CONTAINER" ] && docker inspect "$CONTAINER" --format '{{.State.Health.Status}}' | grep -q healthy; then
    info "NOMAD app is healthy"
else
    warn "App might still be starting. Check with: docker compose ps"
fi

# Reload nginx to pick up new upstream
docker exec nomad_oasis_proxy nginx -s reload 2>/dev/null || true

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Log into https://researchmcp.duckdns.org/nomad-oasis/gui/"
echo "  2. PUBLISH → Uploads → CREATE FROM SCHEMA"
echo "  3. You should see: elabFTW Settings, elabFTW Linked Entry"
echo "  4. Create 'elabFTW Settings' entry with your API key (one-time)"
echo "  5. Create 'elabFTW Linked Entry' with an experiment ID"
echo ""
echo "User guide: https://researchmcp.duckdns.org/nomad-oasis/docs/elabftw/user-guide.html"
echo "GitHub repo: https://github.com/harrytyp/econversion-nomad"

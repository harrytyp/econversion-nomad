# econversion-NOMAD

Bidirectional elabFTW ↔ NOMAD integration for NOMAD Oasis.

**Uses the official NOMAD image.** No custom Docker build needed.
Updates work via `docker compose pull`.

## One-Click Setup

```bash
git clone https://github.com/harrytyp/econversion-nomad.git
cd econversion-nomad
bash setup.sh
```

This clones the distro template, downloads plugins, patches configs,
and restarts NOMAD with the bridge enabled.

## What's in the Repo

| Path | Purpose |
|------|---------|
| `setup.sh` | **One-click installer** — run on a fresh NOMAD Oasis server |
| `scripts/patch-nomad-distro.py` | Patches docker-compose.yaml for the bridge |
| `plugins/startup.sh` | Runs at container boot, installs plugins |
| `plugins/three_way_sync/` | **Bidirectional bridge** — normalizer, schemas, webhook |
| `plugins/three_way_nomad_bridge.egg-info/` | NOMAD entry point registration |
| `plugins/elabftw_linker/` | Legacy (simple cross-referencing) |
| `docs/installation/` | Oasis deployment + plugin install guides |
| `docs/elabftw-integration/` | User guides + architecture docs |
| `docs/instrument-automation/` | **Instrument booking & data pipeline** (TGA, DMA, FTIR, MS) |
| `docs/ATTRIBUTION.md` | FAIRmat vs custom code credits |

## How It Works

The bridge runs **inside NOMAD** via a startup script (`startup.sh`) that:
1. Installs the FAIRmat `nomad-external-eln-integrations` base plugin
2. Registers the custom `three_way_sync` package as a NOMAD schema plugin
3. Deploys the user guide to NOMAD's static docs

Users then see two new schemas in CREATE FROM SCHEMA:

- **"elabFTW Settings"** — set your personal API key once (private entry)
- **"elabFTW Linked Entry"** — link any elabFTW experiment or item to NOMAD

The normalizer auto-links bidirectionally: NOMAD URL → elabFTW extra fields.

## User Guide

- **HTML** (on your NOMAD instance): [researchmcp.duckdns.org/nomad-oasis/docs/elabftw/user-guide.html](https://researchmcp.duckdns.org/nomad-oasis/docs/elabftw/user-guide.html)
- **Markdown** (in this repo): [`docs/elabftw-integration/03-user-guide.md`](docs/elabftw-integration/03-user-guide.md)

## Architecture

```
elabFTW (elntest.ub.tum.de)          NOMAD Oasis (Docker)
  │                                         │
  │  API /api/v2/                           │  startup.sh installs plugins
  │                                         │
  │  ┌─────────────────────────────────┐    │
  │  │   startup.sh at container boot  │    │
  │  │   ├── pip installs FAIRmat      │    │
  │  │   ├── egg-info registers schema │    │
  │  │   └── .pth adds plugin path     │    │
  │  └─────────────────────────────────┘    │
  │                                         │
  ▼                                         ▼
DataTagger (datatagger.ub.tum.de)
```

## Updating NOMAD

Since the official image is used, updates are standard:

```bash
cd ~/nomad-distro-template
git pull                         # latest distro template
docker compose pull              # latest NOMAD image
docker compose up -d             # restart with startup.sh
```

## Links

- User guide (live): [researchmcp.duckdns.org/nomad-oasis/docs/elabftw/user-guide.html](https://researchmcp.duckdns.org/nomad-oasis/docs/elabftw/user-guide.html)
- NOMAD Oasis: [researchmcp.duckdns.org/nomad-oasis/gui/](https://researchmcp.duckdns.org/nomad-oasis/gui/)
- elabFTW instance: [elntest.ub.tum.de](https://elntest.ub.tum.de/)
- FAIRmat plugin: [nomad-external-eln-integrations](https://github.com/FAIRmat-NFDI/nomad-external-eln-integrations)

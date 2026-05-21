# econversion-NOMAD

NOMAD Oasis deployment and elabFTW integration for the econversion project.

## Repository Contents

| Path | What | Author |
|------|------|--------|
| `docs/installation/` | NOMAD Oasis deployment guide + elabFTW plugin install | **Original** — written for this project |
| `docs/elabftw-integration/` | Connection guide + user guide for elabFTW links | **Original** — written for this project |
| `docs/ATTRIBUTION.md` | Third-party code credits and licenses | Required reading |
| `plugins/elabftw_linker/` | Custom NOMAD plugin for dynamic elabFTW linking | **Original** — written for this project |

## Quick Links

- [NOMAD Oasis Deployment Guide](docs/installation/01-oasis-deployment.md) — Full server setup, RAM/swap/Caddy
- [elabFTW Plugin Installation](docs/installation/02-elabftw-plugin-install.md) — Adding elabFTW to the Oasis
- [elabFTW Connection Guide](docs/elabftw-integration/02-elabftw-connection-guide.md) — API setup
- [User Guide](docs/elabftw-integration/03-user-guide.md) — Using elabFTW-NOMAD links
- [Attribution](docs/ATTRIBUTION.md) — What's original vs third-party

## Architecture

```
researchmcp.duckdns.org
│
├── Caddy (reverse proxy)    ─── HTTPS → /nomad-oasis/*
│   └── nginx (nomad proxy:80)
│       └── app:8000 (NOMAD)
│           ├── nomad-external-eln-integrations  (FAIRmat, Apache 2.0)
│           └── plugins/elabftw_linker/           (custom, MIT)
│
└── elabFTW instance (hosted, external)
    └── /api/v2/
```

## Deploy Status

- NOMAD v1.4.2, running on Debian 12, 3.8GB RAM + 10GB swap
- Behind Caddy at `researchmcp.duckdns.org`, integrated with MCP stack
- elabFTW base plugin installed + custom dynamic linker mounted

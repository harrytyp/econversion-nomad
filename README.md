# econversion-NOMAD

NOMAD Oasis deployment and bidirectional elabFTW ↔ NOMAD integration.

## Repository Contents

| Path | Description |
|------|-------------|
| `docs/installation/` | NOMAD Oasis deployment + elabFTW plugin install guide |
| `docs/elabftw-integration/` | Connection, user, and three-way sync guides |
| `plugins/elabftw_linker/` | **Legacy** — simple elabFTW cross-referencing |
| `plugins/three_way_sync/` | **Active** — bidirectional elabFTW ↔ NOMAD bridge |

## Quick Links

- [NOMAD Oasis Deployment](docs/installation/01-oasis-deployment.md)
- [elabFTW Plugin Install](docs/installation/02-elabftw-plugin-install.md)
- [Three-Way Sync Architecture](docs/elabftw-integration/04-three-way-sync.md)

## Architecture

```
elabFTW (elntest.ub.tum.de)          NOMAD Oasis (researchmcp.duckdns.org)
  │                                         │
  │  API /api/v2/experiments/{id}           │  API /api/v1/
  │                                         │
  │  ┌─────────────────────────────────┐    │
  │  │   Three-Way Bridge (in NOMAD)   │    │
  │  │   ├── normalizer.py (auto-link) │    │
  │  │   ├── schema.py (ELN entries)   │    │
  │  │   └── webhook.py (click import) │    │
  │  └─────────────────────────────────┘    │
  │                                         │
  ▼                                         ▼
DataTagger (datatagger.ub.tum.de)
  API /api/v1/
```

## The Integration at a Glance

| Action | What happens |
|--------|-------------|
| elabFTW user clicks "Send to NOMAD" | Webhook creates NOMAD entry, links back |
| Machine uploads data to NOMAD | Normalizer auto-creates elabFTW experiment |
| NOMAD entry saved with external_id | Normalizer links to existing elabFTW experiment |
| elabFTW experiment updated | NOMAD URL appears in extra_fields |

All linking is bidirectional: both systems know about each other.

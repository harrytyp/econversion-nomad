# econversion-NOMAD

NOMAD Oasis configuration and elabFTW integration for the econversion project.

## Contents

| Path | Description |
|------|-------------|
| `docs/elabftw-integration/` | Full installation + user guides |
| `plugins/elabftw-linker/` | Custom NOMAD plugin for dynamic elabFTW linking |

## Quick Links

- [Installation Guide](docs/elabftw-integration/01-installation-guide.md) — How to install the elabFTW plugin on a NOMAD Oasis
- [Connection Guide](docs/elabftw-integration/02-elabftw-connection-guide.md) — How to connect your elabFTW instance
- [User Guide](docs/elabftw-integration/03-user-guide.md) — How users set up elabFTW-NOMAD links

## Architecture

```
NOMAD Oasis (Docker)           Hosted elabFTW
┌──────────────────┐          ┌──────────────┐
│  app:8000        │◄─API───►│  /api/v2     │
│  + elabFTW plugin│          │  experiments │
│  + custom linker │          └──────────────┘
└──────────────────┘
```

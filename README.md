# econversion-NOMAD

elabFTW to NOMAD Oasis integration. Turn your ELN into an instrument booking
system with automated data ingestion. All running on the official NOMAD image
(no custom Docker build).

---

## What Problem This Solves

| Role | Pain | Solution |
|------|------|----------|
| **Scientist** | Emailing parameters, USB sticks, manual data entry | Book instruments in elabFTW, fill structured templates, get results back automatically |
| **Operator** | Chasing people for missing info, manual file exports | See all queued jobs with pre-filled parameters, TRIOS auto-exports, pipeline handles the rest |
| **Admin** | Forked NOMAD images, brittle configs | Official NOMAD image only, plugins auto-install at boot via startup.sh, single repo as source of truth |

---

## What's in This Repo

### elabFTW to NOMAD Bridge (plugins/three_way_sync/)

Two-way linking between elabFTW experiments/items and NOMAD entries.
Create a linked entry in NOMAD, set your API key (stored privately), and
the normalizer auto-fetches experiment data and writes the NOMAD URL back
to elabFTW. Supports manual sync, auto-create, and webhook triggers.

### Instrument Booking & Automation (plugins/instrument_data/)

Four bookable instrument items (TGA, DMA, FTIR, MS) with matching experiment
templates in elabFTW. Working end-to-end pipeline for TGA:

```
User books TGA in elabFTW calendar
  creates experiment from TGA Measurement template (12 structured fields)
  sets status to Running

Operator loads autosampler, runs in TRIOS
  TRIOS auto-exports CSV/TXT to network folder

instrument_ingest.py detects file
  parses metadata + temperature/weight/DTA curves
  computes Tg, residue, mass loss steps, DTG peaks
  pushes results table + NOMAD link back to elabFTW
  sets status to Success
```

Same templates and items exist for DMA, FTIR, and MS.

### Scripts

| Script | Purpose |
|--------|---------|
| `setup.sh` | One-click installer for a fresh NOMAD Oasis |
| `scripts/instrument_ingest.py` | Watch folder / one-shot CSV/TXT processing |
| `scripts/patch-nomad-distro.py` | Patches docker-compose for plugin paths |
| `plugins/startup.sh` | Runs at every NOMAD container boot, installs all plugins |

---

## Quick Start

### For Scientists (book an instrument)

Open elabFTW at elntest.ub.tum.de, switch to the eConversion DataIntelligence
team, go to Database > Devices&Tools, pick an instrument, book a time slot,
then create an experiment from the matching template. Full walkthrough:
[docs/instrument-automation/USER_GUIDE.md](docs/instrument-automation/USER_GUIDE.md)

### For NOMAD Users (link experiments)

Log into NOMAD at researchmcp.duckdns.org/nomad-oasis/gui/, go to
PUBLISH > CREATE A NEW UPLOAD > CREATE FROM SCHEMA. Create an
"elabFTW Settings" entry with your API key (one time), then create
"elabFTW Linked Entry" entries to link experiments.
Guide: [docs/elabftw-integration/03-user-guide.md](docs/elabftw-integration/03-user-guide.md)

### For Admins (deploy from scratch)

```bash
git clone https://github.com/harrytyp/econversion-nomad.git
cd econversion-nomad
bash setup.sh
```

The setup script clones the NOMAD distro template, patches configs, and
prepares plugins. On container boot, startup.sh auto-installs everything
into the official NOMAD image. Setup guide:
[docs/installation/01-oasis-deployment.md](docs/installation/01-oasis-deployment.md)

---

## Documentation

| Document | Audience |
|----------|----------|
| [USER_GUIDE.md](docs/instrument-automation/USER_GUIDE.md) | Scientists + operators: step-by-step with status badges |
| [03-user-guide.md](docs/elabftw-integration/03-user-guide.md) | NOMAD users: linking experiments to elabFTW |
| [01-workflow-overview.md](docs/instrument-automation/01-workflow-overview.md) | Full A-to-Z system flow |
| [02-infrastructure.md](docs/instrument-automation/02-infrastructure.md) | Server, Docker, Caddy, MCP services |
| [03-elabftw-templates.md](docs/instrument-automation/03-elabftw-templates.md) | Instrument items and template field listings |
| [05-data-pipeline.md](docs/instrument-automation/05-data-pipeline.md) | Parser architecture and CSV/TXT format |
| [01-installation-guide.md](docs/elabftw-integration/01-installation-guide.md) | Bridge plugin installation |

---

## Links

| Service | URL |
|---------|-----|
| elabFTW | [elntest.ub.tum.de](https://elntest.ub.tum.de) |
| NOMAD Oasis | [researchmcp.duckdns.org/nomad-oasis/gui/](https://researchmcp.duckdns.org/nomad-oasis/gui/) |
| elab-app Logger | [elab-app.researchmcp.duckdns.org](https://elab-app.researchmcp.duckdns.org) |
| MCP Registration | [researchmcp.duckdns.org](https://researchmcp.duckdns.org) |
| FAIRmat bridge plugin | [github.com/FAIRmat-NFDI/nomad-external-eln-integrations](https://github.com/FAIRmat-NFDI/nomad-external-eln-integrations) |

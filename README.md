# econversion-NOMAD

**elabFTW ↔ NOMAD Oasis integration** — bidirectional bridge, structured data sync,
and automated instrument measurement pipeline.

Uses the **official NOMAD image** — no custom Docker build, updates via `docker compose pull`.

---

## What This Repo Does

### Core: elabFTW ↔ NOMAD Bridge

Two-way linking between elabFTW experiments and NOMAD entries:

| Direction | How |
|-----------|-----|
| **elabFTW → NOMAD** | Create a `ElabftwLinkedEntry` in NOMAD, set your API key → auto-fetches experiment data, stores NOMAD URL back in elabFTW |
| **NOMAD → elabFTW** | Create an experiment in elabFTW → the NOMAD normalizer detects it and creates a linked NOMAD entry with structured metadata |

Works for both experiments and database items (resources). API key is stored in a
private `ElabftwSettings` entry — only you can see it.

### Feature: Instrument Measurement Automation

Built on top of the bridge — turns elabFTW into a full instrument management system
for TGA, DMA, FTIR, and MS measurements:

```
User books instrument  →  creates experiment from template  →  
TRIOS auto-exports CSV  →  NOMAD parses curves  →  
results pushed back to elabFTW experiment
```

[Full user guide →](docs/instrument-automation/USER_GUIDE.md)

---

## Quick Start

### For Users (instrument booking + results)

Just use elabFTW at [elntest.ub.tum.de](https://elntest.ub.tum.de).
Detailed walkthrough: [`docs/instrument-automation/USER_GUIDE.md`](docs/instrument-automation/USER_GUIDE.md)

### For the elabFTW Bridge

1. Log into NOMAD at [researchmcp.duckdns.org/nomad-oasis/gui/](https://researchmcp.duckdns.org/nomad-oasis/gui/)
2. **CREATE FROM SCHEMA → "elabFTW Settings"** — set your API key once
3. **CREATE FROM SCHEMA → "elabFTW Linked Entry"** — link any experiment or item

Your key stays private (only you can see your Settings entry). The normalizer
auto-links bidirectionally on save.

### For Deployers (new NOMAD Oasis)

```bash
git clone https://github.com/harrytyp/econversion-nomad.git
cd econversion-nomad
bash setup.sh
```

Clones the distro template, patches configs, installs plugins. No manual steps.

---

## What's in the Repo

### Plugins (auto-installed into NOMAD at container boot)

| Plugin | What it adds to NOMAD |
|--------|----------------------|
| [`plugins/three_way_sync/`](plugins/three_way_sync/) | **elabFTW Bridge** — `ElabftwLinkedEntry`, `ElabftwSettings` schemas + bidirectional normalizer + webhook support |
| [`plugins/instrument_data/`](plugins/instrument_data/) | **Instrument measurement schemas** — `TgaMeasurement`, `DmaMeasurement`, `FtrMeasurement`, `MsMeasurement` entry types for structured instrument data |

Both are installed via [`plugins/startup.sh`](plugins/startup.sh) which runs at
every NOMAD container boot. No changes to the official NOMAD image needed.

### Scripts

| Script | What it does |
|--------|-------------|
| [`setup.sh`](setup.sh) | One-click installer for a fresh NOMAD Oasis server |
| [`scripts/instrument_ingest.py`](scripts/instrument_ingest.py) | **TRIOS export pipeline** — watches a folder for CSV/TXT files, parses metadata + curves, computes results, pushes back to elabFTW |
| [`scripts/patch-nomad-distro.py`](scripts/patch-nomad-distro.py) | Patches docker-compose for bridge plugin paths |

### Documentation

| Document | Covers |
|----------|--------|
| [`docs/elabftw-integration/03-user-guide.md`](docs/elabftw-integration/03-user-guide.md) | elabFTW Bridge — user-facing setup guide (HTML version deployed to NOMAD) |
| [`docs/elabftw-integration/01-installation-guide.md`](docs/elabftw-integration/01-installation-guide.md) | Bridge plugin installation |
| [`docs/elabftw-integration/02-elabftw-connection-guide.md`](docs/elabftw-integration/02-elabftw-connection-guide.md) | elabFTW API connection setup |
| [`docs/elabftw-integration/04-three-way-sync.md`](docs/elabftw-integration/04-three-way-sync.md) | DataTagger integration |
| [`docs/instrument-automation/USER_GUIDE.md`](docs/instrument-automation/USER_GUIDE.md) | **Instrument automation** — step-by-step for scientists & operators |
| [`docs/instrument-automation/`](docs/instrument-automation/) | Full A-to-Z flow, infrastructure, templates, data pipeline |

---

## Architecture Overview

```
elabFTW (elntest.ub.tum.de)
  │
  ├── experiments + items (resources)
  │
  ├── elabFTW Bridge (three_way_sync plugin)
  │   ├── bidirectional linking via normalizer
  │   ├── per-user API keys (ElabftwSettings)
  │   └── auto-sync on save
  │
  ├── Instrument Automation (instrument_data plugin + ingest script)
  │   ├── 4 bookable instrument items (TGA, DMA, FTIR, MS)
  │   ├── 4 experiment templates with structured extra_fields
  │   ├── TRIOS auto-export → watch folder → parser → compute
  │   └── results pushed back to experiment body + metadata
  │
  └── NOMAD Oasis (researchmcp.duckdns.org)
      ├── EntryData schemas for structured instrument data
      └── DOI-ready archiving
```

## Instrument Templates

| Template | ID | Fields | Purpose |
|----------|----|--------|---------|
| TGA Measurement | 175 | 12 | Thermogravimetric analysis |
| DMA Measurement | 176 | 12 | Dynamic mechanical analysis |
| FTIR Measurement | 177 | 9 | Fourier-transform infrared spectroscopy |
| MS Measurement | 178 | 9 | Mass spectrometry |

Each template uses elabFTW's `extra_fields` system — structured metadata, not
free-text, so NOMAD can read them programmatically.

## Automation Status

| Step | Status |
|------|--------|
| elabFTW ↔ NOMAD bridge | ✅ Live |
| Instrument items + booking | ✅ Live (4 items, bookable) |
| Experiment templates | ✅ Live (4 templates with extra_fields) |
| CSV/TXT parser | ✅ Live (TGA + DMA tested on real data) |
| Results computation | ✅ Live (Tg, residue, DTG peaks, mass loss steps) |
| elabFTW push-back | ✅ Live (body + metadata + status) |
| NOMAD entry creation | 🔴 Planned |
| Summary plot generation | 🔴 Planned |
| .TRPC method auto-generation | 🔴 Planned |

## Links

- [elabFTW instance](https://elntest.ub.tum.de)
- [NOMAD Oasis](https://researchmcp.duckdns.org/nomad-oasis/gui/)
- [elab-app Logger](https://elab-app.researchmcp.duckdns.org)
- [Landing Page (MCP registration)](https://researchmcp.duckdns.org)
- [FAIRmat elabFTW plugin](https://github.com/FAIRmat-NFDI/nomad-external-eln-integrations)

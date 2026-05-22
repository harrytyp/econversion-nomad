# econversion-NOMAD

**elabFTW ↔ NOMAD Oasis integration + automated instrument data pipeline.**

This repo turns elabFTW into a full instrument booking and measurement management
system. Scientists book instruments and fill parameters in elabFTW → TRIOS exports
data automatically → NOMAD parses curves and pushes results back into elabFTW.

All running on a vanilla NOMAD Oasis — **no custom Docker build**, no forked images.

---

## What You Can Do

### 🔬 As a Scientist

| You want to... | How it works |
|---|---|
| **Book instrument time** | Open elabFTW → Database → Devices&Tools → pick TGA/DMA/FTIR/MS → book a slot |
| **Submit a measurement request** | Create experiment from template (e.g. "TGA Measurement"), fill all parameters (sample mass, temperature range, gas, etc.) |
| **Track your sample** | Set status to "Running" → operator sees your pre-filled request in the queue |
| **Get results automatically** | After measurement, your elabFTW experiment gets a results table + NOMAD link — no manual data wrangling |

**Time investment**: ~20 minutes per measurement request. No paper forms, no emails, no USB sticks.

### 🔧 As an Operator

| You want to... | How it works |
|---|---|
| **See what's queued** | Open elabFTW → filter experiments by status "Running" — all parameters are pre-filled |
| **Load and run** | Physical sample goes in the autosampler → start TRIOS measurement |
| **Never export manually** | TRIOS auto-exports CSV/TXT to a network folder — the pipeline picks it up |
| **Results are delivered** | No need to chase users — results appear in their experiment automatically |

**Time investment**: ~8 minutes per run for setup. The rest is automatic.

### 🤖 What Runs Automatically

| Step | What happens |
|---|---|
| 1. TRIOS auto-export | After measurement, CSV/TXT lands in watch folder |
| 2. File detection | `instrument_ingest.py watch` detects new files |
| 3. Parsing | Metadata + signal curves extracted (70+ fields, 6000+ data points) |
| 4. Computation | TGA: Tg, residue, onset, mass loss steps / DMA: Tg from tan delta |
| 5. elabFTW push-back | Experiment body updated with results table, status set to "Success" |

**What's coming next**: NOMAD entry creation with DOI-ready structured data + interactive plots.

---

## Quick Start

### For Users

No installation needed — just use elabFTW at [elntest.ub.tum.de](https://elntest.ub.tum.de).
Full walkthrough: [`docs/instrument-automation/USER_GUIDE.md`](docs/instrument-automation/USER_GUIDE.md)

### For Deployers

```bash
git clone https://github.com/harrytyp/econversion-nomad.git
cd econversion-nomad
bash setup.sh
```

This clones the distro template, installs the elabFTW bridge plugin, and patches configs.
The `startup.sh` inside the container auto-installs all schema plugins at boot.

---

## What's in the Repo

### 📦 Plugins (auto-installed into NOMAD at boot)

| Plugin | What it adds to NOMAD |
|--------|----------------------|
| [`plugins/three_way_sync/`](plugins/three_way_sync/) | **elabFTW ↔ NOMAD bridge** — bidirectional linking, auto-sync, webhook support |
| [`plugins/instrument_data/`](plugins/instrument_data/) | **Instrument measurement schemas** — `TgaMeasurement`, `DmaMeasurement`, `FtrMeasurement`, `MsMeasurement` entry types in CREATE FROM SCHEMA |

### 📜 Scripts

| Script | What it does |
|--------|-------------|
| [`setup.sh`](setup.sh) | One-click installer for a fresh NOMAD Oasis server |
| [`scripts/instrument_ingest.py`](scripts/instrument_ingest.py) | **Watch folder + parse + push-back** — the core automation pipeline. Run it once (`process`) or continuously (`watch`). |
| [`scripts/patch-nomad-distro.py`](scripts/patch-nomad-distro.py) | Patches the NOMAD distro docker-compose for the bridge |

### 📖 Documentation

| Document | Who it's for |
|----------|-------------|
| [`docs/instrument-automation/USER_GUIDE.md`](docs/instrument-automation/USER_GUIDE.md) | **Scientists + Operators** — step-by-step with automation status badges |
| [`docs/instrument-automation/01-workflow-overview.md`](docs/instrument-automation/01-workflow-overview.md) | Complete A-to-Z system flow |
| [`docs/instrument-automation/02-infrastructure.md`](docs/instrument-automation/02-infrastructure.md) | Server architecture, Docker, Caddy, MCP services |
| [`docs/instrument-automation/03-elabftw-templates.md`](docs/instrument-automation/03-elabftw-templates.md) | All 4 instrument items + 4 experiment templates with exact field listings |
| [`docs/instrument-automation/05-data-pipeline.md`](docs/instrument-automation/05-data-pipeline.md) | Parser architecture, NOMAD schemas, CSV/TXT format |
| [`docs/elabftw-integration/`](docs/elabftw-integration/) | Bridge plugin user guide (Markdown + HTML) |

---

## Architecture (the 30-second version)

```
elabFTW (elntest.ub.tum.de)
  │
  ├── 4 bookable instrument items (TGA, DMA, FTIR, MS)  ← Book here
  ├── 4 experiment templates with 9-12 structured fields ← Fill params here
  │
  ▼ TRIOS auto-exports CSV/TXT
  │
instrument_ingest.py  ← Detects, parses, computes
  │
  ├── PATCH → elabFTW experiment (results table + status = Success)
  └── POST → NOMAD entry      (structured data, DOI-ready) [planned]
```

## Key Design Decisions

- **Official NOMAD image only** — no custom fork, updates via `docker compose pull`
- **Per-request credential injection** (elabMCP) — no shared API keys, no persistent storage
- **All automation in Python** — no new services, runs in existing containers or as a simple cron
- **Structured metadata from the start** — extra_fields not free-text, so NOMAD can read them programmatically

## Instrument Templates

| Template | ID | Fields | Select options |
|----------|----|--------|---------------|
| TGA Measurement | 175 | 12 | crucible_type, gas_atmosphere |
| DMA Measurement | 176 | 12 | clamp_type |
| FTIR Measurement | 177 | 9 | sample_state |
| MS Measurement | 178 | 9 | ionization_method |

Each template includes a body with workflow instructions and a pre-formatted HTML results table.

## Links

- [elabFTW instance](https://elntest.ub.tum.de)
- [NOMAD Oasis](https://researchmcp.duckdns.org/nomad-oasis/gui/)
- [elab-app Logger](https://elab-app.researchmcp.duckdns.org)
- [Landing Page](https://researchmcp.duckdns.org)
- [FAIRmat elabFTW plugin](https://github.com/FAIRmat-NFDI/nomad-external-eln-integrations)

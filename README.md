# econversion-NOMAD

Three things this repo makes work:

**① Device booking + instrument automation** — book instruments in elabFTW, auto-parse results back. Working example: TGA (TA Waters / TRIOS).

**② elabFTW ↔ NOMAD bridge** — bidirectional linking, structured sync, per-user API keys.

**③ Machine data upload pipeline** — auto-import from instruments into elabFTW + NOMAD.

---

## ① Device Booking & Instrument Automation

Turn elabFTW into a lab instrument manager. Users book time slots, fill structured
parameters, and get results back automatically — no USB sticks, no Excel, no chasing.

### Working Example: TGA (TA Waters / TRIOS)

```
User books TGA in elabFTW calendar
  → creates experiment from "TGA Measurement" template
  → fills 12 parameters (mass, crucible, temp, gas, etc.)
  → sets status = "Running"
  
Operator reviews queue → loads autosampler → runs in TRIOS
  → TRIOS auto-exports CSV/TXT to network folder
  
Pipeline (instrument_ingest.py):
  → detects file → parses metadata + temperature/weight/DTA curves
  → computes Tg, residue, mass loss steps, onset, DTG peaks
  → pushes results table + NOMAD link back to elabFTW experiment
  → sets status = "Success"
```

Same pattern works for DMA, FTIR, and MS (templates + items already set up).

**What's running:**

| What | Where |
|------|-------|
| 4 bookable instrument items | elabFTW → eConversion team → Devices&Tools |
| 4 experiment templates (9–12 fields each) | elabFTW → Create from template |
| CSV/TXT parser + computation engine | [`plugins/instrument_data/parser.py`](plugins/instrument_data/parser.py) |
| Watch folder + push-back script | [`scripts/instrument_ingest.py`](scripts/instrument_ingest.py) |
| NOMAD schemas (TgaMeasurement, etc.) | [`plugins/instrument_data/schema.py`](plugins/instrument_data/schema.py) |

[Full walkthrough for users & operators →](docs/instrument-automation/USER_GUIDE.md)

---

## ② elabFTW ↔ NOMAD Bridge

Two-way linking between elabFTW experiments/items and NOMAD entries.

| You want to... | Do this in NOMAD |
|---|---|
| Link an elabFTW experiment to NOMAD | CREATE FROM SCHEMA → "elabFTW Linked Entry", fill experiment ID → save. Normalizer auto-fetches title and writes NOMAD URL back into elabFTW. |
| Set your API key once | CREATE FROM SCHEMA → "elabFTW Settings" — private, only you see it. Automatically picked up by all your linked entries. |
| Sync manually | Toggle "sync_now" on any linked entry → triggers fetch + link-back. |
| Create an elabFTW experiment from NOMAD | Toggle "create_elabftw_experiment" → normalizer creates it and links back. |

The bridge works through [`plugins/three_way_sync/`](plugins/three_way_sync/) — a
NOMAD normalizer that runs inside the official NOMAD image (no custom fork).

**Per-user API keys:** Each user stores their key in a private `ElabftwSettings`
entry. The normalizer finds it automatically. Keys are never shared or stored
in config files.

---

## ③ Machine Data Upload Pipeline

Get data from instruments into elabFTW + NOMAD without manual file handling.

### Export from machine → watch folder

Supported instruments:

| Instrument | Export format | Auto-export? | Status |
|---|---|---|---|
| TGA (TA Waters / TRIOS) | CSV / TXT | ✅ Checkbox in TRIOS SW Options | 🟡 Tested with real files |
| DMA (TA Waters / TRIOS) | CSV / TXT | ✅ Same as TGA | 🟡 Tested with real files |
| FTIR | .DAT | Manual | 🟡 Tested sample file |
| MS | .TXT / .BIN | Manual | 🔴 Parser planned |

### Pipeline flow

```
CSV/TXT lands in /home/debian/instrument-exports/
  → instrument_ingest.py watch detects new file
  → parser extracts metadata (sample, mass, operator, method, ...)
  → parser extracts signal data (temperature, weight, modulus, ...)
  → computes derived quantities (Tg, DTG peaks, residue, ...)
  → PATCHes elabFTW experiment body + metadata + status=Success
  → (planned) creates NOMAD entry with structured schema
```

[Parser format documentation →](docs/instrument-automation/05-data-pipeline.md)

---

## Quick Start

### For Bookers & Instrument Users

Open [elntest.ub.tum.de](https://elntest.ub.tum.de) → eConversion team → book instrument
from Devices&Tools → create experiment from template. Full guide:
[`docs/instrument-automation/USER_GUIDE.md`](docs/instrument-automation/USER_GUIDE.md)

### For NOMAD ↔ elabFTW Linking

Log into [researchmcp.duckdns.org/nomad-oasis/gui/](https://researchmcp.duckdns.org/nomad-oasis/gui/) →
CREATE FROM SCHEMA → "elabFTW Settings" (one-time) → "elabFTW Linked Entry" (per experiment).
Detailed: [`docs/elabftw-integration/03-user-guide.md`](docs/elabftw-integration/03-user-guide.md)

### For Deployers

```bash
git clone https://github.com/harrytyp/econversion-nomad.git
cd econversion-nomad
bash setup.sh
```

All plugins auto-install at NOMAD container boot via [`plugins/startup.sh`](plugins/startup.sh).
No custom Docker image needed — uses the official `fairmat/nomad-distro-template`.

---

## What's in the Repo

| Path | What it does |
|------|-------------|
| [`plugins/three_way_sync/`](plugins/three_way_sync/) | **Bridge** — elabFTW ↔ NOMAD normalizer, schemas, webhook |
| [`plugins/instrument_data/`](plugins/instrument_data/) | **Instrument automation** — TGA/DMA/FTIR/MS schemas, CSV parser, elabFTW push-back client |
| [`scripts/instrument_ingest.py`](scripts/instrument_ingest.py) | **Pipeline runner** — watch folder / one-shot processing |
| [`setup.sh`](setup.sh) | One-click NOMAD Oasis setup |
| [`plugins/startup.sh`](plugins/startup.sh) | Container boot hook — installs all plugins |
| [`docs/instrument-automation/`](docs/instrument-automation/) | Booking + pipeline docs + USER_GUIDE |
| [`docs/elabftw-integration/`](docs/elabftw-integration/) | Bridge user guides (HTML deployed to NOMAD) |

## Links

| Service | URL |
|---------|-----|
| elabFTW | [elntest.ub.tum.de](https://elntest.ub.tum.de) |
| NOMAD Oasis | [researchmcp.duckdns.org/nomad-oasis/gui/](https://researchmcp.duckdns.org/nomad-oasis/gui/) |
| elab-app Logger | [elab-app.researchmcp.duckdns.org](https://elab-app.researchmcp.duckdns.org) |
| MCP Registration | [researchmcp.duckdns.org](https://researchmcp.duckdns.org) |
| FAIRmat bridge plugin | [nomad-external-eln-integrations](https://github.com/FAIRmat-NFDI/nomad-external-eln-integrations) |

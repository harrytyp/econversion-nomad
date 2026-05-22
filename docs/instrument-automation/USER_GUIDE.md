# Instrument Measurement Workflow: User & Operator Guide

> **eConversion DataIntelligence** — elabFTW + NOMAD Oasis

---

## Overview

```
   USER (Scientist)                    OPERATOR (Technician)
   ═══════════════                    ═════════════════════
                                       
   ① Book instrument ──────────►   ② Review queue
   (calendar on item page)             
                                       
   ③ Create experiment ─────────►   ④ Load sample in autosampler
   (from template, fill params)        
                                       
   ⑤ Bring sample to lab ───────►   ⑥ Accept request
                                       
                                     ⑦ Run measurement
                                     (TRIOS auto-exports)
                                       
                                     ⑧ Results appear in elabFTW
   ⑨ Open experiment ◄───────────   (body + chart + NOMAD link)
       see results inline
```

---

## Step-by-Step

### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### PHASE 1: Setup (one time only)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#### ① Get Access to elabFTW

| 👤 **USER** | 👷 **OPERATOR** |
|---|---|
| Email Kolja to get an elabFTW account in the **eConversion DataIntelligence** team. | (Already has an account) |
| Open https://elntest.ub.tum.de and log in. | |

---

### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### PHASE 2: Request a Measurement
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#### ② Book the Instrument

| 👤 **USER** | 👷 **OPERATOR** |
|---|---|
| 1. Go to **Database → Devices&Tools** | |
| 2. Pick the instrument you need: | |
|    🟢 **TGA (TA Waters / TRIOS)** | |
|    🟢 **DMA (TA Waters / TRIOS)** | |
|    🟢 **FTIR Spectrometer** | |
|    🟢 **Mass Spectrometer** | |
| 3. Click the **Booking** tab | |
| 4. Select a free time slot on the calendar | |
| 5. Confirm your booking | |
| ✅ **Done: Your time slot is reserved** | |

> ⏰ **Booking rules**: 8 hours max per slot, up to 60 days in advance, no overlapping bookings.

#### ③ Create the Experiment

| 👤 **USER** | 👷 **OPERATOR** |
|---|---|
| 1. Click **Create experiment from template** | |
| 2. Choose the matching template: | |
|    — **TGA Measurement** (if you booked TGA) | |
|    — **DMA Measurement** (if you booked DMA) | |
|    — **FTIR Measurement** (if you booked FTIR) | |
|    — **MS Measurement** (if you booked MS) | |
| 3. Fill in ALL measurement parameters: | |

**TGA Example:**
```
Sample Name:        Polymer-X
Sample Mass [mg]:   12.5
Crucible Type:      Alumina
Temperature Start:  30 °C
Temperature End:    600 °C
Heating Rate:       10 K/min
Gas Atmosphere:     N2
Gas Flow Rate:      50 mL/min
Autosampler Pos:    5
Notes:              Thermal stability test
```

| 👤 **USER** | 👷 **OPERATOR** |
|---|---|
| 4. Click **Link to item** → select the instrument you booked | |
| 5. Set experiment status to **"Running"** | |
| ✅ **Done: Your request is in the queue** | |

> 📌 **Important**: Fill all fields. The operator needs the parameters to set up the instrument. Missing fields cause delays.

#### ④ Bring Your Sample

| 👤 **USER** | 👷 **OPERATOR** |
|---|---|
| 1. Prepare your sample (dry, weigh if needed) | |
| 2. Label it clearly with: | |
|    — **Sample name** (from experiment) | |
|    — **Experiment ID** (from elabFTW) | |
| 3. Place it in the designated **lab drop-off** location | |
| ✅ **Your part is done. Wait for results.** | |

---

### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### PHASE 3: Execute the Measurement
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#### ⑤ Review the Queue

| 👤 **USER** | 👷 **OPERATOR** |
|---|---|
| *(waiting)* | 1. Open **elabFTW → Experiments** |
| | 2. Filter by: **Status = "Running"** |
| | 3. Scan through the list — each experiment shows: |
| |    — 📋 Sample name + all parameters pre-filled |
| |    — 📅 Booked time slot |
| |    — 📍 Autosampler position |
| | ✅ **You see exactly what to do — no paper needed** |

#### ⑥ Load the Sample

| 👤 **USER** | 👷 **OPERATOR** |
|---|---|
| | 1. Pick up the physical sample from the drop-off |
| | 2. Load it into the **autosampler** at the position |
| |    specified in the experiment parameters |
| | 3. Tare the pan (if using autosampler) |

#### ⑦ Accept the Request

| 👤 **USER** | 👷 **OPERATOR** |
|---|---|
| | 1. In the experiment, change status to: |
| |    **"Accepted"** (or similar in-progress status) |
| | 2. This confirms: ✅ Sample loaded ✅ Ready to run |

#### ⑧ Run the Measurement

| 👤 **USER** | 👷 **OPERATOR** |
|---|---|
| | 1. Open **TRIOS software** on the instrument PC |
| | 2. Set up the method using the parameters from elabFTW |
| |    *(future: NOMAD auto-generates the .TRPC method file)* |
| | 3. Start the measurement |
| | 4. TRIOS auto-exports **CSV/TXT** to the network folder |
| | ✅ **Measurement is running. Results will be processed automatically.** |

---

### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### PHASE 4: Automatic Processing
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Step | What happens | Who |
|---|---|---|
| ⑨ | TRIOS exports CSV/TXT to network folder | 🤖 Software |
| ⑩ | Watch folder detects new file | 🤖 Server |
| ⑪ | Parser reads metadata + signal data | 🤖 NOMAD |
| ⑫ | Computes results (Tg, residue, steps, etc.) | 🤖 NOMAD |
| ⑬ | Creates NOMAD entry with structured data | 🤖 NOMAD |
| ⑭ | Generates summary plot | 🤖 NOMAD |
| ⑮ | Pushes results back to elabFTW experiment | 🤖 NOMAD |

**No manual work needed.** The pipeline runs automatically.

---

### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### PHASE 5: Get Your Results
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#### ⑯ See Results in elabFTW

| 👤 **USER** | 👷 **OPERATOR** |
|---|---|
| 1. Open your experiment in elabFTW | |
|    *(refresh if it was already open)* | |
| 2. You'll see: | |

```
┌────────────────────────────────────────────────┐
│  TGA Results: Polymer-X                        │
├────────────────────────────────────────────────┤
│  Property              │ Value                 │
├────────────────────────┼───────────────────────┤
│  Tg (glass transition) │ 125.3 °C              │
│  Residue               │ 2.1 %                 │
│  Onset temperature     │ 320.0 °C              │
│  Td5 (5% mass loss)   │ 350.0 °C              │
│  Td10 (10% mass loss) │ 410.0 °C              │
├────────────────────────┴───────────────────────┤
│  Mass Loss Steps                               │
├──────────┬──────────┬───────────┬──────────────┤
│  Onset   │ Offset   │ Mass Loss │ Assignment   │
├──────────┼──────────┼───────────┼──────────────┤
│  30 °C   │ 150 °C   │ 3.2 %     │ moisture     │
│  350 °C  │ 500 °C   │ 68.4 %    │ degradation  │
│  500 °C  │ 800 °C   │ 26.3 %    │ carbonization│
└──────────┴──────────┴───────────┴──────────────┘

📊 [TG + DTG plot]

🔗 NOMAD Entry: https://researchmcp.duckdns.org/...

✅ Status: Success
```

| 👤 **USER** | 👷 **OPERATOR** |
|---|---|
| 3. Click the NOMAD link for: | |
|    — Full structured data | |
|    — Raw curves (downloadable) | |
|    — DOI-ready citation | |
|    — Share with collaborators | |
| ✅ **Done! Your measurement is complete.** | |

---

## Summary: What Each Person Does

### 👤 User (Scientist)
```
① Book instrument in calendar     (5 minutes)
② Create experiment from template (5 minutes)
③ Fill measurement parameters     (5 minutes)
④ Bring sample to lab             (5 minutes)
⑤ Read results in elabFTW         (5 minutes)
                                  ─────────
                    Total effort: ~20 minutes
```

### 👷 Operator (Technician)
```
① Review queue in elabFTW         (2 minutes)
② Load sample + autosampler       (5 minutes)
③ Accept request                  (1 minute)
④ Run measurement in TRIOS        (setup time)
⑤ Results process automatically   (0 minutes)
                                  ─────────
                    Total effort: ~8 minutes + run time
```

### 🤖 Automatic (Server)
```
① Detect new CSV/TXT file         (instant)
② Parse metadata + signals        (2 seconds)
③ Compute results                 (1 second)
④ Create NOMAD entry              (1 second)
⑤ Push back to elabFTW            (1 second)
                                  ─────────
                    Total effort: ~5 seconds
```

---

## Quick Reference: Links

| Action | Link |
|--------|------|
| elabFTW login | https://elntest.ub.tum.de |
| TGA Instrument (book) | https://elntest.ub.tum.de/database.php?mode=view&id=1367 |
| DMA Instrument (book) | https://elntest.ub.tum.de/database.php?mode=view&id=1368 |
| FTIR Instrument (book) | https://elntest.ub.tum.de/database.php?mode=view&id=1369 |
| MS Instrument (book) | https://elntest.ub.tum.de/database.php?mode=view&id=1370 |
| NOMAD Oasis | https://researchmcp.duckdns.org/nomad-oasis/gui/ |
| elab-app Logger | https://elab-app.researchmcp.duckdns.org |

## Templates Available

| Template | Parameters | Link |
|----------|-----------|------|
| TGA Measurement | 12 fields (mass, crucible, temp, gas, etc.) | Create experiment from template → eConversion team |
| DMA Measurement | 12 fields (geometry, clamp, temp, frequency, etc.) | Create experiment from template → eConversion team |
| FTIR Measurement | 9 fields (state, range, scans, resolution, etc.) | Create experiment from template → eConversion team |
| MS Measurement | 9 fields (ionization, mass range, solvent, etc.) | Create experiment from template → eConversion team |

## Status Flow

```
Planning (draft)
    │
    ▼
Running ──► Success (auto-parsed)
    │            │
    │            ▼
    │         NOMAD entry created
    │
    └──► Fail / Need to be redone
```

---

*Generated: May 22, 2026 — from the [econversion-nomad](https://github.com/harrytyp/econversion-nomad) repository*

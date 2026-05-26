#!/usr/bin/env python3
"""Mock TRIOS instrument run. Generates a realistic CSV/TXT export file from
elabFTW experiment parameters, as if the TGA instrument had just run.

Purpose: demonstrate the full A-to-Z pipeline without a physical instrument.

Usage:
    # Generate a mock TGA export from an existing elabFTW experiment
    python mock_trios_run.py --experiment 4689 --outdir /home/debian/instrument-exports/

    # Generate with random/default parameters (no elabFTW experiment needed)
    python mock_trios_run.py --outdir /tmp/mock-exports/

    # This creates a CSV file in the watch folder.
    # Then run: instrument_ingest.py watch /home/debian/instrument-exports/
    # to see the full pipeline (parse -> compute -> push back to elabFTW).
"""
from __future__ import annotations

import argparse
import csv
import io
import math
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add parent to path for plugin imports
_plugin_dir = Path(__file__).resolve().parent.parent / "plugins"
sys.path.insert(0, str(_plugin_dir))


# ── Realistic TGA signal generation ──────────────────────────────────────────

def generate_tga_signals(
    sample_name: str = "MockSample",
    sample_mass_mg: float = 12.5,
    temp_start: float = 30.0,
    temp_end: float = 1000.0,
    heating_rate: float = 10.0,
    gas: str = "N2",
    flow_rate: float = 50.0,
    crucible: str = "Alumina",
    operator: str = "MockOperator",
    noise_level: float = 0.002,
    seed: int = 42,
) -> Dict[str, Any]:
    """Generate synthetic TGA signal data that looks like a real TRIOS export.

    The weight curve has three mass loss steps (moisture, main degradation,
    carbonization) with realistic temperatures based on the heating rate.

    Returns a dict with 'metadata' (header key-value pairs), 'signals' (column
    arrays), 'signal_units', and 'columns'.
    """
    random.seed(seed)
    rng = random.Random(seed)

    # Time array: from 0 to time needed to reach temp_end
    total_time_min = (temp_end - temp_start) / heating_rate
    num_points = int(total_time_min * 4)  # 4 points per minute (15s interval)
    num_points = max(num_points, 50)

    time_min = [i * total_time_min / num_points for i in range(num_points)]
    temperature = [temp_start + heating_rate * t for t in time_min]

    # Normalize for curve generation
    norm_temp = [(t - temp_start) / (temp_end - temp_start) for t in temperature]

    # Weight curve: 100% at start, then stepwise losses
    # Three mass loss events at normalized temperatures ~0.15, ~0.45, ~0.75
    weight_pct = []
    for nt in norm_temp:
        w = 100.0
        if nt > 0.12:
            fraction = min((nt - 0.12) / 0.08, 1.0)
            w -= 4.0 * fraction  # ~4% moisture loss
        if nt > 0.40:
            fraction = min((nt - 0.40) / 0.15, 1.0)
            w -= 65.0 * fraction  # ~65% main degradation
        if nt > 0.70:
            fraction = min((nt - 0.70) / 0.12, 1.0)
            w -= 28.0 * fraction  # ~28% carbonization
            w = max(w, 3.0)  # residue ~3%
        # Add noise
        w += rng.gauss(0, noise_level * 100)
        weight_pct.append(w)

    # Convert to absolute weight (mg)
    weight_mg = [w / 100.0 * sample_mass_mg for w in weight_pct]

    # DTA signal: derivative-like peaks at transition points
    dta = []
    for nt in norm_temp:
        d = 0.0
        # Endothermic peak at moisture loss
        d -= 0.3 * _gaussian(nt, 0.16, 0.03)
        # Large exothermic peak at degradation
        d += 1.5 * _gaussian(nt, 0.48, 0.05)
        # Small broad peak at carbonization
        d += 0.4 * _gaussian(nt, 0.76, 0.06)
        # Noise
        d += rng.gauss(0, 0.02)
        dta.append(d)

    # Purge flow: constant after initial stabilization
    purge = [flow_rate] * len(time_min)
    for i in range(min(10, len(time_min))):
        purge[i] = flow_rate * (0.5 + 0.5 * i / 10)

    # Build metadata header
    procedure_segments = (
        f"Ramp {heating_rate:.1f} C/min to {temp_end:.0f} C; "
        f"Isothermal 5.0 min; "
        f"Ramp 50.0 C/min to 50.0 C"
    )

    metadata = {
        "filename": f"{sample_name.replace(' ', '_')}_{datetime.now():%Y%m%d}",
        "instrument_name": "0550-1823 (192.168.0.3)",
        "instrument_type": "TGA5500",
        "operator": operator,
        "rundate": datetime.now().strftime("%m/%d/%Y"),
        "sample_name": sample_name,
        "sample mass": f"{sample_mass_mg:.3f} mg",
        "pan_type": crucible,
        "procedure_name": "Char yield with gas and without air cool",
        "proceduresegments": procedure_segments,
        "trios_version": "5.1.1.46572",
        "gas_type": gas,
        "flow_rate": f"{flow_rate:.0f} mL/min",
    }

    # Column signals
    signals = {
        "time": time_min,
        "temperature": temperature,
        "weight": weight_mg,
        "dta": dta,
        "purge_flow": purge,
        "weight_pct": weight_pct,
    }

    signal_units = {
        "time": "min",
        "temperature": "C",
        "weight": "mg",
        "dta": "C",
        "purge_flow": "mL/min",
        "weight_pct": "%",
    }

    return {
        "metadata": metadata,
        "signals": signals,
        "signal_units": signal_units,
        "columns": ["time", "temperature", "weight", "dta", "purge_flow"],
    }


def _gaussian(x: float, mu: float, sigma: float) -> float:
    return math.exp(-0.5 * ((x - mu) / sigma) ** 2)


# ── CSV/TXT writer (TRIOS export format) ─────────────────────────────────────

def write_trios_export(data: Dict[str, Any], filepath: str) -> str:
    """Write synthetic data in TRIOS tab-separated export format.

    The format matches real TRIOS exports: header key-value pairs, then
    [step] section with column names, units, and tab-separated data rows.
    """
    metadata = data["metadata"]
    signals = data["signals"]
    columns = data["columns"]
    signal_units = data.get("signal_units", {})

    lines: List[str] = []

    # Header metadata
    for key, value in metadata.items():
        lines.append(f"{key}\t{value}")

    lines.append("[File Parameters]")
    lines.append(f"Name\t{metadata.get('filename', 'mock')}")
    lines.append(f"Instrument type\t{metadata.get('instrument_type', 'TGA5500')}")
    lines.append(f"Instrument serial number\t{metadata.get('instrument_name', '')}")
    lines.append(f"Instrument name\t{metadata.get('instrument_name', '')}")
    lines.append(f"Instrument location\tLab")
    lines.append(f"Company name\teConversion")
    lines.append(f"Trios version\t{metadata.get('trios_version', '5.1.1.46572')}")
    lines.append(f"File name\tC:\\Mock\\{metadata.get('filename', 'mock')}.tri")
    lines.append(f"Run date\t{metadata.get('rundate', '')} 12:00:00 PM")

    lines.append("[Procedure]")
    lines.append(f"Procedure Name\t{metadata.get('procedure_name', 'Mock Procedure')}")
    lines.append(f"Sample Name\t{metadata.get('sample_name', 'Mock')}")
    lines.append(f"Sample Mass\t{metadata.get('sample mass', '10.000 mg')}")
    lines.append(f"Pan Type\t{metadata.get('pan_type', 'Alumina')}")

    # Signal data section
    lines.append("[step]")
    lines.append("Temperature Ramp - Mock")

    # Column headers
    col_headers = "\t".join(columns)
    lines.append(col_headers)

    # Units row
    units_row = "\t".join(signal_units.get(c, "") for c in columns)
    lines.append(units_row)

    # Data rows
    n = len(signals[columns[0]])
    for i in range(n):
        row = "\t".join(f"{signals[c][i]:.6e}" if i < len(signals[c]) else "" for c in columns)
        lines.append(row)

    # Trailing empty line
    lines.append("")

    # Use \n as separator. Python handles platform-specific line endings
    # when writing in text mode.
    content = "\n".join(lines)

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        f.write(content)

    return filepath


# ── Fetch experiment from elabFTW ────────────────────────────────────────────

def fetch_experiment_params(experiment_id: int, api_key: str = "",
                            api_url: str = "https://elntest.ub.tum.de/api/v2") -> Dict[str, Any]:
    """Fetch an elabFTW experiment and extract extra_fields as parameters."""
    import json
    import requests

    headers = {"Authorization": api_key}
    resp = requests.get(f"{api_url}/experiments/{experiment_id}", headers=headers, timeout=15)
    if resp.status_code != 200:
        print(f"Warning: Could not fetch experiment {experiment_id} (HTTP {resp.status_code})")
        return {}

    exp = resp.json()
    meta_raw = exp.get("metadata")
    meta = {}
    if meta_raw:
        if isinstance(meta_raw, str):
            meta = json.loads(meta_raw)
        else:
            meta = meta_raw

    extra = meta.get("extra_fields", {})
    return {
        "sample_name": extra.get("sample_name", exp.get("title", "MockSample")),
        "sample_mass_mg": _float_or(extra.get("sample_mass_mg"), 12.5),
        "temp_start": _float_or(extra.get("temperature_start"), 30.0),
        "temp_end": _float_or(extra.get("temperature_end"), 1000.0),
        "heating_rate": _float_or(extra.get("heating_rate"), 10.0),
        "gas": extra.get("gas_atmosphere", "N2"),
        "flow_rate": _float_or(extra.get("gas_flow_rate"), 50.0),
        "crucible": extra.get("crucible_type", "Alumina"),
        "operator": extra.get("operator", "MockOperator"),
        "experiment_id": experiment_id,
    }


def _float_or(val, default: float) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Mock TRIOS instrument run. Generates a realistic CSV/TXT "
                    "export as if the TGA had just completed a measurement.",
    )
    parser.add_argument("--experiment", type=int, default=None,
                        help="elabFTW experiment ID to pull parameters from")
    parser.add_argument("--outdir", type=str, default="/tmp/mock-exports",
                        help="Output directory for the mock CSV file")
    parser.add_argument("--api-key", type=str,
                        default=os.environ.get("ELABFTW_API_KEY", ""),
                        help="elabFTW API key")
    parser.add_argument("--api-url", type=str,
                        default=os.environ.get("ELABFTW_API_URL",
                                               "https://elntest.ub.tum.de/api/v2"),
                        help="elabFTW API URL")
    parser.add_argument("--noise", type=float, default=0.002,
                        help="Noise level for synthetic signals")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")

    args = parser.parse_args()

    # Get parameters
    if args.experiment:
        print(f"Fetching experiment {args.experiment} from elabFTW...")
        params = fetch_experiment_params(args.experiment, args.api_key, args.api_url)
        if not params:
            print("Warning: Using default parameters")
            params = {"sample_name": "FallbackSample", "sample_mass_mg": 10.0,
                      "temp_start": 30, "temp_end": 800, "heating_rate": 10,
                      "gas": "N2", "flow_rate": 40, "crucible": "Alumina",
                      "operator": "auto", "experiment_id": args.experiment}
    else:
        params = {
            "sample_name": "Polymer-X",
            "sample_mass_mg": 12.5,
            "temp_start": 30.0,
            "temp_end": 1000.0,
            "heating_rate": 10.0,
            "gas": "N2",
            "flow_rate": 50.0,
            "crucible": "Alumina",
            "operator": "MockOperator",
            "experiment_id": None,
        }

    print(f"Generating mock TGA data for: {params['sample_name']}")
    print(f"  Mass: {params['sample_mass_mg']} mg")
    print(f"  Temp: {params['temp_start']} -> {params['temp_end']} C at {params['heating_rate']} K/min")
    print(f"  Gas: {params['gas']} ({params['flow_rate']} mL/min)")
    print(f"  Crucible: {params['crucible']}")

    # Generate synthetic signals
    data = generate_tga_signals(
        sample_name=params["sample_name"],
        sample_mass_mg=params["sample_mass_mg"],
        temp_start=params["temp_start"],
        temp_end=params["temp_end"],
        heating_rate=params["heating_rate"],
        gas=params["gas"],
        flow_rate=params["flow_rate"],
        crucible=params["crucible"],
        operator=params["operator"],
        noise_level=args.noise,
        seed=args.seed,
    )

    # Build filename
    exp_suffix = f"_exp{params['experiment_id']}" if params.get("experiment_id") else ""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = params["sample_name"].replace(" ", "_").replace("/", "_")
    filename = f"TGA_{safe_name}{exp_suffix}_{timestamp}.txt"

    # Ensure output directory
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    filepath = str(outdir / filename)

    write_trios_export(data, filepath)

    signal_counts = {k: len(v) for k, v in data["signals"].items()}
    peak_count = max(signal_counts.values()) if signal_counts else 0

    print(f"\nWritten: {filepath}")
    print(f"  Signal points: ~{peak_count} per channel")
    print(f"  Channels: {', '.join(data['columns'])}")
    print(f"\nNow run the pipeline:")
    print(f"  python instrument_ingest.py process {filepath}")
    print(f"Or watch the directory:")
    print(f"  ELABFTW_API_KEY=... python instrument_ingest.py watch {args.outdir}")


if __name__ == "__main__":
    main()

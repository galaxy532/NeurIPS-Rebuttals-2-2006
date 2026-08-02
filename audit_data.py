#!/usr/bin/env python3
"""
audit_data.py — report what is ACTUALLY on disk, so nothing is guessed again.

    python audit_data.py

Walks the data root and, for every tabular file it finds, records the real
filename, size, row count, full column list, dtypes, null counts and a few
sample values. Writes results/data_audit.json and results/data_audit.md.

WHY THIS EXISTS
---------------
The first version of download_data.py hard-coded two filenames from memory:
the UCI archive name (wrong — the real one uses hyphens, not plus signs, in
"130-us" and "1999-2008") and the ASSISTments csv name (wrong — the file that
arrived is the 2012-2013 release, not 2009-2010). Both mistakes were invisible
until a human looked in the folder, and one of them made a present file report
as "absent".

The fix is not to guess more carefully. It is to stop guessing: this script
reports ground truth, and the column contracts in download_data.py and the
declarations in PREREGISTRATION.md get reconciled against its output.

Nothing here interprets the data or computes a result. It only describes files.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_DIRNAME = "spurious_rebuttal_data"
DATA_ROOT = Path(os.environ.get(
    "SPURIOUS_DATA_ROOT", REPO_ROOT.parent / DEFAULT_DATA_DIRNAME))

# Files worth opening. Everything else is listed but not parsed.
TABULAR_SUFFIXES = {".csv", ".gz", ".tsv", ".txt", ".parquet"}

# How many rows to read for the column report. Full row counts are obtained
# separately by a cheap line count, so a 2 GB file is never loaded whole.
SNIFF_ROWS = 20_000


def _say(msg: str = "") -> None:
    print(msg, flush=True)


def count_rows(path: Path) -> int | None:
    """Row count without loading the frame. Returns None if not countable."""
    try:
        if path.suffix == ".gz":
            import gzip
            with gzip.open(path, "rt", errors="replace") as fh:
                return sum(1 for _ in fh) - 1
        if path.suffix in {".csv", ".tsv", ".txt"}:
            with open(path, "r", errors="replace") as fh:
                return sum(1 for _ in fh) - 1
    except Exception:                                            # noqa: BLE001
        return None
    return None


def read_head(path: Path) -> tuple[pd.DataFrame | None, str]:
    """Read the first SNIFF_ROWS rows, trying encodings that these files need."""
    if path.suffix == ".parquet":
        try:
            return pd.read_parquet(path), "parquet"
        except Exception as exc:                                 # noqa: BLE001
            return None, f"parquet read failed: {exc}"
    for enc in ("utf-8", "latin-1"):
        try:
            df = pd.read_csv(path, nrows=SNIFF_ROWS, encoding=enc,
                             low_memory=False,
                             sep="\t" if path.suffix == ".tsv" else ",")
            return df, enc
        except UnicodeDecodeError:
            continue
        except Exception as exc:                                 # noqa: BLE001
            return None, f"read failed: {exc}"
    return None, "no working encoding"


def describe(path: Path) -> dict:
    size_mb = path.stat().st_size / 1e6
    rec = {
        "path": str(path),
        "name": path.name,
        "parent": path.parent.name,
        "size_mb": round(size_mb, 2),
    }
    df, how = read_head(path)
    rec["read"] = how
    if df is None:
        return rec

    n_rows = count_rows(path)
    rec["rows_total"] = n_rows
    rec["rows_sniffed"] = int(len(df))
    rec["n_columns"] = int(df.shape[1])
    rec["columns"] = [str(c) for c in df.columns]
    rec["dtypes"] = {str(c): str(t) for c, t in df.dtypes.items()}
    rec["null_frac"] = {str(c): round(float(df[c].isna().mean()), 4)
                        for c in df.columns}
    rec["n_unique_in_sniff"] = {str(c): int(df[c].nunique(dropna=True))
                                for c in df.columns}
    # A couple of real values per column: the fastest way to spot an id column
    # masquerading as a measurement, or a label that is not binary.
    rec["sample_values"] = {
        str(c): [str(v)[:40] for v in df[c].dropna().unique()[:5]]
        for c in df.columns
    }
    return rec


def main() -> int:
    _say(f"data root: {DATA_ROOT}")
    if not DATA_ROOT.exists():
        _say("!! data root does not exist.")
        _say("   Either the download has not run, or the folder was renamed.")
        _say("   Point at it explicitly:  SPURIOUS_DATA_ROOT=/path python audit_data.py")
        return 1

    records, other = [], []
    for path in sorted(DATA_ROOT.rglob("*")):
        if path.is_dir():
            continue
        # skip the raw per-state PUMS cache; it is large and folktables owns it
        if "acs" in path.parts and path.parent.name in {"1-Year", "5-Year"}:
            other.append({"path": str(path), "note": "raw PUMS cache, not audited",
                          "size_mb": round(path.stat().st_size / 1e6, 2)})
            continue
        if path.suffix.lower() in TABULAR_SUFFIXES:
            _say(f"  reading {path.relative_to(DATA_ROOT)} ...")
            records.append(describe(path))
        else:
            other.append({"path": str(path),
                          "size_mb": round(path.stat().st_size / 1e6, 2)})

    out = {"data_root": str(DATA_ROOT), "tabular": records, "other_files": other}
    res_dir = REPO_ROOT / "results"
    res_dir.mkdir(exist_ok=True)
    (res_dir / "data_audit.json").write_text(json.dumps(out, indent=2, default=str))

    # Markdown mirror, because this is the artefact a human reads.
    lines = ["# Data audit", "",
             f"Data root: `{DATA_ROOT}`", "",
             f"{len(records)} tabular file(s), {len(other)} other file(s).", ""]
    for rec in records:
        lines += [f"## `{rec['parent']}/{rec['name']}`", ""]
        lines += [f"- size: {rec['size_mb']} MB",
                  f"- rows: {rec.get('rows_total', 'unknown')}",
                  f"- columns: {rec.get('n_columns', 'unreadable')}",
                  f"- read as: {rec['read']}", ""]
        if "columns" not in rec:
            lines += ["**could not be parsed**", ""]
            continue
        lines += ["| column | dtype | null frac | n unique | sample |",
                  "|---|---|---|---|---|"]
        for c in rec["columns"]:
            sample = ", ".join(rec["sample_values"].get(c, [])[:3])
            lines.append(f"| `{c}` | {rec['dtypes'][c]} | {rec['null_frac'][c]} | "
                         f"{rec['n_unique_in_sniff'][c]} | {sample} |")
        lines.append("")
    if other:
        lines += ["## Other files", ""]
        for o in other:
            note = f" — {o['note']}" if "note" in o else ""
            lines.append(f"- `{o['path']}` ({o['size_mb']} MB){note}")
    (res_dir / "data_audit.md").write_text("\n".join(lines))

    _say()
    _say(f"wrote {res_dir / 'data_audit.json'}")
    _say(f"wrote {res_dir / 'data_audit.md'}")
    _say()
    _say("Commit and push results/ — these two files are what the column")
    _say("contracts and PREREGISTRATION.md get reconciled against.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

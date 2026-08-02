#!/usr/bin/env python3
"""
download_data.py — fetch the three tabular datasets for the real-data arm.

    python download_data.py                 # all three
    python download_data.py --only acs      # one of: acs, readmission, assistments
    python download_data.py --check         # report what is present, download nothing
    python download_data.py --only acs --states CA NY TX     # a cheap subset first

Everything lands in ../spurious_rebuttal_data/ — a SIBLING of this repository,
never inside it. That is deliberate: the files are hundreds of megabytes and,
for ASSISTments and the UCI hospital data, not ours to redistribute. Keeping
them outside the repo means no `git add -A` can ever pull them in. The name is
specific rather than "data" so it cannot collide with the other repos cloned
next to it on a shared machine. Override with the SPURIOUS_DATA_ROOT env var.

    <parent>/
      <this repo>/
      spurious_rebuttal_data/
        acs/              <- raw ACS PUMS csvs, managed by folktables
        acsincome/        <- the assembled table we actually use
        readmission/
        assistments/

WHAT THIS SCRIPT DOES NOT DO
----------------------------
It does not decide which columns are r and which are s. That declaration lives
in PREREGISTRATION.md and is fixed before any result is looked at. This script
only puts bytes on disk and then checks that the columns named in the
pre-registration are actually present — so a silent schema change (ACS renames
columns between survey years) fails here, loudly, rather than three steps later
as a confusing result.

DEPENDENCIES
------------
    pip install numpy pandas folktables
    pip install kaggle           # only for ASSISTments

NETWORK
-------
Each source is fetched from its own host, and each can fail independently:

    acs           census.gov, via the folktables package     no credentials
    readmission   archive.ics.uci.edu, a static zip          no credentials
    assistments   kaggle.com, via the kaggle CLI             KAGGLE credentials

Every fetcher prints a manual fallback if it fails, so a blocked host costs you
a browser download and a file move, not a rewrite.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent

# Sibling of the repo, but with a name that cannot collide with the other repos
# cloned next to it on a shared box. Override with SPURIOUS_DATA_ROOT.
DEFAULT_DATA_DIRNAME = "spurious_rebuttal_data"
DATA_ROOT = Path(os.environ.get(
    "SPURIOUS_DATA_ROOT", REPO_ROOT.parent / DEFAULT_DATA_DIRNAME))

USER_AGENT = "Mozilla/5.0 (compatible; research-data-fetch/1.0)"

# --------------------------------------------------------------------------
# Column contracts.
#
# REQUIRED = the columns named in PREREGISTRATION.md as r, s, group or label.
#            If one of these is missing the dataset is unusable and we say so.
# EXPECTED = columns we would like but can work without; a miss is a warning.
#
# Keeping the contract here rather than in the analysis code means the failure
# surfaces at download time, when it is cheap to fix.
# --------------------------------------------------------------------------

CONTRACTS = {
    "acsincome": {
        "required": ["SCHL", "OCCP", "WKHP", "COW", "AGEP",   # r block
                     "MAR", "RELP", "POBP",                    # s block
                     "ST",                                     # group
                     "y"],                                     # label
        "expected": ["SEX", "RAC1P"],
        "min_rows": 100_000,
    },
    "readmission": {
        "required": ["number_inpatient", "number_diagnoses", "A1Cresult",
                     "max_glu_serum",                          # r block
                     "time_in_hospital", "num_lab_procedures",
                     "num_medications", "num_procedures",      # s block
                     "admission_source_id",                    # group
                     "readmitted"],                            # label
        "expected": ["age", "gender", "discharge_disposition_id"],
        "min_rows": 50_000,
    },
    "assistments": {
        "required": ["user_id", "order_id", "skill_id", "correct",
                     "opportunity",                            # r block source
                     "ms_first_response",                      # s block source
                     "school_id"],                             # group
        "expected": ["attempt_count", "hint_count", "overlap_time",
                     "assistment_id", "problem_id", "original"],
        "min_rows": 100_000,
    },
}


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def _say(msg: str = "") -> None:
    print(msg, flush=True)


def _rule(title: str) -> None:
    _say()
    _say("=" * 74)
    _say(title)
    _say("=" * 74)


def _http_get(url: str, timeout: int = 300) -> bytes:
    """GET with a browser user-agent. Raises with a readable message."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} from {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"cannot reach {url}: {exc.reason}") from exc


def check_contract(name: str, df: pd.DataFrame) -> dict:
    """Verify the pre-registered columns exist. Returns a report; never raises."""
    contract = CONTRACTS[name]
    cols = set(df.columns)
    missing_required = [c for c in contract["required"] if c not in cols]
    missing_expected = [c for c in contract["expected"] if c not in cols]
    too_small = len(df) < contract["min_rows"]

    report = {
        "rows": int(len(df)),
        "cols": int(df.shape[1]),
        "missing_required": missing_required,
        "missing_expected": missing_expected,
        "below_min_rows": bool(too_small),
        "ok": (not missing_required) and (not too_small),
    }

    _say(f"  rows: {len(df):,}   columns: {df.shape[1]}")
    if missing_required:
        _say(f"  !! MISSING REQUIRED COLUMNS: {missing_required}")
        _say("     The pre-registered r/s/group/label split cannot be built.")
        _say("     Either the source schema changed or the wrong file was fetched.")
    if missing_expected:
        _say(f"  -  missing optional columns (not fatal): {missing_expected}")
    if too_small:
        _say(f"  !! only {len(df):,} rows, expected >= {contract['min_rows']:,}")
        _say("     A partial download will silently distort every group count.")
    if report["ok"]:
        _say("  OK — contract satisfied.")
    return report


# --------------------------------------------------------------------------
# 1. ACS Income  (folktables -> census.gov)
# --------------------------------------------------------------------------

ACS_YEAR = 2018          # pinned: RELP is renamed RELSHIPP from 2019 onward
ACS_HORIZON = "1-Year"


def fetch_acsincome(states=None, force=False) -> dict:
    """
    ACS PUMS person records, assembled into the ACSIncome task.

    Year is pinned to 2018 on purpose. The ACS renamed the household-relationship
    variable RELP to RELSHIPP starting in 2019; RELP is in the pre-registered
    s block, so changing the year silently changes the experiment.

    Groups are STATES (column ST), not the race variable folktables uses by
    default for ACSIncome. That is the whole point of the dataset here: the
    coupling between the r block and the s block should differ across states.
    """
    _rule("1/3  ACS Income  (folktables -> census.gov)")

    out_dir = DATA_ROOT / "acsincome"
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = "all" if states is None else "-".join(states)
    out_file = out_dir / f"acsincome_{ACS_YEAR}_{tag}.csv.gz"

    if out_file.exists() and not force:
        _say(f"  already present: {out_file}")
        return check_contract("acsincome", pd.read_csv(out_file, nrows=5000)) | {
            "path": str(out_file), "skipped": True}

    try:
        from folktables import (ACSDataSource, ACSIncome, BasicProblem,
                                adult_filter, state_list)
    except ImportError:
        _say("  !! folktables is not installed.")
        _say("     pip install folktables")
        return {"ok": False, "error": "folktables missing"}

    states = list(states) if states else list(state_list)
    _say(f"  year {ACS_YEAR}, horizon {ACS_HORIZON}, {len(states)} state(s)")
    _say(f"  raw PUMS cache: {DATA_ROOT / 'acs'}")
    _say("  this is a few hundred MB on a first run; folktables caches per state")

    source = ACSDataSource(survey_year=str(ACS_YEAR),
                           horizon=ACS_HORIZON,
                           survey="person",
                           root_dir=str(DATA_ROOT / "acs"))
    try:
        raw = source.get_data(states=states, download=True)
    except Exception as exc:                                    # noqa: BLE001
        _say(f"  !! download failed: {exc}")
        _say("     Manual fallback: the PUMS csvs live at")
        _say(f"     www2.census.gov/programs-surveys/acs/data/pums/{ACS_YEAR}/{ACS_HORIZON}/")
        _say(f"     Unzip csv_p<state>.zip into {DATA_ROOT / 'acs' / str(ACS_YEAR) / ACS_HORIZON}/")
        _say("     then re-run this script; folktables will use the cache.")
        return {"ok": False, "error": str(exc)}

    _say(f"  raw person records: {len(raw):,}")

    # ACSIncome, but grouped by state instead of by race.
    problem = BasicProblem(
        features=ACSIncome.features,          # AGEP COW SCHL MAR OCCP POBP RELP WKHP SEX RAC1P
        target="PINCP",
        target_transform=lambda x: x > 50_000,
        group="ST",
        preprocess=adult_filter,              # AGEP>16, PINCP>100, WKHP>0, PWGTP>=1
        postprocess=lambda x: np.nan_to_num(x, nan=-1),
    )
    X, y, g = problem.df_to_pandas(raw)

    df = X.copy()
    df["ST"] = g["ST"].to_numpy()
    df["y"] = y["PINCP"].to_numpy().astype(int)

    report = check_contract("acsincome", df)
    df.to_csv(out_file, index=False, compression="gzip")
    _say(f"  wrote {out_file}  ({out_file.stat().st_size / 1e6:.1f} MB)")

    n_states = df["ST"].nunique()
    _say(f"  states present: {n_states}   base rate P(y=1) = {df['y'].mean():.3f}")
    return report | {"path": str(out_file), "n_groups": int(n_states)}


# --------------------------------------------------------------------------
# 2. Diabetes 130-US hospitals readmission  (UCI)
# --------------------------------------------------------------------------

# Corrected 2026-07-30 from the filename of a successful manual download.
# The archive uses hyphens in "130-us" and "1999-2008", not plus signs; the
# earlier spelling here was my guess and it was wrong. Do not "tidy" it.
UCI_URL = ("https://archive.ics.uci.edu/static/public/296/"
           "diabetes+130-us+hospitals+for+years+1999-2008.zip")


def fetch_readmission(force=False) -> dict:
    """UCI dataset 296. A single static zip, no credentials."""
    _rule("2/3  Diabetes 130-US hospitals readmission  (UCI)")

    out_dir = DATA_ROOT / "readmission"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "diabetic_data.csv"

    if out_file.exists() and not force:
        _say(f"  already present: {out_file}")
        return check_contract("readmission", pd.read_csv(out_file)) | {
            "path": str(out_file), "skipped": True}

    _say(f"  GET {UCI_URL}")
    try:
        blob = _http_get(UCI_URL)
    except RuntimeError as exc:
        _say(f"  !! {exc}")
        _say("     Manual fallback: open")
        _say("     archive.ics.uci.edu/dataset/296/  and download the zip,")
        _say(f"     then unzip diabetic_data.csv into {out_dir}/")
        _say("     Alternative: pip install ucimlrepo, then")
        _say("       from ucimlrepo import fetch_ucirepo; d = fetch_ucirepo(id=296)")
        return {"ok": False, "error": str(exc)}

    _say(f"  got {len(blob) / 1e6:.1f} MB, unpacking")
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = zf.namelist()
        target = next((n for n in names if n.endswith("diabetic_data.csv")), None)
        if target is None:
            _say(f"  !! diabetic_data.csv not in the archive. Contents: {names}")
            return {"ok": False, "error": "unexpected archive layout"}
        with zf.open(target) as src, open(out_file, "wb") as dst:
            shutil.copyfileobj(src, dst)
        # the id -> description mapping is useful when reading admission_source_id
        mapping = next((n for n in names if n.endswith("IDS_mapping.csv")), None)
        if mapping:
            with zf.open(mapping) as src, open(out_dir / "IDS_mapping.csv", "wb") as dst:
                shutil.copyfileobj(src, dst)
            _say(f"  wrote {out_dir / 'IDS_mapping.csv'}  (admission_source_id decoder)")

    df = pd.read_csv(out_file)
    report = check_contract("readmission", df)
    _say(f"  wrote {out_file}")

    if "readmitted" in df.columns:
        _say(f"  readmitted values: {dict(df['readmitted'].value_counts())}")
        _say("  label is 3-valued in the raw file; PREREGISTRATION.md defines")
        _say("  y = 1[readmitted == '<30'], which is the standard binarisation.")
    if "admission_source_id" in df.columns:
        vc = df["admission_source_id"].value_counts()
        big = (vc >= 200).sum()
        _say(f"  admission_source_id: {df['admission_source_id'].nunique()} distinct, "
             f"{big} with >= 200 rows")
    return report | {"path": str(out_file)}


# --------------------------------------------------------------------------
# 3. ASSISTments skill builder 2009-2010  (Kaggle)
# --------------------------------------------------------------------------

KAGGLE_SLUG = "nicolaswattiez/skillbuilder-data-2009-2010"


def fetch_assistments(force=False) -> dict:
    """
    ASSISTments skill-builder logs. Kaggle-hosted, so this needs credentials:
    a kaggle.json in ~/.kaggle/, or KAGGLE_USERNAME + KAGGLE_KEY in the env.
    """
    _rule("3/3  ASSISTments skill builder 2009-2010  (Kaggle)")

    out_dir = DATA_ROOT / "assistments"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Glob broadly. An earlier version looked only for skill_builder_data*.csv,
    # so a manual download that landed under any other name was reported as
    # "absent" while sitting in the folder. Never hard-code an expected
    # filename for a file fetched by hand.
    existing = sorted(p for p in out_dir.glob("*.csv") if p.stat().st_size > 1_000)
    if existing and not force:
        _say(f"  found {len(existing)} csv(s): {[p.name for p in existing]}")
        df = pd.read_csv(existing[0], encoding="latin-1", low_memory=False)
        return check_contract("assistments", df) | {
            "path": str(existing[0]), "skipped": True}

    have_creds = (Path.home() / ".kaggle" / "kaggle.json").exists() or (
        "KAGGLE_USERNAME" in os.environ and "KAGGLE_KEY" in os.environ)
    if not have_creds:
        _say("  !! no Kaggle credentials found.")
        _say("     Either put kaggle.json in ~/.kaggle/ (Kaggle > Settings > API >")
        _say("     Create New Token), or export KAGGLE_USERNAME and KAGGLE_KEY.")
        _say("     Manual fallback: download from")
        _say(f"     kaggle.com/datasets/{KAGGLE_SLUG}")
        _say(f"     and unzip skill_builder_data.csv into {out_dir}/")
        return {"ok": False, "error": "no kaggle credentials"}

    if shutil.which("kaggle") is None:
        _say("  !! the kaggle CLI is not on PATH.  pip install kaggle")
        return {"ok": False, "error": "kaggle CLI missing"}

    _say(f"  kaggle datasets download -d {KAGGLE_SLUG}")
    proc = subprocess.run(
        ["kaggle", "datasets", "download", "-d", KAGGLE_SLUG,
         "-p", str(out_dir), "--unzip"],
        capture_output=True, text=True)
    if proc.returncode != 0:
        _say(f"  !! kaggle CLI failed (exit {proc.returncode})")
        _say(f"     {proc.stderr.strip()[:500]}")
        _say("     Note: some Kaggle datasets require accepting terms in the")
        _say("     browser once before the API will serve them.")
        return {"ok": False, "error": proc.stderr.strip()[:200]}

    files = sorted(out_dir.glob("*.csv"))
    if not files:
        _say(f"  !! download reported success but no csv in {out_dir}")
        return {"ok": False, "error": "no csv after unzip"}

    # The archive ships several variants; prefer the corrected one if present.
    preferred = next((f for f in files if "corrected" in f.name.lower()), files[0])
    _say(f"  using {preferred.name}  (of {[f.name for f in files]})")

    # These logs are not UTF-8 clean — answer_text carries stray bytes.
    df = pd.read_csv(preferred, encoding="latin-1", low_memory=False)
    report = check_contract("assistments", df)

    if "school_id" in df.columns:
        vc = df["school_id"].value_counts()
        _say(f"  school_id: {df['school_id'].nunique()} distinct, "
             f"{(vc >= 5000).sum()} with >= 5000 rows")
    if "correct" in df.columns:
        _say(f"  base rate P(correct=1) = {df['correct'].mean():.3f}")
    _say("  NOTE: attempt_count, hint_count and the current item's response time")
    _say("  are measured DURING the answer being predicted. PREREGISTRATION.md")
    _say("  therefore builds r and s from the student's PRIOR history only.")
    return report | {"path": str(preferred)}


# --------------------------------------------------------------------------
# check-only mode
# --------------------------------------------------------------------------

def check_only() -> dict:
    _rule("check — what is already on disk")
    out = {}
    # Glob by extension, never by expected filename — see fetch_assistments.
    probes = {
        "acsincome": sorted((DATA_ROOT / "acsincome").glob("*.csv.gz")),
        # IDS_mapping.csv is the id decoder, not the data, and sorts first.
        "readmission": sorted(p for p in (DATA_ROOT / "readmission").glob("*.csv")
                              if "mapping" not in p.name.lower()),
        "assistments": sorted(p for p in (DATA_ROOT / "assistments").glob("*.csv")
                              if p.stat().st_size > 1_000),
    }
    for name, files in probes.items():
        _say()
        _say(f"[{name}]")
        if not files:
            _say(f"  absent — run: python download_data.py --only {name.replace('acsincome','acs')}")
            out[name] = {"ok": False, "error": "absent"}
            continue
        path = files[0]
        _say(f"  {path}")
        kwargs = {"encoding": "latin-1", "low_memory": False} if name == "assistments" else {}
        df = pd.read_csv(path, **kwargs)
        out[name] = check_contract(name, df) | {"path": str(path)}
    return out


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fetch the three tabular datasets into ../data/.")
    ap.add_argument("--only", choices=["acs", "readmission", "assistments"],
                    help="fetch a single dataset instead of all three")
    ap.add_argument("--states", nargs="+", default=None,
                    help="ACS only: two-letter state codes. Default is all 51. "
                         "Use a few (e.g. CA NY TX) for a fast first pass.")
    ap.add_argument("--check", action="store_true",
                    help="report what is present and verify columns; download nothing")
    ap.add_argument("--force", action="store_true",
                    help="re-download even if the file already exists")
    args = ap.parse_args()

    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    _say(f"data root: {DATA_ROOT}")

    if args.check:
        reports = check_only()
    else:
        reports = {}
        if args.only in (None, "acs"):
            reports["acsincome"] = fetch_acsincome(states=args.states, force=args.force)
        if args.only in (None, "readmission"):
            reports["readmission"] = fetch_readmission(force=args.force)
        if args.only in (None, "assistments"):
            reports["assistments"] = fetch_assistments(force=args.force)

    _rule("summary")
    width = max(len(k) for k in reports) if reports else 12
    for name, rep in reports.items():
        status = "OK " if rep.get("ok") else "FAIL"
        detail = ""
        if rep.get("ok"):
            detail = f"{rep.get('rows', 0):,} rows"
            if rep.get("skipped"):
                detail += "  (already present)"
        else:
            detail = rep.get("error", "contract not satisfied")
            if rep.get("missing_required"):
                detail = f"missing {rep['missing_required']}"
        _say(f"  {name:<{width}}  {status}  {detail}")

    manifest = REPO_ROOT / "results" / "download_manifest.json"
    manifest.parent.mkdir(exist_ok=True)
    manifest.write_text(json.dumps(reports, indent=2, default=str))
    _say()
    _say(f"manifest: {manifest}")

    n_fail = sum(1 for r in reports.values() if not r.get("ok"))
    if n_fail:
        _say(f"\n{n_fail} of {len(reports)} dataset(s) not ready. "
             "Each failure above prints its own manual fallback.")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
datasets.py — turn the files on disk into (r, s, y, g, cluster) exactly as
PREREGISTRATION.md declares.

Every judgement call about which column is r and which is s lives in that
document; this module only implements it. If the two ever disagree, the
document wins and this file is the bug.


USAGE
-----
From the command line — prints the shape and the full filter chain for each
dataset, and runs nothing else. This is the quickest way to see how many rows
and groups survive:

    python datasets.py                     # all three
    python datasets.py assistments         # just one
    SPURIOUS_DATA_ROOT=/path python datasets.py     # data lives elsewhere

Expected output per dataset: a one-line summary and the notes dict, e.g.

    <assistments: n=1,402,331 dr=3 ds=2 groups=118 clusters=21,904>
    {
      "rows_raw": 6123270,
      "rows_after_skill_filter": 2789...,      <- skill_id is 54% missing
      "rows_after_original_filter": ...,       <- original == 1 only
      "rows_dropped_no_history": ...,          <- a student's first item
      "groups_before_min_cell": 661,
      "groups_after_min_cell": 118,            <- the 200-row (y,g) floor
      ...
    }

From Python:

    from datasets import load_dataset
    d = load_dataset("acsincome")          # or "readmission", "assistments"

    d.r          # (n, dr) float array, the causal / stable block
    d.s          # (n, ds) float array, the spurious / unstable block
    d.y          # (n,)    int   array, binary label
    d.g          # (n,)    int   array, group index, 0..n_groups-1
    d.cluster    # (n,)    int   array, unit of dependence for the null
    d.r_names, d.s_names, d.group_name
    d.notes      # every filter applied and what it cost

    X = np.column_stack([d.r, d.s])        # the full feature matrix
    mask = (d.y == 1) & (d.g == 0)         # one (y, g) cell

Rows are aligned across r, s, y, g and cluster: index i is the same record in
all five.

Loaders take no options except `load_acsincome(all_states=...)` and
`load_assistments(max_rows=...)`; everything else is fixed by the
pre-registration and is deliberately not a knob.

TESTING
-------
`python validate_datasets.py` checks the prior-history construction against
hand-computed values and verifies that no feature depends on its own row's
outcome. Run it after touching anything in this file.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_DIRNAME = "spurious_rebuttal_data"
DATA_ROOT = Path(os.environ.get(
    "SPURIOUS_DATA_ROOT", REPO_ROOT.parent / DEFAULT_DATA_DIRNAME))

MIN_CELL = 200          # PREREGISTRATION.md, screen rule 1


@dataclass
class LoadedDataset:
    name: str
    r: np.ndarray
    s: np.ndarray
    y: np.ndarray
    g: np.ndarray
    cluster: np.ndarray
    r_names: list[str]
    s_names: list[str]
    group_name: str
    notes: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        return (f"<{self.name}: n={len(self.y):,} "
                f"dr={self.r.shape[1]} ds={self.s.shape[1]} "
                f"groups={len(np.unique(self.g))} "
                f"clusters={len(np.unique(self.cluster)):,}>")


# --------------------------------------------------------------------------
# shared helpers
# --------------------------------------------------------------------------

def _find(subdir: str, patterns: list[str]) -> Path:
    """Locate a data file by extension, never by an expected exact name."""
    folder = DATA_ROOT / subdir
    if not folder.exists():
        raise FileNotFoundError(
            f"{folder} does not exist. Run download_data.py, or set "
            f"SPURIOUS_DATA_ROOT if the data lives elsewhere.")
    for pat in patterns:
        hits = sorted(p for p in folder.glob(pat) if p.stat().st_size > 1_000)
        if hits:
            return hits[0]
    raise FileNotFoundError(
        f"no file matching {patterns} in {folder}. Present: "
        f"{[p.name for p in folder.iterdir()]}")


def apply_min_cell(df: pd.DataFrame, ycol: str, gcol: str,
                   notes: dict, min_cell: int = MIN_CELL) -> pd.DataFrame:
    """
    Screen rule 1: drop any group with a (y, g) cell below min_cell.

    Dropping the whole group, not just the thin cell, is deliberate — a group
    present for one label and absent for the other would make the within-cell
    centring in the screen incomparable across labels.
    """
    counts = df.groupby([gcol, ycol]).size().unstack(fill_value=0)
    n_labels = df[ycol].nunique()
    keep = counts[(counts >= min_cell).sum(axis=1) == n_labels].index
    before_groups, before_rows = df[gcol].nunique(), len(df)
    df = df[df[gcol].isin(keep)].copy()

    notes["min_cell"] = min_cell
    notes["groups_before_min_cell"] = int(before_groups)
    notes["groups_after_min_cell"] = int(df[gcol].nunique())
    notes["rows_dropped_by_min_cell"] = int(before_rows - len(df))
    notes["smallest_surviving_cell"] = (
        int(counts.loc[keep].values.min()) if len(keep) else 0)
    if df.empty:
        raise ValueError(
            f"every group fell below the {min_cell}-row floor. "
            "The dataset cannot support this analysis.")
    return df


def _codes(series: pd.Series) -> np.ndarray:
    """Stable integer coding for a group or cluster column."""
    return pd.Categorical(series).codes.astype(np.int64)


# --------------------------------------------------------------------------
# 1. ACS Income
# --------------------------------------------------------------------------

ACS_R = ["SCHL", "OCCP", "COW", "WKHP", "AGEP"]
ACS_S = ["MAR", "RELP", "POBP"]


def load_acsincome(all_states: bool = True) -> LoadedDataset:
    """
    y = income > $50k, r = job and schooling, s = household and origin,
    groups = states. One row per person, so each row is its own cluster.

    OCCP and POBP are high-cardinality codes (503 and 149 values) and are NOT
    ordinal — occupation 4720 is not "more" than 3605. Each code is replaced by
    the log of how often it occurs, which keeps the block low-dimensional for a
    screen without inventing an ordering.

    The counts are taken over the whole loaded frame rather than a training
    split. That is not label leakage — the transform never touches y — but it is
    a mild form of transduction, and it is recorded here rather than left for a
    reader to discover. If it ever matters, move the counting inside the CV
    split in screen_heterogeneity.
    """
    notes: dict = {}
    pats = ["*_all.csv.gz", "*.csv.gz"] if all_states else ["*.csv.gz"]
    path = _find("acsincome", pats)
    notes["file"] = path.name

    df = pd.read_csv(path)
    notes["rows_raw"] = int(len(df))

    df = apply_min_cell(df, "y", "ST", notes)

    r = df[ACS_R].copy()
    s = df[ACS_S].copy()
    # frequency-encode the nominal codes; label is never touched
    for col, block in (("OCCP", r), ("POBP", s)):
        counts = block[col].value_counts()
        block[col] = np.log1p(block[col].map(counts).astype(float))
    notes["frequency_encoded"] = ["OCCP", "POBP"]
    notes["nominal_note"] = ("MAR and RELP are small nominal codes left as "
                             "integers; the screen's model is tree-based and "
                             "does not assume an ordering.")

    return LoadedDataset(
        name="acsincome",
        r=r.to_numpy(dtype=float), s=s.to_numpy(dtype=float),
        y=df["y"].to_numpy(dtype=int), g=_codes(df["ST"]),
        cluster=np.arange(len(df)),          # one row per person
        r_names=ACS_R, s_names=ACS_S, group_name="ST", notes=notes)


# --------------------------------------------------------------------------
# 2. Hospital readmission
# --------------------------------------------------------------------------

READM_R = ["number_inpatient", "number_emergency", "number_outpatient",
           "number_diagnoses", "n_diag_coded"]
READM_S = ["time_in_hospital", "num_lab_procedures",
           "num_medications", "num_procedures"]

# UCI mapping: 17 is the NULL code. Verified against IDS_mapping.csv at load
# time rather than trusted from memory — see _check_source_17.
READM_DROP_SOURCES = [17]


def _check_source_17(notes: dict) -> None:
    """Confirm from IDS_mapping.csv that source 17 really is a NULL code."""
    try:
        path = DATA_ROOT / "readmission" / "IDS_mapping.csv"
        raw = path.read_text(errors="replace").splitlines()
        # the file concatenates three id->description tables separated by blanks
        in_source, found = False, None
        for line in raw:
            if line.startswith("admission_source_id"):
                in_source = True
                continue
            if in_source:
                if not line.strip() or "," not in line:
                    if found is not None:
                        break
                    continue
                code, _, desc = line.partition(",")
                if code.strip() == "17":
                    found = desc.strip()
                    break
        notes["source_17_decodes_to"] = found
        notes["source_17_drop_justified"] = bool(
            found and found.strip().upper() in {"NULL", "NOT AVAILABLE",
                                                "NOT MAPPED", "?"})
    except Exception as exc:                                     # noqa: BLE001
        notes["source_17_decodes_to"] = f"unreadable: {exc}"
        notes["source_17_drop_justified"] = None


def load_readmission() -> LoadedDataset:
    """
    y = readmitted within 30 days, r = patient history, s = episode handling,
    groups = admission source. First encounter per patient only.
    """
    notes: dict = {}
    path = _find("readmission", ["diabetic_data.csv", "*.csv"])
    notes["file"] = path.name

    df = pd.read_csv(path)
    notes["rows_raw"] = int(len(df))

    # first encounter per patient — removes the within-patient dependence
    df = df.sort_values("encounter_id").drop_duplicates("patient_nbr", keep="first")
    notes["rows_after_first_encounter"] = int(len(df))
    notes["encounters_dropped"] = notes["rows_raw"] - int(len(df))

    _check_source_17(notes)
    before = int(len(df))
    df = df[~df["admission_source_id"].isin(READM_DROP_SOURCES)]
    notes["rows_dropped_source_17"] = before - int(len(df))

    df["y"] = (df["readmitted"].astype(str).str.strip() == "<30").astype(int)
    notes["positive_rate"] = float(df["y"].mean())

    # n_diag_coded: how many of the three diagnosis slots are actually filled.
    # Missing is encoded as "?" in this file, not as NaN.
    diag = df[["diag_1", "diag_2", "diag_3"]].astype(str)
    df["n_diag_coded"] = (diag != "?").sum(axis=1)

    df = apply_min_cell(df, "y", "admission_source_id", notes)

    return LoadedDataset(
        name="readmission",
        r=df[READM_R].to_numpy(dtype=float),
        s=df[READM_S].to_numpy(dtype=float),
        y=df["y"].to_numpy(dtype=int),
        g=_codes(df["admission_source_id"]),
        cluster=np.arange(len(df)),          # one encounter per patient now
        r_names=READM_R, s_names=READM_S,
        group_name="admission_source_id", notes=notes)


# --------------------------------------------------------------------------
# 3. ASSISTments 2012-2013
# --------------------------------------------------------------------------

ASSIST_COLS = ["user_id", "skill_id", "correct", "original", "start_time",
               "ms_first_response", "hint_count", "school_id"]
ASSIST_R = ["n_prior_skill", "rate_prior_skill", "rate_prior_all"]
ASSIST_S = ["mean_prior_ms", "mean_prior_hints"]


def add_prior_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build every r and s feature from STRICTLY EARLIER rows of the same student.

    Separated out so it can be tested against hand-computed values without a
    3 GB file — see validate_datasets.py. This is the single most dangerous
    function in the repo: an off-by-one here leaks the outcome of the item being
    predicted into its own features, and the symptom would be excellent results
    rather than an error.

    Requires columns: user_id, skill_id, start_time (datetime), is_correct,
    ms_first_response, hint_count. Returns a sorted copy with the five features
    added; rows without history carry NaN and are dropped by the caller.

    THE CONSTRUCTION. For a cumulative sum `c_i = x_1 + ... + x_i` over a
    student's rows in time order, the sum over strictly-earlier rows is
    `c_i - x_i`. Dividing by the count of earlier rows gives the prior mean.
    Subtracting the row's own value is what makes it strict, and it is exactly
    the step an off-by-one would omit.

    `n_prior_skill` counts earlier rows of the same student ON THE SAME SKILL
    (grouped by user AND skill); the three student-level means count all earlier
    rows regardless of skill (grouped by user only).
    """
    df = df.sort_values(["user_id", "start_time"], kind="mergesort").copy()

    by_user_skill = df.groupby(["user_id", "skill_id"], sort=False)
    by_user = df.groupby("user_id", sort=False)

    # ---- per (student, skill)
    n_prior_skill = by_user_skill.cumcount()
    df["n_prior_skill"] = n_prior_skill
    denom_skill = n_prior_skill.where(n_prior_skill > 0)      # 0 -> NaN
    prior_correct_skill = by_user_skill["is_correct"].cumsum() - df["is_correct"]
    df["rate_prior_skill"] = prior_correct_skill / denom_skill

    # ---- per student, across all skills
    n_prior_all = by_user.cumcount()
    denom_all = n_prior_all.where(n_prior_all > 0)
    df["rate_prior_all"] = (
        by_user["is_correct"].cumsum() - df["is_correct"]) / denom_all
    df["mean_prior_ms"] = (
        by_user["ms_first_response"].cumsum() - df["ms_first_response"]) / denom_all
    df["mean_prior_hints"] = (
        by_user["hint_count"].cumsum() - df["hint_count"]) / denom_all

    return df


def load_assistments(max_rows: int | None = None) -> LoadedDataset:
    """
    y = answered fully correctly, r = prior practice on this skill,
    s = the student's habitual pace and hint use, groups = schools,
    clusters = students.

    Only ASSIST_COLS are read. The full file is 3 GB, almost all of it the
    `actions` column of raw log text; the eight columns we need are a few
    hundred MB.

    EVERY feature is built from strictly-earlier rows of the same student.
    Nothing measured on the current item enters r or s — that is the leakage
    rule in PREREGISTRATION.md, and it is the reason this dataset is usable at
    all.
    """
    notes: dict = {}
    path = _find("assistments", ["*.csv"])
    notes["file"] = path.name

    df = pd.read_csv(path, usecols=ASSIST_COLS, encoding="latin-1",
                     low_memory=False, nrows=max_rows)
    notes["rows_raw"] = int(len(df))

    # declared filters. .copy() because everything below assigns new columns,
    # and assigning into a slice raises SettingWithCopyWarning and may silently
    # not stick.
    df = df[df["skill_id"].notna()].copy()
    notes["rows_after_skill_filter"] = int(len(df))
    df = df[df["original"] == 1].copy()
    notes["rows_after_original_filter"] = int(len(df))

    # `correct` is not binary. The first run on the real file found EIGHT
    # distinct values — 0, 0.25, 0.5, 0.6, 0.65, 0.75, 0.95, 1 — where the
    # 20k-row audit sniff had shown three. Anything below 1.0 is currently
    # treated as not-fully-correct, which lumps 0.95 in with 0.0. Whether that
    # is right depends on how many rows are fractional, so the count is
    # recorded here for the decision rather than left invisible.
    vals = pd.unique(df["correct"])
    notes["correct_values_seen"] = sorted(float(v) for v in vals)
    partial = df["correct"].between(0, 1, inclusive="neither")
    notes["rows_partial_credit"] = int(partial.sum())
    notes["frac_partial_credit"] = round(float(partial.mean()), 6)

    # Partial credit is dropped rather than binarised. The real file has eight
    # values of `correct` (0, 0.25, 0.5, 0.6, 0.65, 0.75, 0.95, 1), and any
    # threshold rule has to defend itself: `== 1.0` files 0.95 with 0.0, and
    # `>= 0.5` is an arbitrary cut. Dropping them removes the question, and it
    # is free — 211 rows of 2.6M, 0.008%. Recorded above so the cost is visible
    # rather than assumed small.
    df = df[~partial].copy()
    notes["rows_after_partial_credit_drop"] = int(len(df))
    df["is_correct"] = (df["correct"] == 1.0).astype(int)

    # chronological order within student; ties broken deterministically
    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
    n_bad_time = int(df["start_time"].isna().sum())
    df = df[df["start_time"].notna()].copy()
    notes["rows_dropped_unparseable_time"] = n_bad_time

    df = add_prior_features(df)

    # A student's first-ever item has no history, so no r and no s.
    before = int(len(df))
    df = df.dropna(subset=ASSIST_R + ASSIST_S).copy()
    notes["rows_dropped_no_history"] = before - int(len(df))
    notes["rows_after_history"] = int(len(df))

    # log-scale the response time: it is heavy-tailed by orders of magnitude
    df["mean_prior_ms"] = np.log1p(df["mean_prior_ms"].clip(lower=0))
    notes["log1p_applied"] = ["mean_prior_ms"]

    df = apply_min_cell(df, "is_correct", "school_id", notes)
    notes["positive_rate"] = float(df["is_correct"].mean())
    notes["n_students"] = int(df["user_id"].nunique())

    return LoadedDataset(
        name="assistments",
        r=df[ASSIST_R].to_numpy(dtype=float),
        s=df[ASSIST_S].to_numpy(dtype=float),
        y=df["is_correct"].to_numpy(dtype=int),
        g=_codes(df["school_id"]),
        cluster=_codes(df["user_id"]),       # students nest inside schools
        r_names=ASSIST_R, s_names=ASSIST_S,
        group_name="school_id", notes=notes)


DATASETS = {
    "acsincome": load_acsincome,
    "readmission": load_readmission,
    "assistments": load_assistments,
}


def load_dataset(name: str, **kwargs) -> LoadedDataset:
    if name not in DATASETS:
        raise KeyError(f"unknown dataset {name!r}; have {list(DATASETS)}")
    return DATASETS[name](**kwargs)


def _write_notes(records: dict, out_dir: Path) -> None:
    """
    Persist the filter chains. These counts go into the response — how many
    rows each filter cost, how many groups survived the floor — and an earlier
    version only printed them, so they lived in a terminal scrollback and had to
    be pasted back by hand. Merges with any previous run so loading one dataset
    does not erase the others.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "dataset_notes.json"
    merged = {}
    if path.exists():
        try:
            merged = json.loads(path.read_text())
        except Exception:                                        # noqa: BLE001
            merged = {}
    merged.update(records)
    path.write_text(json.dumps(merged, indent=2, default=str))

    lines = ["# Dataset loading — filter chains", "",
             "Every filter applied by `datasets.py`, and what it cost.", ""]
    for name, rec in merged.items():
        lines += [f"## {name}", ""]
        if "error" in rec:
            lines += [f"**FAILED** — {rec['error']}", ""]
            continue
        lines += [f"- {rec['summary']}", "", "| field | value |", "|---|---|"]
        lines += [f"| `{k}` | {v} |" for k, v in rec["notes"].items()
                  if not isinstance(v, (list, dict))]
        lines.append("")
    (out_dir / "dataset_notes.md").write_text("\n".join(lines))
    print(f"\nrecorded in {out_dir / 'dataset_notes.md'}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Load and describe the datasets.")
    ap.add_argument("names", nargs="*", default=None,
                    help=f"any of {list(DATASETS)}; default all")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "results",
                    help="where to write dataset_notes.{json,md}")
    args = ap.parse_args()

    records = {}
    for name in (args.names or list(DATASETS)):
        try:
            d = load_dataset(name)
            print(d)
            print(json.dumps(d.notes, indent=2, default=str))
            records[name] = {"summary": repr(d), "notes": d.notes,
                             "n": int(len(d.y)),
                             "n_groups": int(len(np.unique(d.g))),
                             "n_clusters": int(len(np.unique(d.cluster)))}
        except Exception as exc:                                 # noqa: BLE001
            print(f"{name}: FAILED — {exc}")
            records[name] = {"error": str(exc)}
    _write_notes(records, args.out)

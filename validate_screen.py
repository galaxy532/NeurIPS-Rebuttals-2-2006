#!/usr/bin/env python3
"""
validate_screen.py — check the screen against known ground truth.

    python validate_screen.py

Produces no rebuttal numbers. It builds synthetic data where the answer is known
in advance and checks that the screen gives that answer, in the same spirit as
Estimator_Validation/ for the Waterbirds pipeline. A test that has never been
shown to fire, and never been shown to stay quiet, is not evidence.

Four cases, each a thing that could go wrong:

  1. POWER — the r -> s relation genuinely differs by group.
     Expect: large positive delta R2, small p.

  2. CALIBRATION — one relation shared by every group.
     Expect: delta R2 near zero, p not small. This is the case a naive
     row-level permutation null gets wrong.

  3. LEVEL-ONLY CONFOUND — identical relation, but s sits at a different level
     in each group. A group-aware model wins, yet nothing about the operator
     differs. Expect: relational delta near zero (centring removes it) while
     level_only_delta is large. If this fires, the screen is measuring
     covariate shift and would mislead us.

  4. CLUSTERED NULL — identical relation everywhere, but rows are clustered and
     clusters are entirely inside groups. This is the ASSISTments shape.
     Expect: p not small. A row-level permutation null fails here, which is the
     whole reason the null works on clusters.
"""

from __future__ import annotations

import sys

import numpy as np

from screen_heterogeneity import (heterogeneity_statistic,
                                  permute_groups_by_cluster)

RNG = np.random.default_rng(0)


def _screen(r, s, g, cluster, n_perm=20, seed=0):
    rng = np.random.default_rng(seed)
    obs = heterogeneity_statistic(r, s, g, cluster, seed, centered=True)
    lvl = heterogeneity_statistic(r, s, g, cluster, seed, centered=False)
    null = np.array([
        heterogeneity_statistic(r, s, permute_groups_by_cluster(g, cluster, rng),
                                cluster, seed + 1 + k, centered=True)["delta_r2"]
        for k in range(n_perm)])
    p = float((1 + (null >= obs["delta_r2"]).sum()) / (1 + len(null)))
    return {"delta": obs["delta_r2"],
            "level_only": lvl["delta_r2"] - obs["delta_r2"],
            "null_mean": float(null.mean()), "p": p}


def case_power(n=6000, k=4):
    """Slope of s on r flips sign across groups."""
    g = RNG.integers(0, k, n)
    r = RNG.normal(size=(n, 2))
    slopes = np.linspace(-2, 2, k)[g]
    s = np.column_stack([slopes * r[:, 0] + 0.3 * RNG.normal(size=n),
                         0.5 * r[:, 1] + 0.3 * RNG.normal(size=n)])
    return r, s, g, np.arange(n)


def case_calibration(n=6000, k=4):
    """One relation, shared by every group."""
    g = RNG.integers(0, k, n)
    r = RNG.normal(size=(n, 2))
    s = np.column_stack([1.5 * r[:, 0] + 0.3 * RNG.normal(size=n),
                         0.5 * r[:, 1] + 0.3 * RNG.normal(size=n)])
    return r, s, g, np.arange(n)


def case_level_only(n=6000, k=4):
    """Same relation; s shifted by a group-specific constant."""
    g = RNG.integers(0, k, n)
    r = RNG.normal(size=(n, 2))
    shift = np.linspace(-5, 5, k)[g]
    s = np.column_stack([1.5 * r[:, 0] + shift + 0.3 * RNG.normal(size=n),
                         0.5 * r[:, 1] + 0.3 * RNG.normal(size=n)])
    return r, s, g, np.arange(n)


def case_clustered_null(n_clusters=400, per=15, k=4):
    """
    One relation everywhere, but rows cluster and each cluster sits wholly
    inside one group — with a cluster-level random effect on s.
    """
    n = n_clusters * per
    cluster = np.repeat(np.arange(n_clusters), per)
    cl_group = RNG.integers(0, k, n_clusters)
    g = cl_group[cluster]
    cl_effect = RNG.normal(scale=2.0, size=n_clusters)[cluster]
    r = RNG.normal(size=(n, 2))
    s = np.column_stack([1.5 * r[:, 0] + cl_effect + 0.3 * RNG.normal(size=n),
                         0.5 * r[:, 1] + 0.3 * RNG.normal(size=n)])
    return r, s, g, cluster


def main() -> int:
    import argparse
    import json
    import platform
    from datetime import datetime, timezone
    from pathlib import Path

    ap = argparse.ArgumentParser(description="Check the screen against known truth.")
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).resolve().parent / "results",
                    help="where to write the record. /tmp when testing.")
    args = ap.parse_args()

    cases = [
        ("power           ", case_power,           "delta >> 0, p small"),
        ("calibration     ", case_calibration,     "delta ~ 0, p not small"),
        ("level-only      ", case_level_only,      "delta ~ 0, level_only >> 0"),
        ("clustered null  ", case_clustered_null,  "p not small"),
    ]
    rows, failures = [], []
    for name, fn, expect in cases:
        r, s, g, cl = fn()
        out = _screen(r, s, g, cl)
        rows.append((name, out, expect))
        print(f"{name}  delta {out['delta']:+.4f}  level_only "
              f"{out['level_only']:+.4f}  null {out['null_mean']:+.4f}  "
              f"p {out['p']:.4f}   [expect {expect}]", flush=True)

        key = name.strip()
        if key == "power" and not (out["delta"] > 0.05 and out["p"] <= 0.05):
            failures.append("power: the screen did not detect a relation that "
                            "genuinely differs by group")
        if key == "calibration" and out["p"] <= 0.05:
            failures.append("calibration: the screen fired on a single shared "
                            "relation — false positives")
        if key == "level-only" and out["delta"] > 0.05:
            failures.append("level-only: centring failed, the screen is picking "
                            "up covariate shift rather than the operator")
        if key == "clustered null" and out["p"] <= 0.05:
            failures.append("clustered null: the null is anti-conservative on "
                            "clustered rows — this is exactly the ASSISTments "
                            "shape, so results there would be worthless")

    # Persist, for the same reason as validate_datasets.py: the calibration and
    # clustered-null results are what license every screen number, and they need
    # to sit next to them rather than in a terminal scrollback.
    record = {"when": datetime.now(timezone.utc).isoformat(),
              "host": platform.node(), "python": platform.python_version(),
              "all_passed": not failures,
              "cases": {n.strip(): {"expect": e, **o} for n, o, e in rows},
              "failures": failures}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "validate_screen.json").write_text(
        json.dumps(record, indent=2, default=str))
    lines = ["# Validation — the heterogeneity screen", "",
             f"Run {record['when']} on `{record['host']}`, "
             f"Python {record['python']}.", "",
             "| case | delta R2 | level-only | null mean | p | expected |",
             "|---|---|---|---|---|---|"]
    lines += [f"| {n.strip()} | {o['delta']:+.4f} | {o['level_only']:+.4f} | "
              f"{o['null_mean']:+.4f} | {o['p']:.4f} | {e} |"
              for n, o, e in rows]
    if failures:
        lines += ["", "## Failures", ""] + [f"- {f}" for f in failures]
    (args.out / "validate_screen.md").write_text("\n".join(lines))
    print(f"\nrecorded in {args.out / 'validate_screen.md'}")

    if failures:
        print("FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("All four cases behaved as expected. The screen has power, does not "
          "fire on a shared relation, is not fooled by a level shift, and holds "
          "its size under clustering.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

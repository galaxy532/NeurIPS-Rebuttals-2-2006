#!/usr/bin/env python3
"""
screen_heterogeneity.py — does the r -> s relation differ across groups?

    python screen_heterogeneity.py                    # all three datasets
    python screen_heterogeneity.py --only acsincome
    python screen_heterogeneity.py --n-perm 50        # more permutations
    python screen_heterogeneity.py --budget 100000    # smaller subsample

Writes results/screen_<dataset>.{json,md} and a ranking across datasets.

WHAT IS BEING TESTED, AND WHY THIS AND NOT SOMETHING ELSE
---------------------------------------------------------
The theory needs the coupling operator between the causal and spurious blocks to
DIFFER ACROSS GROUPS. That is the one ingredient training cannot invent: a
representation can linearise a nonlinear relation, but it cannot make a relation
group-dependent if the same relation holds in every group.

So this screen deliberately does NOT test:

  * linear R-squared between raw r and s. Linearity is the representation's job.
    Our own Colored-MNIST run has a nonlinear raw r -> s relation that the
    representation linearised; a linear screen would have thrown it away.
  * conditional dependence between r and s. True independence would indeed rule
    a dataset out, but exact conditional independence does not happen in real
    observational data, so the test passes on everything and gates nothing.

It tests: fit a flexible f(r) -> s pooled across groups, and a group-aware
f_g(r) -> s. If the relation is the same everywhere, the group-aware model has
nothing extra to learn and its out-of-sample R-squared is no better.

THREE THINGS THAT WOULD MAKE THE ANSWER MEANINGLESS, AND THE HANDLING
----------------------------------------------------------------------
1. LEVEL vs RELATION. A group-aware model also wins when s merely sits at a
   different level in that group — ordinary covariate shift, not a different
   operator. So r and s are centred within each (y, g) cell before the
   comparison. Both quantities are reported; only the relational one ranks.

2. CLUSTERED ROWS. A student contributes many ASSISTments responses. Permuting
   group labels row-wise destroys the within-student dependence along with the
   group association, so the null statistic collapses and everything looks
   significant. The null reassigns WHOLE CLUSTERS to groups.

3. GROUP SIZE. A model given a group label can always fit small groups better by
   memorising them. The comparison is out-of-sample, and the split is made BY
   CLUSTER so that no student appears in both halves.

The output is a ranking, not a proof. Passing does not guarantee the trained
representation will show linear group-varying coupling; failing says the dataset
is not worth a GPU.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from datasets import DATASETS, load_dataset

REPO_ROOT = Path(__file__).resolve().parent

try:
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.model_selection import GroupShuffleSplit
except ImportError:                                              # pragma: no cover
    print("scikit-learn is required:  pip install scikit-learn")
    raise


# --------------------------------------------------------------------------
# core statistic
# --------------------------------------------------------------------------

def _center_within_cells(X: np.ndarray, cell: np.ndarray) -> np.ndarray:
    """Subtract the mean of each cell. Isolates relation from level."""
    out = X.astype(float, copy=True)
    for c in np.unique(cell):
        m = cell == c
        out[m] -= out[m].mean(axis=0, keepdims=True)
    return out


def _fit_r2(Xtr, Ytr, Xte, Yte, seed: int) -> float:
    """
    Mean out-of-sample R-squared over the columns of Y.

    R-squared is computed against the TEST mean, so a model that has learnt
    nothing scores 0 and a harmful model scores below 0. Averaging over the
    columns of s keeps the statistic comparable across datasets with different
    numbers of spurious columns.
    """
    scores = []
    for j in range(Ytr.shape[1]):
        model = HistGradientBoostingRegressor(
            max_iter=120, max_depth=6, learning_rate=0.1,
            early_stopping=False, random_state=seed)
        model.fit(Xtr, Ytr[:, j])
        pred = model.predict(Xte)
        resid = ((Yte[:, j] - pred) ** 2).sum()
        total = ((Yte[:, j] - Yte[:, j].mean()) ** 2).sum()
        scores.append(1.0 - resid / total if total > 0 else 0.0)
    return float(np.mean(scores))


def heterogeneity_statistic(r, s, g, cluster, seed: int,
                            centered: bool = True) -> dict:
    """
    Delta R-squared: how much better f(r, g) predicts s than f(r) alone.

    The split is by cluster, so no student straddles train and test. Both models
    see identical rows; the only difference is whether the group label is among
    the inputs.
    """
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=seed)
    tr, te = next(splitter.split(r, groups=cluster))

    R, S = (r, s)
    if centered:
        # centre within (train/test-agnostic) group cells; the caller has
        # already restricted to one label, so cells here are groups
        R = _center_within_cells(r, g)
        S = _center_within_cells(s, g)

    pooled = _fit_r2(R[tr], S[tr], R[te], S[te], seed)

    Rg_tr = np.column_stack([R[tr], g[tr]])
    Rg_te = np.column_stack([R[te], g[te]])
    aware = _fit_r2(Rg_tr, S[tr], Rg_te, S[te], seed)

    return {"r2_pooled": pooled, "r2_group_aware": aware,
            "delta_r2": aware - pooled,
            "n_train": int(len(tr)), "n_test": int(len(te))}


def permute_groups_by_cluster(g: np.ndarray, cluster: np.ndarray,
                              rng: np.random.Generator) -> np.ndarray:
    """
    Reassign whole clusters to groups, preserving group sizes in clusters.

    Each cluster sits in exactly one group in the real data (a student attends
    one school), so the null shuffles the cluster -> group map. Within-cluster
    dependence survives untouched; only the association between group identity
    and the r -> s relation is destroyed.
    """
    # return_index gives the first occurrence of each unique cluster, so
    # g[first_idx] is the group each cluster belongs to. return_inverse maps
    # every row back to its cluster's position. Both are vectorised — an
    # earlier version looped over all rows, which at 200k rows x 20
    # permutations dominated the runtime.
    _, first_idx, inv = np.unique(cluster, return_index=True,
                                  return_inverse=True)
    cluster_group = g[first_idx]
    shuffled = rng.permutation(cluster_group)
    return shuffled[inv]


# --------------------------------------------------------------------------
# per-dataset driver
# --------------------------------------------------------------------------

def screen_dataset(name: str, n_perm: int, budget: int, seed: int,
                   loader_kwargs: dict | None = None) -> dict:
    t0 = time.time()
    print(f"\n{'=' * 74}\n{name}\n{'=' * 74}", flush=True)

    d = load_dataset(name, **(loader_kwargs or {}))
    print(f"  {d}")
    for k in ("rows_raw", "groups_before_min_cell", "groups_after_min_cell",
              "smallest_surviving_cell", "positive_rate"):
        if k in d.notes:
            print(f"  {k}: {d.notes[k]}")

    rng = np.random.default_rng(seed)

    # subsample for cost, BY CLUSTER so no student is split
    if budget and len(d.y) > budget:
        uniq = np.unique(d.cluster)
        frac = budget / len(d.y)
        keep_cl = rng.choice(uniq, size=max(1, int(len(uniq) * frac)),
                             replace=False)
        m = np.isin(d.cluster, keep_cl)
        print(f"  subsampled {m.sum():,} of {len(d.y):,} rows "
              f"({len(keep_cl):,} clusters) for the screen")
    else:
        m = np.ones(len(d.y), dtype=bool)

    r, s, y, g, cl = d.r[m], d.s[m], d.y[m], d.g[m], d.cluster[m]

    out = {"dataset": name, "n_used": int(m.sum()),
           "n_total": int(len(d.y)),
           "n_groups": int(len(np.unique(g))),
           "n_clusters": int(len(np.unique(cl))),
           "r_names": d.r_names, "s_names": d.s_names,
           "group_name": d.group_name, "loader_notes": d.notes,
           "n_perm": n_perm, "seed": seed, "by_label": {}}

    for label in sorted(np.unique(y)):
        lm = y == label
        if lm.sum() < 500:
            out["by_label"][int(label)] = {"skipped": "fewer than 500 rows"}
            continue
        rl, sl, gl, cll = r[lm], s[lm], g[lm], cl[lm]
        print(f"\n  y = {label}   n = {lm.sum():,}   "
              f"groups = {len(np.unique(gl))}")

        obs = heterogeneity_statistic(rl, sl, gl, cll, seed, centered=True)
        lvl = heterogeneity_statistic(rl, sl, gl, cll, seed, centered=False)
        print(f"    pooled R2 {obs['r2_pooled']:+.4f}   "
              f"group-aware {obs['r2_group_aware']:+.4f}   "
              f"delta {obs['delta_r2']:+.4f}")

        null = []
        for k in range(n_perm):
            gp = permute_groups_by_cluster(gl, cll, rng)
            null.append(heterogeneity_statistic(
                rl, sl, gp, cll, seed + 1 + k, centered=True)["delta_r2"])
            if (k + 1) % 5 == 0:
                print(f"    permutation {k + 1}/{n_perm} "
                      f"(null mean {np.mean(null):+.4f})", flush=True)
        null = np.asarray(null)

        # +1 in numerator and denominator: the observed value is one draw from
        # the null under the hypothesis, so p can never be exactly 0.
        p = float((1 + (null >= obs["delta_r2"]).sum()) / (1 + len(null)))
        z = float((obs["delta_r2"] - null.mean()) / null.std(ddof=1)
                  if null.std(ddof=1) > 0 else np.nan)

        out["by_label"][int(label)] = {
            "n": int(lm.sum()),
            "relational": obs,
            "level_and_relational": lvl,
            "level_only_delta": lvl["delta_r2"] - obs["delta_r2"],
            "null_mean": float(null.mean()), "null_sd": float(null.std(ddof=1)),
            "p_value": p, "z": z,
            "passes": bool(p <= 0.05 and obs["delta_r2"] > 0),
        }
        print(f"    null {null.mean():+.4f} +/- {null.std(ddof=1):.4f}   "
              f"p = {p:.4f}   z = {z:+.2f}")

    labels = [v for v in out["by_label"].values() if "relational" in v]
    out["effect_size"] = (float(np.mean([v["relational"]["delta_r2"]
                                         for v in labels])) if labels else None)
    out["passes"] = bool(labels) and all(v["passes"] for v in labels)
    out["seconds"] = round(time.time() - t0, 1)
    return out


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------

def write_report(results: list[dict], out_dir: Path) -> None:
    """
    Write one file per dataset, then rebuild the summary from EVERY per-dataset
    file on disk.

    The first version wrote only screen_summary.{json,md}, so running
    `--only acsincome` and then `--only readmission` silently destroyed the
    first result. Per-dataset files make each run additive, and the summary is
    a view over them rather than a thing that can be clobbered.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    for r in results:
        (out_dir / f"screen_{r['dataset']}.json").write_text(
            json.dumps(r, indent=2, default=str))

    # reload everything, including datasets screened in earlier runs
    merged: dict[str, dict] = {}
    for path in sorted(out_dir.glob("screen_*.json")):
        if path.name == "screen_summary.json":
            continue
        try:
            rec = json.loads(path.read_text())
            merged[rec["dataset"]] = rec
        except Exception:                                        # noqa: BLE001
            continue
    for r in results:                       # this run wins on conflict
        merged[r["dataset"]] = r
    results = list(merged.values())

    ok = [r for r in results if "error" not in r]
    ok.sort(key=lambda r: (r.get("effect_size") or -9e9), reverse=True)

    lines = ["# Screen — does the r -> s relation differ across groups?", "",
             "Delta R-squared is the out-of-sample gain from giving the model "
             "the group label, after r and s are centred within each (y, g) "
             "cell so that a mere difference in level cannot produce it. "
             "The null reassigns whole clusters to groups.", "",
             "| dataset | groups | n used | y | delta R2 | null mean | p | z | passes |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in ok:
        for label, v in r["by_label"].items():
            if "relational" not in v:
                continue
            lines.append(
                f"| {r['dataset']} | {r['n_groups']} | {r['n_used']:,} | "
                f"{label} | {v['relational']['delta_r2']:+.4f} | "
                f"{v['null_mean']:+.4f} | {v['p_value']:.4f} | {v['z']:+.2f} | "
                f"{'yes' if v['passes'] else 'NO'} |")
    lines += ["", "## Ranking (train in this order)", ""]
    for i, r in enumerate(ok, 1):
        es = r.get("effect_size")
        es_str = f"{es:+.4f}" if es is not None else "n/a"
        verdict = "passes" if r.get("passes") else "DOES NOT PASS"
        lines.append(f"{i}. **{r['dataset']}** — effect size {es_str}, {verdict}")
    for r in results:
        if "error" in r:
            lines.append(f"- **{r['dataset']}** — failed: {r['error']}")

    lines += ["", "## Read the effect size, not the p-value", "",
              "These are large samples. At n = 200,000 the null spread is tiny, "
              "so a relational delta of 0.001 lands at z > 4 while explaining "
              "one tenth of one percent of the variance in s. Significance here "
              "says the effect is not exactly zero; it says nothing about "
              "whether it is big enough for the theory to bite. Rank on "
              "`delta R2`, and treat p only as a floor check.", "",
              "## Level versus relation", "",
              "`level_only` is how much of the group-aware advantage came from s "
              "sitting at a different level rather than from a different "
              "relation. A large value with a small relational delta means "
              "ordinary covariate shift, which this paper is not about. The "
              "share column is relational / (relational + level): the fraction "
              "of the group effect that is about the operator.", "",
              "| dataset | y | relational | level-only | relational share |",
              "|---|---|---|---|---|"]
    for r in ok:
        for label, v in r["by_label"].items():
            if "relational" not in v:
                continue
            rel = v["relational"]["delta_r2"]
            lvl = v["level_only_delta"]
            denom = abs(rel) + abs(lvl)
            share = f"{abs(rel) / denom:.1%}" if denom > 0 else "n/a"
            lines.append(f"| {r['dataset']} | {label} | {rel:+.4f} | "
                         f"{lvl:+.4f} | {share} |")

    (out_dir / "screen_summary.md").write_text("\n".join(lines))
    (out_dir / "screen_summary.json").write_text(
        json.dumps(results, indent=2, default=str))
    print("\n" + "\n".join(lines[:14]))
    print(f"\nwrote {out_dir / 'screen_summary.md'}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--only", choices=list(DATASETS))
    ap.add_argument("--n-perm", type=int, default=20,
                    help="permutations per label. 20 gives a p-value floor of "
                         "1/21 = 0.048; raise to 200 for a finer floor.")
    ap.add_argument("--budget", type=int, default=200_000,
                    help="max rows per dataset, subsampled by cluster. 0 = all.")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "results",
                    help="point at /tmp when testing, never at results/")
    args = ap.parse_args()

    names = [args.only] if args.only else list(DATASETS)
    results = []
    for name in names:
        try:
            results.append(screen_dataset(name, args.n_perm, args.budget,
                                          args.seed))
        except Exception as exc:                                 # noqa: BLE001
            print(f"\n!! {name} failed: {exc}")
            results.append({"dataset": name, "error": str(exc)})
    write_report(results, args.out)
    return 0 if any("error" not in r for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

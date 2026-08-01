# Rebuttals_2 — real-data arm on tabular benchmarks

Companion to `Rebuttals/` (Waterbirds). Same theory, different weak point.

**Waterbirds** measures the coupling in a representation where the `(Phi_r,
Phi_s)` split has to be *estimated*, at `corr(y, place) = 0.867` and VIF ≈ 4. A
reviewer can attack the estimate instead of the theory.

**Here** the split is fixed by column semantics and enforced architecturally: a
two-branch network where `Phi_r` sees only the r-columns and `Phi_s` only the
s-columns. Definition 3.3 then holds *by construction*, so the rate prediction
is tested with the identification question removed.

The two arms fail in different ways, which is the point of having both.

---

## Layout

```
Rebuttals_2/            this repo — code only
  PREREGISTRATION.md    the r/s/group/label declaration. Read this first.
  download_data.py      fetch the three datasets
  common.py             migrated verbatim from Rebuttals/
  results/              every script writes here. gitignored.
  reported/             numbers copied here by hand once they go in the
                        response. Tracked, so the text is reproducible.

../data/                SIBLING of this repo. Never committed.
  acs/  acsincome/  readmission/  assistments/
```

## The three datasets

| dataset | y | groups | n | source |
|---|---|---|---|---|
| ACS Income | earns > $50k | 51 US states | ~1.6M | census.gov via `folktables` |
| Hospital readmission | readmitted < 30 days | admission source | ~102k | UCI dataset 296 |
| ASSISTments | next answer correct | school | ~400k | Kaggle |

Who is `r`, who is `s`, and why — see `PREREGISTRATION.md`. That file is fixed
before results are looked at, and all three datasets get reported whether or not
they pass.

## Setup

```bash
pip install numpy scipy scikit-learn pandas folktables
pip install torch --index-url https://download.pytorch.org/whl/cu121   # for the extractor
pip install kaggle                                                     # ASSISTments only
```

ASSISTments is Kaggle-hosted and needs credentials: `~/.kaggle/kaggle.json`, or
`KAGGLE_USERNAME` + `KAGGLE_KEY` in the environment. The other two need none.

## Getting the data

```bash
python download_data.py                          # all three
python download_data.py --only acs --states CA NY TX   # fast first pass
python download_data.py --check                  # what is present, verify columns
```

Each fetcher is independent and prints its own manual fallback on failure, so a
blocked host costs a browser download and a file move. After every download the
script checks that the columns named in `PREREGISTRATION.md` are actually
present — a schema change fails here, loudly, instead of three steps later as a
confusing number. A manifest of what was fetched lands in
`results/download_manifest.json`.

`--force` re-downloads. ACS is pinned to survey year 2018 on purpose: `RELP`,
which is in the s block, is renamed `RELSHIPP` from 2019.

## Pipeline (steps 2–4 not yet written)

| step | script | measures | cost |
|---|---|---|---|
| 1 | `download_data.py` | — | minutes |
| 2 | `screen_dependence.py` | conditional dependence of r and s on the **raw** columns, per `(y,g)` cell, vs a permutation null | seconds |
| 3 | `train_two_branch.py` | the frozen `Phi = (Phi_r, Phi_s)` | hours, GPU |
| 4 | `analyze_tabular.py` | linear coupling `A`, isotropy defects, `alpha` | minutes |
| 5 | `eps_sweep_tabular.py` | the rate prediction under group imbalance | hours |

Step 2 is a necessary condition, not a sufficient one, and it is nearly free —
see the last section of `PREREGISTRATION.md` for why raw-column dependence
constrains the representation but raw-column *linearity* does not. Only datasets
that pass step 2 are worth training an extractor for.

## On `common.py`

Copied byte-for-byte from `Rebuttals/common.py`, so the validation recorded in
`Estimator_Validation/README.md` — alpha recovery to 0.02%, coupling test power
and calibration, isotropy diagnostic — certifies this copy too.

```
sha256  5bb39fad639a6e208a8890dbdf6399be53941ec622d850db688dced008a0aafe
lines   1116
```

If that hash stops matching `Rebuttals/common.py`, the two copies have drifted
and the validation no longer transfers. Check it before trusting a number:

```bash
sha256sum common.py ../Rebuttals/common.py
```

The functions this arm uses: `fit_operators`, `within_cell_coupling`,
`iso_diagnostics`, `compute_alpha`, `logistic_gd`, `subsample_to_eps`,
`local_slope`.

## A note on the .gitignore

The `Rebuttals/` repo ignores `__pycache__/` and `.ipynb_checkpoints/` and
tracks them anyway — the rules were added after the files were already
committed, and a `.gitignore` has no effect on tracked files. It also mixes
generated `results_*.json` into the source tree.

This repo fixes both: outputs go to `results/` (ignored wholesale), anything
that reaches the response is copied to `reported/` by hand, and the ignore file
is in place before the first commit. Verify before that first commit:

```bash
git status --short     # nothing under results/, no .pyc, no checkpoints
```

If something does slip in: `git rm -r --cached <path>`.

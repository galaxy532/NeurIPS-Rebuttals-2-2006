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
<this repo>/           code only
  PREREGISTRATION.md   the r/s/group/label declaration. Read this first.
  download_data.py     fetch the three datasets
  audit_data.py        report what is actually on disk
  common.py            migrated verbatim from Rebuttals/
  results/             every script writes here. TRACKED — this is how
                       numbers get off the training box.
  reported/            the curated subset that goes into the response.

../spurious_rebuttal_data/    SIBLING of this repo. Never committed.
  acs/  acsincome/  readmission/  assistments/
```

The data folder is named `spurious_rebuttal_data`, not `data`, so it cannot
collide with the other repos cloned beside it on a shared machine. Override with
`SPURIOUS_DATA_ROOT`.

## The datasets

Definition 3.3 of the manuscript defines **exactly two groups**, `G1` and `G2`,
by which operator carries `r` to `s`, with a single `eps = P(G2)`. So every
group variable here is binary. A 51-way or 149-way partition is a different
setting and `alpha` is not defined for it — an earlier version of this repo got
that wrong, and `LoadedDataset` now refuses to construct with anything but two
groups.

| dataset | y | G1 / G2 | eps | n | source |
|---|---|---|---|---|---|
| ACS Income | earns > $50k | male / female (`SEX`) | ~0.50 | ~1.6M | census.gov via `folktables` |
| Hospital readmission | readmitted < 30 days | emergency room / physician referral | ~0.34 | ~72k | UCI dataset 296 |
| ~~ASSISTments~~ | — | retired | — | — | — |

**States are replications, not groups.** The same two-group analysis runs inside
each of the 51 states, giving 51 independent instances rather than one pooled
number. States are never filtered by result.

**ASSISTments is retired** — no defensible binary partition. Its only binary
column, `tutor_mode`, separates the groups mechanically through `hint_count`,
which is in the `s` block. The loader and its tests stay in the repo so the
attempt is auditable; it is in `RETIRED`, not `DATASETS`.

Who is `r`, who is `s`, and why — see `PREREGISTRATION.md`. That file is fixed
before results are looked at, and every dataset gets reported whether or not it
passes.

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
| 1b | `audit_data.py --exact` | what is actually on disk: real filenames, columns, dtypes, exact group cell sizes | minutes |
| 2a | `validate_datasets.py` | the feature construction against hand arithmetic. No data needed | seconds |
| 2a | `validate_screen.py` | the screen against known ground truth. No data needed | ~1 min |
| 2b | `screen_heterogeneity.py` | does the `r → s` relation **differ across groups**, vs a cluster-level permutation null | ~10 min/dataset |
| 3 | `train_two_branch.py` | the frozen `Phi = (Phi_r, Phi_s)` | hours, GPU |
| 4 | `analyze_tabular.py` | linear coupling `A`, isotropy defects, `alpha` | minutes |
| 5 | `eps_sweep_tabular.py` | the rate prediction under group imbalance | hours |

`datasets.py` implements the r/s/group/label declarations and returns
`(r, s, y, g, cluster)` plus a `notes` dict recording every filter and what it
cost. `python datasets.py` prints all three without running anything else.

`validate_datasets.py` targets `add_prior_features`, the function that builds
every ASSISTments feature from the student's earlier rows. Six tests: hand-
computed values, no dependence on a row's own outcome, immunity of the final row
(the sharpest off-by-one test), per-skill versus per-student counting, no
cross-student contamination, and order independence. All six were confirmed to
fail under deliberately introduced bugs — dropping the "minus own value" term,
grouping by user without skill, grouping by skill without user, and removing the
internal sort — so they are not passing vacuously.

Run `validate_screen.py` before trusting a screen number. It builds synthetic
data where the answer is known and checks four things: that the screen fires
when the relation really does differ by group, stays quiet when one relation is
shared, is not fooled by a group-specific level shift, and holds its size when
rows are clustered. The third and fourth are the ones that would silently
invalidate the real results.

Step 2 is triage, not proof. It tests the one thing that cannot be created by
training — group-to-group variation in the `r → s` relation — and deliberately
does *not* test linearity, since linearising a nonlinear relation is exactly
what the representation may do. See the screen section of `PREREGISTRATION.md`
for the two wrong versions of this test and why they were dropped. Datasets are
trained in descending order of screen effect size.

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

Two different failures, and this repo has now hit both.

`Rebuttals/` ignores `__pycache__/` and `.ipynb_checkpoints/` and tracks them
anyway, because the rules were added after the files were already committed —
a `.gitignore` has no effect on files git already tracks.

This repo's first `.gitignore` overcorrected: it ignored `results/` wholesale to
keep the tree clean, which silently broke the only channel for getting numbers
off the training box. `results/` is now **tracked**. Its contents are small
`.json` and `.md`; the heavy things that rule was really for (`*.npz`, `*.pt`,
`*.csv`, datasets) are excluded by their own patterns wherever they appear.

Verify before the first commit:

```bash
git status --short     # results/*.json and *.md present; no .pyc, no data
```

If something does slip in: `git rm -r --cached <path>`.

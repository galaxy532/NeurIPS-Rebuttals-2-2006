#!/usr/bin/env python3
"""
validate_datasets.py — check the feature construction in datasets.py.

    python validate_datasets.py

Needs no data files. Builds tiny frames whose correct answers can be worked out
by hand and asserts that the code produces them.

The target is `add_prior_features`, which builds every ASSISTments r and s
feature from the student's earlier rows. It is the most dangerous function in
the repo: if it leaks the current item's outcome into that item's own features,
the failure is silent and the symptom is *better* results. Nothing downstream
would flag it.

Six tests:

  1. HAND VALUES     one student, four items, one skill. Every number checked
                     against arithmetic done on paper.
  2. NO SELF-LEAK    change one row's outcome; no feature anywhere may move
                     except through rows that come strictly after it.
  3. LAST ROW        change the LAST row's outcome; NO feature may move at all,
                     since no row comes after it. The sharpest off-by-one test.
  4. PER-SKILL       one student, two skills. n_prior_skill must count within
                     the skill, while the student-level means count across.
  5. NO CROSS-USER   two students interleaved in file order with overlapping
                     times; neither may see the other's history.
  6. UNSORTED INPUT  rows shuffled before the call; results must match the
                     sorted case, since the function sorts internally.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from datasets import ASSIST_R, ASSIST_S, add_prior_features

FEATURES = ASSIST_R + ASSIST_S


def frame(user_ids, skills, corrects, ms, hints, times=None) -> pd.DataFrame:
    n = len(user_ids)
    times = times if times is not None else list(range(n))
    return pd.DataFrame({
        "user_id": user_ids,
        "skill_id": skills,
        "is_correct": corrects,
        "ms_first_response": ms,
        "hint_count": hints,
        "start_time": pd.to_datetime("2012-09-01") + pd.to_timedelta(times, "h"),
    })


def _close(a, b, tol=1e-9) -> bool:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    both_nan = np.isnan(a) & np.isnan(b)
    return bool(np.all(both_nan | (np.abs(a - b) <= tol)))


# --------------------------------------------------------------------------

def test_hand_values() -> list[str]:
    """
    One student, one skill, four items in time order:

        correct = [1, 0, 1, 1]
        ms      = [100, 200, 300, 400]
        hints   = [0, 1, 2, 3]

    Worked out by hand, using only STRICTLY EARLIER rows:

      row 0: no history                   -> all NaN, n_prior_skill = 0
      row 1: prior {1}                    -> rate 1/1 = 1.0,   ms 100,  hints 0
      row 2: prior {1,0}                  -> rate 1/2 = 0.5,   ms 150,  hints 0.5
      row 3: prior {1,0,1}                -> rate 2/3 = 0.6667, ms 200, hints 1.0
    """
    df = frame([1] * 4, [7.0] * 4, [1, 0, 1, 1], [100, 200, 300, 400], [0, 1, 2, 3])
    out = add_prior_features(df)
    fails = []

    checks = {
        "n_prior_skill": [0, 1, 2, 3],
        "rate_prior_skill": [np.nan, 1.0, 0.5, 2 / 3],
        "rate_prior_all": [np.nan, 1.0, 0.5, 2 / 3],
        "mean_prior_ms": [np.nan, 100.0, 150.0, 200.0],
        "mean_prior_hints": [np.nan, 0.0, 0.5, 1.0],
    }
    for col, expected in checks.items():
        got = out[col].to_numpy()
        if not _close(got, expected):
            fails.append(f"hand values: {col} = {got}, expected {expected}")
    return fails


def test_no_self_leak() -> list[str]:
    """Flipping row 1's outcome must not change row 0's or row 1's features."""
    base = frame([1] * 5, [7.0] * 5, [1, 1, 0, 1, 0],
                 [100, 200, 300, 400, 500], [0, 0, 1, 1, 2])
    flipped = base.copy()
    flipped.loc[1, "is_correct"] = 0

    a = add_prior_features(base)[FEATURES].to_numpy()
    b = add_prior_features(flipped)[FEATURES].to_numpy()

    fails = []
    for i in (0, 1):
        if not _close(a[i], b[i]):
            fails.append(f"self-leak: row {i} changed when row 1's OUTCOME "
                         f"changed: {a[i]} -> {b[i]}")
    # rows after it must change, otherwise the feature is not using history
    if _close(a[2:], b[2:]):
        fails.append("self-leak: rows after the flip did NOT change — "
                     "rate_prior_* is not actually using prior outcomes")
    return fails


def test_last_row_immune() -> list[str]:
    """
    The sharpest test. Nothing comes after the last row, so changing its
    outcome must leave every feature in the frame untouched. An off-by-one
    (using cumsum without subtracting the row's own value) fails here.
    """
    base = frame([1] * 5, [7.0] * 5, [1, 0, 1, 0, 1],
                 [100, 200, 300, 400, 500], [0, 1, 0, 1, 0])
    flipped = base.copy()
    flipped.loc[4, "is_correct"] = 0

    a = add_prior_features(base)[FEATURES].to_numpy()
    b = add_prior_features(flipped)[FEATURES].to_numpy()
    if not _close(a, b):
        bad = [i for i in range(len(a)) if not _close(a[i], b[i])]
        return [f"last row: changing the FINAL outcome moved features on rows "
                f"{bad}. This is outcome leakage."]
    return []


def test_per_skill_counting() -> list[str]:
    """
    One student alternating between two skills:

        skill = [7, 8, 7, 8, 7]

    n_prior_skill counts within the skill      -> [0, 0, 1, 1, 2]
    rate_prior_all counts across all skills    -> denominators [-, 1, 2, 3, 4]
    """
    df = frame([1] * 5, [7.0, 8.0, 7.0, 8.0, 7.0], [1, 1, 1, 1, 1],
               [10, 20, 30, 40, 50], [0, 0, 0, 0, 0])
    out = add_prior_features(df)
    fails = []
    if not _close(out["n_prior_skill"], [0, 0, 1, 1, 2]):
        fails.append(f"per-skill: n_prior_skill = "
                     f"{out['n_prior_skill'].tolist()}, expected [0,0,1,1,2]")
    # all correct, so every defined rate is 1.0; row 0 has no history at all
    if not _close(out["rate_prior_all"], [np.nan, 1.0, 1.0, 1.0, 1.0]):
        fails.append(f"per-skill: rate_prior_all = "
                     f"{out['rate_prior_all'].tolist()}")
    # ms means run across skills: [-, 10, 15, 20, 25]
    if not _close(out["mean_prior_ms"], [np.nan, 10.0, 15.0, 20.0, 25.0]):
        fails.append(f"per-skill: mean_prior_ms = "
                     f"{out['mean_prior_ms'].tolist()}")
    return fails


def test_no_cross_user() -> list[str]:
    """
    Two students interleaved in file order, with overlapping times. Student 2's
    history must be identical to what it would be if student 1 did not exist.
    """
    both = frame([1, 2, 1, 2, 1, 2], [7.0] * 6, [1, 0, 1, 0, 1, 0],
                 [10, 999, 20, 999, 30, 999], [0, 9, 0, 9, 0, 9],
                 times=[0, 0, 1, 1, 2, 2])
    alone = frame([2, 2, 2], [7.0] * 3, [0, 0, 0], [999] * 3, [9] * 3,
                  times=[0, 1, 2])

    got = add_prior_features(both)
    got = got[got["user_id"] == 2][FEATURES].to_numpy()
    want = add_prior_features(alone)[FEATURES].to_numpy()
    if not _close(got, want):
        return [f"cross-user: student 2's features differ when student 1 is "
                f"present:\n{got}\nvs\n{want}"]
    return []


def test_unsorted_input() -> list[str]:
    """The function sorts internally, so input order must not matter."""
    df = frame([1] * 6, [7.0] * 6, [1, 0, 1, 1, 0, 1],
               [10, 20, 30, 40, 50, 60], [0, 1, 2, 3, 4, 5])
    shuffled = df.sample(frac=1.0, random_state=7)

    a = add_prior_features(df).sort_values("start_time")[FEATURES].to_numpy()
    b = add_prior_features(shuffled).sort_values("start_time")[FEATURES].to_numpy()
    if not _close(a, b):
        return ["unsorted input: shuffling the rows changed the result — "
                "the internal sort is not doing its job"]
    return []


def main() -> int:
    tests = [
        ("hand values     ", test_hand_values),
        ("no self-leak    ", test_no_self_leak),
        ("last row immune ", test_last_row_immune),
        ("per-skill count ", test_per_skill_counting),
        ("no cross-user   ", test_no_cross_user),
        ("unsorted input  ", test_unsorted_input),
    ]
    all_fails = []
    for name, fn in tests:
        fails = fn()
        print(f"{name}  {'PASS' if not fails else 'FAIL'}")
        for f in fails:
            print(f"    {f}")
        all_fails += fails

    print()
    if all_fails:
        print(f"{len(all_fails)} failure(s). Do not run the screen until these "
              "are fixed — the leakage ones would produce good-looking numbers.")
        return 1
    print("All six pass. The prior-history features match hand arithmetic, "
          "depend only on strictly-earlier rows of the same student, count "
          "per-skill where they should, and are order-independent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

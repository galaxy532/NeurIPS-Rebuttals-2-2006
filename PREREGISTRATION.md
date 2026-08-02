# Pre-registration — real-data arm, three tabular datasets

**Status: APPROVED 2026-07-30, before any dataset was analysed. The r/s/group/
label declarations below are fixed. Later amendments must be recorded in the
changelog at the bottom, never made silently.**

This document fixes, *before any result is looked at*, which columns play the
role of `r` and which play the role of `s` in each dataset, together with the
group variable and the label.

## Why this document exists

We are screening three datasets in the hope that at least one satisfies the
linear-coupling assumption. That is a legitimate thing to do and a dangerous
thing to report. If the r/s assignment were chosen after seeing which
assignment made `alpha` come out well, every number downstream would be
worthless, and a reviewer at confidence 5 would be right to say so.

Fixing the assignment in advance, in a committed file, costs nothing and
removes the objection entirely. The rule we hold ourselves to:

> The r/s split, the group variable and the label are fixed here. All three
> datasets are reported in the response, including the ones that fail.

A dataset where the coupling assumption fails is not a wasted run. It is
evidence that the assumption has content — that it is a testable restriction on
the data rather than a formality. That is worth more in the response than a
third success.

---

## What r and s mean here

We do not claim to settle causality. The operational definitions are:

- **`r` (relevant / stable):** features that plausibly *generate* the label, and
  whose relationship to the label should hold up across groups.
- **`s` (spurious / unstable):** features that *predict* the label well without
  generating it, and whose relationship to the label (or to `r`) is expected to
  differ across groups.

Whether a column really is unstable across groups is an empirical question, and
one of the things the screen measures. The declarations below are our
prediction, made in advance.

---

## 1. ACS Income — US census microdata

Predict whether a working adult earns more than $50,000, from their own census
record. 2018 1-Year PUMS, ~1.6M records, ~51 groups.

| role | columns | in plain terms |
|---|---|---|
| **y** | `PINCP > 50000` | does this person earn over $50k |
| **r** | `SCHL`, `OCCP`, `COW`, `WKHP`, `AGEP` | education level, occupation, class of worker, hours worked per week, age |
| **s** | `MAR`, `RELP`, `POBP` | marital status, relationship to the head of household, place of birth |
| **g** | `ST` | US state |

**Why `r` is relevant.** These are the things that actually produce a wage. What
job you hold, how much schooling you have, and how many hours you work are the
mechanism by which income is generated. If you changed someone's occupation,
their income would change.

**Why `s` is spurious.** Married people earn more than unmarried people, and the
gap is large enough that marital status is a good predictor. But getting married
does not pay you a salary. The correlation runs through age, household
formation and selection — people who are established enough to marry are also
established enough to earn. Place of birth works the same way: it predicts
income through immigration history and regional opportunity, not through any
mechanism attached to the person's job.

**Why the groups should differ.** Median age at first marriage, cost of living
and household composition vary a lot from state to state. So the relationship
between "has a good job" and "is married" is not the same in Utah as in New
York — which is exactly the group-varying coupling the theory needs.

**Note on year.** Pinned to 2018. The ACS renames `RELP` to `RELSHIPP` from 2019
onward, and `RELP` is in the `s` block. Changing the year silently changes the
experiment.

**Note on what we deliberately did not use.** `SEX` and `RAC1P` are strong
predictors of income that are not mechanisms of it, so they look like natural
`s` candidates. We exclude them because discrimination is a real causal channel
from these attributes to income, which makes "spurious" contestable, and because
it would drag a fairness argument into a paper that is not about fairness.

---

## 2. Hospital readmission — UCI, 130 US hospitals, 1999–2008

Predict whether a diabetic patient is readmitted within 30 days of discharge.
~101,766 encounters.

| role | columns | in plain terms |
|---|---|---|
| **y** | `1[readmitted == "<30"]` | readmitted within 30 days |
| **r** | `number_inpatient`, `number_emergency`, `number_outpatient`, `number_diagnoses`, `n_diag_coded` (count of non-missing `diag_1..3`) | how many times they were already hospitalised, seen in emergency or as an outpatient, and how many distinct conditions are recorded |
| **s** | `time_in_hospital`, `num_lab_procedures`, `num_medications`, `num_procedures` | how long the stay lasted, how many lab tests were ordered, how many drugs and procedures were administered |
| **g** | `admission_source_id` | how the patient arrived — referral, emergency room, transfer from another facility |

**Why `r` is relevant.** These measure how sick the patient actually is. Someone
with many prior admissions and many recorded conditions is genuinely more likely
to come back. The measurement is about the patient's history, not about this
episode's handling.

**Dropped from `r`: `A1Cresult` and `max_glu_serum`.** They were in the first
version of this declaration and they do not belong. Two reasons, the second
decisive.

They are 81% and 90% missing, which alone would make them thin. But the
missingness is not noise: *whether the test was ordered* is a decision made by
the hospital, which is `s`-like, while *the value, given that it was ordered* is
patient state, which is `r`-like. A single column that carries both roles
straddles the split the whole experiment rests on. Any encoding — "not measured"
as a level, imputation, an indicator — mixes an institutional decision into the
`r` block. Dropping them costs little, since the prior-utilisation counts carry
the severity signal, and it keeps the split clean.

**Why `s` is spurious.** These measure what the *hospital did*, not how sick the
patient is. A hospital with a cautious protocol orders more labs and keeps
people longer for the same underlying illness. So the lab count tracks severity,
but only indirectly — through institutional practice. Move the same patient to a
different hospital and the number changes while the patient does not.

**Why the groups should differ.** `admission_source_id` separates patients who
were referred by a physician from those who came through the emergency room or
were transferred. These routes have very different protocols: an emergency
admission generates a burst of tests regardless of chronic severity, a scheduled
referral does not. So the tests-per-diagnosis exchange rate genuinely differs by
group.

**Why this one is strategically useful.** It is the "two institutions score the
same client differently" example from the rebuttal — the one already described
to the AC — occurring in real data rather than as a hypothetical.

---

## 3. ASSISTments 2012–2013 — intelligent tutoring logs

Predict whether a student's next answer on a skill is correct.
**6,123,270 rows**, 381 schools.

*This section was rewritten on 2026-07-30 against the file actually on disk.
The Kaggle slug advertises 2009–2010 but ships
`2012-2013-data-with-predictions-4-final.csv`, whose schema is different: no
`order_id`, no `opportunity`, and `correct` is not binary. The original
declaration referred to columns that do not exist. Nothing had been analysed at
the time of the rewrite.*

| role | columns | in plain terms |
|---|---|---|
| **y** | `1[correct == 1.0]`, on rows with `original == 1` | did the student get this one fully right |
| **r** | `n_prior_skill` (count of the student's earlier items on this same skill), `rate_prior_skill` (their correct rate on those), `rate_prior_all` (their correct rate over all earlier items) | how much this student has already practised this specific skill, and how well they have done so far |
| **s** | `mean_prior_ms` (mean `ms_first_response` over the student's earlier items), `mean_prior_hints` (mean `hint_count` over those) | how long this student typically takes to answer, and how often they typically ask for hints |
| **g** | `school_id` | the student's school |

**Construction rules, fixed here.**

- **Ordering** is by `start_time` within `user_id`. There is no `order_id` in
  this release.
- **`n_prior_skill` is computed, not read.** No `opportunity` column exists;
  it is the count of the student's strictly-earlier rows with the same
  `skill_id`.
- **`correct` takes 5 distinct values**, including 0.25 — partial credit. The
  label is `1[correct == 1.0]`, restricted to `original == 1` so that
  scaffolding sub-problems do not enter as independent items.
- **`skill_id` is 54% missing.** Rows without it are dropped, leaving ~2.8M.
  Reported as a filter, not hidden.

**Excluded, and why it matters.** The columns
`Average_confidence(FRUSTRATED | CONFUSED | CONCENTRATING | BORED)` are the
output of somebody else's affect-detection model — that is the "with
predictions" in the filename. They are not measurements and never enter either
block. Also excluded: `actions` (raw log text, and the source of the embedded
newlines), `answer_text`, `answer_id`, `teacher_id`.

**Why `r` is relevant.** Practice builds skill. A student who has worked through
this skill twenty times, correctly, is genuinely more likely to answer the next
one correctly, and the mechanism is not mysterious.

**Why `s` is spurious.** Slow students tend to be struggling students, so
response time predicts correctness quite well. But taking longer does not
*cause* a wrong answer — a careful strong student can be slow, and a fast
guesser can be wrong. Time is a symptom that happens to correlate with the
thing we care about.

**Why the groups should differ.** Schools differ in pacing, in how the platform
is used in class versus at home, and in how much time students are given. So the
seconds-per-practice-opportunity relationship varies substantially by school.

**Leakage rule — unchanged by the rewrite, and the reason the whole idea nearly
failed.** `attempt_count`, `hint_count`, `ms_first_response`, `overlap_time`,
`first_action` and `bottom_hint` *for the current item* are recorded while the
student answers the item we are predicting. If you needed five attempts, you got
it wrong; the "feature" is the label in disguise. So:

> Both `r` and `s` are built **exclusively from the student's prior history**,
> strictly before the current item in `order_id`. No column measured on the
> current item enters either block.

---

## The screen: what it tests, and what it deliberately does not

Two earlier versions of this section were wrong, and the reasoning is recorded
here because the wrong versions are tempting.

**Wrong version 1: screen on linear `R²` between the raw r and s columns.**
Rejected because the theory needs linear coupling between `Phi_r` and `Phi_s` in
the *learned* representation, and says nothing about the raw columns. Testing
raw columns with a linear head is a one-layer model — not this experiment, and
not what the reviewers asked for. Our own Colored-MNIST run is the
counterexample: the raw `r → s` relation there is nonlinear, and the
representation linearised it. A linear raw screen would have discarded a dataset
that works.

**Wrong version 2: screen on conditional dependence of any form.** The
implication behind it is true — if `Phi_r` is a function of the r-columns alone
and `Phi_s` of the s-columns alone, then `r ⊥ s | (y,g)` forces
`Phi_r ⊥ Phi_s | (y,g)`, because functions of conditionally independent
variables are conditionally independent. So no network can manufacture coupling
out of exact independence. But exact conditional independence does not occur in
real observational data. The test would pass on everything, and a gate that
never fires is not a gate.

**What we actually test.** The theory does not need coupling; it needs coupling
that **differs across groups**. That is the quantity `A` in the two-branch
setting, and if it is the same in every group there is nothing for the theory to
bite on — no group heterogeneity, no `alpha` worth measuring, and no amount of
training will create it. So the screen is:

> Fit a flexible `s ≈ f_g(r)` separately within each group `g` (and within each
> label cell `y`). Test whether the fitted `f_g` differ across groups, against a
> null that permutes the group labels.

This can fail, and on some datasets it will. Being flexible rather than linear
means it inherits the Colored-MNIST lesson: a nonlinear `r → s` relation that
differs by group still passes, because linearisation is the representation's job,
not the screen's.

It is a **ranking and triage** device, not a proof. Passing does not guarantee
the trained representation will show linear group-varying coupling; failing does
say the dataset is not worth a GPU.

| stage | measured on | cost | question |
|---|---|---|---|
| screen | raw columns | seconds | does the `r → s` relation differ across groups at all? |
| coupling | `Phi`, two-branch | hours | is it linear in the representation, and does `A` differ by group? |
| rates | `Phi`, last layer | hours | does the measured `alpha` predict the observed exponent? |

Datasets are trained in descending order of screen effect size. A dataset that
fails the screen is still reported, as a scope statement.

---

## Sign-off

| | |
|---|---|
| drafted | 2026-07-30 |
| approved | 2026-07-30, by the authors |
| data on disk at approval | ACS Income (CA/NY/TX), UCI readmission. No analysis run. |

## Changelog

| date | change | why |
|---|---|---|
| 2026-07-30 | r/s/group/label declarations fixed for all three datasets | initial |
| 2026-07-30 | screen changed from raw-column dependence to group-heterogeneity of the `r → s` relation | the dependence test passes on all real data, so it gated nothing; see the screen section |
| 2026-07-30 | readmission: `A1Cresult` and `max_glu_serum` dropped from `r` | 81% and 90% missing, and the missingness itself is an institutional decision — the columns straddle the r/s split |
| 2026-07-30 | readmission: `number_outpatient` and `n_diag_coded` added to `r` | replace the severity signal lost above, using patient history rather than episode handling |
| 2026-07-30 | ASSISTments: section rewritten against the file on disk | the Kaggle slug ships the 2012–2013 release; `order_id` and `opportunity` do not exist, `correct` is not binary, `skill_id` is 54% missing |

All four amendments were made before any screen, coupling or rate result
existed. The data audit that prompted them (`results/data_audit.md`) describes
file structure only — column names, dtypes, missingness, group counts — and
reports no relationship between any `r`, `s`, `g` and `y`.

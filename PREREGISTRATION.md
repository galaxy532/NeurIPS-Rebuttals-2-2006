# Pre-registration — real-data arm, three tabular datasets

**Status: DRAFT, awaiting approval. Nothing downstream should read this file
until it is approved and committed.**

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
| **r** | `number_inpatient`, `number_emergency`, `number_diagnoses`, `A1Cresult`, `max_glu_serum` | how many times they were already hospitalised, how many conditions they have, and their actual blood-sugar test results |
| **s** | `time_in_hospital`, `num_lab_procedures`, `num_medications`, `num_procedures` | how long the stay lasted, how many lab tests were ordered, how many drugs and procedures were administered |
| **g** | `admission_source_id` | how the patient arrived — referral, emergency room, transfer from another facility |

**Why `r` is relevant.** These measure how sick the patient actually is. Someone
with many prior admissions, many diagnoses and bad glucose control is genuinely
more likely to come back. The measurement is about the patient.

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

## 3. ASSISTments skill builder 2009–2010 — intelligent tutoring logs

Predict whether a student's next answer on a skill is correct. ~400k responses.

| role | columns | in plain terms |
|---|---|---|
| **y** | `correct` on the current item | did the student get this one right |
| **r** | `opportunity` (prior practice count on this skill), prior correct rate on this skill, prior correct rate overall | how much this student has already practised this specific skill, and how well they have done so far |
| **s** | mean `ms_first_response` over the student's prior items, mean `hint_count` over prior items | how long this student typically takes to answer, and how often they typically ask for hints |
| **g** | `school_id` | the student's school |

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

**Leakage rule — this is the trap that killed the original idea.**
`attempt_count`, `hint_count` and `ms_first_response` *for the current item* are
recorded while the student answers the item we are predicting. If you needed
five attempts, you got it wrong; the "feature" is the label in disguise. So:

> Both `r` and `s` are built **exclusively from the student's prior history**,
> strictly before the current item in `order_id`. No column measured on the
> current item enters either block.

---

## The screen, and what it can and cannot conclude

A remark on method, because an earlier version of this plan got the statistic
wrong.

The theory needs a **linear** coupling between `Phi_r` and `Phi_s` in the
*learned* representation. It says nothing directly about the raw columns. A test
on raw columns with a linear head would be a one-layer model — not the
experiment, and not what the reviewers asked for.

But there is one thing the raw columns settle for free. If `Phi_r` is a function
of the r-columns alone and `Phi_s` a function of the s-columns alone, then

> `r` ⊥ `s` given `(y, g)`  ⟹  `Phi_r` ⊥ `Phi_s` given `(y, g)`, for *any*
> deterministic `Phi_r`, `Phi_s`.

No network can manufacture coupling that is not present in the raw data. So
conditional dependence in the raw columns is a genuine **necessary condition**,
and it costs seconds to test. What it is *not* is sufficient: raw dependence may
be nonlinear, and turning it into the linear relation the theory needs is
precisely what the trained representation might do.

So the screen tests **dependence of any form** — not linear `R²` — within each
`(y, g)` cell, against a permutation null. Linearity is measured later, on
`Phi`, after the two-branch extractor is trained.

| stage | measured on | cost | question |
|---|---|---|---|
| screen | raw columns | seconds | is there any conditional dependence at all? |
| coupling | `Phi`, two-branch | hours | is it linear, and does `A` differ by group? |
| rates | `Phi`, last layer | hours | does the measured `alpha` predict the observed exponent? |

Only datasets passing the screen get an extractor trained.

---

## Sign-off

| | |
|---|---|
| drafted | 2026-07-30 |
| approved by | _pending_ |
| commit fixing this file | _pending_ |

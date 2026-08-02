# Screen — does the r -> s relation differ across groups?

Delta R-squared is the out-of-sample gain from giving the model the group label, after r and s are centred within each (y, g) cell so that a mere difference in level cannot produce it. The null reassigns whole clusters to groups.

| dataset | groups | n used | y | delta R2 | null mean | p | z | passes |
|---|---|---|---|---|---|---|---|---|
| acsincome | 51 | 200,000 | 0 | +0.0013 | -0.0003 | 0.0476 | +4.72 | yes |
| acsincome | 51 | 200,000 | 1 | +0.0020 | -0.0003 | 0.0476 | +5.30 | yes |
| readmission | 3 | 62,880 | 0 | +0.0000 | -0.0000 | 0.4762 | +0.34 | NO |
| readmission | 3 | 62,880 | 1 | +0.0004 | +0.0001 | 0.4286 | +0.49 | NO |
| assistments | 147 | 197,295 | 0 | -0.0463 | -0.1134 | 0.0476 | +1.49 | NO |
| assistments | 147 | 197,295 | 1 | -0.0262 | -0.1048 | 0.0476 | +3.63 | NO |

## Ranking (train in this order)

1. **acsincome** — effect size +0.0016, passes
2. **readmission** — effect size +0.0002, DOES NOT PASS
3. **assistments** — effect size -0.0362, DOES NOT PASS

## Level versus relation

`level_only_delta` is how much of the group-aware advantage came from s sitting at a different level rather than from a different relation. A large value with a small relational delta means ordinary covariate shift, which this paper is not about.

- acsincome y=0: relational +0.0013, level-only +0.0492
- acsincome y=1: relational +0.0020, level-only +0.0285
- readmission y=0: relational +0.0000, level-only +0.0474
- readmission y=1: relational +0.0004, level-only +0.0254
- assistments y=0: relational -0.0463, level-only +0.1060
- assistments y=1: relational -0.0262, level-only +0.1922
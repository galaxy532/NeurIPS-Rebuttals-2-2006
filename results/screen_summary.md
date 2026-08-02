# Screen — does the r -> s relation differ across groups?

Delta R-squared is the out-of-sample gain from giving the model the group label, after r and s are centred within each (y, g) cell so that a mere difference in level cannot produce it. The null reassigns whole clusters to groups.

| dataset | groups | n used | y | delta R2 | null mean | p | z | passes |
|---|---|---|---|---|---|---|---|---|
| acsincome | 2 | 200,000 | 0 | +0.0009 | -0.0000 | 0.0476 | +3.43 | yes |
| acsincome | 2 | 200,000 | 1 | -0.0000 | -0.0000 | 0.4762 | -0.03 | NO |
| readmission | 2 | 60,297 | 0 | +0.0001 | -0.0000 | 0.0476 | +1.42 | yes |
| readmission | 2 | 60,297 | 1 | +0.0008 | -0.0000 | 0.0952 | +1.68 | NO |
| assistments | 147 | 197,278 | 0 | -0.0520 | -0.1163 | 0.0476 | +1.41 | NO |
| assistments | 147 | 197,278 | 1 | -0.0277 | -0.1058 | 0.0476 | +3.48 | NO |

## Ranking (train in this order)

1. **acsincome** — effect size +0.0004, DOES NOT PASS
2. **readmission** — effect size +0.0004, DOES NOT PASS
3. **assistments** — effect size -0.0399, DOES NOT PASS

## Read the effect size, not the p-value

These are large samples. At n = 200,000 the null spread is tiny, so a relational delta of 0.001 lands at z > 4 while explaining one tenth of one percent of the variance in s. Significance here says the effect is not exactly zero; it says nothing about whether it is big enough for the theory to bite. Rank on `delta R2`, and treat p only as a floor check.

## Level versus relation

`level_only` is how much of the group-aware advantage came from s sitting at a different level rather than from a different relation. A large value with a small relational delta means ordinary covariate shift, which this paper is not about. The share column is relational / (relational + level): the fraction of the group effect that is about the operator.

| dataset | y | relational | level-only | relational share |
|---|---|---|---|---|
| acsincome | 0 | +0.0009 | +0.0037 | 19.8% |
| acsincome | 1 | -0.0000 | +0.0027 | 1.4% |
| readmission | 0 | +0.0001 | +0.0370 | 0.2% |
| readmission | 1 | +0.0008 | +0.0270 | 2.8% |
| assistments | 0 | -0.0520 | +0.1135 | 31.4% |
| assistments | 1 | -0.0277 | +0.1960 | 12.4% |
# Screen — does the r -> s relation differ across groups?

Delta R-squared is the out-of-sample gain from giving the model the group label, after r and s are centred within each (y, g) cell so that a mere difference in level cannot produce it. The null reassigns whole clusters to groups.

| dataset | groups | n used | y | delta R2 | null mean | p | z | passes |
|---|---|---|---|---|---|---|---|---|
| acsincome | 51 | 200,000 | 0 | +0.0013 | -0.0003 | 0.0476 | +4.72 | yes |
| acsincome | 51 | 200,000 | 1 | +0.0020 | -0.0003 | 0.0476 | +5.30 | yes |

## Ranking (train in this order)

1. **acsincome** — effect size +0.0016, passes

## Level versus relation

`level_only_delta` is how much of the group-aware advantage came from s sitting at a different level rather than from a different relation. A large value with a small relational delta means ordinary covariate shift, which this paper is not about.

- acsincome y=0: relational +0.0013, level-only +0.0492
- acsincome y=1: relational +0.0020, level-only +0.0285
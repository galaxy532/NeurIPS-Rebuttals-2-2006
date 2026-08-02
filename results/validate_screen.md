# Validation — the heterogeneity screen

Run 2026-08-02T04:23:32.809021+00:00 on `nc8jacg86s`, Python 3.12.13.

| case | delta R2 | level-only | null mean | p | expected |
|---|---|---|---|---|---|
| power | +0.5156 | +0.0055 | -0.0025 | 0.0476 | delta >> 0, p small |
| calibration | -0.0003 | +0.0000 | -0.0007 | 0.4286 | delta ~ 0, p not small |
| level-only | -0.0000 | +0.4329 | -0.0025 | 0.1905 | delta ~ 0, level_only >> 0 |
| clustered null | -0.0076 | +0.0052 | -0.0063 | 0.7143 | p not small |
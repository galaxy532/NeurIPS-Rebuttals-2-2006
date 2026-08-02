# Dataset loading — filter chains

Every filter applied by `datasets.py`, and what it cost.

## acsincome

- <acsincome: n=1,664,500 dr=5 ds=3 eps=0.479 reps=51 clusters=1,664,500>

| field | value |
|---|---|
| `file` | acsincome_2018_all.csv.gz |
| `rows_raw` | 1664500 |
| `group_definition` | g = 1[SEX == 2] (female); G1 = male |
| `eps_natural` | 0.4793 |
| `min_cell` | 200 |
| `groups_before_min_cell` | 102 |
| `groups_after_min_cell` | 102 |
| `rows_dropped_by_min_cell` | 0 |
| `smallest_surviving_cell` | 333 |
| `states_surviving` | 51 |
| `nominal_note` | MAR and RELP are small nominal codes left as integers; the screen's model is tree-based and does not assume an ordering. |

## readmission

- <readmission: n=60,297 dr=5 ds=4 eps=0.365 clusters=60,297>

| field | value |
|---|---|
| `file` | diabetic_data.csv |
| `rows_raw` | 101766 |
| `rows_after_first_encounter` | 71518 |
| `encounters_dropped` | 30248 |
| `source_17_decodes_to` | NULL |
| `source_17_drop_justified` | True |
| `group_definition` | G1 = admission_source_id 7 (emergency room), G2 = 1 (physician referral) |
| `rows_dropped_other_sources` | 11221 |
| `eps_natural` | 0.365 |
| `positive_rate` | 0.08842894339685224 |
| `min_cell` | 200 |
| `groups_before_min_cell` | 2 |
| `groups_after_min_cell` | 2 |
| `rows_dropped_by_min_cell` | 0 |
| `smallest_surviving_cell` | 1875 |

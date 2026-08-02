# Data audit

Data root: `/notebooks/spurious_rebuttal_data`

5 tabular file(s), 53 other file(s).

## `acsincome/acsincome_2018_CA-NY-TX.csv.gz`

- size: 3.49 MB
- rows: 434,610 (exact)
- columns: 12
- read as: utf-8
- group `ST`: 3 distinct, 3 with >=200 rows, 3 with >=2000 rows
- group `y`: 2 distinct, 2 with >=200 rows, 2 with >=2000 rows

Column n-unique below is measured on the first 20k rows only. These files are written in blocks, so a block-sorted column (ACS is concatenated state by state) will look constant here and is not. Trust the group lines above, not this table, for cardinality.

| column | dtype | null frac | n unique | sample |
|---|---|---|---|---|
| `AGEP` | float64 | 0.0 | 74 | 30.0, 21.0, 65.0 |
| `COW` | float64 | 0.0 | 8 | 6.0, 4.0, 2.0 |
| `SCHL` | float64 | 0.0 | 24 | 14.0, 16.0, 22.0 |
| `MAR` | float64 | 0.0 | 5 | 1.0, 5.0, 3.0 |
| `OCCP` | float64 | 0.0 | 507 | 9610.0, 1970.0, 2040.0 |
| `POBP` | float64 | 0.0 | 190 | 6.0, 36.0, 17.0 |
| `RELP` | float64 | 0.0 | 17 | 16.0, 17.0, 0.0 |
| `WKHP` | float64 | 0.0 | 93 | 40.0, 20.0, 8.0 |
| `SEX` | float64 | 0.0 | 2 | 1.0, 2.0 |
| `RAC1P` | float64 | 0.0 | 8 | 8.0, 1.0, 9.0 |
| `ST` | int64 | 0.0 | 1 | 6 |
| `y` | int64 | 0.0 | 2 | 0, 1 |

## `acsincome/acsincome_2018_all.csv.gz`

- size: 13.12 MB
- rows: 1,664,500 (exact)
- columns: 12
- read as: utf-8
- group `ST`: 51 distinct, 51 with >=200 rows, 51 with >=2000 rows
- group `y`: 2 distinct, 2 with >=200 rows, 2 with >=2000 rows

Column n-unique below is measured on the first 20k rows only. These files are written in blocks, so a block-sorted column (ACS is concatenated state by state) will look constant here and is not. Trust the group lines above, not this table, for cardinality.

| column | dtype | null frac | n unique | sample |
|---|---|---|---|---|
| `AGEP` | float64 | 0.0 | 74 | 18.0, 53.0, 41.0 |
| `COW` | float64 | 0.0 | 8 | 1.0, 5.0, 6.0 |
| `SCHL` | float64 | 0.0 | 23 | 18.0, 17.0, 16.0 |
| `MAR` | float64 | 0.0 | 5 | 5.0, 4.0, 3.0 |
| `OCCP` | float64 | 0.0 | 503 | 4720.0, 3605.0, 7330.0 |
| `POBP` | float64 | 0.0 | 149 | 13.0, 18.0, 1.0 |
| `RELP` | float64 | 0.0 | 18 | 17.0, 16.0, 0.0 |
| `WKHP` | float64 | 0.0 | 87 | 21.0, 40.0, 2.0 |
| `SEX` | float64 | 0.0 | 2 | 2.0, 1.0 |
| `RAC1P` | float64 | 0.0 | 8 | 2.0, 1.0, 9.0 |
| `ST` | int64 | 0.0 | 1 | 1 |
| `y` | int64 | 0.0 | 2 | 0, 1 |

## `assistments/2012-2013-data-with-predictions-4-final.csv`

- size: 3009.49 MB
- rows: 6,123,270 (exact)
- columns: 35
- read as: utf-8
- **multi-line fields present**: 82,773,406 physical lines vs 6,123,270 rows
- group `school_id`: 661 distinct, 414 with >=200 rows, 243 with >=2000 rows

Column n-unique below is measured on the first 20k rows only. These files are written in blocks, so a block-sorted column (ACS is concatenated state by state) will look constant here and is not. Trust the group lines above, not this table, for cardinality.

| column | dtype | null frac | n unique | sample |
|---|---|---|---|---|
| `problem_log_id` | int64 | 0.0 | 20000 | 137792159, 138083797, 142332619 |
| `skill` | str | 0.5584 | 172 | Rounding, Multiplication and Division Integers, Proportion |
| `problem_id` | int64 | 0.0 | 15400 | 557460, 365981, 426415 |
| `user_id` | int64 | 0.0 | 10559 | 61394, 76592, 77966 |
| `assignment_id` | int64 | 0.0 | 11131 | 565736, 573819, 734130 |
| `assistment_id` | int64 | 0.0 | 14516 | 341511, 204043, 247525 |
| `start_time` | str | 0.0 | 19977 | 2012-09-28 15:11:27, 2012-10-09 11:01:52, 2013-03-07 10:53:20 |
| `end_time` | str | 0.0 | 20000 | 2012-09-28 15:11:36.856, 2012-10-09 11:02:13.182, 2013-03-07 10:53:28.661 |
| `problem_type` | str | 0.0 | 6 | choose_1, algebra, fill_in_1 |
| `original` | int64 | 0.0 | 2 | 1, 0 |
| `correct` | float64 | 0.0 | 5 | 1.0, 0.0, 0.25 |
| `bottom_hint` | float64 | 0.01 | 2 | 0.0, 1.0 |
| `hint_count` | int64 | 0.0 | 9 | 0, 4, 3 |
| `actions` | str | 0.0 | 20000 | --- 
- - start
  - 1348859487561
  - "95, --- 
- - start
  - 1349794912269
  - "62, --- 
- - start
  - 1362671600405
  - "74 |
| `attempt_count` | int64 | 0.0 | 26 | 1, 2, 13 |
| `ms_first_response` | int64 | 0.0 | 17323 | 9852, 21175, 8645 |
| `tutor_mode` | str | 0.0 | 2 | tutor, test |
| `sequence_id` | int64 | 0.0 | 5647 | 55482, 34221, 39601 |
| `student_class_id` | int64 | 0.0 | 1386 | 23643, 22967, 26303 |
| `position` | int64 | 0.0 | 882 | 4, 5, 58 |
| `type` | str | 0.0 | 6 | LinearSection, MasterySection, RandomChildOrderSection |
| `base_sequence_id` | int64 | 0.0 | 4935 | 55482, 34221, 39601 |
| `skill_id` | float64 | 0.5443 | 204 | 54.0, 279.0, 79.0 |
| `teacher_id` | int64 | 0.0 | 730 | 53472, 47424, 152676 |
| `school_id` | int64 | 0.0 | 381 | 5048, 7561, 4986 |
| `overlap_time` | int64 | 0.0 | 17331 | 9852, 21175, 8645 |
| `template_id` | int64 | 0.0 | 9575 | 341511, 204043, 247525 |
| `answer_id` | float64 | 0.9987 | 26 | 57641.0, 495318.0, 214815.0 |
| `answer_text` | str | 0.048 | 6871 | she, 74.29, 00 |
| `first_action` | int64 | 0.0 | 3 | 0, 1, 2 |
| `problemlogid` | int64 | 0.0 | 20000 | 137792159, 138083797, 142332619 |
| `Average_confidence(FRUSTRATED)` | float64 | 0.0 | 87 | 0.361323, 0.775, 0.805195 |
| `Average_confidence(CONFUSED)` | float64 | 0.0 | 151 | 0.0, 0.4558825, 0.96875 |
| `Average_confidence(CONCENTRATING)` | float64 | 0.0 | 76 | 0.336529, 0.766925, 0.4594992857142857 |
| `Average_confidence(BORED)` | float64 | 0.0 | 518 | 0.0, 0.442968, 0.912281 |

## `readmission/IDS_mapping.csv`

- size: 0.0 MB
- rows: 67 (exact)
- columns: 2
- read as: utf-8

Column n-unique below is measured on the first 20k rows only. These files are written in blocks, so a block-sorted column (ACS is concatenated state by state) will look constant here and is not. Trust the group lines above, not this table, for cardinality.

| column | dtype | null frac | n unique | sample |
|---|---|---|---|---|
| `admission_type_id` | str | 0.0299 | 32 | 1, 2, 3 |
| `description` | str | 0.0746 | 58 | Emergency, Urgent, Elective |

## `readmission/diabetic_data.csv`

- size: 19.16 MB
- rows: 101,766 (exact)
- columns: 50
- read as: utf-8
- group `admission_source_id`: 17 distinct, 7 with >=200 rows, 5 with >=2000 rows
- group `readmitted`: 3 distinct, 3 with >=200 rows, 3 with >=2000 rows

Column n-unique below is measured on the first 20k rows only. These files are written in blocks, so a block-sorted column (ACS is concatenated state by state) will look constant here and is not. Trust the group lines above, not this table, for cardinality.

| column | dtype | null frac | n unique | sample |
|---|---|---|---|---|
| `encounter_id` | int64 | 0.0 | 20000 | 2278392, 149190, 64410 |
| `patient_nbr` | int64 | 0.0 | 15262 | 8222157, 55629189, 86047875 |
| `race` | str | 0.0 | 6 | Caucasian, AfricanAmerican, ? |
| `gender` | str | 0.0 | 2 | Female, Male |
| `age` | str | 0.0 | 10 | [0-10), [10-20), [20-30) |
| `weight` | str | 0.0 | 10 | ?, [75-100), [50-75) |
| `admission_type_id` | int64 | 0.0 | 7 | 6, 1, 2 |
| `discharge_disposition_id` | int64 | 0.0 | 20 | 25, 1, 3 |
| `admission_source_id` | int64 | 0.0 | 10 | 1, 7, 2 |
| `time_in_hospital` | int64 | 0.0 | 14 | 1, 3, 2 |
| `payer_code` | str | 0.0 | 1 | ? |
| `medical_specialty` | str | 0.0 | 52 | Pediatrics-Endocrinology, ?, InternalMedicine |
| `num_lab_procedures` | int64 | 0.0 | 109 | 41, 59, 11 |
| `num_procedures` | int64 | 0.0 | 7 | 0, 5, 1 |
| `num_medications` | int64 | 0.0 | 62 | 1, 18, 13 |
| `number_outpatient` | int64 | 0.0 | 15 | 0, 2, 1 |
| `number_emergency` | int64 | 0.0 | 12 | 0, 1, 2 |
| `number_inpatient` | int64 | 0.0 | 14 | 0, 1, 2 |
| `diag_1` | str | 0.0 | 538 | 250.83, 276, 648 |
| `diag_2` | str | 0.0 | 509 | ?, 250.01, 250 |
| `diag_3` | str | 0.0 | 566 | ?, 255, V27 |
| `number_diagnoses` | int64 | 0.0 | 9 | 1, 9, 6 |
| `max_glu_serum` | str | 0.8962 | 3 | >300, Norm, >200 |
| `A1Cresult` | str | 0.8149 | 3 | >7, >8, Norm |
| `metformin` | str | 0.0 | 4 | No, Steady, Up |
| `repaglinide` | str | 0.0 | 4 | No, Up, Steady |
| `nateglinide` | str | 0.0 | 2 | No, Steady |
| `chlorpropamide` | str | 0.0 | 4 | No, Steady, Down |
| `glimepiride` | str | 0.0 | 4 | No, Steady, Down |
| `acetohexamide` | str | 0.0 | 1 | No |
| `glipizide` | str | 0.0 | 4 | No, Steady, Up |
| `glyburide` | str | 0.0 | 4 | No, Steady, Up |
| `tolbutamide` | str | 0.0 | 2 | No, Steady |
| `pioglitazone` | str | 0.0 | 4 | No, Steady, Up |
| `rosiglitazone` | str | 0.0 | 4 | No, Steady, Up |
| `acarbose` | str | 0.0 | 3 | No, Steady, Up |
| `miglitol` | str | 0.0 | 2 | No, Steady |
| `troglitazone` | str | 0.0 | 2 | No, Steady |
| `tolazamide` | str | 0.0 | 3 | No, Steady, Up |
| `examide` | str | 0.0 | 1 | No |
| `citoglipton` | str | 0.0 | 1 | No |
| `insulin` | str | 0.0 | 4 | No, Up, Steady |
| `glyburide-metformin` | str | 0.0 | 4 | No, Steady, Down |
| `glipizide-metformin` | str | 0.0 | 1 | No |
| `glimepiride-pioglitazone` | str | 0.0 | 1 | No |
| `metformin-rosiglitazone` | str | 0.0 | 1 | No |
| `metformin-pioglitazone` | str | 0.0 | 1 | No |
| `change` | str | 0.0 | 2 | No, Ch |
| `diabetesMed` | str | 0.0 | 2 | No, Yes |
| `readmitted` | str | 0.0 | 3 | NO, >30, <30 |

## Other files

- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p01.csv` (33.21 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p02.csv` (4.66 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p04.csv` (49.11 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p05.csv` (21.15 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p06.csv` (267.3 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p08.csv` (39.42 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p09.csv` (25.56 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p10.csv` (6.42 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p12.csv` (142.29 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p13.csv` (70.58 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p15.csv` (10.1 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p16.csv` (11.66 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p17.csv` (88.63 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p18.csv` (47.25 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p19.csv` (22.51 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p20.csv` (20.63 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p21.csv` (31.68 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p22.csv` (30.42 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p23.csv` (9.28 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p24.csv` (42.22 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p25.csv` (49.5 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p26.csv` (69.44 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p27.csv` (38.78 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p28.csv` (20.23 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p29.csv` (43.5 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p30.csv` (7.22 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p31.csv` (13.59 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p32.csv` (20.4 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p33.csv` (9.7 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p34.csv` (62.43 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p35.csv` (13.44 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p36.csv` (138.18 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p37.csv` (71.79 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p38.csv` (5.46 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p39.csv` (83.31 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p40.csv` (26.25 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p41.csv` (29.58 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p42.csv` (90.15 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p44.csv` (7.39 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p45.csv` (34.86 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p46.csv` (6.22 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p47.csv` (47.5 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p48.csv` (188.14 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p49.csv` (22.03 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p50.csv` (4.5 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p51.csv` (59.68 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p53.csv` (53.58 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p54.csv` (12.58 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p55.csv` (41.58 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p56.csv` (4.02 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/acs/2018/1-Year/psam_p72.csv` (19.77 MB) — raw PUMS cache, not audited
- `/notebooks/spurious_rebuttal_data/assistments/archive.zip` (659.05 MB)
- `/notebooks/spurious_rebuttal_data/readmission/diabetes+130-us+hospitals+for+years+1999-2008.zip` (3.17 MB)
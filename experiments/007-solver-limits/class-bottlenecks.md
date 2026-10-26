# Per-class internal adjacency and baselines (experiment 007)

Internal = cell-adjacent pairs of the class within one scene map (A/B/C). n-1 is the spanning-tree
minimum for a connected region; it is NOT a lower bound on shared adjacency. Baseline = expected
shared adjacencies under independent uniform class-respecting placements (AB shown; 'all' = AB+AC+BC
with cross terms split between the two classes). Pigeonhole = max(0, e_A + e_B - C(n,2)), which
is the only counting bound on same-class pairs, and it is 0 for every class here.

## Scene set A

| class | n | internal A/B/C | components A/B/C | n-1 | pigeonhole AB | baseline AB (class share) | baseline all pairs (class share) |
|---|---|---|---|---|---|---|---|
| ME | 24 | 37/34/37 | 1/1/1 | 23 | 0 | 4.73 | 14.57 |
| SK | 21 | 22/24/23 | 1/1/1 | 20 | 0 | 3.51 | 10.9 |
| DP | 10 | 9/9/10 | 2/3/1 | 9 | 0 | 2.86 | 8.93 |
| FO | 9 | 6/4/5 | 3/5/4 | 8 | 0 | 1.56 | 5.01 |
| S/ | 2 | 0/0/0 | 2/2/2 | 1 | 0 | 0.96 | 3.0 |
| RU | 2 | 0/0/0 | 2/2/2 | 1 | 0 | 0.69 | 2.71 |
| PH | 1 | 0/0/0 | 1/1/1 | 0 | 0 | 0.6 | 2.29 |
| SN | 1 | 0/0/0 | 1/1/1 | 0 | 0 | 0.55 | 2.12 |
| F/ | 2 | 0/0/0 | 2/2/2 | 1 | 0 | 0.43 | 1.46 |
| F\ | 2 | 0/0/0 | 2/2/2 | 1 | 0 | 0.4 | 1.38 |
| SU | 1 | 0/0/0 | 1/1/1 | 0 | 0 | 0.46 | 1.04 |
| HL | 1 | 0/0/0 | 1/1/1 | 0 | 0 | 0.2 | 0.9 |
| HB | 1 | 0/0/0 | 1/1/1 | 0 | 0 | 0.25 | 0.85 |
| S\ | 1 | 0/0/0 | 1/1/1 | 0 | 0 | 0.19 | 0.76 |
| HD | 2 | 0/0/0 | 2/2/2 | 1 | 0 | 0.4 | 0.75 |

| pair | random-placement baseline (mean) | forced floor (rigorous) | forced notes |
|---|---|---|---|
| AB | 17.81 | 0 | - |
| AC | 19.02 | 2 | R2 PH touches all 2 RU pieces in both maps |
| BC | 19.82 | 3 | R3 singletons HB-HL adjacent in both maps; R2 SN touches all 2 S/ pieces in both maps |

## Scene set B

| class | n | internal A/B/C | components A/B/C | n-1 | pigeonhole AB | baseline AB (class share) | baseline all pairs (class share) |
|---|---|---|---|---|---|---|---|
| OC | 9 | 11/9/7 | 1/1/2 | 8 | 0 | 3.49 | 8.1 |
| BL | 12 | 8/7/5 | 4/5/7 | 11 | 0 | 1.79 | 4.49 |
| TE | 11 | 9/10/1 | 3/3/10 | 10 | 0 | 2.25 | 3.98 |
| GT | 7 | 5/7/0 | 2/1/7 | 6 | 0 | 1.93 | 2.96 |
| GD | 5 | 1/1/0 | 4/4/5 | 4 | 0 | 1.34 | 2.58 |
| NT | 10 | 7/4/1 | 4/6/9 | 9 | 0 | 1.04 | 2.48 |
| GB | 6 | 2/1/0 | 4/5/6 | 5 | 0 | 1.27 | 2.4 |
| DK | 3 | 0/1/0 | 3/2/3 | 2 | 0 | 0.62 | 1.54 |
| OG | 3 | 0/1/1 | 3/2/2 | 2 | 0 | 0.67 | 1.53 |
| CB | 3 | 0/0/0 | 3/3/3 | 2 | 0 | 0.5 | 1.31 |
| CR | 4 | 0/0/0 | 4/4/4 | 3 | 0 | 0.33 | 0.88 |
| GR | 3 | 1/0/0 | 2/3/3 | 2 | 0 | 0.21 | 0.83 |
| DT | 3 | 1/0/0 | 2/3/3 | 2 | 0 | 0.37 | 0.67 |
| SU | 1 | 0/0/0 | 1/1/1 | 0 | 0 | 0.0 | 0.13 |

| pair | random-placement baseline (mean) | forced floor (rigorous) | forced notes |
|---|---|---|---|
| AB | 15.78 | 0 | - |
| AC | 8.77 | 0 | - |
| BC | 9.34 | 0 | - |

## Scene set A: AB shared adjacencies by class pair

Random baseline vs solver mean over seeds (classes mode). Columns: none 300,000, none 2,000,000, quarter 2,000,000.

| class pair | baseline AB | none 300,000 | none 2,000,000 | quarter 2,000,000 |
|---|---|---|---|---|
| ME / ME | 4.56 | 2.80 | 2.60 | 0.00 |
| SK / SK | 2.51 | 2.00 | 2.00 | 0.00 |
| DP / DP | 1.80 | 0.00 | 0.00 | 0.00 |
| S/ / SN | 1.00 | 1.00 | 1.00 | 1.00 |
| PH / RU | 1.00 | 1.00 | 1.00 | 1.00 |
| DP / FO | 0.98 | 2.00 | 2.00 | 0.40 |
| FO / FO | 0.67 | 0.00 | 0.00 | 0.00 |
| HB / HD | 0.50 | 0.00 | 0.00 | 0.00 |
| S/ / SU | 0.50 | 0.00 | 0.00 | 0.00 |
| S/ / SK | 0.43 | 0.00 | 0.00 | 0.00 |
| SK / SU | 0.43 | 0.00 | 0.00 | 0.00 |
| DP / HL | 0.40 | 0.00 | 0.00 | 0.00 |

## Scene set B: AB shared adjacencies by class pair

Random baseline vs solver mean over seeds (classes mode). Columns: none 300,000, none 2,000,000, quarter 2,000,000.

| class pair | baseline AB | none 300,000 | none 2,000,000 | quarter 2,000,000 |
|---|---|---|---|---|
| OC / OC | 2.75 | 0.00 | 0.00 | 0.00 |
| GT / GT | 1.67 | 0.00 | 0.00 | 0.00 |
| TE / TE | 1.64 | 1.00 | 1.00 | 0.00 |
| OC / OG | 1.33 | 0.00 | 0.00 | 0.00 |
| GB / GD | 1.33 | 0.00 | 0.00 | 0.00 |
| DK / GD | 1.07 | 0.00 | 0.00 | 0.00 |
| BL / BL | 0.85 | 1.60 | 1.80 | 0.00 |
| BL / CB | 0.83 | 0.20 | 0.20 | 0.20 |
| BL / GB | 0.83 | 1.00 | 1.00 | 0.00 |
| NT / NT | 0.62 | 0.00 | 0.00 | 0.00 |
| DT / TE | 0.61 | 1.00 | 1.00 | 0.00 |
| GR / NT | 0.33 | 1.00 | 1.00 | 0.00 |

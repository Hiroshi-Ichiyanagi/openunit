# openunit vintage `v0.3-unwpp-2026-05-15` -- sources & provenance

**Status: REAL DATA.** Population is read from the UN Population Division's own *World Population Prospects 2024* file (not a republication); FX is the same ECB data as `v0.1-2026-05-15`. Re-running `make_vintages.py` reproduces `spec.json` and `artifact.json` byte for byte.

- `input_digest`  : `sha256:9c29dcf536eec7c81a629a5fc97af044d578d31909b0ba83817edf72866780ec`
- `artifact_hash` : `sha256:63812b17a3a73666fad42ab5e53418e4c376802f2c94b1ca0d306f269aabc04f`
- **1 openunit = 0.985654 USD**

## Supersedes `v0.1-2026-05-15`

This vintage is a correction of `v0.1-2026-05-15` (`artifact_hash` `sha256:1e615cf7cffe025667c98150cfb2010ed368bf838fe3b14fd460b05974839a3a`). That vintage is **not rewritten**: its files and hashes stay exactly as published and it still verifies -- verification proves reproduction, not correctness. The link is recorded in this vintage's `spec.json` (`supersedes`, hashed) and in `data/vintages.json`. Reasons:

- `EURO_AREA_MEMBERSHIP` -- v0.1 counts 20 euro-area member states; Bulgaria joined the euro area on 2026-01-01, so on both FX dates (2026-01-09, 2026-05-15) it had 21 members.
- `POPULATION_VIA_REPUBLISHER` -- v0.1 took the UN WPP 2024 figures from Worldometer's republication; this vintage reads the UN Population Division's own file.
- `POPULATION_MISMATCH` -- 2 of v0.1's 25 populations differ from the UN file: Greece 9897115 (v0.1) vs 9897116 (UN); Slovenia 2114573 (v0.1) vs 2114574 (UN).

## Population (UN World Population Prospects 2024, primary file)

| field | value |
|---|---|
| source | United Nations, Department of Economic and Social Affairs, Population Division (2024). World Population Prospects 2024, Online Edition. |
| file | `WPP2024_Demographic_Indicators_Medium.csv.gz` |
| url | <https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20%28Standard%29/CSV_FILES/WPP2024_Demographic_Indicators_Medium.csv.gz> |
| file_bytes | 16557272 |
| file_sha256 | `286ac36bb1415e2e1ade03acfef0a29f0e4c087e2f78e38c48f50c5df89082bc` |
| server_last_modified | Fri, 13 Dec 2024 19:11:17 GMT |
| retrieved | 2026-10-26 |
| licence | CC BY 3.0 IGO |
| variant | Medium |
| field | TPopulation1July (thousands of persons, total population on 1 July) |
| time | 2026 |
| reference_date | 2026-07-01 |
| extract | `data/sources/un_wpp2024_population_2026.csv` |
| extract_sha256 | `cc41a3b2bc61eb17343532506380035487d2f599d5e255682751fb1c4e0a2160` |

- Licence: CC BY 3.0 IGO (Copyright (c) 2024 by United Nations), <http://creativecommons.org/licenses/by/3.0/igo/>. Attribution: *United Nations, Department of Economic and Social Affairs, Population Division (2024). World Population Prospects 2024, Online Edition.* Changes made by openunit: 26 rows selected (Time=2026, Medium; the basket economies and the euro-area members); thousands converted to persons; no other modification. The raw file is **not** redistributed here; only the extract `data/sources/un_wpp2024_population_2026.csv` is.
- WPP 2024 estimates run to 2023; 2026 values are medium-variant projections for 1 July 2026 (the same reference v0.1 used).
- The WPP 2024 interim update released on 19 January 2026 revises Togo only; none of the locations used here changed.
- Download page: <https://population.un.org/wpp/downloads?folder=Standard%20Projections&group=CSV%20format>. The UN data-portal API was not used (it answered HTTP 401 without an account token).

| economy | UN location | population |
|---|---|---|
| United States (USD) | United States of America (USA) | 349035494 |
| Euro area (EUR) | sum of 21 members (below) | 354408517 |
| China (CNY) | China (CHN) | 1412914089 |
| Japan (JPY) | Japan (JPN) | 122427731 |
| United Kingdom (GBP) | United Kingdom (GBR) | 69931528 |
| India (INR) | India (IND) | 1476625576 |

### Euro area = sum of 21 member states (as of 2026-05-15)

Membership source: ECB, <https://www.ecb.europa.eu/euro/intro/html/index.en.html> (read 2026-10-26). Bulgaria joined the euro area on 2026-01-01 at the irrevocably fixed rate BGN 1.95583 = EUR 1 (https://www.ecb.europa.eu/euro/changeover/bulgaria/html/index.en.html). Both FX dates fall after accession, so Bulgaria's population is valued at the EUR rate on both legs.

| member | ISO3 | UN `TPopulation1July` (thousands) | population |
|---|---|---|---|
| Austria | AUT | 9107.266 | 9107266 |
| Belgium | BEL | 11774.642 | 11774642 |
| Bulgaria | BGR | 6667.66 | 6667660 |
| Cyprus | CYP | 1382.334 | 1382334 |
| Germany | DEU | 83644.258 | 83644258 |
| Spain | ESP | 47850.793 | 47850793 |
| Estonia | EST | 1331.062 | 1331062 |
| Finland | FIN | 5621.739 | 5621739 |
| France | FRA | 66746.401 | 66746401 |
| Greece | GRC | 9897.116 | 9897116 |
| Croatia | HRV | 3822.345 | 3822345 |
| Ireland | IRL | 5356.95 | 5356950 |
| Italy | ITA | 58926.166 | 58926166 |
| Lithuania | LTU | 2797.338 | 2797338 |
| Luxembourg | LUX | 687.448 | 687448 |
| Latvia | LVA | 1835.935 | 1835935 |
| Malta | MLT | 549.011 | 549011 |
| Netherlands | NLD | 18448.775 | 18448775 |
| Portugal | PRT | 10395.362 | 10395362 |
| Slovakia | SVK | 5451.342 | 5451342 |
| Slovenia | SVN | 2114.574 | 2114574 |
| **euro area total** | | | **354408517** |

## Foreign exchange (ECB euro reference rates; same as `v0.1-2026-05-15`)

| currency | per EUR @ 2026-01-09 | per EUR @ 2026-05-15 |
|---|---|---|
| EUR | 1 (base) | 1 (base) |
| USD | 1.1642 | 1.1628 |
| JPY | 183.52 | 184.36 |
| GBP | 0.8677 | 0.8705 |
| CNY | 8.1288 | 7.9194 |
| INR | 105.0335 | 111.594 |

- baseline: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml
- valuation: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
- conversion: `usd_per_unit(C) = (USD per EUR) / (C per EUR)`, with `USD=1` and `EUR=(USD per EUR)`.

## Did v0.1's Worldometer numbers match the UN file?

**23 of 25 matched exactly; 2 did not.** Each v0.1 population (5 economies + 20 euro-area members, transcribed from Worldometer) was compared with `TPopulation1July x 1000` in the UN file:

| economy | v0.1 (Worldometer) | UN file | difference |
|---|---|---|---|
| Greece | 9897115 | 9897116 | +1 |
| Slovenia | 2114573 | 2114574 | +1 |

The cause of the 1-person differences is not established from the UN file alone (for Greece, the file's male + female columns sum to 9897.115 thousand while its total column says 9897.116; for Slovenia both say 2114.574). Separately, v0.1 omits Bulgaria (6667660 persons), a euro-area member on both of its FX dates.

## Difference from `v0.1-2026-05-15`

| step | euro-area members | 1 openunit (USD) | change vs v0.1 |
|---|---|---|---|
| v0.1 as published (Worldometer) | 20 | 0.985630795 | 0.0000% |
| UN file, v0.1's 20 members (not shipped) | 20 | 0.985630795 | 0.0000% |
| **UN file, 21 members (this vintage)** | 21 | 0.985653987 | 0.0024% |

Weights, in per cent (population share = realized weight at the pin; realized weight at the 2026-05-15 valuation):

| code | v0.1 share | v0.3 share | v0.1 at valuation | v0.3 at valuation |
|---|---|---|---|---|
| USD | 9.2370 | 9.2207 | 9.3716 | 9.3549 |
| EUR | 9.2027 | 9.3627 | 9.3257 | 9.4875 |
| CNY | 37.3918 | 37.3259 | 38.8932 | 38.8238 |
| JPY | 3.2400 | 3.2343 | 3.2683 | 3.2625 |
| GBP | 1.8507 | 1.8474 | 1.8694 | 1.8660 |
| INR | 39.0779 | 39.0090 | 37.2719 | 37.2053 |

The source change alone (same 20 members; Greece and Slovenia +1 person each) moves 1 openunit by 7.071e-10%. Adding Bulgaria moves it by a further 2.353e-3%: the euro area's population share rises and every other share falls in proportion. At the pin the shares are exactly the population shares; at valuation they drift with the ECB rates exactly as in v0.1.

## How to verify

```
python3 make_vintages.py --verify
python3 verify_independent.py data/v0.3-unwpp-2026-05-15/spec.json data/v0.3-unwpp-2026-05-15/artifact.json
# optional, with the raw UN file downloaded from the URL above:
python3 make_vintages.py --check-un-wpp WPP2024_Demographic_Indicators_Medium.csv.gz
```

`--check-un-wpp` checks the raw file's sha256 and re-derives `data/sources/un_wpp2024_population_2026.csv` from it byte for byte.

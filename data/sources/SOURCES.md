# `data/sources/` -- source extracts

Small extracts of primary source files, committed so that vintages can be
rebuilt and checked without the network. The raw files themselves are **not**
redistributed here; each extract records exactly where it came from, so anyone
can download the raw file, check its sha256, and re-derive the extract byte for
byte. This directory is not a vintage (it has no `spec.json`).

## `un_wpp2024_population_2026.csv`

Total population on 1 July 2026 (medium variant) for the 26 locations openunit
needs: China, India, Japan, the United Kingdom, the United States of America,
and the 21 euro-area member states on 2026-05-15 (Austria, Belgium, Bulgaria,
Croatia, Cyprus, Estonia, Finland, France, Germany, Greece, Ireland, Italy,
Latvia, Lithuania, Luxembourg, Malta, the Netherlands, Portugal, Slovakia,
Slovenia, Spain).

| field | value |
|---|---|
| publisher | United Nations, Department of Economic and Social Affairs, Population Division |
| dataset | World Population Prospects 2024 |
| raw file | `WPP2024_Demographic_Indicators_Medium.csv.gz` |
| url | <https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20%28Standard%29/CSV_FILES/WPP2024_Demographic_Indicators_Medium.csv.gz> |
| raw size | 16557272 bytes |
| raw sha256 | `286ac36bb1415e2e1ade03acfef0a29f0e4c087e2f78e38c48f50c5df89082bc` |
| server Last-Modified | Fri, 13 Dec 2024 19:11:17 GMT |
| retrieved | 2026-10-26 |
| rows used | `Variant = Medium`, `Time = 2026`, column `TPopulation1July` (thousands) |
| extract sha256 | `cc41a3b2bc61eb17343532506380035487d2f599d5e255682751fb1c4e0a2160` |
| used by | `data/v0.3-unwpp-2026-05-15/` |

Columns: `iso3`, `un_loc_id`, `location`, `variant`, `time`,
`tpopulation1july_thousands` (verbatim from the UN file), and
`population_persons` (derived: `tpopulation1july_thousands x 1000`, exact).

**Licence and attribution.** Copyright (c) 2024 by United Nations, made
available under a Creative Commons license CC BY 3.0 IGO:
<http://creativecommons.org/licenses/by/3.0/igo/>. Suggested citation: United
Nations, Department of Economic and Social Affairs, Population Division (2024).
*World Population Prospects 2024, Online Edition.* **Changes made by
openunit:** 26 rows selected; thousands converted to persons in an added
column; no value modified. The United Nations does not endorse openunit.

**Interim update.** The WPP 2024 interim update released on 19 January 2026
revises Togo only; none of the locations in this extract changed. The next WPP
revision was postponed to 11 July 2027 (both per the UN WPP download page,
read 2026-10-26).

**Re-derive it:**

```
python3 make_vintages.py --check-un-wpp /path/to/WPP2024_Demographic_Indicators_Medium.csv.gz
```

`make_vintages.py` refuses to build if the extract's sha256 or canonical form
changes, so the extract cannot drift silently.

# `data/sources/` -- source extracts

Small extracts of primary source files, committed so that vintages can be
rebuilt and checked without the network. Large raw files are **not**
redistributed here; each extract records exactly where it came from, so anyone
can download the raw file, check its sha256, and re-derive the extract byte for
byte. A small API response is committed whole, as received. This directory is
not a vintage (it has no `spec.json`).

## `un_wpp2024_population_2026.csv`

Total population on 1 July 2026 (medium variant) for the 26 locations Worldyard
(formerly openunit) needs: China, India, Japan, the United Kingdom, the United States of America,
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
| used by | `data/v0.3-unwpp-2026-05-15/`, `data/v0.4-ppp-unwpp-2026-05-15/` |

Columns: `iso3`, `un_loc_id`, `location`, `variant`, `time`,
`tpopulation1july_thousands` (verbatim from the UN file), and
`population_persons` (derived: `tpopulation1july_thousands x 1000`, exact).

**Licence and attribution.** Copyright (c) 2024 by United Nations, made
available under a Creative Commons license CC BY 3.0 IGO:
<http://creativecommons.org/licenses/by/3.0/igo/>. Suggested citation: United
Nations, Department of Economic and Social Affairs, Population Division (2024).
*World Population Prospects 2024, Online Edition.* **Changes made by
Worldyard (formerly openunit):** 26 rows selected; thousands converted to
persons in an added column; no value modified. The United Nations does not
endorse Worldyard (formerly openunit).

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

## `wb_pa_nus_ppp_2024_wdi-2026-10-08.json`

The World Bank API response with `PA.NUS.PPP` (*PPP conversion factor, GDP
(LCU per international $)*) for reference year 2024, for the five non-euro
basket economies, the 21 euro-area members and the euro-area aggregate `EMU`
(which is `null`). It is committed **verbatim** (the bytes as received, no
reformatting).

| field | value |
|---|---|
| publisher | World Bank, World Development Indicators (WDI) |
| url | `https://api.worldbank.org/v2/country/AUT;BEL;BGR;CHN;CYP;DEU;EMU;ESP;EST;FIN;FRA;GBR;GRC;HRV;IND;IRL;ITA;JPN;LTU;LUX;LVA;MLT;NLD;PRT;SVK;SVN;USA/indicator/PA.NUS.PPP?date=2024&format=json&footnote=y&per_page=100` |
| retrieved | 2026-10-26 (08:22 UTC) |
| WDI last updated | 2026-10-08 (the response's `lastupdated`) |
| size | 7316 bytes |
| sha256 | `b4db34d4ee9bfef0aa0efbc116bd587cbd480f9cfbfa34c85c845f42fe7aed0d` |
| licence | CC BY 4.0, <https://creativecommons.org/licenses/by/4.0/>; World Bank terms: <https://datacatalog.worldbank.org/public-licenses#cc-by> |
| used by | `data/v0.4-ppp-unwpp-2026-05-15/` |

The values are JSON numbers; `make_vintages.py` reads them as their exact
tokens (`parse_float=str`), never as floats. Each observation's `footnote` says
what it is: `Eurostat-OECD annual PPP` for the Eurostat-OECD PPP Programme's
annual PPPs (Japan, the United Kingdom, the euro-area members, and the United
States, whose factor is 1 by definition), and no footnote for China and India,
whose 2024 values are the ICP 2021 benchmark extrapolated by the World Bank
(see `docs/AUDIT.md`, 2026-10-26). Bulgaria's factor is stated in euros (WDI
country metadata: currency unit Euro, 1 EUR = 1.95583 BGN from 2026-01-01).

**Licence and attribution.** World Bank, World Development Indicators,
`PA.NUS.PPP`, CC BY 4.0. Unmodified. The World Bank does not endorse Worldyard
(formerly openunit).

A new request to the same URL may return a later WDI release with revised
values (the World Bank revised five of v0.2's 2024 values between its April and
July 2026 releases); the committed response is the one the vintage used.
`make_vintages.py` refuses to build if its sha256 or size changes.

# Worldyard vintage `v0.4-ppp-unwpp-2026-05-15` -- sources & provenance

*Worldyard was formerly called openunit; vintages built before the rename carry the method name `openunit`, this one `worldyard`. The unit and its formulas are the same.*

**Status: REAL DATA.** v0.2's PPP-aware method (population weights; nominal ECB FX on the baseline leg; PPP on the valuation leg, so the unit is read in international dollars) with the populations of `v0.3-unwpp-2026-05-15` (the UN Population Division's own WPP 2024 file, 21 euro-area members) and World Bank `PA.NUS.PPP` for reference year 2024, read from a pinned API response. Re-running `make_vintages.py` reproduces `spec.json` and `artifact.json` byte for byte.

- `input_digest`  : `sha256:52525ff9c13ae63ed7feae056ce6f22ed10b0731512779979bdbf72a9774ef3d`
- `artifact_hash` : `sha256:d0fa47764cc918bff0d567eb6528d7f8708f6c7e7ea143f6034004f8af69e175`
- **1 worldyard = 2.845044 international $**

## Supersedes `v0.2-ppp-2026-05-15`

This vintage is a correction of `v0.2-ppp-2026-05-15` (`artifact_hash` `sha256:566c95c1753dbcaa70bbfd58c295ced2117d4907d4d7aabb992d68a93f10b97a`). That vintage is **not rewritten**: its files and hashes stay exactly as published and it still verifies -- verification proves reproduction, not correctness. The link is recorded in this vintage's `spec.json` (`supersedes`, hashed) and in `data/vintages.json`. Reasons:

- `EURO_AREA_MEMBERSHIP` -- v0.2 counts 20 euro-area member states, in the headcount and in the PPP blend; Bulgaria joined the euro area on 2026-01-01, so on v0.2's FX date (2026-05-15) it had 21 members.
- `POPULATION_VIA_REPUBLISHER` -- v0.2 took the UN WPP 2024 figures from Worldometer's republication; this vintage reads the UN Population Division's own file (as v0.3-unwpp-2026-05-15).
- `POPULATION_MISMATCH` -- 2 of v0.2's 25 populations differ from the UN file: Greece 9897115 (v0.2) vs 9897116 (UN); Slovenia 2114573 (v0.2) vs 2114574 (UN).
- `PPP_LABEL` -- v0.2 labels its PA.NUS.PPP 2024 values 'ICP 2024'; no ICP 2024 results have been released (the latest ICP cycle is 2021, released May 2024). The values are the ICP 2021 benchmark extrapolated by the World Bank (China, India) or Eurostat-OECD annual PPPs (Japan, United Kingdom, euro-area members); the United States is 1 by definition.
- `PPP_REVISED` -- v0.2's PA.NUS.PPP values are WDI's April 2026 release; this vintage uses the release last updated 2026-10-08, in which 5 of them differ: China 3.5325492491585 -> 3.52537888953537; Croatia 0.44841971235566 -> 0.448418364962435; Cyprus 0.56709589608174 -> 0.567094524089419; India 20.4219876045922 -> 20.4522424138694; Malta 0.580522225637102 -> 0.580520850861783.

## What the PPP values are (not ICP 2024)

No ICP 2024 results have been released: the International Comparison Program's latest release is the ICP 2021 cycle (May 2024). The World Bank's WDI fills later years in two ways, and each 2024 observation in the API says which:

| economies | API footnote | what the 2024 value is |
|---|---|---|
| China, India | *(none)* | ICP 2021 benchmark, extrapolated to 2024 by the World Bank (WDI; change in the GDP deflator relative to the United States) |
| Japan, United Kingdom, the 21 euro-area members | `Eurostat-OECD annual PPP` | Eurostat-OECD PPP Programme annual PPP for 2024, as published in WDI |
| United States | `Eurostat-OECD annual PPP` | 1 by definition (the international dollar has the purchasing power of the US dollar in the United States) |

The World Bank says it will replace the extrapolations when the next ICP cycle's results are available, and between its April and July 2026 releases it revised five of v0.2's 2024 values (China and India most), so the 2024 values -- the extrapolations in particular -- are provisional. They are pinned here as published on the date retrieved. Sources (read 2026-10-26):

- <https://www.worldbank.org/en/programs/icp>
- <https://www.worldbank.org/en/programs/icp/faq>
- <https://api.worldbank.org/v2/sources/2/series/PA.NUS.PPP/metadata?format=json>
- <https://datahelpdesk.worldbank.org/knowledgebase/articles/665452-how-do-you-extrapolate-the-ppp-conversion-factors>
- full finding: `docs/AUDIT.md`, addendum of 2026-10-26

## World Bank `PA.NUS.PPP` 2024 (the pinned response)

| field | value |
|---|---|
| source | World Bank, World Development Indicators (WDI), PA.NUS.PPP: PPP conversion factor, GDP (LCU per international $) |
| url | `https://api.worldbank.org/v2/country/AUT;BEL;BGR;CHN;CYP;DEU;EMU;ESP;EST;FIN;FRA;GBR;GRC;HRV;IND;IRL;ITA;JPN;LTU;LUX;LVA;MLT;NLD;PRT;SVK;SVN;USA/indicator/PA.NUS.PPP?date=2024&format=json&footnote=y&per_page=100` |
| retrieved | 2026-10-26 |
| WDI last updated | 2026-10-08 |
| response | `data/sources/wb_pa_nus_ppp_2024_wdi-2026-10-08.json` (7316 bytes, verbatim) |
| response sha256 | `b4db34d4ee9bfef0aa0efbc116bd587cbd480f9cfbfa34c85c845f42fe7aed0d` |
| licence | CC BY 4.0, <https://datacatalog.worldbank.org/public-licenses#cc-by> |

PPP conversion factor = local-currency units per international $ (GDP basis); the valuation leg is `1 / factor`. Each factor is the JSON number token of the response, copied as a string. "v0.2" is the value v0.2 transcribed from WDI's April 2026 release.

| currency | economy | this vintage | v0.2 | basis |
|---|---|---|---|---|
| USD | United States | 1 | 1.0 | base |
| EUR | Euro area | 0.63814423018097442283503023151105592645788475788803 | 0.64294952371252610571162827560195652017937322895235 | blend of 21 members (below) |
| CNY | China | 3.52537888953537 | 3.5325492491585 | ICP 2021, extrapolated |
| JPY | Japan | 94.462599 | 94.462599 | Eurostat-OECD annual |
| GBP | United Kingdom | 0.664153 | 0.664153 | Eurostat-OECD annual |
| INR | India | 20.4522424138694 | 20.4219876045922 | ICP 2021, extrapolated |

The euro-area aggregate (`EMU`) is `null` in the response: the World Bank publishes no euro-area value.

### Euro area: population-weighted blend of 21 members

```
ppp(euro area) = sum(pop_i * ppp_i) / sum(pop_i)
```

Populations are the UN WPP 2024 figures of `v0.3-unwpp-2026-05-15` (the same numbers as the euro-area headcount). Weighting by **people** rather than GDP follows the one-person-one-vote stance; it is a **contestable value choice**, not a neutral fact (SPEC.md section 10). WDI states Bulgaria's PPP factor in euros (its country metadata gives the currency unit as the euro and the irrevocable rate 1 EUR = BGN 1.95583 from 2026-01-01); it is used as published, with no conversion here.

| member | ISO3 | population (UN) | PA.NUS.PPP 2024 | v0.2 |
|---|---|---|---|---|
| Austria | AUT | 9107266 | 0.710451 | 0.710451 |
| Belgium | BEL | 11774642 | 0.704288 | 0.704288 |
| Bulgaria | BGR | 6667660 | 0.387533240879461 | *(not in v0.2)* |
| Cyprus | CYP | 1382334 | 0.567094524089419 | 0.56709589608174 |
| Germany | DEU | 83644258 | 0.700862 | 0.700862 |
| Spain | ESP | 47850793 | 0.562107 | 0.562107 |
| Estonia | EST | 1331062 | 0.576166 | 0.576166 |
| Finland | FIN | 5621739 | 0.753945 | 0.753945 |
| France | FRA | 66746401 | 0.681239 | 0.681239 |
| Greece | GRC | 9897116 | 0.515086 | 0.515086 |
| Croatia | HRV | 3822345 | 0.448418364962435 | 0.44841971235566 |
| Ireland | IRL | 5356950 | 0.740894 | 0.740894 |
| Italy | ITA | 58926166 | 0.599627 | 0.599627 |
| Lithuania | LTU | 2797338 | 0.49104 | 0.49104 |
| Luxembourg | LUX | 687448 | 0.815579 | 0.815579 |
| Latvia | LVA | 1835935 | 0.496528 | 0.496528 |
| Malta | MLT | 549011 | 0.580520850861783 | 0.580522225637102 |
| Netherlands | NLD | 18448775 | 0.731421 | 0.731421 |
| Portugal | PRT | 10395362 | 0.515993 | 0.515993 |
| Slovakia | SVK | 5451342 | 0.501903 | 0.501903 |
| Slovenia | SVN | 2114574 | 0.550461 | 0.550461 |
| **euro area (blend)** | | **354408517** | **0.63814423018097442283503023151105592645788475788803** | 0.64294952371252610571162827560195652017937322895235 |

The GDP-weighted sensitivity recorded for v0.2 is not repeated here: it would need Bulgaria's GDP, which was not downloaded.

## Population and nominal FX

- Population: exactly the inputs of `v0.3-unwpp-2026-05-15` -- UN Population Division, *World Population Prospects 2024*, medium variant, `TPopulation1July` for 2026 (reference date 1 July 2026), from `data/sources/un_wpp2024_population_2026.csv` (CC BY 3.0 IGO); see that vintage's `SOURCES.md` and `data/sources/SOURCES.md`.
- Nominal FX (baseline leg): ECB euro reference rates on 2026-05-15, the same rates as v0.1, v0.2 and v0.3: USD 1.1628, JPY 184.36, GBP 0.8705, CNY 7.9194, INR 111.594 per EUR (<https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml>).
- conversion to the USD numeraire: `usd_per_unit(C) = (USD per EUR) / (C per EUR)`, with `USD=1` and `EUR=(USD per EUR)` (as in `spec.json`, `provenance.nominal_fx`).

## Input states (SPEC.md, "Data states and fallbacks")

Every input resolved at the target date 2026-05-15 under the declared rules; none is unavailable.

| input | observation date | state | age (days) | maximum age |
|---|---|---|---|---|
| ECB FX | 2026-05-15 | ok | 0 | 4 |
| UN WPP 2024 | 2024-07-11 | stale | 673 | 1461 |
| PA.NUS.PPP 2024 | 2024-07-01 | stale | 683 | 1096 |

The WPP 2024 release date is from UN DESA (<https://www.un.org/development/desa/pd/world-population-prospects-2024>, read 2026-10-26).

## Difference from `v0.2-ppp-2026-05-15`

Applied one at a time, in this order:

| step | euro-area members | 1 unit (int. $) | change vs v0.2 |
|---|---|---|---|
| v0.2 as published (Worldometer populations, WDI April 2026) | 20 | 2.848010114 | 0% |
| UN file populations, same 20 members, same PPP (not shipped) | 20 | 2.848010113 | -2.381e-8% |
| ... and PPP from WDI 2026-10-08 (not shipped) | 20 | 2.846759798 | -0.04390% |
| **... and Bulgaria: 21 members (this vintage)** | 21 | 2.845044466 | -0.1041% |

Weights, in per cent (population share = realized weight at the pin; realized weight at the PPP valuation):

| code | v0.2 share | v0.4 share | v0.2 at PPP | v0.4 at PPP |
|---|---|---|---|---|
| USD | 9.2370 | 9.2207 | 3.2433 | 3.2410 |
| EUR | 9.2027 | 9.3627 | 4.3221 | 4.4349 |
| CNY | 37.3918 | 37.3259 | 25.3124 | 25.3456 |
| JPY | 3.2400 | 3.2343 | 1.9094 | 1.9080 |
| GBP | 1.8507 | 1.8474 | 0.7325 | 0.7319 |
| INR | 39.0779 | 39.0090 | 64.4803 | 64.3385 |

## How to verify

```
python3 make_vintages.py --verify
python3 verify_independent.py data/v0.4-ppp-unwpp-2026-05-15/spec.json data/v0.4-ppp-unwpp-2026-05-15/artifact.json
```

`make_vintages.py` refuses to build if the World Bank response's sha256 or size changes, if a value is not a plain decimal token, if the footnotes no longer split the economies as above, or if the World Bank starts publishing a euro-area value. A fresh request to the URL above may return a later WDI release; the committed response is the one this vintage used.

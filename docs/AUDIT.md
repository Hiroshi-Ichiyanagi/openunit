# openunit — independent data audit

**Status: CONFIRMED.** Every published number in the shipped vintages
(`data/v0.1-2026-05-15`, `data/v0.2-ppp-2026-05-15`) was independently
re-derived from its primary source and matches, with **zero mismatches**.

- **Audit date:** 2026-06-10 *(addendum 2026-06-13: verbatim normalization — see
  the final section; the v0.1 hashes quoted below are the pre-normalization
  ones, accurate as of the audit date)*
- **Method:** each source was fetched fresh from its official endpoint and
  compared field-by-field against the constants transcribed in
  `make_vintages.py` and the raw tables in each vintage's `SOURCES.md`. FX and
  PPP are compared as exact `Decimal` values (so trailing-zero formatting is not
  a mismatch); populations are compared as exact strings.
- **Engine untouched:** this audit changed no engine code and no spec/artifact.
  The v0 sample artifact hash remains
  `sha256:433d5e9560f8dcf928c6d2aff9c48ecb9eba558d19fc8eff191056f3f18356bd`,
  and both vintage hashes are unchanged
  (`v0.1` `sha256:82bade1f…9655`, `v0.2` `sha256:566c95c1…b97a`).

---

## 1. Foreign exchange — ECB euro reference rates → **CONFIRMED**

- **Source:** European Central Bank, euro foreign exchange reference rates.
- **URL fetched:** <https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml>
  (full historical series; the daily/90-day feeds cited in `SOURCES.md` have
  rolled past these dates, which is exactly why the rates are pinned in the
  vintage).
- **Retrieved:** 2026-06-10 (file dated through 2026-06-09).
- **Result:** all 10 rates (USD/JPY/GBP/CNY/INR × baseline 2026-01-09 +
  valuation 2026-05-15) match the transcribed values exactly (numeric equality).

| leg | date | currency | transcribed | ECB official | match |
|---|---|---|---|---|---|
| baseline | 2026-01-09 | USD | 1.1642 | 1.1642 | ✅ |
| baseline | 2026-01-09 | JPY | 183.52 | 183.52 | ✅ |
| baseline | 2026-01-09 | GBP | 0.8677 | 0.8677 | ✅ |
| baseline | 2026-01-09 | CNY | 8.1288 | 8.1288 | ✅ |
| baseline | 2026-01-09 | INR | 105.0335 | 105.0335 | ✅ |
| valuation | 2026-05-15 | USD | 1.1628 | 1.1628 | ✅ |
| valuation | 2026-05-15 | JPY | 184.36 | 184.36 | ✅ |
| valuation | 2026-05-15 | GBP | 0.87050 | 0.8705 | ✅ (= numerically) |
| valuation | 2026-05-15 | CNY | 7.9194 | 7.9194 | ✅ |
| valuation | 2026-05-15 | INR | 111.5940 | 111.594 | ✅ (= numerically) |

> Note: `0.87050`/`111.5940` carry a cosmetic trailing zero in `SOURCES.md`;
> they parse to the identical `Decimal` the ECB publishes, so the hash and value
> are unaffected.

---

## 2. Population — UN World Population Prospects 2024 → **CONFIRMED**

- **Source:** United Nations, World Population Prospects 2024 Revision (medium
  variant), 2026 estimate, republished by Worldometer.
- **URL fetched:**
  <https://www.worldometers.info/world-population/population-by-country/>
  (page titled "Population by Country (2026)").
- **Retrieved:** 2026-06-10 (vintage `SOURCES.md` records the original
  transcription on 2026-06-08; values are unchanged between the two pulls).
- **Result:** all 25 populations — the 5 non-euro economies plus all 20
  euro-area members — match the transcribed values **exactly** (string
  equality). The euro-area total `347,740,855` equals the sum of the 20 member
  values, and the member list matches the 20 official euro-area states.

| economy | transcribed | Worldometer | match |
|---|---|---|---|
| United States | 349035494 | 349035494 | ✅ |
| China | 1412914089 | 1412914089 | ✅ |
| Japan | 122427731 | 122427731 | ✅ |
| United Kingdom | 69931528 | 69931528 | ✅ |
| India | 1476625576 | 1476625576 | ✅ |

All 20 euro-area members (Germany, France, Italy, Spain, Netherlands, Belgium,
Greece, Portugal, Austria, Ireland, Croatia, Lithuania, Slovenia, Latvia,
Estonia, Cyprus, Luxembourg, Malta, Slovakia, Finland) matched exactly; the
re-summed euro-area total is `347740855`, equal to the pinned value. ✅

---

## 3. PPP — World Bank `PA.NUS.PPP` (ICP 2024) → **CONFIRMED**

- **Source:** World Bank, *PPP conversion factor, GDP (LCU per international $)*,
  indicator `PA.NUS.PPP` (ICP). License CC BY-4.0.
- **URL fetched:** World Bank API,
  `https://api.worldbank.org/v2/country/<codes>/indicator/PA.NUS.PPP?date=2024&format=json`
  (the same series the bulk CSV at
  <https://data.worldbank.org/indicator/PA.NUS.PPP> publishes).
- **Retrieved:** 2026-06-10 (World Bank "last updated" 2026-04-08).
- **Result:** all values match the transcribed full-precision figures exactly
  (numeric equality): USD = 1.0 (base), CNY `3.5325492491585`, JPY `94.462599`,
  GBP `0.664153`, INR `20.4219876045922`, and all 20 euro-area member factors.
- **Euro-area row (EMU):** the World Bank returns **`null`** for the `EMU`
  aggregate in 2024 — independently confirming the claim that there is **no
  single published Euro-area `PA.NUS.PPP` value**, which is why openunit blends
  the members.
- **Latest common year:** across the 25 series, 2022/2023/**2024** are all
  non-empty; **2025 has 2 gaps** (2 of 25 series null). So **2024 is the latest
  year for which every basket economy and every euro-area member has a value** —
  matching `PPP_YEAR = "2024"`. No fallback values are needed (every member is a
  genuine 2024 figure).

---

## 4. Euro-area blend `0.642950` → **CONFIRMED (independently recomputed)**

Recomputing `ppp(euro area) = Σ pop_i·ppp_i / Σ pop_i` from the independently
fetched member populations (§2) and member PPP factors (§3) reproduces the
shipped factor **to full precision**:

```
independent recompute = 0.64294952371252610571162827560195652017937322895235
shipped (SOURCES.md)   = 0.64294952371252610571162827560195652017937322895235
6-dp                   = 0.642950   ✅
```

---

## 5. GDP-weighted sensitivity (documentation only)

To support SPEC.md §10, the GDP-weighted alternative was also computed from World
Bank nominal GDP (`NY.GDP.MKTP.CD`, current US$, 2024;
<https://data.worldbank.org/indicator/NY.GDP.MKTP.CD>, retrieved 2026-06-10, all
20 members non-null):

| euro-area PPP factor | value (6 dp) | 1 openunit, v0.2 |
|---|---|---|
| population-weighted (**shipped**) | 0.642950 | **2.848010** int$ |
| GDP-weighted (sensitivity only) | 0.661121 | 2.844627 int$ |

The shipped vintage stays population-weighted; the GDP-weighted figures change no
spec, artifact, or hash. Full details and the per-member GDP table are recorded
in `data/v0.2-ppp-2026-05-15/SOURCES.md`.

---

## Summary

| source | items checked | mismatches |
|---|---|---|
| ECB FX (baseline + valuation) | 10 | 0 |
| UN/Worldometer population | 25 | 0 |
| World Bank `PA.NUS.PPP` 2024 | 25 (+ EMU null confirmed) | 0 |
| euro-area blend recompute | 1 (full precision) | 0 |
| **total** | **61** | **0** |

Every published number is faithful to its named primary source. **Confirmed.**

*Reproduce this audit by re-fetching the three endpoints above and comparing
against `make_vintages.py` / each vintage's `SOURCES.md`.*

---

## Addendum (2026-06-13): verbatim normalization of two ECB strings

The §1 table flagged two transcriptions carrying a cosmetic trailing zero
relative to the ECB's official XML: valuation GBP `0.87050` (official `0.8705`)
and valuation INR `111.5940` (official `111.594`). On 2026-06-13 these two
strings in `make_vintages.py` were normalized to the **verbatim** official form,
after re-confirming all 10 rates against a fresh pull of
<https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml> (the other 8
already matched verbatim).

- **Numeric values unchanged.** `0.87050 == 0.8705` and `111.5940 == 111.594`
  as exact `Decimal`s; every derived FX quotient, every weight, and
  `value_usd = 0.985631 USD` are byte-identical.
- **v0.1 hashes changed** (the raw `source_eur_per_unit_valuation` strings are
  part of the hashed spec):
  - `input_digest`: `sha256:495f80f2…a80a` → `sha256:90b54dc5…fe25`
  - `artifact_hash`: `sha256:82bade1f…9655` → `sha256:1e615cf7…9a3a`
- **v0.2 hashes unchanged** (`sha256:566c95c1…b97a`): its spec embeds no raw
  ECB strings, and the derived nominal-FX baseline is the identical quotient.
- The v0 sample hash is untouched (`sha256:433d5e95…56bd`).

After normalization, every transcription in `make_vintages.py` is **verbatim
identical** to its official source string, so the "(= numerically)" caveats in
§1 no longer apply to the shipped code.

---

## Addendum (2026-10-26): population re-checked against the UN's own file

§2 above compared the transcribed populations with **Worldometer**, the
republisher they were taken from, not with the United Nations. On 2026-10-26
they were compared with the UN Population Division's own file
(`WPP2024_Demographic_Indicators_Medium.csv.gz`, sha256 `286ac36b…82bc`,
`TPopulation1July`, Time = 2026, medium variant):

- **23 of 25 match exactly; 2 do not.** Greece `9897115` (transcribed) vs
  `9897116` (UN) and Slovenia `2114573` vs `2114574` -- one person each.
- **Euro-area membership.** §2 says the member list "matches the 20 official
  euro-area states". That was wrong for these vintages' dates: Bulgaria joined
  the euro area on 2026-01-01 (ECB), before both FX dates (2026-01-09 and
  2026-05-15), so the euro area had 21 members. Bulgaria's 6667660 persons are
  missing from v0.1 and v0.2.

**Nothing published was rewritten.** v0.1 and v0.2 keep their files and hashes
and still verify (verification proves reproduction, not correctness). The
correction is a new vintage, `v0.3-unwpp-2026-05-15`, whose hashed spec
declares that it supersedes v0.1; `data/vintages.json` records the link and
the warnings, including the same membership warning for v0.2, for which no
corrected PPP vintage has been issued yet.

---

## Addendum (2026-10-26): is v0.2's "ICP 2024" label right?

v0.2 describes its World Bank `PA.NUS.PPP` values for reference year 2024 as
"ICP 2024" (in its `SOURCES.md`, and as `ppp_status` "World Bank PA.NUS.PPP
(ICP) 2024" in its hashed spec). Checked on 2026-10-26 against the World
Bank's own pages and API (small JSON only; no bulk file downloaded):

**Finding: the label is wrong. No ICP 2024 results exist yet, and none of
v0.2's 2024 values is an ICP benchmark value.**

- **No ICP 2024 release.** The ICP home page names the ICP 2021 cycle,
  released in May 2024, as its latest release (benchmark year 2021, revised
  2017, a 2018-2020 time series, and extrapolated GDP PPPs for 2022 and 2023).
  The ICP FAQ says the ICP 2021 results will be revised and published together
  with the ICP 2024 results, and that WDI's extrapolations will be replaced
  once the next cycle's results are available.
- **What WDI publishes for 2024.** The indicator metadata says ICP-estimated
  PPPs cover 2011-2021 and that WDI extrapolates the 2021 PPPs to later years;
  for members of the Eurostat-OECD PPP Programme, the factors come from that
  programme's databases. The Data Help Desk article describes the
  extrapolation: the 2021 benchmark PPP times the change in the economy's GDP
  implicit deflator relative to the change in the US deflator; for European
  and non-European OECD countries WDI incorporates the programme's annual PPPs.
  Each 2024 observation in the API carries a footnote that tells the two apart:

  | economies (v0.2 basket) | 2024 API footnote | what the value is |
  |---|---|---|
  | China, India | *(empty)* | **ICP 2021 benchmark, extrapolated to 2024 by the World Bank** (relative GDP deflator) |
  | Japan, United Kingdom, all euro-area members (Bulgaria included) | `Eurostat-OECD annual PPP` | **Eurostat-OECD PPP Programme annual PPP for 2024**, as incorporated in WDI |
  | United States | `Eurostat-OECD annual PPP` | 1 by definition (the international dollar is the US dollar) |

- **The correct label for v0.2's inputs** is therefore: World Bank WDI
  `PA.NUS.PPP`, reference year 2024 (WDI release of April 2026) -- ICP 2021
  benchmark extrapolated to 2024 for China and India; Eurostat-OECD annual PPPs
  for Japan, the United Kingdom and the euro-area members; US = 1.
- **v0.2 transcribed the April 2026 release faithfully.** All 25 values equal
  WDI Database Archives version `202604` exactly (numerically; USD is `1` in
  the API and `1.0` in v0.2).
- **The World Bank has since revised some of them.** In the July 2026 release
  (archive version `202607`, unchanged in the current release, "last updated"
  2026-10-08): China `3.5325492491585` -> `3.52537888953537` (-0.203%), India
  `20.4219876045922` -> `20.4522424138694` (+0.148%), Croatia, Cyprus and Malta
  by -0.0002% to -0.0003% each; the other 20 are unchanged. Bulgaria (not in
  v0.2) moved from `0.757951749098367` (lev) to `0.387533240879461`: WDI's
  country metadata now gives Bulgaria's currency unit as the euro, with the
  irrevocable rate 1 EUR = 1.95583 BGN from 2026-01-01 (the new value is the
  old one divided by 1.95583, to within -0.0003%). Caution: WDI's official
  exchange rate for Bulgaria 2024 (`PA.NUS.FCRF`, `1.80784166666667`) is still
  in lev in the same release; openunit does not use it.
- The euro-area aggregate (`EMU`) is still `null` for 2024, so a member blend
  is still needed.

**Nothing published was rewritten.** v0.2's files and hashes stay as they are
and still verify. `data/vintages.json` gives v0.2 two new warnings,
`PPP_LABEL` and `PPP_REVISED`.

Sources (all read 2026-10-26):

- ICP home page: <https://www.worldbank.org/en/programs/icp>; ICP data page:
  <https://www.worldbank.org/en/programs/icp/data>; ICP FAQ:
  <https://www.worldbank.org/en/programs/icp/faq>
- Indicator: <https://api.worldbank.org/v2/indicator/PA.NUS.PPP?format=json>
  (source organisations: ICP, published 30 May 2024; Eurostat PPP Programme;
  OECD PPP Programme)
- Series metadata (methodology, licence CC BY-4.0):
  <https://api.worldbank.org/v2/sources/2/series/PA.NUS.PPP/metadata?format=json>
- Extrapolation method:
  <https://datahelpdesk.worldbank.org/knowledgebase/articles/665452-how-do-you-extrapolate-the-ppp-conversion-factors>
- 2024 values with footnotes:
  `https://api.worldbank.org/v2/country/<26 economies + EMU>/indicator/PA.NUS.PPP?date=2024&format=json&footnote=y&per_page=100`
- Earlier releases: `https://api.worldbank.org/v2/sources/57/country/<codes>/series/PA.NUS.PPP/version/202604/time/YR2024?format=json`
  (and `202607`)
- Bulgaria's currency unit:
  <https://api.worldbank.org/v2/sources/2/country/BGR/metadata?format=json>

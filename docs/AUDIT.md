# openunit — independent data audit

**Status: CONFIRMED.** Every published number in the shipped vintages
(`data/v0.1-2026-05-15`, `data/v0.2-ppp-2026-05-15`) was independently
re-derived from its primary source and matches, with **zero mismatches**.

- **Audit date:** 2026-06-10
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

# openunit vintage `v0.2-ppp-illustrative-2026-05-15` -- sources & provenance

**Status: MECHANISM REAL, PPP DATA ILLUSTRATIVE.**

Population (UN WPP 2024) and the nominal-FX baseline (ECB) are real. The **PPP factors are placeholders** chosen only to exercise the v0.2 mechanism end to end. They are **not** World Bank values and must not be used as an authoritative figure.

- `input_digest`  : `sha256:c4f3783cf91a62b8101cd04f1ed125e05760b08ee90bdc664245bac814a50f4c`
- `artifact_hash` : `sha256:37ffa979e7e2770abc7c7fe9a3d4b2a01cf5eb6793e7f60af45153887970034d`

## PPP factors used (ILLUSTRATIVE)

PPP conversion factor = local-currency units per international $; PPP rate = `1 / factor` (international $ per unit), used as the valuation leg.

| currency | PPP factor (illustrative) | status |
|---|---|---|
| USD | 1.0 | ILLUSTRATIVE |
| EUR | 0.73 | ILLUSTRATIVE |
| CNY | 4.2 | ILLUSTRATIVE |
| JPY | 95.0 | ILLUSTRATIVE |
| GBP | 0.70 | ILLUSTRATIVE |
| INR | 23.5 | ILLUSTRATIVE |

## Procedure to make this vintage REAL

1. Open the World Bank series PA.NUS.PPP (PPP conversion factor, GDP, LCU per international $): <https://data.worldbank.org/indicator/PA.NUS.PPP>.
2. For each currency, read the most recent year's value (US = 1.0 by definition). For the euro area, choose and document an aggregation rule (e.g. a GDP-weighted blend of member states, or Eurostat's euro-area price level), because the World Bank does not publish a single euro-area PPP factor.
3. Replace the entries in `PPP_ILLUSTRATIVE` in `make_vintages.py`, set `ppp_status` to the source/year, and re-run `python3 make_vintages.py`.
4. The new `spec.json` / `artifact.json` hashes will change (new inputs) and the vintage id should be renamed to drop `illustrative`.

Why the euro area needs a rule: the euro area spans countries with materially different price levels, so there is no unique 'euro-area PPP'. openunit's stance is to make that choice explicit rather than hide it (see SPEC.md section 8).

# openunit vintage `v0.1-2026-05-15` -- sources & provenance

**Status: REAL DATA.** Every input below is transcribed from a named public source. Re-running `make_vintages.py` reproduces `spec.json` and `artifact.json` byte for byte.

- `input_digest`  : `sha256:495f80f2d6e30f6cb4ecd8da0ee577a4d8c747912c190105f56ba5e9079fa80a`
- `artifact_hash` : `sha256:82bade1f93771aa097376c0c05d5058c70655c970724cf30f82e8a2978169655`

## Foreign exchange (ECB euro reference rates)

Units of currency per 1 EUR, exactly as published by the European Central Bank.

| currency | per EUR @ 2026-01-09 | per EUR @ 2026-05-15 |
|---|---|---|
| EUR | 1 (base) | 1 (base) |
| USD | 1.1642 | 1.1628 |
| JPY | 183.52 | 184.36 |
| GBP | 0.8677 | 0.87050 |
| CNY | 8.1288 | 7.9194 |
| INR | 105.0335 | 111.5940 |

- baseline (2026-01-09): https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml
- valuation (2026-05-15): https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
- conversion to the USD numeraire: `usd_per_unit(C) = (USD per EUR) / (C per EUR)`, with `USD=1` and `EUR=(USD per EUR)`.

## Population (UN World Population Prospects 2024 Revision)

Medium-fertility variant, 2026 estimate; retrieved 2026-06-08 via Worldometer, which republishes the UN figures.

| economy | population |
|---|---|
| United States (USD) | 349035494 |
| Euro area (EUR) | 347740855 |
| China (CNY) | 1412914089 |
| Japan (JPY) | 122427731 |
| United Kingdom (GBP) | 69931528 |
| India (INR) | 1476625576 |

### Euro area = sum of 20 member states

| member | population |
|---|---|
| Germany | 83644258 |
| France | 66746401 |
| Italy | 58926166 |
| Spain | 47850793 |
| Netherlands | 18448775 |
| Belgium | 11774642 |
| Greece | 9897115 |
| Portugal | 10395362 |
| Austria | 9107266 |
| Ireland | 5356950 |
| Croatia | 3822345 |
| Lithuania | 2797338 |
| Slovenia | 2114573 |
| Latvia | 1835935 |
| Estonia | 1331062 |
| Cyprus | 1382334 |
| Luxembourg | 687448 |
| Malta | 549011 |
| Slovakia | 5451342 |
| Finland | 5621739 |
| **euro area total** | **347740855** |

Source page: https://www.worldometers.info/world-population/population-by-country/

## How to verify

```
python3 make_vintages.py            # regenerate
python3 cli.py verify data/v0.1-2026-05-15/artifact.json data/v0.1-2026-05-15/spec.json
```

The two ECB URLs above are revised over time; the exact rates for the pinned dates are reproduced in the table above so the vintage stays verifiable independently of the live feed.

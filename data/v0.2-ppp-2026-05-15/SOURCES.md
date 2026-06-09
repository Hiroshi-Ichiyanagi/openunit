# openunit vintage `v0.2-ppp-2026-05-15` -- sources & provenance

**Status: REAL DATA.** Population (UN WPP 2024), the nominal-FX baseline (ECB), and the PPP valuation leg (World Bank `PA.NUS.PPP`, ICP 2024) are all transcribed from named public sources. Re-running `make_vintages.py` reproduces `spec.json` and `artifact.json` byte for byte.

- `input_digest`  : `sha256:66c92e1f82d84587cd3ad6f36e317b2dba5cc4d34407894acf5c4a37a6d85070`
- `artifact_hash` : `sha256:566c95c1753dbcaa70bbfd58c295ced2117d4907d4d7aabb992d68a93f10b97a`

## PPP conversion factors (World Bank `PA.NUS.PPP`, ICP 2024)

PPP conversion factor = local-currency units per international $ (GDP basis); the valuation leg is `PPP rate = 1 / factor` (international $ per unit). Values are transcribed exactly as published.

- source: World Bank, *PPP conversion factor, GDP (LCU per international $)*, indicator `PA.NUS.PPP` (ICP)
- url: <https://data.worldbank.org/indicator/PA.NUS.PPP>
- reference year: **2024**  |  license: **CC BY-4.0**

| currency | economy | PA.NUS.PPP (2024) |
|---|---|---|
| USD | United States | 1.0 |
| EUR | Euro area | 0.64294952371252610571162827560195652017937322895235 *(population-weighted member blend, see below)* |
| CNY | China | 3.5325492491585 |
| JPY | Japan | 94.462599 |
| GBP | United Kingdom | 0.664153 |
| INR | India | 20.4219876045922 |

(USD = 1.0 is the international-dollar base by definition.)

## Euro area: population-weighted member blend

The World Bank publishes **no single Euro-area `PA.NUS.PPP` value** (the `EMU` aggregate row is empty in both the bulk CSV and the API). openunit therefore derives the euro-area factor as a **population-weighted blend** of the 20 euro-area members:

```
ppp(euro area) = sum(pop_i * ppp_i) / sum(pop_i)
```

Member populations are the UN WPP 2024 figures used for the euro-area headcount (one consistent population source); each member's `PA.NUS.PPP` is the World Bank 2024 value.

| member | population (UN WPP 2024) | PA.NUS.PPP (2024) |
|---|---|---|
| Germany | 83644258 | 0.700862 |
| France | 66746401 | 0.681239 |
| Italy | 58926166 | 0.599627 |
| Spain | 47850793 | 0.562107 |
| Netherlands | 18448775 | 0.731421 |
| Belgium | 11774642 | 0.704288 |
| Greece | 9897115 | 0.515086 |
| Portugal | 10395362 | 0.515993 |
| Austria | 9107266 | 0.710451 |
| Ireland | 5356950 | 0.740894 |
| Croatia | 3822345 | 0.44841971235566 |
| Lithuania | 2797338 | 0.49104 |
| Slovenia | 2114573 | 0.550461 |
| Latvia | 1835935 | 0.496528 |
| Estonia | 1331062 | 0.576166 |
| Cyprus | 1382334 | 0.56709589608174 |
| Luxembourg | 687448 | 0.815579 |
| Malta | 549011 | 0.580522225637102 |
| Slovakia | 5451342 | 0.501903 |
| Finland | 5621739 | 0.753945 |
| **euro area (blend)** | **347740855** | **0.64294952371252610571162827560195652017937322895235** |

Weighting the blend by **people** (rather than by GDP) follows openunit's one-person-one-vote stance. It is deliberately a **value choice, not a neutral fact**, and is therefore a **contestable** input -- exactly the kind of choice openunit makes explicit and auditable rather than hiding (see SPEC.md section 10). A GDP-weighted blend would yield a different euro-area factor; the population-weighted figure is the one pinned here, on the record.

## How to verify

```
python3 make_vintages.py            # regenerate
python3 cli.py verify data/v0.2-ppp-2026-05-15/artifact.json data/v0.2-ppp-2026-05-15/spec.json
```

## Updating to a future ICP / PPP year

1. Open `PA.NUS.PPP` (<https://data.worldbank.org/indicator/PA.NUS.PPP>) and pick the latest year `Y` for which USD/CNY/JPY/GBP/INR and the 20 euro-area members all have values.
2. In `make_vintages.py`, set `PPP_YEAR = "Y"` and update the transcribed values in `PPP_WB` (USD = `"1.0"`) and `EURO_PPP_2024` (full digits as published).
3. Re-run `python3 make_vintages.py`. The euro-area factor is recomputed from the member blend automatically; the new `spec.json` / `artifact.json` hashes change (new inputs).
4. Update the pinned hashes referenced in `README.md`, `ARTIFACT_FORMAT.md`, and `CHANGELOG.md`.

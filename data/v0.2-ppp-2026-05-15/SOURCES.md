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

## Sensitivity: GDP-weighted euro-area blend (not shipped)

The euro-area weighting is a **contestable value choice** (SPEC.md section 10). To make that explicit on the record, here is the GDP-weighted alternative computed from the same member `PA.NUS.PPP` values, weighted by World Bank nominal GDP (`NY.GDP.MKTP.CD`, current US$, 2024) instead of by population:

```
ppp(euro area, GDP-weighted) = sum(gdp_i * ppp_i) / sum(gdp_i)
```

- GDP source: World Bank, *GDP (current US$)*, indicator `NY.GDP.MKTP.CD` -- <https://data.worldbank.org/indicator/NY.GDP.MKTP.CD> (CC BY-4.0), year **2024**, retrieved 2026-06-10.

| euro-area PPP factor | value | 1 openunit (v0.2) |
|---|---|---|
| **population-weighted (shipped)** | 0.642950 | **2.848010 international $** |
| GDP-weighted (sensitivity only) | 0.661121 | 2.844627 international $ |

Full-precision GDP-weighted factor: `0.66112120618005818593670491280445665606493251460018`.

Per-member nominal GDP used for the GDP-weighted blend (transcribed exactly as published):

| member | nominal GDP 2024 (current US$) | PA.NUS.PPP (2024) |
|---|---|---|
| Germany | 4685592577804.69 | 0.700862 |
| France | 3160442622465.08 | 0.681239 |
| Italy | 2380825077243.59 | 0.599627 |
| Spain | 1725671652742.19 | 0.562107 |
| Netherlands | 1214927698572.66 | 0.731421 |
| Belgium | 671370081636.406 | 0.704288 |
| Greece | 256238371778.118 | 0.515086 |
| Portugal | 313271185085.102 | 0.515993 |
| Austria | 534790720466.822 | 0.710451 |
| Ireland | 609157459747.205 | 0.740894 |
| Croatia | 92983810328.9088 | 0.44841971235566 |
| Lithuania | 84869215513.3648 | 0.49104 |
| Slovenia | 72972015197.3859 | 0.550461 |
| Latvia | 43684254432.3609 | 0.496528 |
| Estonia | 43130419829.35 | 0.576166 |
| Cyprus | 37634533331.8902 | 0.56709589608174 |
| Luxembourg | 93279851863.4062 | 0.815579 |
| Malta | 24971574502.4475 | 0.580522225637102 |
| Slovakia | 140934076532.375 | 0.501903 |
| Finland | 298696961297.656 | 0.753945 |

**openunit ships the population-weighted factor**, consistent with its one-person-one-vote stance (SPEC.md section 10). The GDP-weighted figures above change no shipped spec, artifact, or hash; they are recorded so a GDP weighting can be argued against the exact numbers rather than in the abstract. Here the GDP weighting raises the euro-area PPP factor by about 2.8%, which moves 1 openunit by about 0.12% (2.848010 -> 2.844627 international $) -- a small but real difference, made in the open.

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

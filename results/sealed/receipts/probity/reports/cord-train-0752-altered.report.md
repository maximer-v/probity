# Verification report: cord-train-0752-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_SUBTOTAL.

## Reading

| Field | Value |
|---|---|
| subtotal | 49500 |
| tax | 5198 |
| service | 2475 |
| discount | None |
| total | 57173 |
| cash | None |
| change | None |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | PECEL MADIUN | 1 | None | 39500 |
| 1 | AIR MINERAL | 1 | None | 17000 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected
- after the third reading: 1 failure(s), 0 cell(s) corrected

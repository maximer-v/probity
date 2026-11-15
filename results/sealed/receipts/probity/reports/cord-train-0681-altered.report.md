# Verification report: cord-train-0681-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_SUBTOTAL.

## Reading

| Field | Value |
|---|---|
| subtotal | 350500 |
| tax | 37153 |
| service | 21030 |
| discount | None |
| total | 408683 |
| cash | None |
| change | None |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | SALMON PESTO | 1 | None | 85500 |
| 1 | GRILLED SALMON TERIYAK | 1 | None | 177000 |
| 2 | MINERAL WATER | 1 | None | 23000 |
| 3 | FRESH FRUIT COCKTAIL | 1 | None | 60000 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected
- after the third reading: 1 failure(s), 0 cell(s) corrected

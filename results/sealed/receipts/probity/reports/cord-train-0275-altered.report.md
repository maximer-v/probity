# Verification report: cord-train-0275-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_SUBTOTAL.

## Reading

| Field | Value |
|---|---|
| subtotal | 215000 |
| tax | 23650 |
| service | 21500 |
| discount | None |
| total | 260150 |
| cash | None |
| change | None |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | Benedict Burrito | 1 | None | 85000 |
| 1 | Lychee Ice Tea | 1 | None | 42000 |
| 2 | Soup Of The Day | 1 | None | 45000 |
| 3 | Strawberry jc | 1 | None | 45000 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected
- after the third reading: 1 failure(s), 0 cell(s) corrected

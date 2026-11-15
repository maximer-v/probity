# Verification report: cord-train-0054-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_SUBTOTAL.

## Reading

| Field | Value |
|---|---|
| subtotal | 26364 |
| tax | 2636 |
| service | None |
| discount | None |
| total | 29000 |
| cash | 30000 |
| change | 1000 |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | KFC Winger HC | 1 | None | 20000 |
| 1 | Rice | 1 | None | 4364 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected
- after the third reading: 1 failure(s), 0 cell(s) corrected

# Verification report: cord-train-0582-altered

**UNRESOLVED**

Reason: a rule fails, and the two readers disagree on a value it uses without either reading satisfying it.

## Reading

| Field | Value |
|---|---|
| subtotal | None |
| tax | None |
| service | None |
| discount | None |
| total | 56000 |
| cash | 56000 |
| change | 0 |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | BLACKPINK | 1 | None | 38000 |
| 1 | MATCHABERRY | 1 | None | 28000 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_TOTAL`: `sum(items.price) + (tax or 0) + (service or 0) - (discount or 0) == total` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected

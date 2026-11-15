# Verification report: cord-train-0269-altered

**UNRESOLVED**

Reason: a rule fails, and the two readers disagree on a value it uses without either reading satisfying it.

## Reading

| Field | Value |
|---|---|
| subtotal | None |
| tax | None |
| service | None |
| discount | None |
| total | 81400 |
| cash | 100000 |
| change | 18600 |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | 01110000 TUNA & CHEDDAR | None | None | 55000 |
| 1 | 04100000 ONION RINGS | None | None | 49800 |
| 2 | 13100000 AQUA BTL | None | None | 6600 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_TOTAL`: `sum(items.price) + (tax or 0) + (service or 0) - (discount or 0) == total` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected

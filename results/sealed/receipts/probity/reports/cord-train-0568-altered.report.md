# Verification report: cord-train-0568-altered

**UNRESOLVED**

Reason: a rule fails and the second reading was not obtained: reply ended with length.

## Reading

| Field | Value |
|---|---|
| subtotal | None |
| tax | None |
| service | None |
| discount | None |
| total | 46000 |
| cash | 50000 |
| change | 4000 |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | Large 1 | 2 | None | 24000 |
| 1 | Polo 1 | 2 | None | 0 |
| 2 | *Plastik Kcl | 1 | None | None |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_TOTAL`: `sum(items.price) + (tax or 0) + (service or 0) - (discount or 0) == total` a value it needs was not read

## Steps

- first reading: 1 rule failure(s)

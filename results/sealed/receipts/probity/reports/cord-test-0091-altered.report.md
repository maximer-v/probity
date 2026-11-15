# Verification report: cord-test-0091-altered

**UNRESOLVED**

Reason: a rule fails, and the two readers disagree on a value it uses without either reading satisfying it.

## Reading

| Field | Value |
|---|---|
| subtotal | None |
| tax | None |
| service | None |
| discount | None |
| total | 21000 |
| cash | 30000 |
| change | 9000 |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | BAKSO BNGKS | 1 | None | 35000 |
| 1 | GORENGAN | 6 | None | 6000 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_TOTAL`: `sum(items.price) + (tax or 0) + (service or 0) - (discount or 0) == total` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected

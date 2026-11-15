# Verification report: cord-test-0073-altered

**UNRESOLVED**

Reason: a rule fails, and the two readers disagree on a value it uses without either reading satisfying it.

## Reading

| Field | Value |
|---|---|
| subtotal | None |
| tax | None |
| service | None |
| discount | None |
| total | 22000 |
| cash | 25000 |
| change | 3000 |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | 1001-Choco Bun | 1 | 22000 | 24000 |
| 1 | 6001-Plastic Bag Small | 1 | 0 | 0 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_TOTAL`: `sum(items.price) + (tax or 0) + (service or 0) - (discount or 0) == total` does not hold
- `LINE_AMOUNT` at items[0]: `row.quantity * row.unit_price == row.price` does not hold

## Steps

- first reading: 2 rule failure(s)
- after the second reading: 2 failure(s), 0 cell(s) corrected

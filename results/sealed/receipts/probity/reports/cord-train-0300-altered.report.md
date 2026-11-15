# Verification report: cord-train-0300-altered

**UNRESOLVED**

Reason: a rule fails, and the two readers disagree on a value it uses without either reading satisfying it.

## Reading

| Field | Value |
|---|---|
| subtotal | 65455 |
| tax | 6546 |
| service | None |
| discount | None |
| total | 72001 |
| cash | None |
| change | None |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | PAKET SUPER MANTAP 2A RAACHA | 1 | 59091 | 53091 |
| 1 | RICE | 1 | 6364 | 6364 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold
- `LINE_AMOUNT` at items[0]: `row.quantity * row.unit_price == row.price` does not hold

## Steps

- first reading: 2 rule failure(s)
- after the second reading: 2 failure(s), 0 cell(s) corrected

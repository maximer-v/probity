# Verification report: cord-train-0700-altered

**UNRESOLVED**

Reason: a rule fails, and the two readers disagree on a value it uses without either reading satisfying it.

## Reading

| Field | Value |
|---|---|
| subtotal | 55500 |
| tax | None |
| service | None |
| discount | None |
| total | 55500 |
| cash | 100000 |
| change | 44500 |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | ROTI | 6 | 5000 | 30000 |
| 1 | ROTI | 3 | 4500 | 53500 |
| 2 | ROTI | 2 | 6000 | 12000 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold
- `LINE_AMOUNT` at items[1]: `row.quantity * row.unit_price == row.price` does not hold

## Steps

- first reading: 2 rule failure(s)
- after the second reading: 2 failure(s), 0 cell(s) corrected

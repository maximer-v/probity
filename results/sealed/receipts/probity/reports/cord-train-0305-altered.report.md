# Verification report: cord-train-0305-altered

**UNRESOLVED**

Reason: a rule fails, and the two readers disagree on a value it uses without either reading satisfying it.

## Reading

| Field | Value |
|---|---|
| subtotal | 42000 |
| tax | None |
| service | None |
| discount | None |
| total | 42000 |
| cash | 100000 |
| change | 58000 |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | CARAMEL ALMOND | 1 | 23000 | 23000 |
| 1 | STIX ECLAIRS | 1 | 19000 | 39000 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold
- `LINE_AMOUNT` at items[1]: `row.quantity * row.unit_price == row.price` does not hold

## Steps

- first reading: 2 rule failure(s)
- after the second reading: 2 failure(s), 0 cell(s) corrected

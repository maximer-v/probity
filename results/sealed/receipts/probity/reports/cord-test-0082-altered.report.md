# Verification report: cord-test-0082-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_SUBTOTAL, LINE_AMOUNT[1].

## Reading

| Field | Value |
|---|---|
| subtotal | 385000 |
| tax | None |
| service | None |
| discount | None |
| total | 385000 |
| cash | 385000 |
| change | 0 |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | Chocolate Log Cake | 1 | 115000 | 115000 |
| 1 | Snowman Cake Chocolate | 1 | 60000 | 20000 |
| 2 | Strawberry Log Cake | 2 | 105000 | 210000 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold
- `LINE_AMOUNT` at items[1]: `row.quantity * row.unit_price == row.price` does not hold

## Steps

- first reading: 2 rule failure(s)
- after the second reading: 2 failure(s), 0 cell(s) corrected
- after the third reading: 2 failure(s), 0 cell(s) corrected

# Verification report: cord-test-0088-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_SUBTOTAL, LINE_AMOUNT[0].

## Reading

| Field | Value |
|---|---|
| subtotal | 47000 |
| tax | None |
| service | None |
| discount | None |
| total | 47000 |
| cash | 47000 |
| change | 0 |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | STIX ECLAIRS | 1 | 19000 | 12000 |
| 1 | ALMOND CREAM CHEESE | 1 | 28000 | 28000 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold
- `LINE_AMOUNT` at items[0]: `row.quantity * row.unit_price == row.price` does not hold

## Steps

- first reading: 2 rule failure(s)
- after the second reading: 2 failure(s), 0 cell(s) corrected
- after the third reading: 2 failure(s), 0 cell(s) corrected

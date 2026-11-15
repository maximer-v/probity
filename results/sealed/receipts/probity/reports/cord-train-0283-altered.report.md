# Verification report: cord-train-0283-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_TOTAL, LINE_AMOUNT[0].

## Reading

| Field | Value |
|---|---|
| subtotal | None |
| tax | None |
| service | None |
| discount | None |
| total | 22000 |
| cash | 22000 |
| change | 0 |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | ELEPHANT READ BEAN | 1 | 12000 | 92000 |
| 1 | chapsal twister donnut | 1 | 10000 | 10000 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_TOTAL`: `sum(items.price) + (tax or 0) + (service or 0) - (discount or 0) == total` does not hold
- `LINE_AMOUNT` at items[0]: `row.quantity * row.unit_price == row.price` does not hold

## Steps

- first reading: 2 rule failure(s)
- after the second reading: 2 failure(s), 0 cell(s) corrected
- after the third reading: 2 failure(s), 0 cell(s) corrected

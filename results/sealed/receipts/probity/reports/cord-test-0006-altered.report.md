# Verification report: cord-test-0006-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_TOTAL.

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
| 0 | EGG TART | 1 | None | 13000 |
| 1 | CHOCO CUSTARD PASTRY | 2 | None | 24000 |
| 2 | REDBEAN BREAD | 1 | None | 8000 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_TOTAL`: `sum(items.price) + (tax or 0) + (service or 0) - (discount or 0) == total` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected
- after the third reading: 1 failure(s), 0 cell(s) corrected

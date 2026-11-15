# Verification report: cord-test-0024-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_TOTAL.

## Reading

| Field | Value |
|---|---|
| subtotal | None |
| tax | None |
| service | None |
| discount | None |
| total | 118000 |
| cash | None |
| change | None |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | 5001-Corn Flakes Cookies | None | 56000 | 56000 |
| 1 | 5003-Chokoreto Cookies | None | 62000 | 64000 |
| 2 | 6002-Plastic Bag Medium | None | 0 | 0 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_TOTAL`: `sum(items.price) + (tax or 0) + (service or 0) - (discount or 0) == total` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected
- after the third reading: 1 failure(s), 0 cell(s) corrected

# Verification report: cord-train-0481-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_TOTAL.

## Reading

| Field | Value |
|---|---|
| subtotal | None |
| tax | None |
| service | None |
| discount | None |
| total | 62000 |
| cash | 100000 |
| change | 38000 |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | 1517-ROTI KENTANG KEJU MANIS | None | 23500 | 23500 |
| 1 | 1009-ROTI KELAPA | None | 8000 | 84000 |
| 2 | 1439-TUNA CHEESE WHEAT SANDWICH | None | 14500 | 14500 |
| 3 | 1244-PLASTIK TENTENGAN SEDANG | None | 0 | 0 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_TOTAL`: `sum(items.price) + (tax or 0) + (service or 0) - (discount or 0) == total` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected
- after the third reading: 1 failure(s), 0 cell(s) corrected

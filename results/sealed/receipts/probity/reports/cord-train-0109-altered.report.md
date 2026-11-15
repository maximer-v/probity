# Verification report: cord-train-0109-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_TOTAL.

## Reading

| Field | Value |
|---|---|
| subtotal | None |
| tax | None |
| service | None |
| discount | None |
| total | 35000 |
| cash | 50000 |
| change | 15000 |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | 1069-ROTI KEJU COKLAT | None | 8500 | 8500 |
| 1 | 1037-ROTI MAHKOTA/RING | None | 10500 | 10500 |
| 2 | 1022-ROTI KACANG MERAH | None | 8000 | 8500 |
| 3 | 1001-ROTI COKLAT | None | 8000 | 8000 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_TOTAL`: `sum(items.price) + (tax or 0) + (service or 0) - (discount or 0) == total` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected
- after the third reading: 1 failure(s), 0 cell(s) corrected

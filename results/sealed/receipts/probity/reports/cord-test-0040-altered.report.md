# Verification report: cord-test-0040-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_TOTAL, LINE_AMOUNT[0].

## Reading

| Field | Value |
|---|---|
| subtotal | None |
| tax | None |
| service | None |
| discount | None |
| total | 68000 |
| cash | 100000 |
| change | 32000 |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | Snack Lestari All | 2 | 27000 | 58000 |
| 1 | Bakery Aneka Sisir banana,Pizza,yoko,Mar mer,Daging,abon,keju,cokelat,dll | 2 | 7000 | 14000 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_TOTAL`: `sum(items.price) + (tax or 0) + (service or 0) - (discount or 0) == total` does not hold
- `LINE_AMOUNT` at items[0]: `row.quantity * row.unit_price == row.price` does not hold

## Steps

- first reading: 2 rule failure(s)
- after the second reading: 2 failure(s), 0 cell(s) corrected
- after the third reading: 2 failure(s), 0 cell(s) corrected

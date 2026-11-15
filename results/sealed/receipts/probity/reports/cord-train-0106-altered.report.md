# Verification report: cord-train-0106-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_SUBTOTAL.

## Reading

| Field | Value |
|---|---|
| subtotal | 43637 |
| tax | 4364 |
| service | None |
| discount | None |
| total | 48001 |
| cash | 100000 |
| change | 51999 |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | Toblerone BanCheese | 1 | None | 28182 |
| 1 | Roast Beef Crepes | 1 | None | 35455 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected
- after the third reading: 1 failure(s), 0 cell(s) corrected

# Verification report: cord-train-0192-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_SUBTOTAL.

## Reading

| Field | Value |
|---|---|
| subtotal | 50909 |
| tax | 5091 |
| service | None |
| discount | None |
| total | 56000 |
| cash | 56000 |
| change | None |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | Kupon 7 | None | None | 32727 |
| 1 | MINERAL WATER | None | None | 8182 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected
- after the third reading: 1 failure(s), 0 cell(s) corrected

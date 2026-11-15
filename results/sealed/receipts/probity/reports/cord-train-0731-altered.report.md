# Verification report: cord-train-0731-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_SUBTOTAL.

## Reading

| Field | Value |
|---|---|
| subtotal | 82727 |
| tax | 8273 |
| service | None |
| discount | None |
| total | 91000 |
| cash | 91000 |
| change | None |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | TEH PUCUK | 1 | None | 9091 |
| 1 | SPICY C CHEESE | 1 | None | 40000 |
| 2 | WOOSAM RICE R | 1 | None | 83636 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected
- after the third reading: 1 failure(s), 0 cell(s) corrected

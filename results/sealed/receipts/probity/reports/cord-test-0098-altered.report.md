# Verification report: cord-test-0098-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_SUBTOTAL.

## Reading

| Field | Value |
|---|---|
| subtotal | 215000 |
| tax | 22790 |
| service | 12900 |
| discount | None |
| total | 250690 |
| cash | None |
| change | None |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | BLACK PEPPER MEATBALL PAS | 1 | None | 79000 |
| 1 | TRUFFLE CREAM | 1 | None | 77000 |
| 2 | EARL GREY MILK TEA | 1 | None | 50000 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected
- after the third reading: 1 failure(s), 0 cell(s) corrected

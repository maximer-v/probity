# Verification report: cord-train-0442-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_SUBTOTAL.

## Reading

| Field | Value |
|---|---|
| subtotal | 166000 |
| tax | 17679 |
| service | 10790 |
| discount | None |
| total | 194469 |
| cash | None |
| change | None |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | SHISAMO MENTAIKO | 1 | None | 33000 |
| 1 | SALMON BACON | 1 | None | 49000 |
| 2 | DYNAMITE SCALLOP | 1 | None | 53000 |
| 3 | TOBIKO TOFU | 1 | None | 29000 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected
- after the third reading: 1 failure(s), 0 cell(s) corrected

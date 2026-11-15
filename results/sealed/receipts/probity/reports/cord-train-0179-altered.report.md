# Verification report: cord-train-0179-altered

**UNRESOLVED**

Reason: a rule fails, and the two readers disagree on a value it uses without either reading satisfying it.

## Reading

| Field | Value |
|---|---|
| subtotal | 109400 |
| tax | 11706 |
| service | 7658 |
| discount | None |
| total | 128764 |
| cash | None |
| change | None |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | I09.NG NANAS | 1 | None | 49800 |
| 1 | DE13.PSANG IJO MDM | 1 | None | 29800 |
| 2 | CT12.BLK JELY KPI IC | 1 | None | 39800 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected

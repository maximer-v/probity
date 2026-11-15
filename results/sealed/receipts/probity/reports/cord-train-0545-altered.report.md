# Verification report: cord-train-0545-altered

**UNRESOLVED**

Reason: a rule fails, and the two readers disagree on a value it uses without either reading satisfying it.

## Reading

| Field | Value |
|---|---|
| subtotal | 320000 |
| tax | 34240 |
| service | 22400 |
| discount | None |
| total | 376640 |
| cash | None |
| change | None |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | M02.LMK BEEF RNDANG | 1 | None | 55800 |
| 1 | I13.SIMANGOSONG | 1 | None | 22800 |
| 2 | I01.NS BEBEK KAMPUNG | 1 | None | 52800 |
| 3 | A13.MIE ACP | 1 | None | 40800 |
| 4 | CT06.TEA O HOT R. | 2 | None | 27600 |
| 5 | CT06.TEA O ICE R. | 3 | None | 44400 |
| 6 | N01.MR.MI TLR ASIN | 1 | None | 45800 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold

## Steps

- first reading: 1 rule failure(s)
- after the second reading: 1 failure(s), 0 cell(s) corrected

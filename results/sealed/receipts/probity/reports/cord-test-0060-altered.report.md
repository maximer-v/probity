# Verification report: cord-test-0060-altered

**DOCUMENT_INCONSISTENT**

Reason: two readers agree on every value these rules use, and they do not hold: ITEMS_SUM_TO_SUBTOTAL, LINE_AMOUNT[0].

## Reading

| Field | Value |
|---|---|
| subtotal | 26250 |
| tax | None |
| service | None |
| discount | None |
| total | 26250 |
| cash | None |
| change | None |

### items

| # | name | quantity | unit_price | price |
|---:|---|---|---|---|
| 0 | Topping Milo Sparkle (untuk 1 Porsi) | 1 | 1250 | 6250 |
| 1 | Bola Ubi Mini Original (14 Pcs ) | 2 | 12500 | 25000 |

## Corrections

None.

## Rules that do not hold

- `ITEMS_SUM_TO_SUBTOTAL`: `sum(items.price) == subtotal` does not hold
- `LINE_AMOUNT` at items[0]: `row.quantity * row.unit_price == row.price` does not hold

## Steps

- first reading: 2 rule failure(s)
- after the second reading: 2 failure(s), 0 cell(s) corrected
- after the third reading: 2 failure(s), 0 cell(s) corrected

from pathlib import Path

BASE_DIR = Path(__file__).parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_RANGE = range(45, 0, -1)
CONTRACT_VALUE_IDX = -1
ROWS_TO_SKIP = (
    "",
    "-",
    "Количество\nДоговоров,\nшт.",
    "Итого",
    "Итого по секции:",
)
EXCHANGE_PRODUCT_ID_COL = 1
EXCHANGE_PRODUCT_NAME_COL = 2
OIL_ID_SLICE = slice(None, 4)
DELIVERY_BASIS_ID_SLICE = slice(4, 7)
DELIVERY_BASIS_NAME_COL = 3
DELIVERY_TYPE_ID_SLICE = slice(-1, None)
VOLUME_COL = 4
TOTAL_COL = 5
COUNT_COL = CONTRACT_VALUE_IDX

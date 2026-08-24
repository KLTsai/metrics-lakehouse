"""四類髒資料注入與比例→筆數換算。

四類各自的分母(handoff §3):
- 缺值:required 欄位數 × 基底列數(儲存格)
- 重複:基底列數
- 漂移:(decimal+datetime 欄位數) × 基底列數(儲存格)
- 遲到:基底列數

注入目標互斥,四條驗證斷言才能同時精確成立:
- 缺值只打 missing_pool(不含主鍵);漂移避開已缺值的儲存格
- 重複與遲到由 generate.py 挑列時排除彼此與被注入的列

漂移樣式抄藍本實戰分類器(health/checker.py:201-213 的 reason 常數):
數值 currency/acct_neg/percent/chinese_unit/space_thousand/nan_inf/european,
日期 chinese_date/dot_date。千分位類樣式在值 <1000 時墊高數字,
保證帶出分隔符、必定通不過嚴格型別解析。
"""

import math
import random
from datetime import date

from generator.schema import DATETIME, DECIMAL, Table


def injection_count(denominator: int, rate: float) -> int:
    """比例→筆數:floor(分母 × rate)。驗證斷言與此同一算式。"""
    return math.floor(denominator * rate)


Cell = tuple[int, str]  # (row index, name_en)


def inject_missing(
    rng: random.Random, rows: list[dict[str, str]], table: Table, rate: float
) -> set[Cell]:
    """required 欄位變空字串;回傳命中的儲存格供漂移排除。"""
    required = sum(1 for f in table.fields if f.required)
    count = injection_count(required * len(rows), rate)
    pool = [(i, col) for i in range(len(rows)) for col in table.missing_pool]
    cells = rng.sample(pool, count)
    for i, col in cells:
        rows[i][col] = ""
    return set(cells)


def inject_drift(
    rng: random.Random,
    rows: list[dict[str, str]],
    table: Table,
    rate: float,
    occupied: set[Cell],
) -> set[Cell]:
    """decimal/datetime 欄位改寫成漂移樣式;避開 occupied(已缺值)儲存格。"""
    typed = [f for f in table.fields if f.kind in (DECIMAL, DATETIME)]
    count = injection_count(len(typed) * len(rows), rate)
    candidates = [
        (i, f.name_en)
        for i in range(len(rows))
        for f in typed
        if (i, f.name_en) not in occupied
    ]
    cells = rng.sample(candidates, count)
    kind_of = {f.name_en: f.kind for f in typed}
    for i, col in cells:
        if kind_of[col] == DECIMAL:
            rows[i][col] = _drift_decimal(rng, rows[i][col])
        else:
            rows[i][col] = _drift_datetime(rng, rows[i][col])
    return set(cells)


def pick_late_rows(
    rng: random.Random, batch_of: list[int], n_batches: int, rate: float
) -> dict[int, int]:
    """挑遲到列,回傳 {row index: 延後到的批次}。整列不動,只換輸出檔案。"""
    count = injection_count(len(batch_of), rate)
    eligible = [i for i, b in enumerate(batch_of) if b < n_batches - 1]
    if len(eligible) < count:
        raise ValueError(
            f"遲到注入需要 {count} 列有後續批次可延,只有 {len(eligible)} 列;"
            "請加大 --batches 或 --rows"
        )
    return {i: rng.randint(batch_of[i] + 1, n_batches - 1) for i in sorted(rng.sample(eligible, count))}


def pick_duplicate_sources(
    rng: random.Random, n_rows: int, rate: float, excluded: set[int]
) -> list[int]:
    """挑重複列來源(完整複製含主鍵)。排除被注入或遲到的列,
    複本才會與來源逐格相同、且不影響其他三類的計數。"""
    count = injection_count(n_rows, rate)
    eligible = sorted(set(range(n_rows)) - excluded)
    if len(eligible) < count:
        raise ValueError(
            f"重複注入需要 {count} 列乾淨來源,只剩 {len(eligible)} 列;"
            "請加大 --rows 或調低比例"
        )
    return sorted(rng.sample(eligible, count))


# --- 漂移樣式 ---------------------------------------------------------------

_DECIMAL_STYLES = (
    "currency",
    "acct_neg",
    "percent",
    "chinese_unit",
    "space_thousand",
    "nan_inf",
    "european",
)


def _drift_decimal(rng: random.Random, value: str) -> str:
    style = rng.choice(_DECIMAL_STYLES)
    n = int(abs(float(value)))
    grouped = n if n >= 1000 else n + 1234  # 千分位樣式保證帶分隔符
    if style == "currency":
        return f"NT${grouped:,}"
    if style == "acct_neg":
        return f"({grouped:,})"
    if style == "percent":
        return f"{n}%"
    if style == "chinese_unit":
        return f"{n}元"
    if style == "space_thousand":
        return f"{grouped:,}".replace(",", " ")
    if style == "nan_inf":
        return "NaN"
    return f"{grouped:,}".replace(",", ".") + f",{rng.randint(10, 99)}"  # european


def _drift_datetime(rng: random.Random, value: str) -> str:
    d = date.fromisoformat(value)
    if rng.random() < 0.5:
        return f"{d.year}年{d.month}月{d.day}日"  # chinese_date
    return f"{d.year}.{d.month}.{d.day}"  # dot_date

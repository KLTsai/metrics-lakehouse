"""L1 驗票口:比對 landing CSV 表頭與上傳契約(generator/schema.py)。

只看欄位名稱的組成(缺欄/多欄),不看順序、不看值——欄位值漂移
(如中文日期、千分位數字)屬 T2.4 dbt test 範疇,見 CONTEXT.md「漂移」詞條。
"""

from generator.schema import Table


class HeaderDriftError(Exception):
    """表頭與契約不符;訊息列出缺欄與多欄,供 Airflow log 直接顯示。"""


def validate_header(table: Table, header: list[str]) -> None:
    expected = {f.name_zh for f in table.fields}
    actual = set(header)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        raise HeaderDriftError(
            f"{table.name} 表頭與契約不符——"
            f"缺欄:{missing or '無'};多欄:{extra or '無'}"
        )

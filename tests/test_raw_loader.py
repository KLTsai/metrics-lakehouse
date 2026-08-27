"""T1.4 入倉單元測試:純函式層(欄名映射、SQL 產生)與 load_partition 的
「先刪後插、同一交易」順序;真實交易語意(commit/rollback、kill 重跑)
用真實 Airflow + Postgres 實測(驗證標準 #2/#3),不在單元測試 mock。

契約來源同產生器(generator/schema.py),避免另外手抄一份欄名對照。
"""

from generator.schema import ACCOUNTS_RECEIVABLE, TRANSACTION_DETAIL
from ingestion.raw_loader import (
    METADATA_COLUMNS,
    create_table_sql,
    delete_partition_sql,
    insert_sql,
    load_partition,
    map_header_to_columns,
)


def test_map_header_follows_contract_order():
    header = [f.name_zh for f in TRANSACTION_DETAIL.fields]
    expected = [f.name_en for f in TRANSACTION_DETAIL.fields]
    assert map_header_to_columns(TRANSACTION_DETAIL, header) == expected


def test_map_header_follows_file_column_order_not_contract_order():
    # 驗票口(T1.3)不管欄序,所以映射必須逐位跟著檔案欄序走,不能假設契約欄序
    header = list(reversed([f.name_zh for f in ACCOUNTS_RECEIVABLE.fields]))
    expected = list(reversed([f.name_en for f in ACCOUNTS_RECEIVABLE.fields]))
    assert map_header_to_columns(ACCOUNTS_RECEIVABLE, header) == expected


def test_create_table_all_data_columns_are_text():
    sql = create_table_sql(TRANSACTION_DETAIL)
    for f in TRANSACTION_DETAIL.fields:
        assert f"{f.name_en} text" in sql


def test_create_table_has_metadata_columns_and_is_idempotent():
    sql = create_table_sql(ACCOUNTS_RECEIVABLE)
    for col in METADATA_COLUMNS:
        assert col in sql
    assert "raw.accounts_receivable" in sql
    # DDL 由 load task 每次跑,必須可重複執行
    assert "CREATE SCHEMA IF NOT EXISTS" in sql
    assert "CREATE TABLE IF NOT EXISTS" in sql


def test_delete_partition_targets_tenant_and_file_date():
    sql = delete_partition_sql(TRANSACTION_DETAIL)
    assert "raw.transaction_detail" in sql
    assert "tenant_id = %s" in sql
    assert "file_date = %s" in sql


def test_insert_sql_appends_metadata_after_csv_columns():
    csv_cols = [f.name_en for f in ACCOUNTS_RECEIVABLE.fields]
    sql = insert_sql(ACCOUNTS_RECEIVABLE, csv_cols)
    # loaded_at 用 SQL 端 now()(交易時間戳,同一次載入的列共用同一值),不佔 placeholder
    assert sql.count("%s") == len(csv_cols) + len(METADATA_COLUMNS) - 1
    assert "now()" in sql
    assert "raw.accounts_receivable" in sql


class _FakeCursor:
    def __init__(self, log):
        self._log = log

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params=None):
        self._log.append(("execute", sql, params))

    def executemany(self, sql, rows):
        self._log.append(("executemany", sql, list(rows)))


class _FakeConn:
    """只記錄呼叫順序,驗「begin → 刪 → 插 → commit」的骨架;交易語意不在此驗。"""

    def __init__(self):
        self.log = []

    def __enter__(self):
        self.log.append(("begin",))
        return self

    def __exit__(self, *args):
        self.log.append(("commit",))
        return False

    def cursor(self):
        return _FakeCursor(self.log)


def _write_csv(tmp_path, table, rows):
    path = tmp_path / f"{table.name}_2026-01-01.csv"
    header = ",".join(f.name_zh for f in table.fields)
    lines = [header] + [",".join(row) for row in rows]
    # 產生器輸出帶 BOM(utf-8-sig),loader 必須吃得下
    path.write_text("\ufeff" + "\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def test_load_partition_deletes_then_inserts_inside_one_transaction(tmp_path):
    row = ["x"] * len(ACCOUNTS_RECEIVABLE.fields)
    path = _write_csv(tmp_path, ACCOUNTS_RECEIVABLE, [row, row])  # 重複列也要原樣保留
    conn = _FakeConn()

    n = load_partition(conn, ACCOUNTS_RECEIVABLE, path, "alpha", "2026-01-01")

    assert n == 2
    assert [entry[0] for entry in conn.log] == ["begin", "execute", "executemany", "commit"]
    _, delete_sql, delete_params = conn.log[1]
    assert delete_params == ("alpha", "2026-01-01")
    _, _, inserted = conn.log[2]
    assert len(inserted) == 2  # 兩列重複列都進倉,不去重
    assert inserted[0][-3:] == ("alpha", "2026-01-01", "accounts_receivable_2026-01-01.csv")

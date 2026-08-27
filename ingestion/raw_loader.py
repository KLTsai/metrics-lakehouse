"""L1 入倉:landing CSV → Postgres raw 區,idempotency 走分區替換(ADR 0002)。

資料欄全 text、欄名用契約英文名(唯一來源 generator/schema.py);髒資料
(重複列、怪值)原樣入倉不清洗——raw 是證物保存,清洗屬 dbt(L3)責任。
metadata 四欄(tenant_id/file_date/source_filename/loaded_at)由 loader 自填,
值可信故可帶型別(date/timestamptz);上游資料欄不可信,一律 text。

分區替換 = 先刪 (租戶, 檔案日) 整格、再整檔插入,兩步包在同一個交易:
中途被 kill 就整筆回滾,倉庫不會出現「刪了沒補」的半成品。
"""

import csv
import os

from generator.schema import Table

RAW_SCHEMA = "raw"
METADATA_COLUMNS = ("tenant_id", "file_date", "source_filename", "loaded_at")


def map_header_to_columns(table: Table, header: list[str]) -> list[str]:
    """CSV 表頭(中文,已過驗票口)逐位映射為英文欄名——跟檔案欄序,不假設契約欄序。"""
    zh_to_en = {f.name_zh: f.name_en for f in table.fields}
    return [zh_to_en[name] for name in header]


def create_table_sql(table: Table) -> str:
    data_columns = ",\n    ".join(f"{f.name_en} text" for f in table.fields)
    return (
        f"CREATE SCHEMA IF NOT EXISTS {RAW_SCHEMA};\n"
        f"CREATE TABLE IF NOT EXISTS {RAW_SCHEMA}.{table.name} (\n"
        f"    {data_columns},\n"
        f"    tenant_id text NOT NULL,\n"
        f"    file_date date NOT NULL,\n"
        f"    source_filename text NOT NULL,\n"
        f"    loaded_at timestamptz NOT NULL\n"
        f")"
    )


def delete_partition_sql(table: Table) -> str:
    return (
        f"DELETE FROM {RAW_SCHEMA}.{table.name} "
        f"WHERE tenant_id = %s AND file_date = %s"
    )


def insert_sql(table: Table, csv_columns: list[str]) -> str:
    columns = ", ".join(list(csv_columns) + list(METADATA_COLUMNS))
    # loaded_at 用 SQL 端 now()(交易時間戳):同一分區同一次載入的列共用同一時刻,
    # 故 placeholder 數 = csv 欄數 + metadata 欄數扣掉 loaded_at
    n_params = len(csv_columns) + len(METADATA_COLUMNS) - 1
    placeholders = ", ".join(["%s"] * n_params + ["now()"])
    return f"INSERT INTO {RAW_SCHEMA}.{table.name} ({columns}) VALUES ({placeholders})"


def load_partition(conn, table: Table, csv_path: str, tenant: str, file_date: str) -> int:
    """分區替換寫入一個 (租戶, 檔案日, 表) 的檔案,回傳插入列數。

    conn 是 DB-API 連線(psycopg2);`with conn` 即一個交易——正常結束 commit、
    例外或中斷 rollback,保證「刪」「插」要嘛全做要嘛全不做。
    """
    with open(csv_path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)

    columns = map_header_to_columns(table, header)
    source_filename = os.path.basename(csv_path)
    metadata = (tenant, file_date, source_filename)

    with conn:
        with conn.cursor() as cur:
            cur.execute(delete_partition_sql(table), (tenant, file_date))
            cur.executemany(
                insert_sql(table, columns),
                [tuple(row) + metadata for row in rows],
            )
    return len(rows)

"""T1.2/T1.3/T1.4 — 從 Drive landing 資料夾把 logical_date 那天的檔案下載到本機分區,
過驗票口(表頭比對契約),再入倉(分區替換寫進 Postgres raw 區)。T1.5 加排程/catchup/retry/告警。

依 CONTEXT.md 約定:logical_date = D 的 run,負責檔案日 = D 的檔案。
landing 底下是租戶子資料夾(alpha/beta),list_files() 只列直接子項,要逐租戶列。
"""
from __future__ import annotations

import csv
import os
from datetime import timedelta

import pendulum
import psycopg2
from airflow.sdk import DAG, task
from googleapiclient.discovery import build

from generator.schema import TABLES as SCHEMA_TABLES
from ingestion.drive_client import (
    FOLDER_ID,
    download_file,
    find_file_id,
    get_credentials,
    list_files,
    resolve_tenant_folders,
)
from ingestion.header_validator import validate_header
from ingestion.raw_loader import create_table_sql, load_partition

TENANTS = ["alpha", "beta"]
TABLES = ["transaction_detail", "accounts_receivable"]
LANDING_DIR = "/opt/airflow/landing"
WAREHOUSE_HOST = "postgres-warehouse"  # compose service 名;帳密走 .env 的 POSTGRES_*

# email_on_retry=False:只在最終失敗才通知,重試期間不吵。
DEFAULT_ARGS = {
    "email": [os.environ["AIRFLOW_ALERT_EMAIL"]],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=2),
}


def landing_csv_path(tenant: str, table_name: str, file_date: str) -> str:
    """landing 分區內單一檔案的路徑:{LANDING_DIR}/{租戶}/{檔案日}/{表}_{檔案日}.csv。"""
    return os.path.join(LANDING_DIR, tenant, file_date, f"{table_name}_{file_date}.csv")

@task(retries=3, retry_delay=timedelta(minutes=2))
def download_day(logical_date=None) -> None:
    """下載 logical_date(檔案日)當天、兩個租戶、兩張表的 4 個 CSV,落地到
    LANDING_DIR/{tenant}/{file_date}/{table}_{file_date}.csv。任一檔案缺席直接 raise——
    找不到就大聲失敗,不安靜跳過(對應藍本 silently-drop 事故,見 CONTEXT.md)。

    先把 4 個檔案都在 Drive 上解析存在(resolve_tenant_folders + find_file_id 都不落地),
    全部確認到才開始下載:避免「租戶 A 的兩檔已下載、租戶 B 缺檔才 raise」這種半完成
    landing——run 失敗時,那天的分區不該看起來像部分完成過(對應驗證標準 #4 的精神:
    同一天的結果要一致,不能因為跑失敗留下不完整的殘留)。
    """
    file_date = logical_date.to_date_string()

    service = build("drive", "v3", credentials=get_credentials())
    tenant_folder_ids = resolve_tenant_folders(list_files(service, FOLDER_ID), TENANTS)

    to_download = []  # [(dest_path, file_id), ...], 只有全部解析成功才會非空
    for tenant in TENANTS:
        tenant_files = list_files(service, tenant_folder_ids[tenant])
        dest_dir = os.path.join(LANDING_DIR, tenant, file_date)
        for table in TABLES:
            file_id = find_file_id(tenant_files, tenant=tenant, table=table, file_date=file_date)
            to_download.append((dest_dir, f"{table}_{file_date}.csv", file_id))

    for dest_dir, filename, file_id in to_download:
        os.makedirs(dest_dir, exist_ok=True)
        download_file(service, file_id, os.path.join(dest_dir, filename))


@task
def validate_headers(logical_date=None) -> None:
    """驗票口:逐檔表頭比對契約(generator/schema.py),對不上就讓 task 失敗
    ——連帶讓整個 run 失敗,不安靜跳過(對應藍本 silently-drop 事故,見 CONTEXT.md)。

    只看表頭欄位名稱,不看值:值的怪樣式(中文日期、千分位)屬欄位值漂移,
    是 T2.4 dbt test 的責任,這一關故意放行。

    不覆寫 retries(沿用 0):表頭漂移重試結果不變。
    """
    file_date = logical_date.to_date_string()
    for tenant in TENANTS:
        for table_name in TABLES:
            table = SCHEMA_TABLES[table_name]
            path = landing_csv_path(tenant, table_name, file_date)
            with open(path, encoding="utf-8-sig", newline="") as fh:
                header = next(csv.reader(fh))
            validate_header(table, header)


@task(retries=2, retry_delay=timedelta(minutes=1))
def load_day(logical_date=None) -> None:
    """入倉(T1.4):驗過票的 4 檔寫進 raw 區,每檔一次分區替換(ADR 0002)。

    DDL 冪等(IF NOT EXISTS),每次跑先確保 schema/表存在;之後逐 (租戶, 表)
    呼叫 load_partition——刪整格再插整檔、同一交易,重跑或中途被 kill 都不會
    讓倉庫偏離「乾淨跑一次」的結果。

    retries=2:DB 連線值得重試,分區替換的交易性質保證重跑安全。
    """
    file_date = logical_date.to_date_string()
    conn = psycopg2.connect(
        host=WAREHOUSE_HOST,
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    try:
        with conn:
            with conn.cursor() as cur:
                for table_name in TABLES:
                    cur.execute(create_table_sql(SCHEMA_TABLES[table_name]))
        for tenant in TENANTS:
            for table_name in TABLES:
                path = landing_csv_path(tenant, table_name, file_date)
                n_rows = load_partition(
                    conn, SCHEMA_TABLES[table_name], path, tenant, file_date
                )
                print(f"raw.{table_name} ← {tenant}/{file_date}:{n_rows} 列")
    finally:
        conn.close()


with DAG(
    dag_id="drive_ingestion",
    description="Drive landing → 本機分區 → 驗票 → raw 入倉,排程/catchup/retry/告警(T1.2–T1.5)",
    # catchup=True + end_date 圈住 2026-01-01~01-05,剛好排 5 趟(D3)。
    schedule="@daily",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    end_date=pendulum.datetime(2026, 1, 5, tz="UTC"),
    catchup=True,
    default_args=DEFAULT_ARGS,
    tags=["t1.2", "t1.3", "t1.4", "t1.5", "ingestion"],
) as dag:
    download_day() >> validate_headers() >> load_day()

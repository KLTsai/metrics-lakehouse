"""T1.2 — 從 Drive landing 資料夾把 logical_date 那天的檔案下載到本機分區。

依 CONTEXT.md 約定:logical_date = D 的 run,負責檔案日 = D 的檔案。
landing 底下是租戶子資料夾(alpha/beta),list_files() 只列直接子項,要逐租戶列。
"""
from __future__ import annotations

import os

import pendulum
from airflow.sdk import DAG, task
from googleapiclient.discovery import build

from ingestion.drive_client import (
    FOLDER_ID,
    download_file,
    find_file_id,
    get_credentials,
    list_files,
    resolve_tenant_folders,
)

TENANTS = ["alpha", "beta"]
TABLES = ["transaction_detail", "accounts_receivable"]
LANDING_DIR = "/opt/airflow/landing"


@task
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


with DAG(
    dag_id="drive_ingestion",
    description="Drive landing → 本機分區(T1.2)",
    schedule=None,  # 手動觸發;catchup/backfill 排程屬 T1.5(D3:2026-01-01~01-05 資料窗口)
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    tags=["t1.2", "ingestion"],
) as dag:
    download_day()

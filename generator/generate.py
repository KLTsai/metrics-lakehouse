"""乾淨資料合成、髒資料編排與 CSV 輸出。

輸出:out_dir/{tenant_id}/{table}_{YYYY-MM-DD}.csv,UTF-8 with BOM
(藍本 loader 用 utf-8-sig 讀)。一個檔案日一個檔案,檔名日期即該檔的檔案日。

主鍵內嵌歸屬日(ORD-{tenant}-{YYYYMMDD}-{seq} / AR-{tenant}-{YYYYMMDD}-{seq}),
遲到列的判定走主鍵而非日期欄——日期欄可能被缺值/漂移注入命中,主鍵保證不被注入。

決定性:每個 (seed, tenant, table) 派生一顆 random.Random(字串 seeding 不經
hash(),跨執行穩定),生成與注入全走這顆 rng;同 seed 兩次輸出 byte-identical。
"""

import csv
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from generator.dirty import (
    inject_drift,
    inject_missing,
    pick_duplicate_sources,
    pick_late_rows,
)
from generator.schema import ACCOUNTS_RECEIVABLE, TABLES, TRANSACTION_DETAIL, Table


@dataclass(frozen=True)
class Rates:
    """四類髒資料各自的注入比例(對各自的自然分母)。"""

    missing: float
    duplicate: float
    drift: float
    late: float


_CHANNELS = ("官網", "門市", "經銷", "電商平台")
_CHANNEL_DETAILS = ("台北信義店", "台中旗艦店", "momo", "PChome", "-")
_AREAS = ("北區", "中區", "南區", "東區")
_SALES_REPS = ("Amy", "Ben", "Cindy", "Derek", "無業務")
_STATUSES = ("成交", "成交", "成交", "進行中", "關閉")  # 成交為大宗
_REMARKS = ("-", "大客戶專案價", "行銷檔期", "補單")
_CUSTOMERS = (
    ("C00001", "大同精密股份有限公司"),
    ("C00002", "永豐商行"),
    ("C00003", "禾風食品股份有限公司"),
    ("C00004", "青山貿易有限公司"),
    ("C00005", "明志工業股份有限公司"),
    ("C00006", "光洋實業有限公司"),
    ("C00007", "尚益電子股份有限公司"),
    ("C00008", "允成企業社"),
)


def _order_row(rng: random.Random, tenant: str, idx: int, batch_date: date) -> dict:
    price = rng.uniform(50, 5000)
    return {
        "order_id": f"ORD-{tenant}-{batch_date:%Y%m%d}-{idx:05d}",
        "customer_id": f"CUST{rng.randint(1, 40):06d}",
        "product_id": f"P{rng.randint(1, 30):06d}",
        "channel": rng.choice(_CHANNELS),
        "channel_detail": rng.choice(_CHANNEL_DETAILS),
        "area": rng.choice(_AREAS),
        "sales_re_name": rng.choice(_SALES_REPS),
        "status": rng.choice(_STATUSES),
        "opportunity_opened_at": batch_date.isoformat(),
        "closed_at": (batch_date + timedelta(days=rng.randint(0, 30))).isoformat(),
        "quantity": str(rng.randint(1, 500)),
        "exchange_rate": "1.0000",
        "currency_code": "TWD",
        "actual_price_ex_tax": f"{price:.2f}",
        "tax_rate": "1.5",
        "remark": rng.choice(_REMARKS),
    }


def _ar_row(rng: random.Random, tenant: str, idx: int, batch_date: date) -> dict:
    customer_id, customer_name = rng.choice(_CUSTOMERS)
    amount = rng.uniform(10_000, 800_000)
    roll = rng.random()
    if roll < 0.4:
        received, status = amount, "全收款"
    elif roll < 0.7:
        received, status = amount * rng.uniform(0.1, 0.9), "部分收款"
    else:
        received, status = 0.0, "未收款"
    due = batch_date + timedelta(days=60)
    return {
        "document_no": f"AR-{tenant}-{batch_date:%Y%m%d}-{idx:05d}",
        "customer_id": customer_id,
        "customer_name": customer_name,
        "invoice_date": batch_date.isoformat(),
        "original_currency": "TWD",
        "exchange_rate": "1.0000",
        "original_amount": f"{amount:.2f}",
        "received_amount": f"{received:.2f}",
        "due_date": due.isoformat(),
        "actual_collection_date": (
            batch_date + timedelta(days=rng.randint(5, 90))
        ).isoformat(),
        "expected_collection_date": (
            due + timedelta(days=rng.randint(-10, 10))
        ).isoformat(),
        "payment_status": status,
        "memo": rng.choice(_REMARKS),
    }


_ROW_MAKERS = {
    TRANSACTION_DETAIL.name: _order_row,
    ACCOUNTS_RECEIVABLE.name: _ar_row,
}


def generate_tenant_table(
    rng: random.Random,
    table: Table,
    tenant: str,
    rows: int,
    batch_dates: list[date],
    rates: Rates,
) -> dict[date, list[dict]]:
    """生成單一 (tenant, table) 的所有批次,回傳 {批次日期: 列}。"""
    n_batches = len(batch_dates)
    batch_of = [rng.randrange(n_batches) for _ in range(rows)]
    base = [
        _ROW_MAKERS[table.name](rng, tenant, i, batch_dates[batch_of[i]])
        for i in range(rows)
    ]

    late = pick_late_rows(rng, batch_of, n_batches, rates.late)
    missing_cells = inject_missing(rng, base, table, rates.missing)
    drift_cells = inject_drift(rng, base, table, rates.drift, missing_cells)
    touched = {i for i, _ in missing_cells | drift_cells} | set(late)
    dup_sources = pick_duplicate_sources(rng, rows, rates.duplicate, touched)

    by_batch: dict[date, list[dict]] = {d: [] for d in batch_dates}
    for i, row in enumerate(base):
        by_batch[batch_dates[late.get(i, batch_of[i])]].append(row)
    for i in dup_sources:
        by_batch[batch_dates[batch_of[i]]].append(dict(base[i]))
    return by_batch


def _header_row(table: Table, header_drift: tuple[str, str, str] | None) -> list[str]:
    if header_drift is not None:
        drift_table, drift_field, new_name = header_drift
        if table.name == drift_table:
            return [
                new_name if f.name_en == drift_field else f.name_zh
                for f in table.fields
            ]
    return [f.name_zh for f in table.fields]


def _write_csv(
    path: Path,
    table: Table,
    rows: list[dict],
    header_drift: tuple[str, str, str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(_header_row(table, header_drift))
        for row in rows:
            writer.writerow([row[f.name_en] for f in table.fields])


def generate_all(
    out_dir: Path | str,
    tenants: list[str],
    rows: int,
    batches: int,
    start_date: date,
    seed: int,
    rates: Rates,
    header_drift: tuple[str, str, str] | None = None,
) -> list[Path]:
    """生成全部租戶兩張表的批次 CSV,回傳寫出的檔案路徑。

    header_drift = (table_name, field_name_en, new_name_zh):單欄表頭改名,
    模擬 T1.3 要擋下的欄位名稱漂移(藍本真實事故:上游改欄名,舊系統安靜丟欄)。
    只改表頭那一行,資料列與其他表不受影響。
    """
    if header_drift is not None:
        drift_table, drift_field, _ = header_drift
        if drift_table not in TABLES:
            raise ValueError(f"--header-drift 的 table 不在契約裡:{drift_table}")
        if drift_field not in {f.name_en for f in TABLES[drift_table].fields}:
            raise ValueError(
                f"--header-drift 的 field 不在 {drift_table} 契約裡:{drift_field}"
            )

    out_dir = Path(out_dir)
    batch_dates = [start_date + timedelta(days=i) for i in range(batches)]
    written = []
    for tenant in tenants:
        for table in TABLES.values():
            rng = random.Random(f"{seed}:{tenant}:{table.name}")
            by_batch = generate_tenant_table(
                rng, table, tenant, rows, batch_dates, rates
            )
            for batch_date, batch_rows in by_batch.items():
                path = out_dir / tenant / f"{table.name}_{batch_date.isoformat()}.csv"
                _write_csv(path, table, batch_rows, header_drift)
                written.append(path)
    return written

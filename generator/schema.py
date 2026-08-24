"""上傳契約層 schema 常數(逐欄照抄藍本,不含落地層衍生欄位)。

藍本出處(唯讀,決策 #4):
/Users/kun/projects/Genie-AI/8ndpoint-gen2-be-feature-cxo-integration/
endpoint/extensions/data_mapping/domain/target_tables/{cro,cfo}.py
- transaction_detail(訂單,16 欄)取自 cro.py TRANSACTION_DETAIL_FIELDS
- accounts_receivable(應收帳款,13 欄)取自 cfo.py ACCOUNTS_RECEIVABLE_FIELDS

CSV 表頭用 name_zh(客戶上傳的原始欄名;藍本 loader 以表頭原樣建表)。

missing_pool(缺值注入欄位池)= required 欄位扣掉主鍵;訂單表另納入
「客戶編號」(2026-08-13 裁示)。主鍵不注入缺值:兩個以上空主鍵會互相
碰撞,打破「總列數 − 相異主鍵數」的精確斷言,也會污染 dbt unique 的語意。
缺值筆數的分母仍照任務卡 = required 欄位數 × 基底列數。
"""

from dataclasses import dataclass

STRING = "string"
DECIMAL = "decimal"
DATETIME = "datetime"


@dataclass(frozen=True)
class Field:
    name_en: str
    name_zh: str
    kind: str
    required: bool = False


@dataclass(frozen=True)
class Table:
    name: str  # 藍本 table_name,也是輸出檔名前綴
    primary_key: str  # name_en
    fields: tuple[Field, ...]
    missing_pool: tuple[str, ...]  # name_en


TRANSACTION_DETAIL = Table(
    name="transaction_detail",
    primary_key="order_id",
    fields=(
        Field("order_id", "訂單編號", STRING, required=True),
        Field("customer_id", "客戶編號", STRING),
        Field("product_id", "產品編號", STRING, required=True),
        Field("channel", "銷售管道", STRING),
        Field("channel_detail", "管道細項", STRING),
        Field("area", "銷售區域", STRING),
        Field("sales_re_name", "業務名稱", STRING),
        Field("status", "訂單狀態", STRING),
        Field("opportunity_opened_at", "商機開放日", DATETIME, required=True),
        Field("closed_at", "商機關閉日", DATETIME),
        Field("quantity", "銷售量", DECIMAL, required=True),
        Field("exchange_rate", "匯率", DECIMAL),
        Field("currency_code", "金額單位", STRING),
        Field("actual_price_ex_tax", "實際售價（未稅）", DECIMAL),
        Field("tax_rate", "稅率", DECIMAL),
        Field("remark", "備註說明", STRING),
    ),
    missing_pool=("customer_id", "product_id", "opportunity_opened_at", "quantity"),
)

ACCOUNTS_RECEIVABLE = Table(
    name="accounts_receivable",
    primary_key="document_no",
    fields=(
        Field("document_no", "單據號碼", STRING, required=True),
        Field("customer_id", "客戶代碼", STRING, required=True),
        Field("customer_name", "客戶名稱", STRING, required=True),
        Field("invoice_date", "發票日期", DATETIME, required=True),
        Field("original_currency", "幣別", STRING),
        Field("exchange_rate", "匯率", DECIMAL),
        Field("original_amount", "發票金額", DECIMAL, required=True),
        Field("received_amount", "已收金額", DECIMAL),
        Field("due_date", "發票到期日", DATETIME),
        Field("actual_collection_date", "實際入帳日", DATETIME, required=True),
        Field("expected_collection_date", "預計入帳日", DATETIME),
        Field("payment_status", "收款狀態", STRING),
        Field("memo", "備註", STRING),
    ),
    missing_pool=(
        "customer_id",
        "customer_name",
        "invoice_date",
        "original_amount",
        "actual_collection_date",
    ),
)

TABLES: dict[str, Table] = {
    TRANSACTION_DETAIL.name: TRANSACTION_DETAIL,
    ACCOUNTS_RECEIVABLE.name: ACCOUNTS_RECEIVABLE,
}

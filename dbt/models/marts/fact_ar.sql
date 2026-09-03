with source as (
    select * from {{ ref('stg_accounts_receivable') }}
),

deduped as (
    -- document_no 內嵌租戶代號，partition 不會跨租戶誤併；
    -- 同鍵取檔案日最大者，ADR 0005「去重在 fact」
    select
        *,
        row_number() over (
            partition by document_no
            order by file_date desc
        ) as rn
    from source
)

select
    document_no,
    coalesce(customer_id, {{ unknown_customer_id() }}) as customer_id,
    -- customer_name 不留在 fact，是 dim_ar_customer 的屬性（本卡新增）
    coalesce(invoice_date, {{ unknown_date() }}) as invoice_date,
    original_currency,
    exchange_rate,
    original_amount,
    received_amount,
    coalesce(due_date, {{ unknown_date() }}) as due_date,
    coalesce(actual_collection_date, {{ unknown_date() }}) as actual_collection_date,
    coalesce(expected_collection_date, {{ unknown_date() }}) as expected_collection_date,
    payment_status,
    memo,
    tenant_id,
    file_date,
    source_filename,
    loaded_at
from deduped
where rn = 1

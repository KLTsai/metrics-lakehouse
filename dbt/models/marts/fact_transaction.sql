with source as (
    select * from {{ ref('stg_transaction_detail') }}
),

deduped as (
    -- 同一 order_id 多列（產生器整列複製或未來的狀態更新）留檔案日最新者，
    -- ADR 0005「去重在 fact，規則是同鍵取檔案日最大者」
    select
        *,
        row_number() over (
            partition by order_id
            order by file_date desc
        ) as rn
    from source
)

select
    order_id,
    coalesce(customer_id, {{ unknown_customer_id() }}) as customer_id,
    product_id,
    channel,
    channel_detail,
    area,
    sales_re_name,
    status,
    coalesce(opportunity_opened_at, {{ unknown_date() }}) as opportunity_opened_at,
    coalesce(closed_at, {{ unknown_date() }}) as closed_at,
    quantity,
    exchange_rate,
    currency_code,
    actual_price_ex_tax,
    tax_rate,
    remark,
    tenant_id,
    file_date,
    source_filename,
    loaded_at
from deduped
where rn = 1

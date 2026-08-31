with source as (
    select * from {{ source('raw', 'transaction_detail') }}
)

select
    nullif(trim(order_id), '') as order_id,
    nullif(trim(customer_id), '') as customer_id,
    nullif(trim(product_id), '') as product_id,
    nullif(trim(channel), '') as channel,
    nullif(trim(channel_detail), '') as channel_detail,
    nullif(trim(area), '') as area,
    nullif(trim(sales_re_name), '') as sales_re_name,
    nullif(trim(status), '') as status,
    {{ parse_date('opportunity_opened_at') }} as opportunity_opened_at,
    {{ parse_date('closed_at') }} as closed_at,
    {{ parse_numeric('quantity') }} as quantity,
    {{ parse_numeric('exchange_rate') }} as exchange_rate,
    nullif(trim(currency_code), '') as currency_code,
    {{ parse_numeric('actual_price_ex_tax') }} as actual_price_ex_tax,
    {{ parse_numeric('tax_rate') }} as tax_rate,
    nullif(trim(remark), '') as remark,
    tenant_id,
    file_date,
    source_filename,
    loaded_at
from source

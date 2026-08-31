with source as (
    select * from {{ source('raw', 'accounts_receivable') }}
)

select
    nullif(trim(document_no), '') as document_no,
    nullif(trim(customer_id), '') as customer_id,
    nullif(trim(customer_name), '') as customer_name,
    {{ parse_date('invoice_date') }} as invoice_date,
    nullif(trim(original_currency), '') as original_currency,
    {{ parse_numeric('exchange_rate') }} as exchange_rate,
    {{ parse_numeric('original_amount') }} as original_amount,
    {{ parse_numeric('received_amount') }} as received_amount,
    {{ parse_date('due_date') }} as due_date,
    {{ parse_date('actual_collection_date') }} as actual_collection_date,
    {{ parse_date('expected_collection_date') }} as expected_collection_date,
    nullif(trim(payment_status), '') as payment_status,
    nullif(trim(memo), '') as memo,
    tenant_id,
    file_date,
    source_filename,
    loaded_at
from source

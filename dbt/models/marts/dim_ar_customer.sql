with source as (
    select * from {{ ref('stg_accounts_receivable') }}
),

customers as (
    select distinct
        tenant_id,
        customer_id
    from source
    where customer_id is not null
),

named as (
    -- Type 1:同鍵、檔案日最大、名稱非缺值那列的名稱蓋掉舊的（ADR 0005 鍵的三個決定）
    select
        tenant_id,
        customer_id,
        customer_name,
        row_number() over (
            partition by tenant_id, customer_id
            order by file_date desc
        ) as rn
    from source
    where customer_id is not null
        and customer_name is not null
),

tenants as (
    select distinct tenant_id
    from source
),

unknown as (
    select
        tenant_id,
        {{ unknown_customer_id() }} as customer_id,
        {{ unknown_customer_id() }} as customer_name
    from tenants
)

select
    c.tenant_id,
    c.customer_id,
    n.customer_name
from customers c
left join named n
    on n.tenant_id = c.tenant_id
    and n.customer_id = c.customer_id
    and n.rn = 1

union all

select * from unknown

with source as (
    select * from {{ ref('stg_transaction_detail') }}
),

customers as (
    select distinct
        tenant_id,
        customer_id
    from source
    where customer_id is not null
),

tenants as (
    select distinct tenant_id
    from source
),

unknown as (
    select
        tenant_id,
        {{ unknown_customer_id() }} as customer_id
    from tenants
)

select * from customers
union all
select * from unknown

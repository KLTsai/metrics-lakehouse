with calendar as (
    select generate_series(
        '2026-01-01'::date,
        '2026-12-31'::date,
        interval '1 day'
    )::date as date_day
),

unknown as (
    select {{ unknown_date() }} as date_day
),

all_dates as (
    select date_day from calendar
    union all
    select date_day from unknown
)

select
    date_day,
    extract(year from date_day)::int as year,
    extract(quarter from date_day)::int as quarter,
    extract(month from date_day)::int as month,
    extract(dow from date_day)::int as day_of_week
from all_dates

{#
  未知客戶代號(ADR 0005「未知客戶用『其他』」)。dim_customer/dim_ar_customer 各租戶
  多一列同代號,fact 的 customer_id 缺值換成它——代號沿用藍本缺值時塞的字串,不是自創。
#}
{% macro unknown_customer_id() -%}
'其他'
{%- endmacro %}

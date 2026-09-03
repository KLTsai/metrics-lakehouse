{#
  dbt 官方標準覆寫(見 dbt docs "generate_schema_name"):預設行為會把
  custom_schema_name 接在 target schema 後面拼成 staging_marts;此卡的
  marts: +schema: marts 要的是「直接照用」,所以覆寫成 custom_schema_name
  為空時用 target schema、非空時原樣採用,不拼接。
#}
{% macro generate_schema_name(custom_schema_name, node) -%}

    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}

        {{ default_schema }}

    {%- else -%}

        {{ custom_schema_name | trim }}

    {%- endif -%}

{%- endmacro %}

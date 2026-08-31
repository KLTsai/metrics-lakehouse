{#
  raw text → numeric 的守門轉型(議題 A 裁示:標準化 → regex 守門 → 沒過轉 NULL)。
  漂移樣式清單以 generator/dirty.py 的 _DECIMAL_STYLES 為準;
  percent(279%)語意不明(÷100 與否依欄位而異)、NaN 非數值,兩者刻意不救,落 else → NULL。
#}
{% macro parse_numeric(column) %}
    case
        when trim({{ column }}) ~ '^-?[0-9]+(\.[0-9]+)?$'
            then trim({{ column }})::numeric
        {# currency:NT$1,648 #}
        when trim({{ column }}) ~ '^NT\$[0-9]{1,3}(,[0-9]{3})*(\.[0-9]+)?$'
            then replace(replace(trim({{ column }}), 'NT$', ''), ',', '')::numeric
        {# acct_neg:(1,361) = 會計負數 #}
        when trim({{ column }}) ~ '^\([0-9]{1,3}(,[0-9]{3})*(\.[0-9]+)?\)$'
            then -(replace(btrim(trim({{ column }}), '()'), ',', '')::numeric)
        {# space_thousand:1 234 #}
        when trim({{ column }}) ~ '^[0-9]{1,3}( [0-9]{3})+$'
            then replace(trim({{ column }}), ' ', '')::numeric
        {# european:1.234,56 = 點千分位+逗號小數 #}
        when trim({{ column }}) ~ '^[0-9]{1,3}(\.[0-9]{3})*,[0-9]+$'
            then replace(replace(trim({{ column }}), '.', ''), ',', '.')::numeric
        {# chinese_unit:50元 #}
        when trim({{ column }}) ~ '^[0-9]+(\.[0-9]+)?元$'
            then replace(trim({{ column }}), '元', '')::numeric
        else null
    end
{% endmacro %}

{#
  raw text → date 的守門轉型。欄位值漂移樣式以 generator/dirty.py 的 _drift_datetime 為準:
  regex 先認樣式:chinese_date(2026年1月2日)與 dot_date(2026.1.2)兩種,認得的才標準化後轉型,其餘 → NULL。
  regex 只守形狀不驗曆法(2026-02-30 會過 regex、在 cast 時報錯,整個 view 的查詢會失敗而非該格變 NULL)——上游是產生器
  契約、只產合法日期;真要防曆法錯值得上 DB 端 UDF,議題 A 裁示不走那條路。
#}
{% macro parse_date(column) %}
    case
        when trim({{ column }}) ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
            then trim({{ column }})::date
        {# chinese_date:年/月 → 「-」,日 → 移除,再走寬鬆 to_date(可吃未補零月日) #}
        when trim({{ column }}) ~ '^[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日$'
            then to_date(translate(trim({{ column }}), '年月日', '--'), 'YYYY-MM-DD')
        {# dot_date:2026.1.2 #}
        when trim({{ column }}) ~ '^[0-9]{4}\.[0-9]{1,2}\.[0-9]{1,2}$'
            then to_date(replace(trim({{ column }}), '.', '-'), 'YYYY-MM-DD')
        else null
    end
{% endmacro %}

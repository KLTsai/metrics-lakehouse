# raw 層保留髒資料,idempotency 走分區替換不走 upsert

raw 層(L1 入倉,T1.4)的形狀:`metrics` DB 開 `raw` schema,每表一張(`raw.transaction_detail`、`raw.accounts_receivable`),資料欄全 `text`、欄名用契約層的英文名(中文表頭由 loader 按契約對照表映射),外加四支 metadata 欄:`tenant_id`、`file_date`(檔案日)、`source_filename`、`loaded_at`。**重複列與各類髒資料原樣入倉,不在 L1 清洗**;idempotent 重跑的機制是**分區替換**——載入前先刪整個分區(租戶 × 檔案日),再整檔插入。

直覺的做法是入倉時就去重(upsert / `ON CONFLICT`),被否決,理由有三:

1. **T2.4 的驗收會空轉**。驗證標準是「產生器注入的每一類髒資料都被至少一個 test 抓到」;若 L1 先吃掉重複列,dbt 的 `unique` test 永遠沒東西抓,品質層戰績落空。
2. **upsert 需要可信主鍵,但 raw 層的前提是「上游不可信」**。主鍵欄位本身可能被漂移/缺值污染,拿它當合併鍵,錯誤會被靜默吸收——這正是藍本事故(silently drop)的行為模式。
3. **分區替換讓 T1.4/T1.5 的驗證有乾淨語意**:「中途 kill 重跑 = 一次跑完」與「刪任意一天 → backfill 補齊」都化約為「一個分區整個換新」,刪與補完全對稱;遲到列跟著它所在的檔案走(見 CONTEXT.md「遲到列」「一天的資料」),不會跨分區牽扯。

連帶約定:Airflow 的 `logical_date` = D 的 run 負責檔案日 = D 的檔案(對齊是設計,兩者不是同義詞;詞條見 CONTEXT.md)。

出處:Phase 1 grilling(2026-08-26)。

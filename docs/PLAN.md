# DE 轉職學習計畫（metrics-lakehouse）

> 狀態：v1 草稿，待 kun 自審
> 簽核日：2026-07-17（grilling session 共識，12 項決策全數 sign off）；repo 定名 metrics-lakehouse：2026-07-18；Phase 0 開發環境建置完成：2026-07-19；T0.3 完成：2026-07-19
> 本文件為內部工作文件（中文）；公開 repo 的 README 與架構文件為英文，由本文件的定稿內容翻譯產出。
> **實體位置變更**：本檔案的事實來源已從 Windows 側路徑遷移至 WSL 原生檔案系統 `~/projects/metrics-lakehouse/docs/PLAN.md`（見決策 #13）。Windows 側 `C:\Users\d8105\Desktop\Genie-AI\metrics-lakehouse\` 為建置過程留下的舊副本，待清除（見 §11）。
> **開發環境二次變更（2026-07-27 確認）**：開發已改為單一 macOS 機器（非 WSL、非兩台並行），決策 #13 同步改寫；T0.1/T0.2 的 WSL2 完成紀錄為當時實況，予以保留。

---

## 1. 目標與成功標準

**主目標（轉職導向）**：8 週後，能在 Data Engineer 面試中講出一段 20 分鐘、經得起「由難到易遞進追問」的真實 pipeline 戰績（面經證據：17LIVE 面試官對履歷上的 Airflow 深問到 Docker build 與測試環境層級）。

**底層目標（能力內化）**：內化 DE 核心思維——idempotency、backfill、data quality、DAG 編排、資料建模、規模化取捨。

**驗收方式**：
- 每個任務附「驗證標準」與「三個為什麼」自檢，答不出來 = 還沒學會
- 第 4 週：repo 丟 DE 社群（Data Engineering Taiwan / r/dataengineering）討真人回饋
- 第 6 週：SQL 限時診斷（2 小時，DataLemur/StrataScratch medium 題，模擬筆試條件）
- 第 8 週：真人 mock interview

**明確的期望校準**：portfolio 是彈藥庫不是入場券——從業者共識是它對轉職者最有價值，但價值在「面試時每句話有實作背書」，不在「被 HR 點開」。台灣面試的入場券是 SQL 筆試（見 §6）。

---

## 2. 決策總表（12 項，含證據）

| # | 決策 | 結論與依據 |
|---|---|---|
| 1 | 成功標準 | 轉職為主、能力為底 |
| 2 | 市場 | 台灣有規模公司 + 外商通用（查證 12+ 張實際 JD） |
| 3 | 工具組 | Airflow（momo 列必備、國泰加分）+ dbt（載體，見 #8）+ Spark/Databricks FE（LINE/KKBOX/Appier 必備，mid→senior 分水嶺）；微軟三件套不做（台灣大公司 JD 出現次數為零） |
| 4 | 專案形式 | 獨立資料平台 repo：「多租戶 SMB 財務/業務資料平台」。Genie-AI 三 repo 為唯讀藍本——只取 schema/邏輯/事故教材，重新實作，不搬 code（IP 乾淨） |
| 5 | 資料 | 合成資料產生器，內建髒資料注入（缺值、格式漂移、重複列、遲到資料）；CSV 放自有 Google Drive 讓整條鏈真實運轉。依據：過乾淨的合成資料是從業者點名的減分項；藍本產品的真實事故（欄位被 silently drop、schema drift）就是髒資料的設計規格 |
| 6 | 時間 | ~20 小時/週 × 8 週；核心 ~90 小時，其餘為緩衝與加碼 |
| 7 | 加碼層 | Kimball 維度建模（融入 Phase 2）第一、data quality 第二；BigQuery 不做 |
| 8 | dbt 定位 | dbt 在台灣大公司 JD 出現次數為零，但它是練「進階 SQL、data modeling、data quality」（玉山/KKBOX/台積電 JD 明列）最有效率的載體。履歷寫法：data modeling 與 data quality 是主詞，dbt 是工具名 |
| 9 | SQL | 8 週內靠專案練（Phase 2 是大量進階 SQL 實戰）；第 6 週限時診斷量差距；刷題（易逝技能）留到求職期前衝刺。「先量測再優化」本身是可講的工程決策 |
| 10 | 證據形式 | 公開 repo：英文 README + 架構圖 + 每 Phase 一篇 ADR（含本計畫的 JD/面經出處，可回查） |
| 11 | 分工 | 結對協作：kun 站 top-down 決策位；核心產出（DAG、dbt models、star schema、Spark job）必須過 kun 的手、且能複述原理才算完成；環境雜活與英文翻譯由 Claude 扛 |
| 12 | 刻意不做 | Kafka/streaming、K8s、BigQuery → §9「第 3 個月以後」。皆為真實 JD 需求，但 8 週塞入必然全盤半吊子 |
| 13 | 開發環境 | ~~WSL2（Ubuntu 24.04）原生開發 + Docker Engine 原生安裝（非 Docker Desktop）~~ → **改為 macOS 原生開發**（2026-07-27 確認換機，非兩台並行），repo 實體位置在此機器（`~/projects/metrics-lakehouse`）。容器執行時改用 **Colima**（非 Docker Desktop）：以輕量 Linux VM 提供 Docker daemon，避開 Docker Desktop 的授權與資源開銷。原本 bind-mount 到 `/mnt/c` 效能差、inotify 跨界不觸發兩項理由是 WSL↔Windows 跨界才有的問題，macOS 原生執行不受影響；Linux 環境需求（國泰等 JD 明列）由 Colima 內部的 Linux VM 滿足，不受環境變更影響。**GitHub 私有 repo 從第一個 commit 就同步備份**（`github.com/KLTsai/metrics-lakehouse`），直接對應上次原機器全毀、資料/憑證盡失的教訓；開發期維持 private，轉 public 時機見 §11 |

---

## 3. 架構五層（公開 repo 的骨架）

```
┌─────────────────────────────────────────────────────────┐
│ L5 文件層    英文 README／架構圖／ADR×3（Before→After 敘事）│
├─────────────────────────────────────────────────────────┤
│ L4 規模驗證  Databricks FE + PySpark：大劑量重做同套指標，  │
│              找 Postgres→Spark 的瓶頸臨界點                │
├─────────────────────────────────────────────────────────┤
│ L3 轉換層    dbt：staging → Kimball star schema marts，    │
│              schema tests 抓髒資料，dbt run/test 掛回 DAG   │
├─────────────────────────────────────────────────────────┤
│ L2 編排層    Airflow（Docker, LocalExecutor）：Drive 下載   │
│              → 驗證/drift 檢查 → 入倉 Postgres              │
│              retry／backfill／idempotency                  │
├─────────────────────────────────────────────────────────┤
│ L1 資料源    髒資料產生器 → 多租戶 SMB 試算表 → Google Drive │
└─────────────────────────────────────────────────────────┘
```

設計藍本對照（面試敘事的根）：L1 髒資料規格 ← 藍本的真實事故；L2 ← 藍本的 systemd timer + outbox 土法排程（ADR#1 的 Before）；L3 ← 藍本 102 張版本化 chart SQL；L4 ← 「如果租戶數 ×1000」的規模化推演。

---

## 4. 八週計畫與任務清單

> 執行方式：每個任務開工時，Claude 先出「任務卡」（目標／步驟提示／驗證標準／三個為什麼），討論後 kun 實作，Claude 審查。卡關 30 分鐘即求援——先給方向、不給答案。
> 時數為預估上限，做完即停；累計落後 >1 週時觸發 §8 砍範圍規則。

### Phase 0（週 1，~12h）：地基

| 任務 | 內容 | 驗證標準 |
|---|---|---|
| T0.1 | ~~Docker Desktop 安裝~~ → **WSL2(Ubuntu 24.04) 全新安裝 + `.wslconfig` 設記憶體上限（8GB/6 核心/2GB swap）+ Docker Engine 原生安裝**（見決策 #13） | ✅ 已完成（2026-07-19）：`docker run hello-world` 以一般使用者身分通過；`free -h` 確認 WSL2 記憶體上限生效。環境已於 2026-07-27 改為 macOS + Colima（決策 #13 已更新），此筆為當時 WSL2 環境下的驗證紀錄 |
| T0.2 | repo 骨架：WSL 原生 fs 內 git init、GitHub private repo 備份、目錄結構（`generator/ airflow/ dbt/ spark/ docs/`）、README stub | ✅ 已完成（2026-07-19）：`~/projects/metrics-lakehouse` 已 git init 並 push 至 `github.com/KLTsai/metrics-lakehouse`（private）；VS Code Remote-WSL 連線確認可用；conventional commits 從第一個 commit 開始。環境已於 2026-07-27 改為 macOS（決策 #13 已更新），repo 實體位置改在此機器；**VS Code Remote-WSL 該項不再適用**（該 extension 為 WSL 專屬，macOS 上不存在） |
| T0.3 | Postgres via docker compose | ✅ 已完成（2026-07-19）：named volume + healthcheck；本機 `psql -h localhost` 連線通過；持久化以「寫入標記列 → `down` → `up -d` → 查回」驗證，並以 `down -v` 反向實驗對照（volume 被刪、資料蒸發、重跑 initdb），確認 `down` 與 `down -v` 的差異 |
| T0.4 | GCP 專案 + Drive API OAuth 憑證 | ✅ 已完成（2026-07-27）：沿用既有 GCP 專案（Console 新版 UI 為 Google Auth Platform，Audience 分頁設定 External + test user）；OAuth client（Desktop app）下載 `credentials.json`；`ingestion/drive_client.py` 四個 TODO 由 kun 填完、我 review 修正（SCOPES 改為單一 `drive.readonly`——原本 `drive.file`+`drive.metadata.readonly` 組合看不到既有檔案且無下載權限；`get_credentials` 清掉授權後多餘的 `raise NotImplementedError`）；`list_files`/`download_file` 皆驗證通過（實際列出並下載 Drive 檔案） |
| T0.5 | 髒資料產生器 v1：參考藍本 schema（訂單、應收帳款），生成多租戶 CSV；髒資料注入可設比例（缺值/重複/格式漂移/遲到） | ✅ 產生器完成（2026-08-24，commit `544c95d`+`4dacb8f`）：`generator/` 套件（schema/dirty/generate/cli/`__main__`）+ `tests/test_generator.py` 19 個測試，套件全綠（含既有 smoke 共 20）；四類注入為**精確相等**斷言（筆數 = `floor(分母×5%)` 逐項吻合，突變測試驗過斷言鑑別力）；同 seed 兩跑 byte-identical；輸出 `generator/out/{tenant}/{table}_{YYYY-MM-DD}.csv`（UTF-8 with BOM）。設計決策見 `docs/adr/0001-generator-contract-layer.md`（契約層界線、兩表取捨、注入互斥）。分工為 agent 全包（2026-08-13 裁示，產生器不在 §5.2 核心產出清單）。✅ Drive 上傳驗證通過（2026-08-25）：檔案在 `我的雲端硬碟/lakehouse/landing/{alpha,beta}/`（landing 資料夾 ID `1DgrZIkA2Pis-sYz_2v3BDj4I0YOk75xh`，非 `drive_client.py:15` 寫死的舊測試資料夾——T1.2 設計時要決定 folder ID 的設定方式），以 T0.4 `list_files` 核對 20 檔齊全、抽樣下載與本地 byte-identical。⚠️ 過程中撞到：OAuth app 為 External+Testing 模式，**refresh token 七天過期**（`invalid_grant`，需刪 token.json 重授權）——T1.2 排程化前必解（發佈 app 或改 service account），列入 Phase 1 grilling 議題 |
| T0.6 | WSL 原生環境內 Node.js/npm + Claude Code CLI 可執行（T0.1/T0.2 建置當時漏列，直到搬遷個人設定才發現 `claude: command not found`） | ✅ 已完成（2026-07-19）：`node -v`/`npm -v`/`claude --version` 皆正常（僅互動 shell 下如此——非互動 shell 因 `~/.bashrc` 開頭的 interactive guard 看不到 nvm，屬正常現象非 bug）；個人 CLAUDE.md/playbooks/6 個本地 skills 已從 Windows 側搬遷；5 個個人 plugin marketplace 全數重新啟用。**環境已於 2026-07-27 改為 macOS**（決策 #13 已更新）——上述 WSL/`~/.bashrc` 情境不再適用（本機 shell 為 zsh、無 `~/.bashrc`，nvm 走 `~/.zshrc`）；已於 macOS 重新驗證：`node v24.18.0`／`npm 11.16.0`／`claude 2.1.220` 皆正常 |

三個為什麼（示例）：為什麼髒資料要可設比例？為什麼產生器要固定 random seed？為什麼多租戶要分檔而不是合一張表？

### Phase 1（週 2–4，~28h）：Airflow 編排層

| 任務 | 內容 | 驗證標準 |
|---|---|---|
| T1.1 | Airflow（docker compose、LocalExecutor、不跑 Celery/Redis） | ✅ 全關（2026-08-26）：環境實作與驗證完成（2026-08-25），kun 已口頭複述四個為什麼。版本：`apache/airflow:3.3.1`（當時 stable，2026-08-12 發布；arm64 manifest 已確認）——任務卡 sign off 時定案採 3.x 而非 2.x，第四個為什麼即此決策。官方 compose 範本裁剪：留 airflow-init/scheduler/**api-server**/**dag-processor**（3.x 的 webserver 改名 api-server，dag-processor 為 3.x 新增必要元件），去 celery worker/redis/flower，**triggerer 一併裁掉**（Phase 1 無 deferrable 任務，需要時加回幾行即可）；logs 用 named volume（`airflow_logs`）而非 bind-mount（避免 host 權限問題）。metadata DB 為獨立 service `postgres-airflow`，**不對 host 曝 port**（host 5432 屬 `postgres-warehouse`）、配獨立 volume `airflow_metadata_data`；`.env` 變數用 `AIRFLOW_` 前綴與倉庫 `POSTGRES_*` 分開。驗證：①`up -d` 一次起全 stack、五服務 healthy，倉庫 `metrics` DB 與 `warehouse` role 完好（T0.3 標記列在本次之前已不存在——非此次弄丟，依 T0.3 驗法重建 `persistence_marker` 一列參與後續驗證）；②admin 帳密經 `/auth/token` 取得 JWT（登入驗證）、UI 頁面 `GET /` 與 `/auth/login` 皆 HTTP 200 回 HTML、`example_bash_operator` 三跑皆 success（kun 於瀏覽器實際登入為人工驗收步驟）；③記憶體基線（Colima VM 8 GiB，容器可見 7.737 GiB）：閒置 5 分鐘後 apiserver 304 / dag-processor 294 / scheduler 666 / postgres-airflow 85 / postgres-warehouse 38 MiB，合計約 1.39 GiB；example DAG 執行中僅 scheduler 升至峰值 780 MiB（LocalExecutor 任務跑在 scheduler 下），合計約 1.50 GiB；VM 層（`colima ssh -- free -m`，補量於 code review 後）used 約 1.4–1.7 GiB（total 7,922 MiB）——距 8 GiB 配額餘裕充足，webserver 反覆重啟症狀未出現，不需調資源；④`down`（不帶 `-v`）→ `up -d` 後 DAG run 歷史（3 筆）與倉庫標記列皆查得回 |
| T1.2 | DAG v1：Drive 下載 → landing 區 | ✅ 全關（2026-08-26）：kun 已口頭複述三個為什麼（Q1/Q2 兩輪修正後過、Q3 一次過）。認證改 service account（ADR 0003),`ingestion/drive_client.py` 新增 `get_credentials()`(讀 `SERVICE_ACCOUNT_KEY_PATH`,金鑰檔 `service-account-key.json` 進 `.gitignore`,repo 根)、純函式 `resolve_tenant_folders`/`find_file_id`(landing 底下先列一次拿租戶資料夾 ID,再逐租戶列檔;找不到檔案 raise 並點名租戶+表+檔案日)。新增 `airflow/dags/drive_ingestion.py`(TaskFlow DAG,`download_day()` 先把 4 個檔案在 Drive 上全部解析存在、確認到才開始下載——避免半完成分區殘留)。compose 新增三個掛載(`ingestion/` 套件、金鑰唯讀、`landing/` 下載目錄),`airflow-init` 一併建目錄+chown。分工本次臨時改為 agent 全包(kun 因時程壓力明確要求,見協作契約下方備註)、TDD 覆蓋純函式(`tests/test_drive_client.py` 6 測試,全專案 26 全綠),code review 兩軸(Standards/Spec)跑過,Spec 軸抓到「逐租戶逐表邊找邊下載,失敗會留下半完成分區」問題,已修正為「先全部解析、確認到才下載」並重新實測。四條驗證標準皆用真實 Airflow 容器+真實 Drive 實測:①手動觸發 logical_date=2026-01-01 → success,4 檔落地 `landing/{alpha,beta}/2026-01-01/`;②抽 `alpha/accounts_receivable` 與 Drive 原檔 `diff` byte-identical;③觸發 2026-02-01(無檔案)→ failed,log 精準點名「租戶 alpha 的 transaction_detail 表在檔案日 2026-02-01 找不到檔案」;④`airflow dags clear` 重跑同一天 → 4 檔 md5 前後一致,未累積 |
| T1.3 | 驗證/drift 檢查 task：schema 對照、欄位漂移偵測 | ✅ 全關（2026-08-27）：kun 已口頭複述三個為什麼（Q2 一次過,Q1 兩輪修正後過,Q3 三輪修正後過)。四項驗證標準皆通過。新增 `ingestion/header_validator.py`：`validate_header(table, header)` 比對「缺欄」「多欄」兩個集合（改名會同時出現在兩邊,是最清楚的告警內容),契約唯一來源 `generator/schema.py`,故意不管欄位順序（CONTEXT.md「欄位名稱漂移」只界定名稱/組成）;`tests/test_header_validator.py` 5 測試。產生器加 `--header-drift table:field_en:new_name_zh`（`generator/cli.py`+`generate.py`),只改指定表指定欄的表頭那一行,`tests/test_generator.py` 新增 5 測試（含同 seed byte-identical 不被破壞）。`airflow/dags/drive_ingestion.py` 新增 `validate_headers` task,接在 `download_day` 後面（`download_day() >> validate_headers()`);compose 新增 `generator/` 掛載,讓 DAG 容器內可 import 契約(不另抄一份欄名清單)。分工延續 T1.2「agent 全包」臨時例外（kun 因時程需求延續,非永久改協作契約,見 memory `feedback_urgent_comprehension_first.md`）。過程中驗票口意外抓到一個既有落差:Drive/`landing/` 現有的 T0.5 測試資料是 2026-08-24 commit `4dacb8f`(表頭括號全形化)之前產生的舊檔,`transaction_detail` 表頭（`實際售價(未稅)` 半形 vs 契約 `實際售價（未稅）` 全形)跟目前契約不符——已用現行 schema 重新產生 20 個檔案,kun 手動覆蓋上傳 Drive 排除。四條驗證標準皆用真實 Airflow 容器+真實 Drive 實測:①正常一整天（2026-01-01,重新上傳後)→ `download_day`/`validate_headers` 皆 success;②`--header-drift transaction_detail:customer_id:客戶代碼` 重產 2026-01-06 全部 4 檔（kun 手動上傳)→ 觸發後 `download_day` success、`validate_headers` failed,log 明確列出「缺欄:['客戶編號'];多欄:['客戶代碼']」;③反向邊界由①一併驗過——2026-01-01 資料本身含預設 5% 欄位值漂移(千分位、中文日期等樣式),驗票照樣放行;④`--header-drift` 有 pytest 覆蓋且不破壞同 seed byte-identical 性質。全專案 pytest 35 綠 |
| T1.4 | 入倉 task：idempotent 寫入 Postgres | **中途 kill 任務再重跑，結果與一次跑完完全一致** |
| T1.5 | backfill/catchup + retry + 失敗告警 | 刪除任意一天的資料 → backfill 補齊且無重複列 |
| T1.6 | ADR#1：Before（土法排程架構圖與痛點）→ After（Airflow）| kun 能不看稿講出 3 個遷移理由與 1 個 trade-off |

### Phase 2（週 4–6，~24h）：dbt + 維度建模

| 任務 | 內容 | 驗證標準 |
|---|---|---|
| T2.1 | dbt 接 Postgres；staging models | `dbt run` 全綠 |
| T2.2 | star schema 設計（fact/dim 切分、ERD）；Kimball 精選章節閱讀 | kun 能講出每張 dim 的 grain 與 SCD 策略 |
| T2.3 | 遷移核心 20–30 張指標 SQL 成 marts（取藍本邏輯重寫，非複製） | 指標數值與手算樣本一致 |
| T2.4 | schema tests + dbt-expectations | **產生器注入的每一類髒資料都被至少一個 test 抓到** |
| T2.5 | `dbt run/test` 掛進 Airflow DAG（L2+L3 打通） | 端到端一鍵跑完：Drive → 入倉 → marts → tests |
| T2.6 | 【週 6】SQL 限時診斷（2h，模擬筆試） | 產出差距報告，寫入 §6 決策 |
| T2.7 | ADR#2：建模與品質決策 | 同 ADR#1 標準 |

### Phase 3（週 6–8，~26h）：Spark 規模驗證 + 收尾

| 任務 | 內容 | 驗證標準 |
|---|---|---|
| T3.1 | Databricks Free Edition 環境；產生器開大劑量（量級以瓶頸現形為準，不硬追固定行數） | 大劑量資料成功載入 |
| T3.2 | PySpark 重做核心指標 | 與 Phase 2 的 marts 數值對帳一致 |
| T3.3 | 瓶頸實驗：逐級放大，記錄 shuffle/skew/OOM 現象與對策（repartition、broadcast join…） | 每個現象有「觸發條件→觀測證據→對策→效果」四段紀錄（Appier 面試實錄直接考 skew 與 OOM） |
| T3.4 | ADR#3：Postgres vs Spark 的臨界點分析 | kun 能回答「什麼時候該從 Postgres 換 Spark」並給出自己量測的數字 |
| T3.5 | 英文 README + 架構圖 + repo 整理（草稿可中文，翻譯 Claude 代勞、kun 審） | 不點開 code 也能看懂專案（從業者對 README 的核心要求） |
| T3.6 | 【週 8】mock interview + 社群回饋整合 | 回饋寫入 backlog |

### 貫穿事項
- 週 4：repo 丟 DE 社群討回饋（丟之前 README 至少有架構圖）
- 每 Phase 結束：決策紀錄一篇（這就是「證據形式」的本體，不是額外作業）

---

## 5. 協作協議

1. **任務卡先行**：每任務開工前 Claude 出卡（目標／步驟提示／驗證標準／三個為什麼），kun 有異議先討論再動手。
2. **核心產出規則**（2026-08-27 修訂）：DAG、dbt models、star schema、Spark job、入倉等核心邏輯，改由 Claude 全包實作，不再要求 kun 親手改過。完成關卡是**三個為什麼口試**：收工時 Claude 須交付①相關應用目的、②為什麼這樣寫（對齊軟體工程準則）、③矛盾/衝突主動反應、④手動驗證或真實情境操作流程；kun 要能用自己的話複述「三個為什麼」才算全關——概念對但講不出為什麼只算部分過，允許多輪修正，不能直接告知答案結案。（此前 T1.2/T1.3 走的「骨架+TODO(kun)」為條件式例外時期的過渡分工，本次起正式取代原「必須 kun 改過」規則。）
3. **雜活歸 Claude**：環境 troubleshooting、boilerplate、英文翻譯。
4. **卡關 30 分鐘規則**：超過即求援；Claude 先給方向、不直接給答案。
5. **誠實回報**：宣稱「完成」須附驗證輸出（測試結果、對帳數字），與 kun 的 commit 紀律一致。

## 6. SQL 門檻策略

台灣 DE 面試 SQL 筆試/OA 幾乎 100% 前置（台積電面試前寄測驗連結、PChome/FUNNOW/鴻海筆試前置；題型集中 window functions/CTE/Top-K）。策略：8 週內靠 Phase 2 實戰練深度；第 6 週限時診斷量速度差距；診斷結果分流——差距小 → 投履歷前 1–2 週衝刺即可；差距大 → 第 3 個月排正式刷題計畫。

## 7. 風險與緩解

| 風險 | 緩解 |
|---|---|
| ~~**容器記憶體配額偏緊**（Colima VM 4 GiB，正好卡在 Airflow 官方下限）~~ → **已解除（2026-08-01 調至 8 GiB）** | 舊風險「RAM 16GB 偏緊」的依據已隨換機失效（原文為 Ryzen 7 4800U 機器 + `.wslconfig` 8GB 上限的觀測）。**真正的天花板不是 host RAM，是 Colima VM 配額**：實測 Apple M4 / 10 核 / 16GB（free 40%，host 不是瓶頸）、磁碟餘 377GB，但 `colima list` 顯示 VM 僅 **4 GiB**（容器可見 3.813 GiB）——**比舊機 `.wslconfig` 的 8GB 上限更小**。Airflow 官方文件（docker-compose 頁）明載「至少 4GB、macOS 理想 8GB」，並點名 macOS 預設配額常不足、症狀是 **webserver 反覆重啟**。但該數字針對 CeleryExecutor；T1.1 明訂 LocalExecutor、不跑 Celery/Redis，實際需求應更低（低多少無官方數字——**這正是 T1.1 驗證標準「記憶體佔用有量測紀錄」要產出的東西**）。Spark 不佔本機（L4 在 Databricks 雲端跑），4 GiB 不必為 Phase 3 預留。**緩解**：~~維持 4 GiB 進 T1.1，讓量測有意義~~ → **已於 2026-08-01 提前執行 `colima stop && colima start --memory 8`**，VM 現為 8 GiB（容器可見 7,922 MB）；**T1.1 的記憶體量測基準隨之改為 8 GiB**。docker 資料碟是獨立的 Lima external disk，改配額不影響既有 volume——**已實測**（調整前先 `pg_dumpall`；重啟後 volume 存活、`metrics` DB 與 `warehouse` role 完整、8 秒內 healthy、host 端 `psql -h localhost` 通過） |
| ARM64（aarch64）平台相容性——換機至 Apple Silicon 帶來的新暴露面 | **已全數查證消除（2026-07-27）**，屬「踩到再處理」型風險，無沉沒成本。實際暴露面僅三處，全部驗證可用：①`apache/airflow` **≥ 2.3.0** 有官方 arm64 manifest（2.2.0 僅 amd64，實測二分確認；官方限定 ARM64 image 只內含 Postgres client——對本專案無影響）；②`postgres:16` 有 arm64/v8，且**已在本機 healthy 運行逾 22 小時**（實證非宣稱）；③dbt 全套在 aarch64 macOS 解析乾淨（`dbt-core`/`dbt-postgres` 為 pure-python，唯一原生相依 `psycopg2-binary` 有現成 cp311 arm64 wheel，不需編譯）。Spark 在 Databricks 雲端跑（x86_64），**不暴露**。唯一 amd64-only 命中是 `ghcr.io/dbt-labs/dbt-postgres` 官方 image——不在本專案用法內（以 `uv` 裝套件），**僅在未來想把 dbt 容器化時才會撞到**，退路為 Colima 的 `--vz-rosetta`（目前未啟用）或 QEMU binfmt（慢）。唯一需落進任務的動作：T1.1 選 Airflow image 時確認 tag ≥ 2.3.0 |
| Databricks FE 運算限制 | 資料量級以「瓶頸現形」為目標而非固定行數；「找到臨界點」比「跑過一億行」更有工程含量 |
| 進度落後（自學計畫死因第一名：超載） | 砍範圍順序：先砍 Phase 3 深度（保 T3.2 對帳 + 一個瓶頸實驗）→ 再砍 T2.3 遷移張數（30→15）；**Phase 1 完整性不可砍**（Airflow 是台灣 JD 最高頻的編排工具） |
| 環境挫折（死因第二名） | 雜活歸 Claude；卡關 30 分鐘規則 |
| 驗證者單一（只有 Claude 說了算） | 週 4 社群回饋、週 8 mock interview、本文件全部出處可回查（§10） |

## 8. 砍範圍規則

累計落後 >1 週時觸發，依 §7 順序砍，砍前需 kun 確認。禁止用「加班補進度」硬撐——那是計畫失敗的訊號，不是解法。

## 9. 刻意不做（第 3 個月以後的候選）

- **Kafka/streaming**：LINE、Appier、TSMC JD 要求；面試中頻考點
- **K8s**：國泰列必備、TSMC 在 K8s 上跑 DataOps
- **BigQuery**：momo/國泰加分項
- **SQL 正式刷題**：依 §6 診斷結果排程
- **正式求職材料**（履歷、LinkedIn）：repo 與 ADR 完成後製作成本最低

## 10. 出處（查證於 2026-07-17）

**JD 證據（節選）**：momo Ads 資料工程師（104，Airflow 必備）、國泰雲端數據工程師（官方招募頁全文，pipeline/ETL 必備，Airflow/Spark/BigQuery 加分）、玉山資料工程師（資料建模與品質監控）、台積電 IT Data Engineer（Cake 全文，data governance/quality）、LINE Data Engineer ×3（Hadoop/Spark/Kafka 必備）、Appier Data Backend（Greenhouse 全文，Kafka/Spark/Databricks、GCP preferred、PII handling）、KKBOX（AWS 系 + Spark 必備 + data modeling）。Azure Data Factory/Synapse/Fabric：零出現。

**Portfolio 共識（r/dataengineering，經 pullpush 存檔取得原文）**：架構圖 + 設計決策是最強共識；cookie-cutter 教學專案（Spotify pipeline 類）是最強紅旗；合成資料形式被主流教學專案採用（Joseph Machado fake e-comm）但須刻意做髒；「不需要 big data，需要能解釋 scale」。

**面經證據**：台灣 SQL 筆試前置近 100%（台積電/PChome/FUNNOW/鴻海）；Appier 實錄考 data skew 與 OOM；17LIVE 對履歷上的 Airflow 由難到易深問；外商標配 dimensional modeling（fact/dim、SCD）。

完整連結清單見 grilling session 三份研究報告（`jd-evidence.md` / `portfolio-consensus.md` / `interview-evidence.md`，2026-07-17 產出）。**經評估後決定不納入 repo**（避免 JD 原文與面經細節進入公開版本歷史），研究報告以個人附錄形式離線保存，未隨 codebase 發布。

## 11. 待決事項

- **Private → Public 轉換時機**：目前 GitHub repo 為 private（kun 明確決定,開發期先不公開）。建議與 T3.5（英文 README + 架構圖整理）綁定,整理好再轉 public；但**週 4 的社群回饋步驟需要 repo 對外可見**,若屆時仍是 private,需改為「邀請特定人當 collaborator」或屆時提前轉 public——**這個決定留到週 4 前再確認,不現在預先決定**。
- ~~Windows 側舊資料夾清理~~：**已完成（2026-07-19）**。刪除前已 diff 確認 PLAN.md 與 WSL 版本完全一致、`.git` 為原本 NTFS 設定的殘留、`.claude/settings.json` 已同步進 WSL 版，故安全刪除 `C:\Users\d8105\Desktop\Genie-AI\metrics-lakehouse\`。

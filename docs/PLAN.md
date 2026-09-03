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
| 11 | 分工 | 結對協作：kun 站 top-down 決策位；核心產出（DAG、dbt models、star schema、Spark job）原規則為必須過 kun 的手、且能複述原理才算完成——已於 2026-08-27 由 §5.2 修訂取代，改為 Claude 全包實作＋三個為什麼口試；環境雜活與英文翻譯由 Claude 扛 |
| 12 | 刻意不做 | Kafka/streaming、K8s、BigQuery → §9「第 3 個月以後」。皆為真實 JD 需求，但 8 週塞入必然全盤半吊子 |
| 13 | 開發環境 | ~~WSL2（Ubuntu 24.04）原生開發 + Docker Engine 原生安裝（非 Docker Desktop）~~ → **改為 macOS 原生開發**（2026-07-27 確認換機，非兩台並行），repo 實體位置在此機器（`~/projects/metrics-lakehouse`）。容器執行時改用 **Colima**（非 Docker Desktop）：以輕量 Linux VM 提供 Docker daemon，避開 Docker Desktop 的授權與資源開銷。原本 bind-mount 到 `/mnt/c` 效能差、inotify 跨界不觸發兩項理由是 WSL↔Windows 跨界才有的問題，macOS 原生執行不受影響；Linux 環境需求（國泰等 JD 明列）由 Colima 內部的 Linux VM 滿足，不受環境變更影響。**GitHub 私有 repo 從第一個 commit 就同步備份**（`github.com/KLTsai/metrics-lakehouse`），直接對應上次原機器全毀、資料/憑證盡失的教訓；開發期維持 private，轉 public 時機見 §11 |

---

## 3. 架構五層（公開 repo 的骨架）

```
┌─────────────────────────────────────────────────────────┐
│ L5 文件層    英文 README／架構圖／ADR（Before→After 敘事）  │
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
| T0.2 | repo 骨架：WSL 原生 fs 內 git init、GitHub private repo 備份、目錄結構（`generator/ airflow/ dbt/ spark/ docs/`）、README stub | ✅ 已完成（2026-07-19）：`~/projects/metrics-lakehouse` 已 git init 並 push 至 `github.com/KLTsai/metrics-lakehouse`（private）；VS Code Remote-WSL 連線確認可用；conventional commits 從第一個自寫 commit（`34e84ff`）開始；GitHub 自動產生的 Initial commit 與該次 merge commit 不在此規範內。環境已於 2026-07-27 改為 macOS（決策 #13 已更新），repo 實體位置改在此機器；**VS Code Remote-WSL 該項不再適用**（該 extension 為 WSL 專屬，macOS 上不存在） |
| T0.3 | Postgres via docker compose | ✅ 已完成（2026-07-19）：named volume + healthcheck；本機 `psql -h localhost` 連線通過；持久化以「寫入標記列 → `down` → `up -d` → 查回」驗證，並以 `down -v` 反向實驗對照（volume 被刪、資料蒸發、重跑 initdb），確認 `down` 與 `down -v` 的差異 |
| T0.4 | GCP 專案 + Drive API OAuth 憑證 | ✅ 已完成（2026-07-27）：沿用既有 GCP 專案（Console 新版 UI 為 Google Auth Platform，Audience 分頁設定 External + test user）；OAuth client（Desktop app）下載 `credentials.json`；`ingestion/drive_client.py` 四個 TODO 由 kun 填完、我 review 修正（SCOPES 改為單一 `drive.readonly`——原本 `drive.file`+`drive.metadata.readonly` 組合看不到既有檔案且無下載權限；`get_credentials` 清掉授權後多餘的 `raise NotImplementedError`）；`list_files`/`download_file` 皆驗證通過（實際列出並下載 Drive 檔案） |
| T0.5 | 髒資料產生器 v1：參考藍本 schema（訂單、應收帳款），生成多租戶 CSV；髒資料注入可設比例（缺值/重複/格式漂移/遲到） | ✅ 產生器完成（2026-08-24，commit `544c95d`+`4dacb8f`）：`generator/` 套件（schema/dirty/generate/cli/`__main__`）+ `tests/test_generator.py` 19 個測試，套件全綠（含既有 smoke 共 20）；四類注入為**精確相等**斷言（筆數 = `floor(分母×5%)` 逐項吻合，突變測試驗過斷言鑑別力）；同 seed 兩跑 byte-identical；輸出 `generator/out/{tenant}/{table}_{YYYY-MM-DD}.csv`（UTF-8 with BOM）。設計決策見 `docs/adr/0001-generator-contract-layer.md`（契約層界線、兩表取捨、注入互斥）。分工為 agent 全包（2026-08-13 裁示，產生器不在 §5.2 核心產出清單）。✅ Drive 上傳驗證通過（2026-08-25）：檔案在 `我的雲端硬碟/lakehouse/landing/{alpha,beta}/`（landing 資料夾 ID `1DgrZIkA2Pis-sYz_2v3BDj4I0YOk75xh`，當時 `drive_client.py` 寫死的是舊測試資料夾；已由 T1.2 commit `e3c5443` 統一指向 landing，現為 `drive_client.py:13`），以 T0.4 `list_files` 核對 20 檔齊全、抽樣下載與本地 byte-identical。⚠️ 過程中撞到：OAuth app 為 External+Testing 模式，**refresh token 七天過期**（`invalid_grant`，需刪 token.json 重授權）——T1.2 排程化前必解（發佈 app 或改 service account），列入 Phase 1 grilling 議題——已於 T1.2 改用 service account 解決（ADR 0003、commit `ad818e2`），不再依賴會過期的 refresh token |
| T0.6 | WSL 原生環境內 Node.js/npm + Claude Code CLI 可執行（T0.1/T0.2 建置當時漏列，直到搬遷個人設定才發現 `claude: command not found`） | ✅ 已完成（2026-07-19）：`node -v`/`npm -v`/`claude --version` 皆正常（僅互動 shell 下如此——非互動 shell 因 `~/.bashrc` 開頭的 interactive guard 看不到 nvm，屬正常現象非 bug）；個人 CLAUDE.md/playbooks/6 個本地 skills 已從 Windows 側搬遷；5 個個人 plugin marketplace 全數重新啟用。**環境已於 2026-07-27 改為 macOS**（決策 #13 已更新）——上述 WSL/`~/.bashrc` 情境不再適用（本機 shell 為 zsh、無 `~/.bashrc`，nvm 走 `~/.zshrc`）；已於 macOS 重新驗證：`node v24.18.0`／`npm 11.16.0`／`claude CLI 可執行（版本隨自動更新前進，不再逐版記錄）` 皆正常 |

三個為什麼（示例）：為什麼髒資料要可設比例？為什麼產生器要固定 random seed？為什麼多租戶要分檔而不是合一張表？

### Phase 1（週 2–4，~28h）：Airflow 編排層

| 任務 | 內容 | 驗證標準 |
|---|---|---|
| T1.1 | Airflow（docker compose、LocalExecutor、不跑 Celery/Redis） | ✅ 全關（2026-08-26）：環境實作與驗證完成（2026-08-25），kun 已口頭複述四個為什麼。版本：`apache/airflow:3.3.1`（當時 stable，2026-08-12 發布；arm64 manifest 已確認）——任務卡 sign off 時定案採 3.x 而非 2.x，第四個為什麼即此決策。官方 compose 範本裁剪：留 airflow-init/scheduler/**api-server**/**dag-processor**（3.x 的 webserver 改名 api-server，dag-processor 為 3.x 新增必要元件），去 celery worker/redis/flower，**triggerer 一併裁掉**（Phase 1 無 deferrable 任務，需要時加回幾行即可）；logs 用 named volume（`airflow_logs`）而非 bind-mount（避免 host 權限問題）。metadata DB 為獨立 service `postgres-airflow`，**不對 host 曝 port**（host 5432 屬 `postgres-warehouse`）、配獨立 volume `airflow_metadata_data`；`.env` 變數用 `AIRFLOW_` 前綴與倉庫 `POSTGRES_*` 分開。驗證：①`up -d` 一次起全 stack、五服務 healthy，倉庫 `metrics` DB 與 `warehouse` role 完好（T0.3 標記列在本次之前已不存在——非此次弄丟，依 T0.3 驗法重建 `persistence_marker` 一列參與後續驗證）；②admin 帳密經 `/auth/token` 取得 JWT（登入驗證）、UI 頁面 `GET /` 與 `/auth/login` 皆 HTTP 200 回 HTML、`example_bash_operator` 三跑皆 success（kun 於瀏覽器實際登入為人工驗收步驟）；③記憶體基線（Colima VM 8 GiB，容器可見 7.737 GiB）：閒置 5 分鐘後 apiserver 304 / dag-processor 294 / scheduler 666 / postgres-airflow 85 / postgres-warehouse 38 MiB，合計約 1.39 GiB；example DAG 執行中僅 scheduler 升至峰值 780 MiB（LocalExecutor 任務跑在 scheduler 下），合計約 1.50 GiB；VM 層（`colima ssh -- free -m`，補量於 code review 後）used 約 1.4–1.7 GiB（total 7,922 MiB）——距 8 GiB 配額餘裕充足，webserver 反覆重啟症狀未出現，不需調資源；④`down`（不帶 `-v`）→ `up -d` 後 DAG run 歷史（3 筆）與倉庫標記列皆查得回 |
| T1.2 | DAG v1：Drive 下載 → landing 區 | ✅ 全關（2026-08-26）：kun 已口頭複述三個為什麼（Q1/Q2 兩輪修正後過、Q3 一次過）。認證改 service account（ADR 0003),`ingestion/drive_client.py` 新增 `get_credentials()`(讀 `SERVICE_ACCOUNT_KEY_PATH`,金鑰檔 `service-account-key.json` 進 `.gitignore`,repo 根)、純函式 `resolve_tenant_folders`/`find_file_id`(landing 底下先列一次拿租戶資料夾 ID,再逐租戶列檔;找不到檔案 raise 並點名租戶+表+檔案日)。新增 `airflow/dags/drive_ingestion.py`(TaskFlow DAG,`download_day()` 先把 4 個檔案在 Drive 上全部解析存在、確認到才開始下載——避免半完成分區殘留)。compose 新增三個掛載(`ingestion/` 套件、金鑰唯讀、`landing/` 下載目錄),`airflow-init` 一併建目錄+chown。分工本次臨時改為 agent 全包(kun 因時程壓力明確要求,見協作契約下方備註)、TDD 覆蓋純函式(`tests/test_drive_client.py` 6 測試,全專案 26 全綠),code review 兩軸(Standards/Spec)跑過,Spec 軸抓到「逐租戶逐表邊找邊下載,失敗會留下半完成分區」問題,已修正為「先全部解析、確認到才下載」並重新實測。四條驗證標準皆用真實 Airflow 容器+真實 Drive 實測:①手動觸發 logical_date=2026-01-01 → success,4 檔落地 `landing/{alpha,beta}/2026-01-01/`;②抽 `alpha/accounts_receivable` 與 Drive 原檔 `diff` byte-identical;③觸發 2026-02-01(無檔案)→ failed,log 精準點名「租戶 alpha 的 transaction_detail 表在檔案日 2026-02-01 找不到檔案」;④`airflow dags clear` 重跑同一天 → 4 檔 md5 前後一致,未累積 |
| T1.3 | 驗證/drift 檢查 task：schema 對照、欄位漂移偵測 | ✅ 全關（2026-08-27）：kun 已口頭複述三個為什麼（Q2 一次過,Q1 兩輪修正後過,Q3 三輪修正後過)。四項驗證標準皆通過。新增 `ingestion/header_validator.py`：`validate_header(table, header)` 比對「缺欄」「多欄」兩個集合（改名會同時出現在兩邊,是最清楚的告警內容),契約唯一來源 `generator/schema.py`,故意不管欄位順序（CONTEXT.md「欄位名稱漂移」只界定名稱/組成）;`tests/test_header_validator.py` 5 測試。產生器加 `--header-drift table:field_en:new_name_zh`（`generator/cli.py`+`generate.py`),只改指定表指定欄的表頭那一行,`tests/test_generator.py` 新增 4 測試（改名只動目標欄、同 seed byte-identical 不被破壞、未知表/欄報錯、CLI 端到端）。`airflow/dags/drive_ingestion.py` 新增 `validate_headers` task,接在 `download_day` 後面（`download_day() >> validate_headers()`);compose 新增 `generator/` 掛載,讓 DAG 容器內可 import 契約(不另抄一份欄名清單)。分工延續 T1.2「agent 全包」臨時例外（kun 因時程需求延續,非永久改協作契約,見 memory `feedback_urgent_comprehension_first.md`）。過程中驗票口意外抓到一個既有落差:Drive/`landing/` 現有的 T0.5 測試資料是 2026-08-24 commit `4dacb8f`(表頭括號全形化)之前產生的舊檔,`transaction_detail` 表頭（`實際售價(未稅)` 半形 vs 契約 `實際售價（未稅）` 全形)跟目前契約不符——已用現行 schema 重新產生 20 個檔案,kun 手動覆蓋上傳 Drive 排除。四條驗證標準皆用真實 Airflow 容器+真實 Drive 實測:①正常一整天（2026-01-01,重新上傳後)→ `download_day`/`validate_headers` 皆 success;②`--header-drift transaction_detail:customer_id:客戶代碼` 重產 2026-01-06 全部 4 檔（kun 手動上傳)→ 觸發後 `download_day` success、`validate_headers` failed,log 明確列出「缺欄:['客戶編號'];多欄:['客戶代碼']」;③反向邊界由①一併驗過——2026-01-01 資料本身含預設 5% 欄位值漂移(千分位、中文日期等樣式),驗票照樣放行;④`--header-drift` 有 pytest 覆蓋且不破壞同 seed byte-identical 性質。全專案 pytest 35 綠 |
| T1.4 | 入倉 task：idempotent 寫入 Postgres | ✅ 全關（2026-08-27）：kun 已口頭複述三個為什麼（Q1 存文字/Q2 分區替換 vs upsert/Q3 刪插同交易，三題皆兩輪修正後過）。實作 commit `86b8d3f`：`ingestion/raw_loader.py`（純函式 + `load_partition`，`with conn:` 包住 DELETE+INSERT——psycopg2 連線 context manager 即一個交易）、`tests/test_raw_loader.py` 7 測試（全專案 42 綠）；DAG 新增 `load_day` task 接在 `validate_headers` 後；compose 把 `POSTGRES_*` 三變數注入 Airflow 容器。設計依據 `docs/adr/0002-raw-partition-replace.md`（unique test 空轉/upsert 需可信主鍵但 raw 前提是上游不可信/刪補對稱鏡射檔案）。關鍵實作點：欄位映射逐位跟檔案欄序（T1.3 驗票口不管欄序）；metadata 四欄帶型別——「全 text」只約束上游資料欄，loader 自填值可信（Spec review 同判）。四條驗證標準皆真實容器實測：①列數 100/82/105/86 與檔案吻合；②三連跑 md5 指紋不變（排除 loaded_at）；③殺手測試把 SIGKILL 打在 DELETE 後 INSERT 前（exit 137）→ 回滾零殘留，重跑等於乾淨跑；④重複主鍵與「2026年1月1日」怪值可查、26 筆空值保留（證物完整落地）。已知邊界（code review (c) 項，非缺陷）：各 (租戶,表) 分區各自成交易，kill 打在兩分區之間會短暫留「alpha 已入、beta 未入」，重跑即全數替換。本任務起分工依 §5.2 修訂後常態（agent 全包 + 三個為什麼口試，commit `f1d97e6`），不再屬臨時例外 |
| T1.5 | backfill/catchup + retry + 失敗告警 | ✅ 全關（2026-08-28）：kun 已口頭複述三個為什麼（Q1「backfill 補檔案日、遲到列不歸它管」兩輪修正後過,Q2「表頭漂移為何不該 retry」多輪修正後過——最後一輪自己講出「重試結果每次都一樣,沒有不確定性可確認」,Q3「catchup 開關差在哪」一輪接近全過）。實作:`airflow/dags/drive_ingestion.py` 排程改 `schedule="@daily"`、`start_date=2026-01-01`/`end_date=2026-01-05`、`catchup=True`（D3,實測 `CronDataIntervalTimetable` 確認此窗口剛好排出 5 趟 logical_date）;`DEFAULT_ARGS` 加 `email_on_failure=True`/`email_on_retry=False`（收件人走 `AIRFLOW_ALERT_EMAIL` 環境變數,不寫死進程式碼）;retry 依錯誤性質分流——`download_day` retries=3（Drive API 網路抖動值得重試）、`validate_headers` retries=0（表頭漂移是檔案本身的問題,重試結果恆定,不會因等待而改變)、`load_day` retries=2（DB 連線值得重試,且分區替換的交易性質保證重跑安全)。compose 新增 `AIRFLOW__SMTP__*` 與 `AIRFLOW_CONN_SMTP_DEFAULT`（D2:Gmail SMTP + 應用程式密碼,經 `mattpocock-skills:wizard` 產生的一次性腳本寫入 `.env`）。四條驗證標準皆用真實 Airflow 容器+真實 Gmail 實測:①刪 2026-01-02 兩張表分區、用 Airflow UI 的 Backfill 表單（`Reprocess Behavior: All Runs`,對照 UI 上另一條「Clear 一個 run」backfill 路徑)補回→列數(108/110/98/103)與全表總數(1050/1050)跟刪除前快照完全一致、DagRun 無重複;②backfill 2026-01-01 後,3 筆已知遲到列（歸屬日 1/1、實際落在 2026-01-03 分區,如 `ORD-alpha-20260101-00338`)確認仍留在 01-03、且各只有 1 份,證明 backfill 只動 `file_date` 對上的那個分區;③金鑰內容改壞(JSON 解析錯誤)→ `download_day` 依設定重試 3 次後最終失敗、`validate_headers`/`load_day` 顯示 `upstream_failed`、告警信送達 Gmail 收件匣;改回金鑰後重跑→全綠復原;④排程首次打開後,5 趟 `scheduled__2026-01-0{1..5}` 全 success,`next_dagrun` 之後為空(不再排新的)。過程中意外抓到並修掉兩個環境層 bug（皆與 DAG/Python 邏輯無關）:(a) `dag_run` 表對 `(dag_id, logical_date)` 有唯一約束、不分 run_type——排程要接手一個已有同 logical_date 手動 run 的日期時,scheduler 只會靜默重試「run already exists; skipping」卡住不前進,不會報錯也不會跳過,需手動刪掉舊 run 才能解卡;(b) Docker 對單一檔案的 bind mount 是綁 inode、不是綁路徑——已在跑的容器不會因為 host 端改檔名或用 TextEdit 存檔(等同整檔替換)而看到新內容,必須 `--force-recreate` 才會重新解析掛載,這個坑在測「金鑰失效」情境時連撞兩次(先是重新命名不生效,才知道要 force-recreate;跟 airflow-init 在檔案暫時消失時直接拒絕啟動的行為放在一起看,說明這個機制既非「即時生效」也非「優雅降級」);(c) `SmtpNotifier.use_ssl` 預設 `True`（除非連線 `extra` 明講 `disable_ssl`)——對 Gmail 587 埠（STARTTLS,非隱式 SSL)送信會撞 `[SSL: WRONG_VERSION_NUMBER]`,修法是在 `AIRFLOW_CONN_SMTP_DEFAULT` 的 URI 後加 `?disable_ssl=true`（實測確認查詢字串會被正確解析成 JSON boolean,不會踩 `bool("false")==True` 的坑)。已知待辦（不阻塞本卡收工,kun 裁示延後):`SmtpNotifier` 預設信件主旨/內容是把 TaskInstance 物件整包 repr 塞進去,不易讀,之後可透過連線 `extra` 的 `subject_template`/`html_content_template` 指向自訂模板檔案改善 |
| T1.6 | ADR#1：Before（土法排程架構圖與痛點）→ After（Airflow）| ✅ 全關（2026-08-30）：kun 已不看稿講出 3 個遷移理由與 1 個 trade-off（理由 1 可觀測性與 trade-off 一次過;理由 2 補跑、理由 3 依賴宣告的 After 側機制一次過,Before 側三輪未講出——正解攤開、kun 重讀 Before 段後補考,用自己的話複述「到點判斷只認今天,漏掉那天概念上不存在」與「時間錯開表達先後、上游失敗下游照跑」兩個機制通過)。產出 `docs/adr/0004-airflow-over-homegrown-scheduling.md`:Before 素材來自對藍本產品 codebase 的實地盤點（Explore agent,證據含 due 判斷只認今天、執行程序不在錯誤監控範圍、run 紀錄僅留 50 筆、雙套定時器定義其一為死碼等),全文匿名化為「該產品」,**文件與 commit 均不得出現產品名**。結構:Before（排程拆在三層的架構圖+三個維運痛點）→ After（本 repo `drive_ingestion` DAG T1.2–T1.5 為第一手實據,逐點對照)→ 該產品若遷移怎麼接（含證據邊界聲明:per-客戶排程時間僅推演、無第一手實作)→ trade-off（運維複雜度+非 DE 團隊採用門檻)。兩張 mermaid 圖的箭頭都帶圈號讀圖編號（Before 圖 ①–⑦、After 圖 ①–⑥；kun 要求,改圖時保留)。初稿曾被 kun 判「實作者也看不懂」,經 sepia 流程重寫為白話版定稿;grilling 時 kun 原選的理由組合（可觀測性/多客戶排程管理/單一事實來源)成文時後兩者分別轉入銜接段與 After 收尾,kun 裁定不改回（2026-08-30) |

### Phase 2（週 4–6，~24h）：dbt + 維度建模

| 任務 | 內容 | 驗證標準 |
|---|---|---|
| T2.1 | dbt 接 Postgres；staging models | ✅ 全關（2026-08-31）：實作 commit `ade38dd`，口試三題通過。任務卡三議題裁示：A 漂移值走「自寫巨集逐樣式 regex 先對原值守門、認得的才剝符號轉型、認不得的轉 NULL」，不走 fail-fast（髒資料是產生器刻意注入、比例固定的——四類各 5%、分母各異，對每個租戶的每張表整體注入後隨機分佈到各檔案日、單日比例浮動——報錯會讓 run 永遠紅）、不用 DB 端 UDF（多一層部署相依，且 Postgres 對日期寬鬆解析「不報錯≠語意對」）；裁示依據 subagent 研究——**Postgres 上 dbt 內建 `safe_cast()` 沒有 adapter override，等於普通 cast，壞值照炸**，守門只能自寫。B 密碼不進對話：kun 自己 `cd dbt && source ../.env && uv run dbt …`，agent 以 `docker exec … psql`（容器內免密碼）做證據面查證。C 兩租戶同表不拆，`tenant_id` 維持列屬性。實作：dbt-core 1.12.3 + dbt-postgres 1.11.0（uv 管理）；`dbt/dbt_project.yml`（staging 統一 view）、`profiles.yml`（跟 repo 走、憑證 `env_var`）、`macros/parse_numeric.sql` + `parse_date.sql`（樣式清單對齊 `generator/dirty.py`；percent 語意不明、NaN 非數，刻意不救）、`models/staging/sources.yml` + `stg_transaction_detail.sql` + `stg_accounts_receivable.sql`（欄序照 `generator/schema.py`，不去重不補值，metadata 四欄原樣帶過）。文字欄套 `nullif(trim(x), '')` 讓 CSV 空字串以 NULL 表示缺值——Spec review 點出這偏離任務卡「原樣往下傳」字面，kun 裁示維持（缺值對 T2.4 的 not_null test 才可見，且與 typed 欄的缺值表示法一致）。四條驗證皆真實 `postgres-warehouse` 實測：①`dbt debug` 通過（kun 側）；②`dbt run` 建出 2 個 view；③兩表 raw = staging 皆 1050/1050；④資料欄中 6+7 個 typed 欄型別正確（numeric/date），metadata 的 `file_date`/`loaded_at` 保留原型別，各租戶 SUM 與日期比較零報錯；六個 typed 欄「raw 不可救值（空/NaN/百分比）」與「staging NULL」逐欄相等（71/16/11/14/48/0）。pytest 42 綠。兩軸 code review 通過（Standards：`sources.yml` 用語「空值」改「缺值」對齊 ADR 0001；兩 model 尾端 metadata 四欄重複判定不抽巨集。Spec：欄位/型別/樣式逐一對照契約無誤、無偷去重、無偷做 test）。**口試**：原列五題，kun 裁示減為三題（view vs table 移到 T2.3 有真實查詢成本時再考；「不去重不補值」併入 Q1）。Q1（分層責任）三輪未過——混淆「view 有快取」、抓錯答成 `dbt run`、test 對 raw——攤開正解後補考過，兩處修正：後續對 NULL 是 test 數出來、不是補值；test 對 staging 不對 raw（raw 是 source 非 model）。kun 要求把三題正解寫成複習頁（artifact，經 sepia 語句修訂，含 ①–④ 編號圖與「上次錯答」對照表），閱後補考：Q2 首答貼複習頁原文被退回，改用自己的話後過（動態組字串讓 grep 找不到表名、搜尋給清單而依賴圖給保證、手寫地址的 model 在圖裡是孤兒節點所以才禁手寫、`dbt ls` 加號前後 = 上游/下游、搬 schema 只改 `sources.yml` 一行）；Q3 過（fail-fast 適合錯是意外的資料、我們是設計好的比率——整體固定、單日浮動；判準「只拿掉格式符號、不做語意假設就能得出唯一數字」；severity 在 T2.4 回來——主鍵錯會透過 join 傳染要 error 擋，金額錯鎖在一格 warn 記下即可）。過程觀察：kun 對 view/table、`dbt run`/`dbt test`、`source()`/`ref()` 的機制原本不熟，口試前先補了機制講解；kun 反饋「驗證不該要記 docker 指令」，實務答案是 T2.4 把檢查寫成 `dbt test`，kun 現以 pgAdmin 4 連 localhost:5432 看結果 |
| T2.2 | star schema 設計（fact/dim 切分、ERD）；Kimball 精選章節閱讀 | ✅ 全關（2026-09-03）：實作 commit `cfacea0`，口試六題通過。五張 marts 表的實作併入本任務（任務卡議題 D，PLAN 內容欄不動）。任務卡四議題裁示（2026-09-02）：A 缺日期的 fact 列接 dim_date 用「未知日」`1900-01-01`；B 未知客戶「其他」每租戶一列（鍵含 tenant_id，alpha/beta 各自一列，不是全表一列）；C 表名沿用暫名（`fact_transaction`/`fact_ar`/`dim_date`/`dim_customer`/`dim_ar_customer`）；D 本列內容欄不動、完成紀錄寫明五表併入。實作：`dbt/dbt_project.yml`（`marts: +materialized: table +schema: marts`）、`macros/generate_schema_name.sql`（dbt 官方標準覆寫，讓自訂 schema 名照用不拼接）、`models/marts/dim_date.sql`（`generate_series` 產 2026 全年日曆 + 未知日，366 列）、`dim_customer.sql`/`dim_ar_customer.sql`（distinct 鍵 + 每租戶一列「其他」；`dim_ar_customer` 客戶名稱取「同鍵、檔案日最大、名稱非缺值」Type 1）、`fact_transaction.sql`/`fact_ar.sql`（`row_number() over (partition by 主鍵 order by file_date desc) = 1` 去重、缺值換「其他」/未知日、`fact_ar` 不留 `customer_name`——是 dim_ar_customer 的屬性）。code review 後把 `'其他'`/`1900-01-01` 兩個散在多檔案的 sentinel 值收成 `unknown_customer_id()`/`unknown_date()` 兩個 macro。ADR 0005「表的形狀」節末補六條線 mermaid ERD（六條線指向同一張 dim_date，role-playing dimension；兩條線指向兩張客戶 dim）。八條驗證標準皆真實 `postgres-warehouse` 實測：①`dbt run` 全綠，5 張 table 落在 `marts` schema；②去重：兩表 staging 1050 列 → fact 各 1000 列（各去 50 列重複），主鍵唯一；③按客戶加總：inner join dim 前後列數/金額合計一致，「其他」列金額兩租戶皆 >0；④六條日期線 inner join dim_date 列數 = fact 全部列數，未知日列數與 staging NULL 數逐欄相符；⑤`dim_date` 366 列、2026-01-01~12-31、`day_of_week` 與 `extract(dow)` 全一致；⑥`dim_ar_customer` 無重複鍵，beta C00001 名稱抓到「大同精密股份有限公司」；⑦pytest 42 綠；⑧`/code-review` 兩軸過（Standards 3 個判斷題：macro 排版樣板差異可不改、兩個 sentinel 值已收成 macro、`dim_date` 年份範圍硬編未來若跨年會靜默漏接可留意；Spec 0 違規，僅 1 個邊界提醒——若某客戶所有歷史列名稱皆缺值，`dim_ar_customer` 會拿到 NULL 非「其他」，現況資料不會觸發）。**口試**：六題，去重判準（Q1 兩次答成「留較舊/金額大」，攤開正解「唯一判準是檔案日新舊」後複述過）、`dim_customer` 存在意義（首答只講鍵含租戶，未答到「其他」防止 inner join 篩掉，換問法後答對）、遲到列（一次過）、SCD Type 1 升級路徑（首答「改 dim_ar_customer 寫法」錯，提示後答出 dbt snapshot）、未知日陷阱（1900-01-01 月份數字剛好是 1，若無腦用 `extract(month)=1` 會誤抓；首答誤以為系統自動排除，正解攤開後複述出「closed_at 不在缺值池、值永不為 NULL」）、三張 dim 的 grain + SCD 策略（grain 一次答對，SCD 策略追問後補答 Type 1）。過程觀察：`/private/tmp/.../t2.2-task-card.md` 在 session 中途被清空（kun 手動處理服務時機器重開機所致，非意外），因 session 開頭已讀過任務卡全文而逐字寫回，未影響後續 Spec review；Spec review 第一輪因任務卡遺失只能對 ADR 比對、誤判 `dim_ar_customer` 名稱取法「與 ADR 字面不完全一致」，任務卡救回後重跑排除此誤判 |
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
2. **核心產出規則**（2026-08-27 修訂）：DAG、dbt models、star schema、Spark job、入倉等核心邏輯，改由 Claude 全包實作，不再要求 kun 親手改過。完成關卡是**三個為什麼口試**：收工時 Claude 須交付①相關應用目的、②為什麼這樣寫（對齊軟體工程準則）、③矛盾/衝突主動反應、④手動驗證或真實情境操作流程；kun 要能用自己的話複述「三個為什麼」才算全關——概念對但講不出為什麼只算部分過，允許多輪修正，不能直接告知答案結案。（此前 T0.4 走的「骨架+TODO(kun)」、T1.2/T1.3 走的「agent 全包」臨時例外，皆為條件式例外時期的過渡分工；本次起正式取代原「必須 kun 改過」規則。）
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

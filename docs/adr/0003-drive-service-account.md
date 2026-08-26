# Drive 讀取改用 service account,不沿用人類帳號 OAuth

T0.4 的 Drive 認證是「借 kun 的身分」:OAuth 同意畫面 + `token.json`。但 app 處於 External + Testing,Google 規定 refresh token **七天作廢**(症狀:`get_credentials()` 拋 `invalid_grant` 直接 crash),作廢後必須真人開瀏覽器重新授權——排程系統無人值守,這是隱形的人肉依賴。T1.2 排程化前改用 **service account**:GCP 專案裡建機器身分、Drive 的 `landing` 資料夾分享給它的 email、程式改用金鑰檔(JSON 私鑰)認證。無瀏覽器、憑證不過期、零成本(GCP 身分不計費,Drive API 走免費配額),也是業界排程 pipeline 的標準做法。

## 否決的選項

- **發佈 app 到 production**:程式碼零改動、refresh token 不再過期,但授權本質仍是人類帳號+瀏覽器流程(token 一旦失效就要有人救);且 `drive.readonly` 屬 restricted scope,未驗證 app 掛 production 會有警告畫面、行為有變數。留作 SA 卡關時的退路。
- **換 `drive.file` scope 迴避 restricted 限制**:看不到既有檔案,T0.4 已驗證過此路不通。

## Consequences

- 金鑰檔是一把**不會過期的鑰匙**:不進 git、外流即撤銷重發;正式環境會再進階到免金鑰方案(Workload Identity),超出本專案範圍,但認知上要知道有這一層。
- `get_credentials()` 改讀金鑰檔(`google.oauth2.service_account`),舊的 `credentials.json`/`token.json` 流程退役。
- 金鑰要能被 Airflow 容器讀到(掛載方式屬 T1.2 任務卡細節)。

出處:Phase 1 grilling(2026-08-26)。

# Sandcastle 夜班編排

啟動:`colima start`(本機 Docker 走 colima)→ `npm run sandcastle`。
commit 全部落在 `night/<日期>` branch,隔天早上人工 review 過了才合併,不自動 merge。

## 地雷(改 prompt.md / main.mts / Dockerfile 前必讀)

1. sandcastle 用 stdin 餵 `claude -p`,**slash 指令不會展開**(upstream issue #928)。prompt 要寫貼近 skill description 的自然語言,靠 model-invoked 觸發(#853 證實可行)。
2. 標 `disable-model-invocation: true` 的 skill(如 mattpocock 的 `implement`)在沙盒裡永遠觸發不了——需要的話把內容直接內聯進 prompt.md。
3. skill 進沙盒的唯一可靠路徑:vendor 進 repo 的 `.claude/skills/` 並 commit。沙盒 bind-mount 的是 git worktree,**只有 committed 的檔案進得去**;host 的 `~/.claude` 不會進沙盒(issue #866),gitignored 的憑證(credentials.json、`.env`)也進不去——需要憑證的工作(如 Drive 上傳)拆到白天做。

這些結論來自官方 issues 與實測;直覺做法(prompt 裡打 `/skill`、把 plugin 裝進 image)會**靜默失敗**。其他 repo 要接 sandcastle,可照本目錄為範本。

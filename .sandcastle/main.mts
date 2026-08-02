import { run, claudeCode } from "@ai-hero/sandcastle";
import { docker } from "@ai-hero/sandcastle/sandboxes/docker";

// 夜班編排:一次 run 消化多張 ready 的 GitHub issues,一張一個 iteration。
// 啟動:npm run sandcastle
// 產出:commit 全部落在 night/<日期> branch,隔天早上人工 /code-review 過了才合併。

const branch = `night/${new Date().toISOString().slice(0, 10)}`;

await run({
  name: "night-shift",
  sandbox: docker({ imageName: "metrics-lakehouse-sandcastle" }),

  // sonnet 做實作;難題可改 "claude-opus-4-8"。
  agent: claudeCode("sonnet"),

  // prompt 內的 shell 區塊每個 iteration 都會在沙盒內重新求值(issue 清單保持新鮮)。
  promptFile: "./.sandcastle/prompt.md",

  // 一個 iteration 做一張 issue;要消化更多張就調高。
  maxIterations: 3,

  // commit 留在具名 branch 等人工 review,不自動 merge 回 HEAD。
  branchStrategy: { type: "branch", branch },

  hooks: {
    sandbox: {
      // Python 專案:把依賴(含 dev group 的 pytest)裝進 worktree 的 .venv。
      onSandboxReady: [{ command: "uv sync" }],
    },
  },
});

<!--
keywords / 关键词:
发票报销 报销 发票报销skill 费用报销 报销整理 费用明细表 整理发票 贴票报账 差旅报销
增值税发票 电子发票 OFD 铁路电子客票 财务报销 报销助手 报销模板 报销技能
invoice reimbursement expense-report expense reimbursement skill agent-skill claude-skill
fapiao travel-expense OCR finance automation
-->

# Expense‑Reimbursement Skill · 发票报销整理技能

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
[![Skill](https://img.shields.io/badge/type-agent--skill-6E56CF.svg)](#)
[![python3](https://img.shields.io/badge/python-3.x-3776AB.svg)](#requirements--环境要求)
[![lang](https://img.shields.io/badge/docs-EN%20%7C%20中文-success.svg)](#)

> **EN** — An [Agent Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) that turns a messy folder of receipts (jpg / png / pdf / **OFD** / xlsx) **+** a reimbursement Excel template into a **finance‑ready expense detail table (费用明细表)** — backed up, classified into buckets, renamed, reconciled, and filled into a *copy* of the template (the original is never modified).
>
> **中文** — 一个把杂乱的**发票/票据**（jpg / png / pdf / **OFD** / xlsx）**+** 一份**报销 Excel 模板**，整理成可直接交财务的**费用明细表**的 Agent 技能：备份原件、分桶归档、规范命名、去重勾稽、回填模板副本（**原模板绝不修改**）。适用于 **发票报销 / 费用报销 / 差旅报销 / 贴票报账**。

**Languages / 语言**：[English](#english) ·  [中文](#中文)

---

<a name="english"></a>
## English

### ✨ Why this skill
Real reimbursement folders are a minefield: VAT invoices **plus** their payment screenshots (double‑count risk), rebooked/refunded train tickets, foreign‑currency taxi receipts, hotels with no invoice, suspected personal expenses. This skill encodes the hard‑won rules to get the **numbers right**, and **asks instead of inventing** when something is unclear. It is **model‑agnostic** and **self‑contained**: pure‑`python3` helpers, no LibreOffice or cloud paths required.

### 🤖 For AI agents — quick apply
**Trigger when** the user wants to organize / file a reimbursement — keywords: `报销 / 发票报销 / 费用报销 / 费用明细表 / 整理发票 / 贴票报账 / 差旅报销` — and they provide a materials folder + an xlsx template.

**30‑second mental model**
1. Read [`expense-reimbursement/SKILL.md`](./expense-reimbursement/SKILL.md) first — it is the entry point and orchestrates everything.
2. Three red lines: ① originals & original template are never modified; ② never invent info — unclear items go to a 存疑清单 (open‑questions list) for the user; ③ **one expense = one ledger row, never double‑count** (an invoice and its payment screenshot are the *same* event).
3. Workflow: `setup_workspace.py` → read every material → bucket & classify → build 物料台账 (item ledger) → de‑dup into `ledger.json` → `fill_template.py` → recalc → 审阅报告 (review report).
4. Reconcile three ways before delivering: `Σ(ledger) == fill_template "computed" == recalc total`, with `total_errors == 0`.

**Minimal command sequence**
```bash
cd expense-reimbursement
# 0) workspace + backup (+ writable copy of template; the template itself & *.skill are skipped from backup)
python3 scripts/setup_workspace.py --source <materials_folder> --out <workspace> --template <template.xlsx>
# read OFD national e-invoices as text (fall back to vision/raster if empty)
python3 scripts/extract_ofd.py <file.ofd> --json
# 6) after building 过程文件/ledger.json -> fill the template COPY (never the original)
python3 scripts/fill_template.py --xlsx <workspace>/<name>_已填写.xlsx --ledger <workspace>/过程文件/ledger.json
# recalc: prefer the xlsx skill's recalc.py (LibreOffice); otherwise the bundled fallback:
python3 scripts/recalc_fallback.py <workspace>/<name>_已填写.xlsx --write
```
`fill_template.py` prints a `computed` block (per‑column subtotals + grand total) so you know the right numbers **without** LibreOffice. Read the three files in [`references/`](./expense-reimbursement/references/) before classifying.

### 🗂 What it produces — six buckets
| Folder | Meaning | Contents |
|---|---|---|
| `有票/` | has‑invoice | formal invoices that stand alone as primary proof (VAT e‑invoices, rail e‑tickets, flight/hotel invoices…) |
| `无票/` | no‑invoice | real spend with **no** formal invoice but a usable primary record (overseas receipts, non‑invoice slips, screenshot‑only expenses) |
| `辅助材料/` | supporting | side evidence only (payment / order / itinerary / refund screenshots) |
| `额外说明/` | notes for finance | plain‑text explainers: merges, partial refunds, rebookings, FX conversion, company‑paid/personal splits |
| `过程文件/` | process | `身份信息.json`, `manifest.json`, `extracted/`, `物料台账.csv`, `ledger.json` |
| `备份/` | backup | 1:1 backup of originals + `_模板原件/` |
| `待核实/` | to‑verify | uncertain items park here — **don't** pre‑file into `有票`/`无票` until the user confirms |
| `替票/` | substitute‑invoice pool | the client's *optional* spare invoices from other spending, used to loosely offset `无票` totals for finance. They are **not** 1:1 matches, so they **stay here** and are **not** counted in the ledger — `无票` items are **never** promoted to `有票` |
| `补充材料/` | supplements intake | drop later‑supplied materials here; backed up & re‑classified, then **emptied** |
| `无关/` | unrelated | items confirmed unrelated / not‑this‑period; kept aside, excluded from this run |

…plus `<name>_已填写.xlsx` (the filled table, rows **in chronological order**) and `审阅报告.md` (summary + reconciliation + open questions).

### 🧠 Correctness invariants (what makes the numbers right)
- **One ledger row per event** — never sum an invoice together with its own payment screenshot.
- **VAT invoice amount = tax‑inclusive total (价税合计)**, not the pre‑tax 金额.
- **Train refund** = the small 退票费 only; **rebooking (改签)** = count the final valid ticket once.
- **Company‑paid / AA** = reimburse only the individual’s out‑of‑pocket portion.
- **Screenshot‑only real expense (no invoice) → `无票`** (it *is* the primary proof), not `辅助材料`.
- **Suspected personal / unrelated** (utilities, unrelated‑country visa, personal subscriptions) → open‑questions list, excluded by default.
- **Foreign currency** → convert to RMB with a stated rate/source; if no rate, **ask** — don’t guess.

### 📦 Install
**A. Drop‑in folder (Claude Code / most agent runtimes):**
```bash
git clone https://github.com/Auromix/expense-reimbursement-skill.git
cp -R expense-reimbursement-skill/expense-reimbursement ~/.claude/skills/
```
**B. Build a `.skill` package (Claude desktop “add skill” UI):** `./pack.sh` → `dist/expense-reimbursement.skill`
**C. Reference in place:** point your skill loader at the `expense-reimbursement/` directory.

---

<a name="中文"></a>
## 中文

### ✨ 这个技能解决什么
真实的**报销**材料是雷区：增值税**发票**和它的支付截图并存（重复计费风险）、火车票**改签/退票**、外币打车收据、没有发票的酒店、疑似私人消费。本技能把这些"踩过的坑"固化成规则，确保**金额算对**，并且**看不清/对不上就问用户、绝不臆造**。它**与模型无关**、**自带依赖**：纯 `python3` 脚本，无需 LibreOffice 或云端路径。

### 🤖 给 AI Agent —— 快速上手
**触发场景**：用户想整理 / 提交报销，触发词：`报销 / 发票报销 / 费用报销 / 费用明细表 / 整理发票 / 贴票报账 / 差旅报销`，并提供一个材料文件夹 + 一份 xlsx 报销模板。

**30 秒理解**
1. 先读 [`expense-reimbursement/SKILL.md`](./expense-reimbursement/SKILL.md) —— 这是入口，统领整个流程。
2. 三条红线：① 原始材料与原模板**绝不修改**；② **绝不臆造**，看不清/对不上的进**存疑清单**问用户；③ **一笔消费只入表一行，绝不重复计费**（发票和它的支付截图是**同一笔**）。
3. 工作流：`setup_workspace.py` → 逐份读材料 → 分桶归类 → 建**物料台账** → 去重成 `ledger.json` → `fill_template.py` → 重算 → **审阅报告**。
4. 交付前三方勾稽：`Σ(台账) == fill_template 的 computed == 重算总额`，且公式错误数为 `0`。

**最小命令序列**
```bash
cd expense-reimbursement
# 0) 搭工作区 + 备份（并生成模板可写副本；模板本身与 *.skill 不计入材料备份）
python3 scripts/setup_workspace.py --source <材料文件夹> --out <工作区> --template <模板.xlsx>
# 读 OFD 国标电子发票文本（取不到文本则转图片用视觉识别）
python3 scripts/extract_ofd.py <file.ofd> --json
# 6) 生成 过程文件/ledger.json 后，回填模板「副本」（绝不动原件）
python3 scripts/fill_template.py --xlsx <工作区>/<名称>_已填写.xlsx --ledger <工作区>/过程文件/ledger.json
# 重算：优先 xlsx skill 的 recalc.py（需 LibreOffice）；没有就用自带兜底：
python3 scripts/recalc_fallback.py <工作区>/<名称>_已填写.xlsx --write
```
`fill_template.py` 会输出 `computed`（各列小计 + 总额），**无需 LibreOffice** 也能知道正确数值。归类前请先读 [`references/`](./expense-reimbursement/references/) 三个参考文件。

### 🗂 产出 —— 六个分桶
| 目录 | 含义 | 内容 |
|---|---|---|
| `有票/` | 有正式票据 | 能独立作主证据的正式发票（增值税电子发票、铁路电子客票、机票/酒店发票…） |
| `无票/` | 无正式发票 | 消费真实但拿不到发票、只有一份能当主证据的记录（境外收据、非发票小票、仅有截图的消费） |
| `辅助材料/` | 侧面佐证 | 本身不能独立证明消费（支付/下单/行程/退款截图） |
| `额外说明/` | 给财务看的说明 | 纯文本：合并、部分退费、改签、外币换算、企业代付/个人垫付拆分 |
| `过程文件/` | 过程信息 | `身份信息.json`、`manifest.json`、`extracted/`、`物料台账.csv`、`ledger.json` |
| `备份/` | 原件备份 | 原始材料 1:1 备份 + `_模板原件/` |
| `待核实/` | 待核实 | 拿不准的先放这里，**别急着**进 `有票`/`无票`，用户确认后再移走 |
| `替票/` | 替票池 | 客户*可选*提供的其他消费发票，在金额上大致冲抵 `无票` 合计给财务；与无票**非一一对应**，故**留在本目录**、不计入台账，`无票` **不改判为** `有票` |
| `补充材料/` | 补充材料入口 | 客户后续补的材料丢这里；备份并归桶后**自动清空** |
| `无关/` | 无关 | 经确认与本次无关/本期不报/跨期的材料，单独存放、不计入本期 |

…外加 `<名称>_已填写.xlsx`（填好的明细表，**按时间顺序排列**）和 `审阅报告.md`（汇总 + 勾稽 + 存疑清单）。

### 🧠 正确性铁律（让金额算对的关键）
- **一事件一行** —— 绝不把发票和它的支付截图算成两笔。
- **增值税发票按价税合计（含税）入表**，不是不含税的「金额」。
- **退票**只计退票费；**改签**以改签后的有效票为准、只算一次。
- **企业代付 / AA**：只报个人实际承担部分。
- **只有截图、无发票的真实消费 → `无票`**（它就是主证据），不是 `辅助材料`。
- **疑似私人 / 与本次无关**（水电费、无关国家签证、个人订阅）→ 存疑清单，默认不计入。
- **外币** → 换算成 RMB 并注明汇率/来源；没有汇率就**问用户**，不要拍脑袋。

### 📦 安装
**A. 直接拷贝技能目录（Claude Code / 多数 Agent 运行时）：**
```bash
git clone https://github.com/Auromix/expense-reimbursement-skill.git
cp -R expense-reimbursement-skill/expense-reimbursement ~/.claude/skills/
```
**B. 打包成 `.skill`（Claude 桌面端"添加技能"）：** `./pack.sh` → `dist/expense-reimbursement.skill`
**C. 原地引用：** 让技能加载器指向本仓 `expense-reimbursement/` 目录。

---

## 🧩 Repository layout / 仓库结构
```
expense-reimbursement-skill/
├── expense-reimbursement/        # the skill / 技能本体 (drop-in installable)
│   ├── SKILL.md                  # entry point + workflow / 入口与工作流（先读这个）
│   ├── references/
│   │   ├── 模板与字段映射.md       # template structure, column map, 价税合计 rule
│   │   ├── 归类与命名规范.md       # bucket rules, naming, no-double-count, 改签/退票, 疑似私人
│   │   └── 额外说明写法.md         # finance-facing note templates
│   └── scripts/
│       ├── setup_workspace.py    # build workspace + back up originals
│       ├── extract_ofd.py        # extract text from OFD national e-invoices
│       ├── fill_template.py      # fill the template copy + self-check computed totals
│       └── recalc_fallback.py    # pure-python recalc (no LibreOffice needed)
├── pack.sh                       # build dist/expense-reimbursement.skill
├── LICENSE                       # Apache-2.0
└── README.md
```

## ⚙️ Requirements / 环境要求
- `python3` with `openpyxl` (xlsx fill/recalc) and `pdfplumber` (PDF text). OFD parsing uses only the stdlib.
- LibreOffice is **optional** — `recalc_fallback.py` covers recalculation when it’s absent.
```bash
python3 -m pip install openpyxl pdfplumber
```

## 🤝 Contributing / 贡献
Issues & PRs welcome. The skill is tuned against messy real‑world Chinese reimbursement data (rail rebookings/refunds, OFD invoices, KRW receipts, invoice‑less hotels). When adding a rule, update the relevant file in `references/` **and** the self‑check list in `SKILL.md`, and keep the scripts dependency‑light and `python3`‑only.
欢迎提 Issue / PR。新增规则时，请同时更新 `references/` 对应文件与 `SKILL.md` 的收尾自检清单，并保持脚本轻依赖、仅用 `python3`。

## 📄 License
[Apache‑2.0](./LICENSE) © 2026 Auromix

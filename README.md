<!--
keywords / 关键词:
发票报销 报销 发票报销skill 费用报销 报销整理 费用明细表 整理发票 贴票报账 差旅报销
增值税发票 电子发票 价税合计 OFD 铁路电子客票 改签 退票 替票 财务报销 报销助手 报销模板 报销技能
invoice reimbursement expense-report expense reimbursement skill agent-skill claude-skill
fapiao travel-expense OCR finance automation
-->

# Expense‑Reimbursement Skill · 发票报销整理技能

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
[![Skill](https://img.shields.io/badge/type-agent--skill-6E56CF.svg)](#)
[![python3](https://img.shields.io/badge/python-3.x-3776AB.svg)](#requirements--环境要求)
[![lang](https://img.shields.io/badge/docs-EN%20%7C%20中文-success.svg)](#)

> **EN** — An [Agent Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) that turns a folder of messy receipts (jpg / png / pdf / **OFD** / xlsx / …) **+** a reimbursement Excel template into a **finance‑ready 费用明细表**: it backs up the originals, reads & understands every file, sorts them into ten purpose‑built folders, renames them, de‑duplicates into one row per expense, fills a **copy** of the template in chronological order, and reconciles the totals — **the originals are never modified**.
>
> **中文** — 一个把杂乱的**发票/票据**（jpg / png / pdf / **OFD** / xlsx 等）**+** 一份**报销 Excel 模板**整理成可直接交财务的**费用明细表**的 Agent 技能：备份原件、逐份读懂、分进十个用途明确的文件夹、规范命名、按"一笔消费一行"去重、按时间顺序回填**模板副本**、并做三方勾稽——**原件绝不修改**。适用 **发票报销 / 费用报销 / 差旅报销 / 贴票报账**。

**Languages / 语言**：[English](#english) ·  [中文](#中文)

---

<a name="english"></a>
## English

### ✨ Why this skill
Real reimbursement folders are a minefield: a VAT invoice **plus** its payment screenshot (double‑count risk), rebooked/refunded train tickets, foreign‑currency taxi receipts, company‑paid‑vs‑personal splits, hotels with no invoice, suspected personal expenses. This skill encodes the hard‑won rules to get the **numbers right**, and **asks instead of inventing** when something is unclear. It is **model‑agnostic** and **self‑contained**: pure‑`python3` helper scripts, no LibreOffice or cloud paths required.

### 🚦 Three red lines (never cross)
1. **Originals and the original template are never modified** — every change happens on backups / a template copy.
2. **Never invent information** — anything unclear / mismatched / missing goes on an open‑questions list (`存疑清单`) for the user. Ask, don't guess.
3. **One expense = one ledger row, never double‑count** — an invoice and its payment screenshot are the *same* event; a ticket before/after rebooking is the *same* trip; the company‑paid portion is not claimed again.

### 🤖 For AI agents — quick apply
**Trigger when** the user wants to organize / file a reimbursement — keywords: `报销 / 发票报销 / 费用报销 / 费用明细表 / 整理发票 / 贴票报账 / 差旅报销` — and they provide a materials folder + an xlsx template.

**Read [`expense-reimbursement/SKILL.md`](./expense-reimbursement/SKILL.md) first** — it is the entry point and orchestrates the whole flow. Then the three references in [`references/`](./expense-reimbursement/references/): the template/column map, the bucket+naming rules, and the finance‑note templates.

**Core workflow (steps 0–7):**
| # | Step | What happens |
|---|---|---|
| 0 | Setup + backup | `setup_workspace.py` builds the 10 folders, backs up originals, makes the writable template copy |
| 1 | Read each material | images by vision; PDF by text (raster fallback); OFD via `extract_ofd.py`; write `extracted/<name>.json` |
| 2 | Bucket + classify + link events | pick 有票/无票/辅助材料; map to a template column; give same‑expense materials one **event id**; park unsure → `待核实/` |
| 3 | Build the item ledger | `过程文件/物料台账.csv` — one row per **material** (the single source of truth) |
| 4 | Copy + rename + file | `日期_费用类型_关键信息_金额`; same event keeps the same name across folders |
| 5 | Write finance notes | `额外说明/` txt for merges / refunds / FX / splits |
| 6 | De‑dup → ledger → fill → recalc | collapse to **one row per event**, sort **chronologically**, `fill_template.py` then recalc; three‑way total must match. **No template → `make_default_table.py`** generates a default 费用明细表 (xlsx+md) |
| 7 | Review report + deliver | `审阅报告.md` with category totals, reconciliation, open‑questions list |

**Minimal commands**
```bash
cd expense-reimbursement
# --out & --template are OPTIONAL: no --out → a meaningfully-named workspace next to the source;
# no --template → the no-template branch (different users may have different templates, or none)
python3 scripts/setup_workspace.py --source <materials> [--out <workspace>] [--template <template.xlsx>]
python3 scripts/extract_ofd.py <file.ofd> --json          # OFD national e-invoices -> text
# WITH a template:
python3 scripts/fill_template.py --xlsx <workspace>/<name>_已填写.xlsx --ledger <workspace>/过程文件/ledger.json
python3 scripts/recalc_fallback.py <workspace>/<name>_已填写.xlsx --write   # if no LibreOffice/recalc.py
# WITHOUT a template — generate a default 费用明细表 (xlsx + md):
python3 scripts/make_default_table.py --ledger <workspace>/过程文件/ledger.json --out <workspace>/<meaningful-name>.xlsx
```
`fill_template.py` prints a `computed` block (per‑column subtotals + grand total) so you know the right numbers **without** LibreOffice, and auto‑sorts rows by date. All scripts are pure `python3` + `openpyxl`/stdlib — **cross‑platform (macOS / Linux / Windows)**, no system‑specific commands.

**Three adjustable defaults** (the user can change with one sentence): **autonomy** (default: *ask only when unsure*) · **identity** (default: *ask once, save to `身份信息.json`, reuse*) · **multi‑currency** (default: *convert to RMB; if no rate is given, ask — don't guess*).

### 🗂 What it produces — ten folders
| Folder | Role |
|---|---|
| `有票/` | **has‑invoice** — formal invoices that stand alone as primary proof (VAT e‑invoices, rail e‑tickets, flight/hotel invoices, taxi invoices…) |
| `无票/` | **no‑invoice** — real spend with no formal invoice but a usable primary record (overseas receipts, non‑invoice slips, **screenshot‑only** expenses) |
| `辅助材料/` | **supporting** — side evidence only (payment / order / itinerary / refund screenshots); always sits next to a primary proof |
| `待核实/` | **to‑verify** — uncertain items park here; **never** pre‑filed into 有票/无票 until the user confirms |
| `替票/` | **substitute‑invoice pool** — the client's *optional* spare invoices used to loosely offset `无票` totals for finance. **Not 1:1 matches** → they stay here, are **not** counted in the ledger, and `无票` items are **never** promoted to `有票` |
| `额外说明/` | finance‑facing txt notes (merges / partial refunds / rebookings / FX / company‑vs‑personal splits) |
| `过程文件/` | process: `身份信息.json`, `manifest.json`, `extracted/`, `物料台账.csv`, `ledger.json`, optional `替票池.csv` |
| `备份/` | 1:1 backup of originals + `_模板原件/` |
| `补充材料/` | intake for later‑supplied materials → backed up & re‑classified, then **emptied** |
| `无关/` | confirmed unrelated / not‑this‑period / next‑period; kept aside, excluded from this run |

…plus `<name>_已填写.xlsx` (the filled table, rows in **chronological** order) and `审阅报告.md`.

### 🧠 Correctness invariants (what makes the numbers right)
- **One ledger row per event** — never sum an invoice together with its own payment screenshot.
- **VAT invoice amount = tax‑inclusive total (价税合计)**, not the pre‑tax 金额.
- **Train refund** = the small 退票费 only (not the fare); **rebooking (改签)** = count the final valid ticket once, **by face value** (don't fuss over a few yuan of change‑fee).
- **Company‑paid / AA** = reimburse only the individual's out‑of‑pocket portion.
- **Screenshot‑only real expense (no invoice) → `无票`** (it *is* the primary proof), not `辅助材料`.
- **Foreign currency** → convert to RMB with a stated rate/source; if no rate, **ask**.
- **Suspected personal / unrelated** → `待核实/` then `无关/`; excluded by default, surfaced for the user.
- **替票 never converts 无票 into 有票** and is never added to the totals.
- **Annual (包年) subscriptions → prorate monthly** (annual ÷ 12) when reimbursed monthly; a forgotten earlier month can be back‑filled.
- **No template? No problem** — `make_default_table.py` emits a generic 费用明细表; workspaces get **meaningful auto‑names** next to the source; everything is **cross‑platform**.
- **Opens on macOS / Windows / Linux** — `finalize_encoding.py` saves all `.txt/.md/.csv` as **UTF‑8 with BOM + CRLF** and normalizes filenames to **NFC**, so titles & Chinese never turn into 乱码 (or one giant line) in Notepad/Excel/TextEdit/gedit/LibreOffice. JSON stays plain UTF‑8 (so it still parses); `.xlsx` is portable OOXML (Excel / LibreOffice / Numbers / WPS).
- **Chronological order** — rows go in date order.

### 📦 Install
**A. Drop‑in folder (Claude Code / most agent runtimes):**
```bash
git clone https://github.com/Auromix/expense-reimbursement-skill.git
cp -R expense-reimbursement-skill/expense-reimbursement ~/.claude/skills/
```
**B. Build a `.skill` package (Claude desktop "add skill"):** `./pack.sh` → `dist/expense-reimbursement.skill`
**C. Reference in place:** point your skill loader at the `expense-reimbursement/` directory.

---

<a name="中文"></a>
## 中文

### ✨ 这个技能解决什么
真实的**报销**材料是雷区：增值税**发票**和它的支付截图并存（重复计费风险）、火车票**改签/退票**、外币打车收据、**企业代付 vs 个人垫付**、没有发票的酒店、疑似私人消费。本技能把这些"踩过的坑"固化成规则，确保**金额算对**，**看不清/对不上就问用户、绝不臆造**。它**与模型无关**、**自带依赖**：纯 `python3` 脚本，无需 LibreOffice 或云端路径。

### 🚦 三条不可逾越的红线
1. **原始材料与原模板绝不修改**——一切改动只发生在备份件 / 模板副本上。
2. **绝不臆造**——看不清 / 对不上 / 要素缺失的，列入**存疑清单**问用户；宁可问，不要编。
3. **一笔消费只入表一行，绝不重复计费**——发票和它的支付截图是同一笔；改签前后是同一程；企业已代付的部分不再报。

### 🤖 给 AI Agent —— 快速上手
**触发场景**：用户想整理 / 提交报销，触发词 `报销 / 发票报销 / 费用报销 / 费用明细表 / 整理发票 / 贴票报账 / 差旅报销`，并提供材料文件夹 + xlsx 模板。

**先读 [`expense-reimbursement/SKILL.md`](./expense-reimbursement/SKILL.md)**（入口，统领全流程），再读 [`references/`](./expense-reimbursement/references/) 三个参考：模板与字段映射、归类与命名规范、额外说明写法。

**核心工作流（第 0–7 步）：**
| # | 步骤 | 做什么 |
|---|---|---|
| 0 | 搭工作区 + 备份 | `setup_workspace.py` 建 10 个文件夹、备份原件、生成可写模板副本 |
| 1 | 逐份读懂材料 | 图片用视觉；PDF 取文本（取不到转图片）；OFD 用 `extract_ofd.py`；写 `extracted/<原名>.json` |
| 2 | 归桶 + 归类 + 串事件 | 判 有票/无票/辅助材料、对应模板列、同笔消费共用**事件号**；拿不准先放 `待核实/` |
| 3 | 建物料台账 | `过程文件/物料台账.csv`——每份**材料**一行（唯一数据源） |
| 4 | 复制 + 重命名 + 归桶 | `日期_费用类型_关键信息_金额`；同事件跨桶同名 |
| 5 | 写额外说明 | `额外说明/` txt：合并 / 退费 / 外币 / 拆分 |
| 6 | 去重→ledger→回填→重算 | 折叠成**一事件一行**、按**时间顺序**排、`fill_template.py` 后重算；三方总额一致。**无模板→ `make_default_table.py`** 生成通用费用明细表（xlsx+md） |
| 7 | 审阅报告 + 交付 | `审阅报告.md`：分类汇总、勾稽核对、存疑清单 |

**最小命令**
```bash
cd expense-reimbursement
# --out 与 --template 都可不给：不给 --out → 在源旁边建有含义名字的工作区；不给 --template → 走无模板分支
python3 scripts/setup_workspace.py --source <材料文件夹> [--out <工作区>] [--template <模板.xlsx>]
python3 scripts/extract_ofd.py <file.ofd> --json          # OFD 国标电子发票 -> 文本
# 有模板：
python3 scripts/fill_template.py --xlsx <工作区>/<名称>_已填写.xlsx --ledger <工作区>/过程文件/ledger.json
python3 scripts/recalc_fallback.py <工作区>/<名称>_已填写.xlsx --write   # 没有 LibreOffice/recalc.py 时
# 无模板 —— 生成通用费用明细表（xlsx + md）：
python3 scripts/make_default_table.py --ledger <工作区>/过程文件/ledger.json --out <工作区>/<有含义的名字>.xlsx
```
`fill_template.py` 会输出 `computed`（各列小计 + 总额），**无需 LibreOffice** 即可知道正确数值，并自动按日期排序。所有脚本纯 `python3` + `openpyxl`/标准库，**跨平台（mac / linux / windows）**、不依赖系统专有命令。

**三个可调默认**（用户一句话即可改）：**自主程度**（默认*拿不准才问*）· **身份信息**（默认*第一次问、存 `身份信息.json`、复用*）· **多币种**（默认*换算成 RMB；没给汇率就问，不要拍脑袋*）。

### 🗂 产出 —— 十个文件夹
| 目录 | 作用 |
|---|---|
| `有票/` | **有正式票据**——能独立作主证据（增值税电子发票、铁路电子客票、机票/酒店/出租车发票…） |
| `无票/` | **无正式发票**——真实消费但拿不到发票、只有一份能当主证据的记录（境外收据、非发票小票、**仅有截图**的消费） |
| `辅助材料/` | **侧面佐证**——本身不能独立证明消费（支付/下单/行程/退款截图）；旁边必须有主证据 |
| `待核实/` | **待核实**——拿不准的先放这里，**绝不**先塞进 有票/无票，确认后再移走 |
| `替票/` | **替票池**——客户*可选*提供的其他消费发票，在金额上大致冲抵 `无票` 合计给财务。**非一一对应** → 留在本目录、**不计入台账**，`无票` **绝不改判为** `有票` |
| `额外说明/` | 给财务看的 txt（合并 / 退费 / 改签 / 外币 / 企业个人拆分） |
| `过程文件/` | 过程信息：`身份信息.json`、`manifest.json`、`extracted/`、`物料台账.csv`、`ledger.json`、可选 `替票池.csv` |
| `备份/` | 原始材料 1:1 备份 + `_模板原件/` |
| `补充材料/` | 客户后续补的材料入口 → 备份并归桶后**自动清空** |
| `无关/` | 经确认与本次无关 / 本期不报 / 跨期；单独存放、不计入本期 |

…外加 `<名称>_已填写.xlsx`（填好的明细表，**按时间顺序**）和 `审阅报告.md`。

### 🧠 正确性铁律（让金额算对的关键）
- **一事件一行**——绝不把发票和它的支付截图算成两笔。
- **增值税发票按价税合计（含税）入表**，不是不含税的「金额」。
- **退票**只计退票费；**改签**以改签后有效票为准、按**票面**只算一次（几元差额不纠结）。
- **企业代付 / AA**：只报个人实际承担部分。
- **只有截图、无发票的真实消费 → `无票`**（它就是主证据），不是 `辅助材料`。
- **外币** → 换算成 RMB 并注明汇率/来源；没有汇率就**问用户**。
- **疑似私人 / 与本次无关** → 先 `待核实/`、确认后 `无关/`；默认不计入、列存疑。
- **替票绝不把 `无票` 变 `有票`**，也不计入任何合计。
- **包年/连续包年 → 按月摊销**（年费 ÷ 12）：按月报销时只报当月那份；忘报的往月可一并补上。
- **没有模板也能用**——`make_default_table.py` 生成通用费用明细表；工作区自动取**有含义的名字**建在源旁边；全程**跨平台**。
- **mac / Windows / Linux 都能打开**——`finalize_encoding.py` 把所有 `.txt/.md/.csv` 存成 **UTF‑8 带 BOM + CRLF**、文件名规范成 **NFC**，记事本/Excel/TextEdit/gedit/LibreOffice 打开标题与中文都正常、不乱码也不挤成一行（JSON 保持纯 UTF‑8 才能解析；xlsx 为通用 OOXML，Excel/LibreOffice/Numbers/WPS 通吃）。
- **按时间顺序**填表。

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
│   │   ├── 模板与字段映射.md       # template structure, column map, 价税合计 & 时间顺序 rules
│   │   ├── 归类与命名规范.md       # buckets, naming, no-double-count, 改签/退票, 替票, 疑似私人
│   │   └── 额外说明写法.md         # finance-facing note templates (合并/退票/改签/外币/拆分)
│   └── scripts/
│       ├── setup_workspace.py    # build the 10 folders + back up originals (--out/--template optional)
│       ├── extract_ofd.py        # extract text from OFD national e-invoices
│       ├── fill_template.py      # fill the template copy, chronological, self-check computed totals
│       ├── recalc_fallback.py    # pure-python recalc (no LibreOffice needed)
│       ├── make_default_table.py # generate a default 费用明细表 (xlsx+md) when the user has no template
│       └── finalize_encoding.py  # Windows-safe pass: txt/md/csv -> UTF-8 BOM, filenames -> NFC
├── pack.sh                       # build dist/expense-reimbursement.skill
├── LICENSE                       # Apache-2.0
└── README.md
```

## ⚙️ Requirements / 环境要求
- The scripts hard‑require only **`python3` + `openpyxl`** (xlsx fill/recalc); OFD parsing uses the **stdlib** only.
- Reading PDFs is done by the agent's own tooling (`extract-text` / a PDF skill / vision); `pdfplumber` is an **optional** pure‑python helper, not a skill dependency.
- LibreOffice is **optional** — `recalc_fallback.py` covers recalculation when it's absent.
- 脚本只硬依赖 `python3 + openpyxl`（OFD 仅用标准库）；PDF 文本由 Agent 自带工具读取，`pdfplumber` 可选；LibreOffice 可选（没有就用 `recalc_fallback.py`）。
```bash
python3 -m pip install openpyxl       # required / 必需
python3 -m pip install pdfplumber     # optional / 可选：纯 python 读 PDF 文本
```

## 🤝 Contributing / 贡献
Issues & PRs welcome. The skill is tuned against messy real‑world Chinese reimbursement data (rail rebookings/refunds, OFD invoices, KRW receipts, invoice‑less hotels, company‑paid taxis). When adding a rule, update the relevant file in `references/` **and** the self‑check list in `SKILL.md`, and keep the scripts dependency‑light and `python3`‑only.
欢迎提 Issue / PR。新增规则时，请同时更新 `references/` 对应文件与 `SKILL.md` 的收尾自检清单，并保持脚本轻依赖、仅用 `python3`。

## 📄 License
[Apache‑2.0](./LICENSE) © 2026 Auromix

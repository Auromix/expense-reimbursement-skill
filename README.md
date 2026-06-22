# Expense‑Reimbursement Skill · 企业报销材料整理技能

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
[![Skill](https://img.shields.io/badge/type-agent--skill-6E56CF.svg)](#)
[![python3](https://img.shields.io/badge/python-3.x-3776AB.svg)](#requirements)

> An [Agent Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) that turns a messy folder of receipts (jpg / png / pdf / **ofd** / xlsx) **+** a reimbursement Excel template into a **finance‑ready 费用明细表** — backed up, classified into buckets, renamed, reconciled, and filled into a copy of the template (the original is never touched).
>
> 把一堆杂乱的报销票据 + 一份报销 Excel 模板，整理成可直接交财务的费用明细表：备份原件、分桶归档、规范命名、去重勾稽、回填模板副本（原模板绝不修改）。

---

## ✨ Why this skill

Real reimbursement folders are a minefield: VAT invoices **plus** their payment screenshots (double‑count risk), rebooked/refunded train tickets, foreign‑currency taxi receipts, hotels with no invoice, suspected personal expenses. This skill encodes the hard‑won rules to get the **numbers right**, and **asks instead of inventing** when something is unclear.

It is **model‑agnostic** and **self‑contained**: pure‑`python3` helper scripts, no LibreOffice or cloud paths required.

---

## 🤖 For AI agents — quick apply

**Trigger when** the user wants to organize / file a reimbursement: keywords like `报销 / 费用报销 / 费用明细表 / 整理发票 / 贴票报账 / 差旅报销`, and they provide a materials folder + an xlsx template.

**The 30‑second mental model:**
1. Read [`expense-reimbursement/SKILL.md`](./expense-reimbursement/SKILL.md) first — it is the entry point and orchestrates everything.
2. Three red lines (never violate): ① originals & original template are never modified; ② never invent info — unclear items go to a 存疑清单 for the user; ③ **one expense = one ledger row, never double‑count** (an invoice and its payment screenshot are the *same* event).
3. Run the workflow: `setup_workspace.py` → read every material → bucket & classify → build 物料台账 → de‑dup into `ledger.json` → `fill_template.py` → recalc → 审阅报告.
4. Reconcile three ways before delivering: `Σ(ledger) == fill_template "computed" == recalc total`, with `total_errors == 0`.

**Minimal command sequence** (paths are examples):

```bash
cd expense-reimbursement

# 0) workspace + backup (+ writable copy of template; original template & *.skill are skipped from backup)
python3 scripts/setup_workspace.py \
  --source <materials_folder> --out <workspace> --template <template.xlsx>

# read OFD national e-invoices as text (fall back to vision/raster if empty)
python3 scripts/extract_ofd.py <file.ofd> --json

# 6) after you build 过程文件/ledger.json -> fill the template COPY (never the original)
python3 scripts/fill_template.py --xlsx <workspace>/<name>_已填写.xlsx --ledger <workspace>/过程文件/ledger.json

# recalc: prefer the xlsx skill's recalc.py (needs LibreOffice); otherwise use the bundled fallback:
python3 scripts/recalc_fallback.py <workspace>/<name>_已填写.xlsx --write
```

`fill_template.py` prints a `computed` block (per‑column subtotals + grand total) so you know the right numbers **without** LibreOffice. `recalc_fallback.py` evaluates the template's `SUM` / subtraction / reference formulas in pure Python and reports `total_errors`.

> Read the three references in [`expense-reimbursement/references/`](./expense-reimbursement/references/) before classifying — they contain the column map, the naming/bucket rules, and the 额外说明 templates.

---

## 📦 Install

Pick whichever fits your runtime:

**A. Drop‑in folder (most agent runtimes / Claude Code):**
```bash
git clone https://github.com/auromix/expense-reimbursement-skill.git
cp -R expense-reimbursement-skill/expense-reimbursement ~/.claude/skills/
```

**B. Build a `.skill` package** (for the Claude desktop “add skill” UI):
```bash
./pack.sh           # -> dist/expense-reimbursement.skill
```

**C. Reference in place:** point your skill loader at the `expense-reimbursement/` directory in this repo.

---

## 🗂 What it produces

A clean workspace with six buckets:

| Folder | 中文 | Contents |
|---|---|---|
| `有票/` | has‑invoice | formal invoices that stand alone as primary proof (VAT e‑invoices, rail e‑tickets, flight invoices, hotel invoices…) |
| `无票/` | no‑invoice | real spend with **no** formal invoice but a usable primary record (overseas receipts, non‑invoice slips, screenshot‑only expenses) |
| `辅助材料/` | supporting | side evidence only (payment / order / itinerary / refund screenshots) — always sits *next to* a primary proof |
| `额外说明/` | notes for finance | plain‑text explainers: merges, partial refunds, **rebookings**, FX conversion, company‑paid/personal splits |
| `过程文件/` | process | `身份信息.json`, `manifest.json`, `extracted/`, `物料台账.csv`, `ledger.json` |
| `备份/` | backup | 1:1 backup of originals + `_模板原件/` |

…plus `<name>_已填写.xlsx` (the filled detail table) and `审阅报告.md` (summary + reconciliation + 存疑清单).

---

## 🧠 Correctness invariants (the part that makes numbers right)

- **One ledger row per event** — never sum an invoice together with its own payment screenshot.
- **VAT invoice amount = 价税合计 (tax‑inclusive)**, not the pre‑tax 金额.
- **Train refund** = the small 退票费 only (not the fare); **rebooking (改签)** = count the final valid ticket once.
- **Company‑paid / AA** = reimburse only the individual’s out‑of‑pocket portion.
- **Screenshot‑only real expense (no invoice) → `无票`** (it *is* the primary proof), not `辅助材料`.
- **Suspected personal / unrelated** (utilities, unrelated‑country visa, personal subscriptions) → 存疑清单, excluded by default.
- **Foreign currency** → convert to RMB with a stated rate/source; if no rate, **ask** — don’t guess.

---

## 🧩 Repository layout

```
expense-reimbursement-skill/
├── expense-reimbursement/        # the skill (drop-in installable)
│   ├── SKILL.md                  # entry point + workflow (read this first)
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

---

## ⚙️ Requirements

- `python3` with `openpyxl` (for the xlsx fill/recalc) and `pdfplumber` (for PDF text). OFD parsing uses only the stdlib.
- LibreOffice is **optional** — `recalc_fallback.py` covers recalculation when it’s absent.

```bash
python3 -m pip install openpyxl pdfplumber
```

---

## 🤝 Contributing

Issues and PRs welcome. The skill is tuned against messy real‑world Chinese reimbursement data (rail rebookings/refunds, OFD invoices, KRW receipts, invoice‑less hotels). When adding rules, update the relevant file in `references/` **and** the self‑check list in `SKILL.md`, and keep the scripts dependency‑light and `python3`‑only.

## 📄 License

[Apache‑2.0](./LICENSE) © 2026 Auromix

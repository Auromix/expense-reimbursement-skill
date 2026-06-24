#!/usr/bin/env python3
"""
在交付工作区根目录生成一份「阅读说明.md」, 向收到这个包的人(财务/审阅人)解释里面都是什么、先看哪个,
并自动把**空文件夹**标成「空·无需理会」。

用法:
  python3 make_package_readme.py <工作区根目录>

跨平台、纯标准库。输出用 UTF-8 带 BOM + CRLF(Windows/mac/Linux 打开都不乱码)。
"""
import os, sys, datetime

# 已知文件夹含义(按展示顺序)。未知文件夹也会被列出(通用说明)。
FOLDER_DESC = [
    ("有票",   "正式发票/票据，报销**主证据**（增值税发票、铁路电子客票、机票/酒店/出租车发票等）"),
    ("无票",   "真实消费但拿不到正式发票的主证据（境外收据、仅有截图的消费、非发票小票等）"),
    ("辅助材料", "支付/下单/行程/退款**截图**，辅助佐证（不单独计金额，只为佐证有票/无票）"),
    ("待核实", "归属/能否报销待确认的材料"),
    ("替票",   "备用发票池（可选；与无票非一一对应，仅金额上冲抵，不计入合计）"),
    ("额外说明", "给财务看的**文字说明**（合并/退票/改签/外币换算/包年摊销/拆分等口径)"),
    ("过程文件", "AI 处理过程的中间文件（物料台账、ledger、提取信息）——**追溯用，一般无需细看**"),
    ("备份",   "原始材料 1:1 **备份** + 原模板原件（仅存档，原件从未改动）"),
    ("补充材料", "客户后续补材料的**入口**（处理完会清空）"),
    ("无关",   "经确认与本次无关 / 本期不报 / 跨期的材料（**不计入本次**）"),
]

def count_files(path):
    return sum(len(fs) for _, _, fs in os.walk(path))

def main():
    if len(sys.argv) < 2:
        print("用法: python3 make_package_readme.py <工作区根目录>", file=sys.stderr); sys.exit(2)
    ws = os.path.abspath(sys.argv[1])
    if not os.path.isdir(ws):
        print(f"ERROR: 目录不存在: {ws}", file=sys.stderr); sys.exit(2)

    # 根目录下的交付件(xlsx / 报销明细 md / 审阅报告)
    root_files = sorted(f for f in os.listdir(ws) if os.path.isfile(os.path.join(ws, f)))
    xlsx = [f for f in root_files if f.lower().endswith(".xlsx")]
    md_tables = [f for f in root_files if f.lower().endswith(".md") and f not in ("阅读说明.md", "审阅报告.md")]
    has_review = "审阅报告.md" in root_files

    L = []
    L.append("# 报销材料整理包 · 阅读说明")
    L.append("")
    L.append("本包由 AI 按公司报销口径自动整理。**先看这几项**：")
    for x in xlsx:
        L.append(f"- ★ **{x}** —— 费用明细表（主交付，金额都在这里）")
    for m in md_tables:
        L.append(f"- {m} —— 明细表的 Markdown 版（同上内容，方便预览）")
    if has_review:
        L.append("- **审阅报告.md** —— 金额汇总、三方勾稽核对、以及**存疑清单**（需你补充/确认的项）")
    L.append("")
    L.append("## 文件夹里都是什么")
    L.append("")
    L.append("| 文件夹 | 里面是什么 | 状态 |")
    L.append("|---|---|---|")

    shown = set()
    empty_names = []
    for name, desc in FOLDER_DESC:
        p = os.path.join(ws, name)
        if not os.path.isdir(p):
            continue
        shown.add(name)
        n = count_files(p)
        status = f"{n} 个文件" if n else "空 · 无需理会"
        if not n:
            empty_names.append(name)
        L.append(f"| `{name}/` | {desc} | {status} |")
    # 其它未知文件夹
    for name in sorted(os.listdir(ws)):
        p = os.path.join(ws, name)
        if os.path.isdir(p) and name not in shown:
            n = count_files(p)
            L.append(f"| `{name}/` | （其它材料） | {'%d 个文件' % n if n else '空 · 无需理会'} |")

    L.append("")
    if empty_names:
        L.append("> 标「空 · 无需理会」的文件夹本次没有内容（" + "、".join(empty_names) + "），可直接忽略。")
    L.append("> `过程文件/`、`备份/` 是 AI 处理痕迹与原件存档，财务一般无需细看；其余都已分门别类。")
    L.append("")
    L.append("---")
    L.append(f"*生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}　|　所有文本为 UTF-8(BOM)+CRLF，Windows / macOS / Linux 打开均不乱码。*")

    out = os.path.join(ws, "阅读说明.md")
    with open(out, "w", encoding="utf-8-sig", newline="\r\n") as f:
        f.write("\n".join(L) + "\n")
    print(f"已生成 {out}（空文件夹：{', '.join(empty_names) or '无'}）")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
搭建报销工作区并备份原始材料。

用法:
  python setup_workspace.py --source <原始材料文件夹> --out <工作区根目录> [--template <报销模板.xlsx>]

行为:
  1. 在 <工作区根目录> 下创建 6 个子文件夹: 有票 无票 辅助材料 额外说明 过程文件 备份
  2. 把 <原始材料文件夹> 内全部文件递归复制到 备份/ (保留相对目录结构, 原始材料绝不修改)
  3. 若提供 --template, 把模板原件也复制进 备份/_模板原件/, 并在工作区根目录复制出一份
     "<原名>_已填写.xlsx" 作为后续唯一可写的回填对象 (原模板绝不动)
  4. 输出一份 manifest.json 到 过程文件/, 记录全部备份文件的清单与基本属性

退出码 0 表示成功; 任何异常以非 0 退出并打印原因。
"""
import argparse, hashlib, json, os, shutil, sys
from datetime import datetime

SUBFOLDERS = ["有票", "无票", "辅助材料", "待核实", "替票", "额外说明", "过程文件", "备份", "补充材料", "无关"]
# 待核实: 拿不准(桶/类别/能否报)的材料先放这里, 不要急着塞进 有票/无票; 核实后再移走。
# 替票:   客户平时其他消费的正规发票池, 用来冲抵"无票"项(拿不到发票的真实消费)。
#         有无票项时要提醒客户把替票放进来; 按金额把替票匹配到无票项, 匹配上的替票移入 有票/。
# 补充材料: 客户后续补的材料先丢这里; 处理时备份进 备份/ 并归桶, 处理完应清空。
# 无关:     经确认与本次报销无关 / 本期不报 / 跨到下一期的材料, 单独存这里, 不计入本期台账与模板。

def sha1_head(path, nbytes=1 << 20):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        h.update(f.read(nbytes))
    return h.hexdigest()[:12]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="原始材料文件夹")
    ap.add_argument("--out", required=True, help="工作区根目录(会被创建)")
    ap.add_argument("--template", default=None, help="报销模板 .xlsx (可选)")
    args = ap.parse_args()

    src = os.path.abspath(args.source)
    out = os.path.abspath(args.out)
    if not os.path.isdir(src):
        print(f"ERROR: 原始材料文件夹不存在: {src}", file=sys.stderr); sys.exit(2)
    if os.path.abspath(out).startswith(src + os.sep):
        print("ERROR: 工作区不能建在原始材料文件夹内部, 以免污染原件", file=sys.stderr); sys.exit(2)

    # 不算作"材料"、不应进备份的文件: 报销模板本身、skill 包、说明文档等
    tpl_basename = os.path.basename(os.path.abspath(args.template)) if args.template else None
    SKIP_EXTS = {"skill"}                       # skill 包
    SKIP_NAMES = {tpl_basename} if tpl_basename else set()

    os.makedirs(out, exist_ok=True)
    paths = {name: os.path.join(out, name) for name in SUBFOLDERS}
    for p in paths.values():
        os.makedirs(p, exist_ok=True)

    # 备份原始材料 (保留相对结构)
    backup = paths["备份"]
    manifest = []
    skipped = []
    for root, _, files in os.walk(src):
        # 不要把(可能误建在源目录里的)工作区自身也备份进去
        if os.path.abspath(root) == out or os.path.abspath(root).startswith(out + os.sep):
            continue
        for fn in files:
            if fn.startswith("~$") or fn == ".DS_Store":
                continue
            ext_l = os.path.splitext(fn)[1].lower().lstrip(".")
            if ext_l in SKIP_EXTS or fn in SKIP_NAMES:
                skipped.append(fn)            # 模板/ skill 不当作材料备份(模板单独存 _模板原件/)
                continue
            abspath = os.path.join(root, fn)
            rel = os.path.relpath(abspath, src)
            dst = os.path.join(backup, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(abspath, dst)
            manifest.append({
                "原始相对路径": rel,
                "备份路径": os.path.relpath(dst, out),
                "扩展名": os.path.splitext(fn)[1].lower().lstrip("."),
                "字节": os.path.getsize(abspath),
                "指纹": sha1_head(abspath),
            })

    # 复制模板: 备份原件 + 工作区生成可写副本
    writable_template = None
    if args.template:
        tpl = os.path.abspath(args.template)
        if not os.path.isfile(tpl):
            print(f"ERROR: 模板文件不存在: {tpl}", file=sys.stderr); sys.exit(2)
        tpl_backup_dir = os.path.join(backup, "_模板原件")
        os.makedirs(tpl_backup_dir, exist_ok=True)
        shutil.copy2(tpl, os.path.join(tpl_backup_dir, os.path.basename(tpl)))
        stem, ext = os.path.splitext(os.path.basename(tpl))
        writable_template = os.path.join(out, f"{stem}_已填写{ext}")
        shutil.copy2(tpl, writable_template)

    summary = {
        "创建时间": datetime.now().isoformat(timespec="seconds"),
        "原始材料文件夹": src,
        "工作区根目录": out,
        "子文件夹": list(paths.keys()),
        "备份文件数": len(manifest),
        "跳过未备份(模板/skill包等)": skipped,
        "可写模板副本": os.path.relpath(writable_template, out) if writable_template else None,
        "备份清单": manifest,
    }
    with open(os.path.join(paths["过程文件"], "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 给 stdout 一个机器可读的小结, 便于上层读取关键路径
    print(json.dumps({
        "status": "ok",
        "workspace": out,
        "folders": paths,
        "backup_count": len(manifest),
        "skipped": skipped,
        "writable_template": writable_template,
        "manifest": os.path.join(paths["过程文件"], "manifest.json"),
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()

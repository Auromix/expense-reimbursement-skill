#!/usr/bin/env python3
"""
交付前的跨平台兼容收尾 —— 保证给人/财务看的文本在 Windows / macOS / Linux 都能正确打开、不乱码。

为什么需要它:
  1) 编码: Windows 记事本/Excel 打开「无 BOM 的 UTF-8」中文会乱码(标题、说明全花)。
  2) 换行: 只用 LF(\\n) 的文本在「旧版 Windows 记事本」里会挤成一行。
  本脚本把交付目录里的人读文本统一成「UTF-8 带 BOM + CRLF 换行」, 并把文件名规范成 NFC。
  这种组合 Windows 原生友好, 而 macOS(TextEdit/Numbers/Excel)与 Linux(gedit/VSCode/LibreOffice)
  也都能正常打开 —— 三平台通用。

处理:
  - .txt / .md / .csv  -> UTF-8 带 BOM + CRLF(\\r\\n)。
  - 文件名/目录名 -> NFC(mac 的 NFD 名在 Windows 可能显示异常)。
  - .json 保持纯 UTF-8(不加 BOM, 否则 json 解析会报错; 它是机读过程文件)。
  - .xlsx / .pdf / 图片等二进制不动(xlsx 内部本就是 UTF-8, 三平台 Excel/LibreOffice/Numbers/WPS 均可开)。

用法:
  python3 finalize_encoding.py <工作区目录>

纯标准库、跨平台。建议交付前(第 7 步)对整个工作区跑一次; 可重复运行(幂等)。
"""
import os, sys, json, unicodedata

TEXT_EXTS = {".txt", ".md", ".csv"}
BOM = b"\xef\xbb\xbf"

def normalize_for_windows(path):
    """把文本转成 UTF-8 带 BOM + CRLF。已是该形态则跳过(幂等)。返回是否改动。"""
    raw = open(path, "rb").read()
    text = None
    for enc in ("utf-8-sig", "utf-8", "gb18030"):   # utf-8-sig 先行: 顺带吃掉已有 BOM
        try:
            text = raw.decode(enc); break
        except UnicodeDecodeError:
            continue
    if text is None:
        return False                                # 解不出来就不动, 避免破坏
    text = text.lstrip("﻿")                    # 去掉残留 BOM 字符
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")  # 统一 CRLF
    target = BOM + text.encode("utf-8")
    if raw == target:
        return False                                # 已是 UTF-8 BOM + CRLF
    open(path, "wb").write(target)
    return True

def main():
    if len(sys.argv) < 2:
        print("用法: python3 finalize_encoding.py <工作区目录>", file=sys.stderr); sys.exit(2)
    root = os.path.abspath(sys.argv[1])
    if not os.path.isdir(root):
        print(f"ERROR: 目录不存在: {root}", file=sys.stderr); sys.exit(2)

    fixed = []
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if os.path.splitext(fn)[1].lower() in TEXT_EXTS:
                p = os.path.join(dp, fn)
                if normalize_for_windows(p):
                    fixed.append(os.path.relpath(p, root))

    # 文件名/目录名规范成 NFC(自底向上, 先文件后目录)
    renamed = []
    for dp, dns, fns in os.walk(root, topdown=False):
        for name in fns + dns:
            nfc = unicodedata.normalize("NFC", name)
            if nfc != name:
                src, dst = os.path.join(dp, name), os.path.join(dp, nfc)
                if not os.path.exists(dst):
                    os.rename(src, dst); renamed.append(os.path.relpath(dst, root))

    print(json.dumps({
        "status": "ok", "root": root,
        "normalized_utf8bom_crlf": fixed, "normalized_count": len(fixed),
        "renamed_to_nfc": renamed, "renamed_count": len(renamed),
        "note": "txt/md/csv 已统一为 UTF-8 带 BOM + CRLF(Windows/mac/Linux 通用不乱码); "
                "json 保持纯 UTF-8; xlsx/二进制未动。",
    }, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()

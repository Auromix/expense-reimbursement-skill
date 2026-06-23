#!/usr/bin/env python3
"""
交付前的 Windows 兼容性收尾 —— 保证所有给人/财务看的文本在 Windows 上不乱码。

为什么需要它:
  Windows 记事本/Excel 打开「无 BOM 的 UTF-8」中文文本时会显示乱码(标题、说明全花)。
  本脚本把交付目录里的人读文本统一成「UTF-8 带 BOM」, 并把文件名规范成 NFC。

行为:
  - .txt / .md / .csv  -> 统一存成 UTF-8 带 BOM(utf-8-sig); Windows 记事本/Excel 直接正确显示中文。
  - 文件名/目录名 -> 规范成 NFC(Windows 友好; mac 的 NFD 文件名在 Windows 可能显示异常)。
  - .json 保持纯 UTF-8(不加 BOM, 否则 json 解析会报错); .xlsx/.pdf/图片等二进制不动
    (xlsx 内部本就是 UTF-8, Excel 不会乱码)。

用法:
  python3 finalize_encoding.py <工作区目录>

纯标准库、跨平台(mac/linux/windows)。建议在交付前(第 7 步)对整个工作区跑一次。
"""
import os, sys, json, unicodedata

TEXT_BOM_EXTS = {".txt", ".md", ".csv"}
BOM = b"\xef\xbb\xbf"

def reencode_to_utf8bom(path):
    raw = open(path, "rb").read()
    if raw.startswith(BOM):
        return False                      # 已带 BOM, 跳过
    text = None
    for enc in ("utf-8", "gb18030"):      # gb18030 兼容旧 windows 中文文本
        try:
            text = raw.decode(enc); break
        except UnicodeDecodeError:
            continue
    if text is None:
        return False                      # 解不出来就不动, 避免破坏
    open(path, "wb").write(BOM + text.encode("utf-8"))
    return True

def main():
    if len(sys.argv) < 2:
        print("用法: python3 finalize_encoding.py <工作区目录>", file=sys.stderr); sys.exit(2)
    root = os.path.abspath(sys.argv[1])
    if not os.path.isdir(root):
        print(f"ERROR: 目录不存在: {root}", file=sys.stderr); sys.exit(2)

    reencoded = []
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if os.path.splitext(fn)[1].lower() in TEXT_BOM_EXTS:
                p = os.path.join(dp, fn)
                if reencode_to_utf8bom(p):
                    reencoded.append(os.path.relpath(p, root))

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
        "reencoded_to_utf8bom": reencoded, "reencoded_count": len(reencoded),
        "renamed_to_nfc": renamed, "renamed_count": len(renamed),
        "note": "txt/md/csv 已统一为 UTF-8 带 BOM(Windows 不乱码); json 保持纯 UTF-8; xlsx/二进制未动。",
    }, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()

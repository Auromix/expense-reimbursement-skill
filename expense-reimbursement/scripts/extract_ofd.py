#!/usr/bin/env python3
"""
从 OFD 文件提取文本 (OFD 是国标电子票据格式: 本质是 zip + XML)。

用法:
  python3 extract_ofd.py <file.ofd> [--json]

策略:
  - 解压 OFD, 遍历各页 Content.xml, 抽取 <TextCode> 内文本, 按出现顺序拼接。
  - 同时尝试读取 OFD.xml / Document.xml 里的元数据 (标题、作者、自定义标签)。
  - 发票常见关键字段 (金额、日期、税号、销售方等) 多以 TextCode 散落出现,
    拼接后的全文足以让上层模型理解并提取; 不做强结构化, 保留原始可读文本。

注意: OFD 内的数字常被拆成单字符 TextCode, 拼接时按页输出, 上层据全文判断。
若解析为空, 上层应改用渲染成图片后视觉识别 (见 SKILL.md 的兜底说明)。
"""
import argparse, json, re, sys, zipfile
import xml.etree.ElementTree as ET

def localname(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag

def extract_textcodes(xml_bytes):
    out = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return out
    for el in root.iter():
        if localname(el.tag) == "TextCode" and el.text:
            t = el.text.strip("\n")
            if t:
                out.append(t)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true", help="输出 JSON (含分页与元数据)")
    args = ap.parse_args()

    try:
        zf = zipfile.ZipFile(args.path)
    except zipfile.BadZipFile:
        print("ERROR: 不是有效的 OFD/zip 文件", file=sys.stderr); sys.exit(2)

    names = zf.namelist()
    # 页面内容文件: 形如 Doc_0/Pages/Page_0/Content.xml
    page_files = sorted(
        [n for n in names if re.search(r"Pages/Page_\d+/Content\.xml$", n, re.I)],
        key=lambda n: int(re.search(r"Page_(\d+)", n).group(1))
    )
    pages = []
    for pf in page_files:
        codes = extract_textcodes(zf.read(pf))
        pages.append({"page": pf, "text": " ".join(codes)})

    # 兜底: 若没找到标准页结构, 扫描所有 xml
    if not pages:
        allcodes = []
        for n in names:
            if n.lower().endswith(".xml"):
                allcodes += extract_textcodes(zf.read(n))
        if allcodes:
            pages.append({"page": "(all-xml)", "text": " ".join(allcodes)})

    meta = {}
    for cand in ("OFD.xml", "Doc_0/Document.xml"):
        if cand in names:
            try:
                root = ET.fromstring(zf.read(cand))
                for el in root.iter():
                    ln = localname(el.tag)
                    if ln in ("Title", "Author", "DocID", "Abstract") and el.text:
                        meta[ln] = el.text.strip()
            except ET.ParseError:
                pass

    full_text = "\n".join(p["text"] for p in pages)
    if args.json:
        print(json.dumps({"meta": meta, "pages": pages, "full_text": full_text},
                         ensure_ascii=False, indent=2))
    else:
        if meta:
            print("# META:", json.dumps(meta, ensure_ascii=False))
        print(full_text)

if __name__ == "__main__":
    main()

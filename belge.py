#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — belge.py
#  Copyright (c) 2026 BTM Code — MIT License
#
#  BELGE OKUMA — sıfır bağımlılık
#  .docx / .xlsx / .pptx / .pdf / .csv / .json / .html / .md / kod dosyaları
#  docx/xlsx/pptx aslında birer ZIP + XML'dir: zipfile + xml ile okunur.
#  PDF: metin katmanı varsa çıkarılır (saf Python, kütüphanesiz kaba ayrıştırma).
# ============================================================================

import csv
import io
import json
import os
import re
import zipfile

MAX_TEXT = 60_000


def _clean(s):
    s = re.sub(r"[ \t]+", " ", s or "")
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _xml_text(xml_bytes):
    """XML'den metin düğümlerini çıkarır (namespace bağımsız)."""
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        # bozuk XML → kaba temizlik
        t = re.sub(rb"<[^>]+>", b" ", xml_bytes)
        return _clean(t.decode("utf-8", "replace"))
    parts = []

    def walk(node):
        tag = node.tag.split("}")[-1]
        if tag in ("t", "v", "text", "p", "si"):
            if node.text and node.text.strip():
                parts.append(node.text)
            if tag in ("p", "si"):
                parts.append("\n")
        for ch in node:
            walk(ch)

    walk(root)
    return _clean("".join(parts))


# ----------------------------------------------------------------- docx
def read_docx(path):
    with zipfile.ZipFile(path) as z:
        out = []
        if "word/document.xml" in z.namelist():
            out.append(_xml_text(z.read("word/document.xml")))
        # tablo hücreleri document.xml içinde; dipnotlar ayrı
        for extra in ("word/footnotes.xml", "word/endnotes.xml"):
            if extra in z.namelist():
                t = _xml_text(z.read(extra))
                if t:
                    out.append("\n[notlar]\n" + t)
        return _clean("\n".join(out))


# ----------------------------------------------------------------- xlsx
def read_xlsx(path, max_rows=400):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        shared = []
        if "xl/sharedStrings.xml" in names:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root:
                shared.append("".join(t.text or "" for t in si.iter()
                                      if t.tag.endswith("}t")))
        # sayfa adları
        sheets = {}
        if "xl/workbook.xml" in names:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(z.read("xl/workbook.xml"))
            for sh in root.iter():
                if sh.tag.endswith("}sheet"):
                    rid = None
                    for k, v in sh.attrib.items():
                        if k.endswith("}id"):
                            rid = v
                    sheets[rid] = sh.attrib.get("name", "Sayfa")

        blocks = []
        sheet_files = sorted(n for n in names
                             if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"))
        for i, sf in enumerate(sheet_files):
            name = next(iter(sheets.values()), f"Sayfa{i + 1}") if sheets else f"Sayfa{i + 1}"
            import xml.etree.ElementTree as ET
            root = ET.fromstring(z.read(sf))
            rows = []
            for r_i, row in enumerate(root.iter()):
                if not row.tag.endswith("}row"):
                    continue
                if len(rows) >= max_rows:
                    rows.append(["… (satır sınırı)"])
                    break
                cells = []
                for c in row:
                    if not c.tag.endswith("}c"):
                        continue
                    t = c.attrib.get("t")
                    val = ""
                    for node in c:
                        if node.tag.endswith("}v"):
                            val = node.text or ""
                        elif node.tag.endswith("}is"):
                            val = "".join(x.text or "" for x in node.iter()
                                          if x.tag.endswith("}t"))
                    if t == "s" and val.isdigit():
                        idx = int(val)
                        val = shared[idx] if idx < len(shared) else val
                    cells.append(val)
                if any(x.strip() for x in cells):
                    rows.append(cells)
            if rows:
                blocks.append(f"### {name}\n" + "\n".join(
                    " | ".join(cells) for cells in rows))
        return _clean("\n\n".join(blocks))


# ----------------------------------------------------------------- pptx
def read_pptx(path):
    with zipfile.ZipFile(path) as z:
        slides = sorted((n for n in z.namelist()
                         if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                        key=lambda x: int(re.findall(r"\d+", x)[-1]))
        out = []
        for i, s in enumerate(slides, 1):
            out.append(f"### Slayt {i}\n" + _xml_text(z.read(s)))
        return _clean("\n\n".join(out))


# ----------------------------------------------------------------- pdf
def read_pdf(path, max_pages=40):
    """PDF metin katmanını çıkarır (kütüphanesiz, kaba ama işe yarar)."""
    data = open(path, "rb").read()
    if not data.startswith(b"%PDF"):
        return "(PDF imzası yok)"
    out = []
    # stream ... endstream blokları
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
        chunk = m.group(1)
        if b"BT" not in chunk:
            continue
        # Tj ve TJ operatörlerindeki metinleri topla
        for tm in re.finditer(rb"\((?:[^()\\]|\\.)*\)", chunk):
            raw = tm.group(0)[1:-1]
            raw = raw.replace(b"\\(", b"(").replace(b"\\)", b")")
            raw = raw.replace(b"\\\\", b"\\")
            try:
                out.append(raw.decode("utf-8", "replace"))
            except Exception:
                pass
        if len(out) > 20000:
            break
    if not out:
        return ("(Bu PDF'de seçilebilir metin yok — taranmış görüntü olabilir. "
                "OCR gerekir.)")
    return _clean(" ".join(out))[:MAX_TEXT]


# ----------------------------------------------------------------- diğer
def read_csv(path):
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except Exception:
            dialect = csv.excel
        rows = list(csv.reader(f, dialect))[:600]
    return _clean("\n".join(" | ".join(r) for r in rows))


def read_html(path):
    raw = open(path, "rb").read().decode("utf-8", "replace")
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    return _clean(re.sub(r"(?s)<[^>]+>", " ", raw))


def read_json(path):
    d = json.load(open(path, "r", encoding="utf-8", errors="replace"))
    return json.dumps(d, indent=2, ensure_ascii=False)[:MAX_TEXT]


def read_plain(path):
    return open(path, "r", encoding="utf-8", errors="replace").read()[:MAX_TEXT]


READERS = {
    ".docx": read_docx,
    ".xlsx": read_xlsx,
    ".xlsm": read_xlsx,
    ".pptx": read_pptx,
    ".pdf": read_pdf,
    ".csv": read_csv,
    ".tsv": read_csv,
    ".json": read_json,
    ".html": read_html,
    ".htm": read_html,
    ".md": read_plain,
    ".txt": read_plain,
    ".log": read_plain,
    ".py": read_plain, ".js": read_plain, ".ts": read_plain,
    ".css": read_plain, ".html5": read_plain, ".sql": read_plain,
    ".xml": read_plain, ".yml": read_plain, ".yaml": read_plain,
    ".ini": read_plain, ".cfg": read_plain, ".bat": read_plain,
    ".ps1": read_plain, ".sh": read_plain,
}

SUPPORTED = sorted(READERS.keys())


def read_document(path):
    ext = os.path.splitext(path)[1].lower()
    if ext not in READERS:
        return {"ok": False,
                "error": f"Desteklenmeyen tür: {ext or '(uzantısız)'}",
                "supported": SUPPORTED,
                "hint": "read aracı düz metin okur; belge için doc_read kullanın."}
    if not os.path.isfile(path):
        return {"ok": False, "error": "Dosya yok."}
    size = os.path.getsize(path)
    if size > 60 * 1024 * 1024:
        return {"ok": False, "error": f"Dosya çok büyük ({size // 1048576} MB)."}
    try:
        text = READERS[ext](path)
    except zipfile.BadZipFile:
        return {"ok": False, "error": "Dosya bozuk veya şifreli (ZIP açılamadı)."}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    text = text or ""
    trunc = len(text) > MAX_TEXT
    return {"ok": True, "path": os.path.abspath(path), "type": ext,
            "bytes": size, "chars": len(text), "truncated": trunc,
            "text": text[:MAX_TEXT]}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        r = read_document(sys.argv[1])
        if r.get("ok"):
            print(r["text"][:1500])
        else:
            print("HATA:", r.get("error"))
    else:
        print("desteklenen:", ", ".join(SUPPORTED))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — guncelle.py
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Otomatik güncelleme: GitHub Releases'ten en son sürümü indirir, dosyaları
#  yerine koyar. Sıfır bağımlılık (stdlib urllib + zipfile).
# ============================================================================

import io
import json
import os
import shutil
import sys
import zipfile

REPO = "Btmcode/GhostPilot"
API = f"https://api.github.com/repos/{REPO}/releases/latest"


def surum_coz(s):
    """'5.0.0' → (5,0,0), 'v4.2.0' → (4,2,0)"""
    s = str(s or "").strip().lstrip("vV")
    out = []
    for part in s.split("."):
        num = ""
        for ch in part:
            if ch.isdigit():
                num += ch
            else:
                break
        out.append(int(num or 0))
    while len(out) < 3:
        out.append(0)
    return tuple(out[:3])


def son_surum():
    """GitHub'dan en son release bilgisi. (tag, zip_url, notlar) veya hata."""
    import urllib.request
    req = urllib.request.Request(API, headers={
        "User-Agent": "GhostPilot-Updater",
        "Accept": "application/vnd.github+json",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.load(r)
    except Exception as e:
        return None, None, f"GitHub'a ulaşılamadı: {e}"
    tag = d.get("tag_name") or ""
    zip_url = None
    for a in d.get("assets") or []:
        if a.get("name", "").lower().endswith(".zip"):
            zip_url = a.get("browser_download_url")
            break
    return tag, zip_url, (d.get("body") or "")[:1500]


def kontrol(mevcut):
    """Güncelleme var mı? True → var."""
    tag, url, _ = son_surum()
    if not tag:
        return None
    return surum_coz(tag) > surum_coz(mevcut)


def indir_ve_kur(hedef_dir, sessiz=False):
    """En son zip'i indirip hedef_dir içine açar (eski .py dosyaları korunur)."""
    tag, url, notlar = son_surum()
    if not tag or not url:
        return {"ok": False, "error": notlar or "Release bulunamadı."}
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GhostPilot-Updater"})
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read()
    except Exception as e:
        return {"ok": False, "error": f"İndirilemedi: {e}"}

    yedek = os.path.join(hedef_dir, "_yedek")
    os.makedirs(yedek, exist_ok=True)
    yazilan = []
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for name in z.namelist():
                if name.endswith("/") or "__pycache__" in name:
                    continue
                # zip içinde klasör varsa düzleştir
                rel = "/".join([p for p in name.split("/")[1:]]) if "/" in name else name
                if not rel or rel.startswith("."):
                    continue
                dst = os.path.join(hedef_dir, rel.replace("/", os.sep))
                os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
                if os.path.exists(dst):
                    try:
                        shutil.copy2(dst, os.path.join(yedek, os.path.basename(dst)))
                    except Exception:
                        pass
                with z.open(name) as src, open(dst, "wb") as out:
                    out.write(src.read())
                yazilan.append(rel)
    except Exception as e:
        return {"ok": False, "error": f"Zip açılamadı: {e}"}

    return {"ok": True, "version": tag, "files": yazilan,
            "backup": yedek, "notes": notlar}


if __name__ == "__main__":
    mevcut = "0.0.0"
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import ghostpilot
        mevcut = ghostpilot.VERSION
    except Exception:
        pass
    if "--kontrol" in sys.argv:
        v = kontrol(mevcut)
        print("Güncelleme var." if v else ("Güncelsiniz." if v is False else "Kontrol edilemedi."))
    else:
        r = indir_ve_kur(os.path.dirname(os.path.abspath(__file__)))
        print(json.dumps(r, ensure_ascii=False, indent=1))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — sanalortam.py  ·  Python sanal ortamı (.venv)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  NEDEN?  Pillow gibi ek paketler kullanıcının SİSTEM Python'unu kirletmesin.
#          Her şey .venv içine kurulur; silmek için klasörü silmek yeter.
#
#  Windows : .venv\Scripts\python.exe
#  Linux/macOS: .venv/bin/python
#
#  Başarısız olursa (yönetici izni/eksik ensurepip) sessizce sistem Python'una
#  döner — kurulum asla bu yüzden durmaz.
# ============================================================================

import os
import subprocess
import sys

BURASI = os.path.dirname(os.path.abspath(__file__))
VENV = os.path.join(BURASI, ".venv")
IS_WIN = os.name == "nt"


def venv_python():
    """Sanal ortamın python yolu (yoksa "")."""
    aday = (os.path.join(VENV, "Scripts", "python.exe") if IS_WIN
            else os.path.join(VENV, "bin", "python3"))
    if os.path.exists(aday):
        return aday
    aday2 = os.path.join(VENV, "bin", "python")
    return aday2 if os.path.exists(aday2) else ""


def var_mi():
    p = venv_python()
    if not p:
        return False
    try:
        r = subprocess.run([p, "-c", "import sys;print(sys.prefix)"],
                           capture_output=True, text=True, timeout=30)
        return VENV.replace("\\", "/") in (r.stdout or "").replace("\\", "/")
    except Exception:
        return False


def olustur(sessiz=False, paketler=("pillow",)):
    """Sanal ortamı kurar. Döner: python yolu veya "" (başarısız → sistem python)."""
    def s(m):
        if not sessiz:
            print(m)

    if var_mi():
        s(f"     ✅ sanal ortam hazır: {venv_python()}")
        return venv_python()

    # 1) venv modülü var mı? (Debian/Ubuntu'da python3-venv gerekebilir)
    try:
        r = subprocess.run([sys.executable, "-c", "import venv; print('ok')"],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise RuntimeError("venv modülü yok")
    except Exception:
        s("     ⚠️  bu Python'da venv modülü yok — sistem Python'u kullanılacak")
        if sys.platform.startswith("linux"):
            s("        (düzeltmek için: sudo apt install python3-venv)")
        return ""

    # 2) oluştur
    #    --without-pip: pip'i ensurepip ile elle kurarız (çift indirme olmasın)
    for ek in ([], ["--without-pip"]):
        try:
            s("     ⚙️  sanal ortam oluşturuluyor (.venv)…")
            cmd = [sys.executable, "-m", "venv", VENV] + ek
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode == 0 and venv_python():
                break
        except Exception as e:
            s(f"     ⚠️  {e}")
    p = venv_python()
    if not p:
        s("     ⚠️  sanal ortam oluşturulamadı — sistem Python'u kullanılacak")
        return ""

    # 3) pip'i garanti altına al
    try:
        r = subprocess.run([p, "-m", "pip", "--version"], capture_output=True,
                           text=True, timeout=120)
        if r.returncode != 0:
            subprocess.run([p, "-m", "ensurepip", "--upgrade", "--default-pip"],
                           capture_output=True, text=True, timeout=300)
    except Exception:
        pass

    # 4) paketleri venv'e kur
    ok = 0
    for pk in paketler:
        try:
            r = subprocess.run([p, "-m", "pip", "install", "--quiet",
                                "--disable-pip-version-check", pk],
                               capture_output=True, text=True, timeout=900)
            if r.returncode == 0:
                ok += 1
        except Exception:
            pass
    s(f"     ✅ sanal ortam hazır: {p}" + (f" · {ok} paket kuruldu" if ok else ""))
    s("        (silmek için klasörü silin: .venv)")
    return p


def temizle(sessiz=False):
    """Sanal ortamı siler (sistem Python'una dönülür)."""
    import shutil
    if not os.path.isdir(VENV):
        if not sessiz:
            print("  ℹ️  sanal ortam yok.")
        return False
    try:
        shutil.rmtree(VENV)
        if not sessiz:
            print(f"  ✅ silindi: {VENV}")
        return True
    except Exception as e:
        if not sessiz:
            print(f"  ❌ silinemedi: {e}")
        return False


def bilgi():
    p = venv_python()
    if not p:
        return {"var": False, "yol": "", "surum": ""}
    try:
        r = subprocess.run([p, "-c", "import sys;print(sys.version.split()[0])"],
                           capture_output=True, text=True, timeout=30)
        surum = (r.stdout or "").strip()
    except Exception:
        surum = ""
    return {"var": True, "yol": p, "surum": surum}


def main():
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "kur").lower()
    if cmd in ("kur", "olustur", "create", "setup"):
        print()
        p = olustur()
        return 0 if p else 1
    if cmd in ("sil", "kaldir", "remove"):
        return 0 if temizle() else 1
    if cmd in ("durum", "status", "bilgi"):
        b = bilgi()
        if b["var"]:
            print(f"  ✅ sanal ortam: {b['yol']} (Python {b['surum']})")
        else:
            print("  ❌ sanal ortam yok — kurmak için: python sanalortam.py kur")
        return 0
    print("Kullanım: python sanalortam.py kur | sil | durum")
    return 1


if __name__ == "__main__":
    sys.exit(main())

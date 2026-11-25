#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — exe_yap.py  ·  Tek dosya kurulum uygulaması üretir
#  Copyright (c) 2026 BTM Code — MIT License
#
#  NE YAPAR
#    Windows : dist/GhostPilot-Kurulum.exe   (tek dosya, çift tıkla çalışır)
#    macOS   : dist/GhostPilot-Kurulum       (tek dosya)
#    Linux   : dist/GhostPilot-Kurulum       (tek dosya)
#
#  ÖNEMLİ: Çapraz derleme YOKTUR. Windows .exe yalnızca Windows'ta üretilebilir.
#          Bu yüzden bu betiği kendi Windows makinenizde çalıştırın.
#
#  Kullanım:
#      pip install pyinstaller
#      python exe_yap.py
# ============================================================================

import os
import platform
import shutil
import subprocess
import sys

BURASI = os.path.dirname(os.path.abspath(__file__))

# Kurulum uygulamasına gömülecek dosyalar (kaynak kod + varlıklar)
GOMULE = [
    "ghostpilot.py", "screen.py", "kur.py", "setup.py", "lisans.py",
    "lisans_online.py", "paketler.py", "diller.py", "sanalortam.py",
    "ui.py", "kurulum_ui.py", "ikon.py", "tepsi.py", "kaldir.py",
    "input_bg.py", "goverlay.py", "belge.py",
    "GhostPilot.ico", "icon-256.png", "icon-128.png", "icon-48.png",
    "chatgpt-icon-256.png",
    "LICENSE", "COPYRIGHT", "README.md", "GIZLILIK.md", "KOSULLAR.md",
    "BASLA.bat", "PANEL.bat", "KURULUM.bat", "KALDIR.bat", "_bitis.bat",
    "basla.sh", "kurulum.sh", "GhostPilot.command",
]


def main():
    if not shutil.which("pyinstaller") and not _modul_var("PyInstaller"):
        print("  ❌ PyInstaller yok. Kurun:  pip install pyinstaller")
        return 1

    hedef_os = platform.system()
    print(f"\n  👻 GhostPilot — kurulum uygulaması üretiliyor ({hedef_os})")
    print("  " + "─" * 58)

    # ---- gömülecek dosyaları topla
    veri_arg = []
    eksik = []
    for ad in GOMULE:
        yol = os.path.join(BURASI, ad)
        if os.path.exists(yol):
            # PyInstaller sözdizimi: kaynak;hedef
            veri_arg += ["--add-data", f"{yol}{os.pathsep}."]
        else:
            eksik.append(ad)
    if eksik:
        print(f"  ⚠️  {len(eksik)} dosya bulunamadı (atlanıyor): {', '.join(eksik[:6])}"
              + (" …" if len(eksik) > 6 else ""))

    ikon = os.path.join(BURASI, "GhostPilot.ico")
    ad = "GhostPilot-Kurulum"
    komut = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile",                       # tek dosya
        "--name", ad,
        "--distpath", os.path.join(BURASI, "dist"),
        "--workpath", os.path.join(BURASI, "build_exe"),
        "--specpath", os.path.join(BURASI, "build_exe"),
        "--windowed",                      # konsol penceresi açılmasın
        "--collect-submodules", "tkinter",
        "--hidden-import", "pystray",
        "--hidden-import", "pystray._win32" if hedef_os == "Windows" else "pystray._xorg",
        "--hidden-import", "PIL",
    ] + veri_arg
    if os.path.exists(ikon):
        komut += ["--icon", ikon]
    komut.append(os.path.join(BURASI, "kurulum.py"))

    print("  PyInstaller çalışıyor… (1–3 dakika)\n")
    r = subprocess.run(komut, cwd=BURASI)
    if r.returncode != 0:
        print("\n  ❌ Derleme başarısız. Yukarıdaki hataya bakın.")
        return r.returncode

    cikti = os.path.join(BURASI, "dist",
                         ad + (".exe" if hedef_os == "Windows" else ""))
    if os.path.exists(cikti):
        boy = os.path.getsize(cikti) / (1024 * 1024)
        print("\n  " + "─" * 58)
        print(f"  ✅ HAZIR: {cikti}")
        print(f"     Boyut: {boy:.1f} MB")
        print("\n  Bu tek dosyayı kullanıcıya gönderin:")
        print("     • Çift tıklar → kurulum sihirbazı açılır")
        print("     • Klasör seçer, kurar, kısayol ekler")
        print("     • Python kurulu olmayan bilgisayarda da çalışır")
        print("  " + "─" * 58 + "\n")
        return 0
    print("  ⚠️  Derleme bitti ama çıktı bulunamadı:", cikti)
    return 1


def _modul_var(ad):
    try:
        __import__(ad)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    sys.exit(main())

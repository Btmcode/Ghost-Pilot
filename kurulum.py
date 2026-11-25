#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — kurulum.py  ·  GERÇEK KURULUM UYGULAMASI
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Neden .bat değil?
#    .bat dosyaları kırılgandır: kod sayfası, yönetici hakkı, PATH, tırnak/kaçış,
#    "çift tıkla çalışmıyor" sorunları. Kurulum mantığı Python'da olmalı;
#    .bat yalnızca Python'u bulup bu dosyayı açar.
#
#  Kullanım:
#      python kurulum.py                 → grafik kurulum (önerilen)
#      python kurulum.py --konsol        → konsol kurulumu (GUI yoksa)
#      python kurulum.py --hedef "D:\GhostPilot" --sessiz
#      python kurulum.py --onar          → kurulumu onar
#      python kurulum.py --kaldir        → kaldır
#
#  Ne yapar:
#    1) Kurulum dizinini SEÇTİRİR (varsayılan: %LOCALAPPDATA%\GhostPilot)
#    2) Dosyaları oraya kopyalar (Program Files'a yazmaz → yönetici gerekmez)
#    3) Sanal ortam kurar + bağımlılıkları yükler
#    4) Masaüstü + Başlat menüsü kısayolu + ikon
#    5) "Programlar ve Özellikler" kaydı (kaldırma için)
#    6) Lisans anahtarı sorar, sunucuyu başlatır
# ============================================================================

import os
import platform
import shutil
import subprocess
import sys
import time

import os as _os


def _kok_dizin():
    """Kaynak klasör: normal çalışmada script yanı, .exe'de _MEIPASS."""
    if getattr(sys, "frozen", False):
        # PyInstaller: veriler _MEIPASS altında; .exe'nin yanına da bak
        adaylar = [getattr(sys, "_MEIPASS", ""), os.path.dirname(sys.executable)]
        for a in adaylar:
            if a and os.path.exists(os.path.join(a, "ghostpilot.py")):
                return a
        return adaylar[0] or os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BURASI = _kok_dizin()
IS_WIN = os.name == "nt"
IS_MAC = sys.platform == "darwin"
APP = "GhostPilot"

# Kurulumla taşınacak dosyalar (kaynak kod + varlıklar)
KOPYALANACAK = [
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

BAGIMLILIKLAR = ["pillow", "pystray"]


# ===========================================================================
#  YARDIMCILAR
# ===========================================================================
def _varsayilan_dizin():
    if IS_WIN:
        taban = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
        return os.path.join(taban, APP)
    if IS_MAC:
        return os.path.join(os.path.expanduser("~"), "Applications", APP)
    return os.path.join(os.path.expanduser("~"), ".local", "share", APP.lower())


def _pythonw():
    """Windows'ta konsol açmayan python."""
    if not IS_WIN:
        return sys.executable
    p = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    return p if os.path.exists(p) else sys.executable


def _yaz(s, tur=""):
    renk = {"ok": "\033[92m", "err": "\033[91m", "warn": "\033[93m",
            "dim": "\033[2m"}.get(tur, "")
    print((renk + s + "\033[0m") if renk else s, flush=True)


def _kaynak_var_mi():
    """Zip içinden çalıştırılıyor mu? (kaynak dosyalar yoksa kurulum yapılamaz)"""
    eksik = [f for f in ("ghostpilot.py", "lisans.py", "kur.py") if not os.path.exists(os.path.join(BURASI, f))]
    return eksik


# ===========================================================================
#  KURULUM ADIMLARI
# ===========================================================================
def hedef_hazirla(hedef):
    """Dizini oluşturur, yazılabilir mi diye bakar."""
    try:
        os.makedirs(hedef, exist_ok=True)
    except Exception as e:
        return False, str(e)
    deneme = os.path.join(hedef, ".gp_yazma_testi")
    try:
        with open(deneme, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(deneme)
        return True, ""
    except Exception as e:
        return False, str(e)


def dosyalari_kopyala(hedef, ilerleme=None):
    """Kaynak dosyaları hedef dizine kopyalar."""
    kopyalanan, atlanan = 0, 0
    toplam = len(KOPYALANACAK)
    for i, ad in enumerate(KOPYALANACAK, start=1):
        kaynak = os.path.join(BURASI, ad)
        if not os.path.exists(kaynak):
            atlanan += 1
            continue
        varis = os.path.join(hedef, ad)
        try:
            if os.path.isdir(kaynak):
                shutil.copytree(kaynak, varis, dirs_exist_ok=True)
            else:
                os.makedirs(os.path.dirname(varis) or hedef, exist_ok=True)
                shutil.copy2(kaynak, varis)
            kopyalanan += 1
        except Exception:
            atlanan += 1
        if ilerleme:
            ilerleme(i, toplam, ad)
    return kopyalanan, atlanan


def _gercek_python():
    """Kurulumu yürüten GERÇEK Python (exe içinde sys.executable exe olur!)."""
    if not getattr(sys, "frozen", False):
        return sys.executable
    # 1) PATH'teki python
    for ad in ("python", "python3", "py"):
        try:
            r = subprocess.run([ad, "-c", "import sys;print(sys.executable)"],
                               capture_output=True, text=True, timeout=15)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except Exception:
            continue
    # 2) bilinen yerler
    for y in (os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Python", "Python313", "python.exe"),
              os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Python", "Python312", "python.exe")):
        if os.path.exists(y):
            return y
    return sys.executable


def sanalortam_kur(hedef, ilerleme=None):
    """Hedef dizinde .venv oluşturur + bağımlılıkları yükler."""
    vd = os.path.join(hedef, ".venv")
    py = _gercek_python()
    if ilerleme:
        ilerleme("Sanal ortam oluşturuluyor…")
    if not os.path.exists(os.path.join(vd, "Scripts" if IS_WIN else "bin",
                                       "python.exe" if IS_WIN else "python")):
        r = subprocess.run([py, "-m", "venv", vd], capture_output=True, text=True)
        if r.returncode != 0:
            return False, (r.stderr or "").strip()[-300:]
    vpy = os.path.join(vd, "Scripts" if IS_WIN else "bin",
                       "python.exe" if IS_WIN else "python")
    if not os.path.exists(vpy):
        return False, "venv oluşmadı"
    if ilerleme:
        ilerleme("Paketler yükleniyor (Pillow, pystray)…")
    r = subprocess.run([vpy, "-m", "pip", "install", "--quiet", "--disable-pip-version-check"]
                       + BAGIMLILIKLAR,
                       capture_output=True, text=True, timeout=600)
    # pip başarısız olsa da devam: program bu paketler olmadan da çalışır
    return True, ("" if r.returncode == 0 else "bazı paketler yüklenemedi (önemli değil)")


def kisayol_kur(hedef, masaustu=True, baslat_menu=True):
    """Masaüstü + Başlat menüsü kısayolu. Döner: oluşturulan yollar."""
    yapilan = []
    giris = os.path.join(hedef, "ui.py")
    if not os.path.exists(giris):
        giris = os.path.join(hedef, "ghostpilot.py")
    if IS_WIN:
        masa = os.path.join(os.environ.get("USERPROFILE") or os.path.expanduser("~"), "Desktop")
        if not os.path.isdir(masa):
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                    r"Software\Microsoft\Windows\CurrentVersion\Explorer"
                                    r"\User Shell Folders") as k:
                    masa = os.path.expandvars(winreg.QueryValueEx(k, "Desktop")[0])
            except Exception:
                pass
        ikon = os.path.join(hedef, "GhostPilot.ico")
        hedefler = []
        if masaustu and os.path.isdir(masa):
            hedefler.append(os.path.join(masa, f"{APP}.lnk"))
        if baslat_menu:
            appdata = os.environ.get("APPDATA") or ""
            bm = os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs")
            if os.path.isdir(bm):
                hedefler.append(os.path.join(bm, f"{APP}.lnk"))
        for lnk in hedefler:
            ps = (
                "$ErrorActionPreference='Stop';"
                "$s=(New-Object -ComObject WScript.Shell);"
                f"$l=$s.CreateShortcut('{lnk}');"
                f"$l.TargetPath='{_pythonw()}';"
                f"$l.Arguments='\"{giris}\"';"
                f"$l.WorkingDirectory='{hedef}';"
                f"$l.IconLocation='{ikon},0';"
                f"$l.Description='{APP} — bilgisayarınız için sessiz yardımcı';"
                "$l.WindowStyle=1;"
                "$l.Save();"
            )
            try:
                subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                                "-Command", ps], capture_output=True, text=True, timeout=90)
                if os.path.exists(lnk):
                    yapilan.append(lnk)
            except Exception:
                pass
    elif IS_MAC:
        uyg = os.path.join(os.path.expanduser("~"), "Applications")
        os.makedirs(uyg, exist_ok=True)
        cmd = os.path.join(hedef, "GhostPilot.command")
        try:
            with open(cmd, "w", encoding="utf-8") as f:
                f.write("#!/bin/bash\ncd \"$(dirname \"$0\")\"\n"
                        "exec python3 ui.py\n")
            os.chmod(cmd, 0o755)
            yapilan.append(cmd)
        except Exception:
            pass
    else:
        # Linux: .desktop
        uyg = os.path.join(os.path.expanduser("~"), ".local", "share", "applications")
        os.makedirs(uyg, exist_ok=True)
        d = os.path.join(uyg, "ghostpilot.desktop")
        try:
            with open(d, "w", encoding="utf-8") as f:
                f.write("[Desktop Entry]\nType=Application\n"
                        f"Name={APP}\nComment=Bilgisayarınız için sessiz yardımcı\n"
                        f"Exec=python3 {os.path.join(hedef, 'ui.py')}\n"
                        f"Path={hedef}\nIcon={os.path.join(hedef, 'icon-256.png')}\n"
                        "Terminal=false\nCategories=Utility;\n")
            os.chmod(d, 0o755)
            yapilan.append(d)
        except Exception:
            pass
    return yapilan


def programlar_kaydi(hedef):
    """Windows 'Programlar ve Özellikler' kaydı (yönetici gerekmez)."""
    if not IS_WIN:
        return False
    try:
        import winreg
        kaldirici = os.path.join(hedef, "kaldir.py")
        anahtar = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\%s" % APP
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, anahtar) as k:
            winreg.SetValueEx(k, "DisplayName", 0, winreg.REG_SZ,
                              "GhostPilot — bilgisayarınız için sessiz yardımcı")
            winreg.SetValueEx(k, "Publisher", 0, winreg.REG_SZ, "BTM Code")
            winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ, hedef)
            winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ,
                              f'"{_pythonw()}" "{kaldirici}" --sessiz')
            winreg.SetValueEx(k, "QuietUninstallString", 0, winreg.REG_SZ,
                              f'"{_pythonw()}" "{kaldirici}" --sessiz --tum')
            winreg.SetValueEx(k, "DisplayIcon", 0, winreg.REG_SZ,
                              os.path.join(hedef, "GhostPilot.ico"))
            try:
                surum = _surum()
            except Exception:
                surum = _surum()
            winreg.SetValueEx(k, "DisplayVersion", 0, winreg.REG_SZ, surum)
            winreg.SetValueEx(k, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(k, "NoRepair", 0, winreg.REG_DWORD, 1)
        return True
    except Exception:
        return False


# ===========================================================================
#  KONSOL KURULUMU (GUI yoksa veya --konsol)
# ===========================================================================

def _surum():
    """Sürüm TEK kaynaktan: ghostpilot.py içindeki VERSION."""
    try:
        import re
        yol = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ghostpilot.py")
        with open(yol, encoding="utf-8") as f:
            m = re.search(r'^VERSION\s*=\s*"([^"]+)"', f.read(), re.M)
        if m:
            return m.group(1)
    except Exception:
        pass
    return "?"

def konsol_kurum(hedef=None, sessiz=False):
    _yaz(f"\n  👻 GhostPilot v{_surum()} — kurulum\n  " + "─" * 54)

    eksik = _kaynak_var_mi()
    if eksik:
        _yaz(f"\n  ❌ Kurulum dosyaları eksik: {', '.join(eksik)}", "err")
        _yaz("     Zip'i açıp KLASÖRÜN İÇİNDEN çalıştırın (zip'in içinden çift tıklamayın).", "warn")
        return 1

    if not hedef:
        varsayilan = _varsayilan_dizin()
        _yaz(f"\n  Kurulum yeri: {varsayilan}")
        if not sessiz:
            try:
                c = input("  Başka bir klasör mü? (boş = bu klasör): ").strip().strip('"')
            except (EOFError, KeyboardInterrupt):
                c = ""
            if c:
                hedef = c
    hedef = os.path.abspath(hedef or _varsayilan_dizin())

    ok, hata = hedef_hazirla(hedef)
    if not ok:
        _yaz(f"\n  ❌ Bu klasöre yazılamıyor: {hata}", "err")
        _yaz("     Başka bir klasör seçin (C:\\Program Files olmaz).", "warn")
        return 1
    _yaz(f"  ✅ Kurulum yeri: {hedef}", "ok")

    # ---- dosyalar
    _yaz("\n  [1/5] Dosyalar kopyalanıyor…")
    k, a = dosyalari_kopyala(hedef, lambda i, t, ad: None)
    _yaz(f"        {k} dosya kopyalandı" + (f", {a} atlandı" if a else ""), "dim")

    # ---- venv
    _yaz("\n  [2/5] Sanal ortam ve paketler…")
    ok, mesaj = sanalortam_kur(hedef, lambda s: _yaz(f"        {s}", "dim"))
    if not ok:
        _yaz(f"        ⚠️  {mesaj} (program yine çalışır)", "warn")
    else:
        _yaz("        ✅ hazır", "dim")

    # ---- kısayol
    _yaz("\n  [3/5] Kısayollar…")
    kis = kisayol_kur(hedef)
    for x in kis:
        _yaz(f"        ✅ {x}", "dim")
    if not kis:
        _yaz("        ⚠️  kısayol oluşmadı", "warn")

    # ---- kayıt
    _yaz("\n  [4/5] Programlar listesi kaydı…")
    _yaz("        ✅ kaydedildi" if programlar_kaydi(hedef) else
         "        ℹ️  Windows dışı — kayıt gerekmiyor", "dim")

    # ---- lisans
    _yaz("\n  [5/5] Lisans")
    if not sessiz:
        _yaz("        Anahtarınız varsa yapıştırın (boş = ücretsiz plan):")
        try:
            anahtar = input("        > ").strip()
        except (EOFError, KeyboardInterrupt):
            anahtar = ""
        if anahtar:
            kod = (
                "import sys;sys.path.insert(0,%r)\n"
                "import ghostpilot as G\n"
                "r=G.lisans_ayarla(%r)\n"
                "print(('OK ' if r.get('ok') else 'HATA ')+str(r.get('message') or r.get('error')))\n"
                % (hedef, anahtar)
            )
            r = subprocess.run([sys.executable, "-c", kod], capture_output=True,
                               text=True, cwd=hedef)
            _yaz("        " + (r.stdout or r.stderr).strip()[:200],
                 "ok" if "OK" in (r.stdout or "") else "warn")

    _yaz("\n  " + "─" * 54)
    _yaz("  ✅ KURULUM TAMAM", "ok")
    _yaz(f"     Klasör   : {hedef}")
    _yaz(f"     Başlat   : masaüstündeki 👻 {APP} kısayolu")
    _yaz(f"              veya: python {os.path.join(hedef, 'ui.py')}")
    _yaz("     Kaldır   : Ayarlar → Uygulamalar → GhostPilot → Kaldır")
    _yaz("  " + "─" * 54 + "\n")
    if not sessiz:
        try:
            input("  Devam etmek için Enter… ")
        except (EOFError, KeyboardInterrupt):
            pass
    return 0


if __name__ == "__main__":
    arg = sys.argv[1:]
    hedef = None
    sessiz = "--sessiz" in arg
    if "--hedef" in arg:
        i = arg.index("--hedef")
        if i + 1 < len(arg):
            hedef = arg[i + 1]
    if "--konsol" in arg or sessiz or not IS_WIN:
        sys.exit(konsol_kurum(hedef, sessiz))
    # Windows: grafik kurulum (kurulum_gui.py)
    try:
        import kurulum_gui
        sys.exit(kurulum_gui.main(hedef))
    except Exception as e:
        _yaz(f"  ℹ️  Grafik kurulum açılamadı ({e}) — konsol kurulumuna geçiliyor", "warn")
        sys.exit(konsol_kurum(hedef, sessiz))

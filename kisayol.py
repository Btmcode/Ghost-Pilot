#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — kisayol.py   ·   Masaüstü kısayolu (Windows / Linux / macOS)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Kurulumdan sonra:
#    Windows → Masaüstü + Başlat Menüsü kısayolu (hayalet ikonlu)
#    Linux   → ~/.local/share/applications + Masaüstü (.desktop, ikonlu)
#    macOS   → Masaüstü .command kısayolu + uygulama ikonu
#
#  Kısayol "BASLA" menüsünü açar; sunucu zaten arka planda çalışır.
#  Kullanım:  python kisayol.py ekle | kaldir | durum
# ============================================================================

import os
import platform
import shutil
import subprocess
import sys

BURASI = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
SISTEM = platform.system()
IS_WIN = SISTEM == "Windows"
IS_MAC = SISTEM == "Darwin"
PY = sys.executable or ("python" if IS_WIN else "python3")
KUR = os.path.join(BURASI, "kur.py")
UI = os.path.join(BURASI, "ui.py")
IKON_ICO = os.path.join(BURASI, "GhostPilot.ico")
IKON_PNG = os.path.join(BURASI, "icon-256.png")
AD = "GhostPilot"

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def say(s="", c=""):
    kod = {"ok": "\033[92m", "warn": "\033[93m", "err": "\033[91m"}.get(c, "")
    son = "\033[0m" if kod else ""
    print(f"{kod}{s}{son}")


def _masaustu():
    """Masaüstü klasörünü bul (Türkçe/İngilizce, OneDrive dahil)."""
    adaylar = []
    if IS_WIN:
        for kn in ("USERPROFILE", "OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
            k = os.environ.get(kn)
            if k:
                adaylar += [os.path.join(k, "Desktop"), os.path.join(k, "Masaüstü")]
        adaylar += [os.path.join(HOME, "Desktop"), os.path.join(HOME, "Masaüstü")]
    else:
        adaylar += [os.path.join(HOME, "Desktop"), os.path.join(HOME, "Masaüstü"),
                    os.path.join(HOME, "Рабочий стол")]
        # XDG
        try:
            r = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True,
                               text=True, timeout=10)
            if r.returncode == 0 and (r.stdout or "").strip():
                adaylar.insert(0, r.stdout.strip())
        except Exception:
            pass
    for a in adaylar:
        if a and os.path.isdir(a):
            return a
    # yoksa oluştur (Windows/Linux)
    hedef = os.path.join(HOME, "Desktop")
    try:
        os.makedirs(hedef, exist_ok=True)
        return hedef
    except Exception:
        return ""


def _pythonw():
    """Windows'ta konsol penceresi açmayan Python (varsa)."""
    if not IS_WIN:
        return PY
    p = os.path.join(os.path.dirname(PY), "pythonw.exe")
    return p if os.path.exists(p) else PY


# ===========================================================================
#  WINDOWS — .lnk (PowerShell / WScript.Shell)
# ===========================================================================
def _win_kisayol(hedef_yol, aciklama="GhostPilot — menü ve panel"):
    # ikon yoksa kısayol yine oluşturulsun (ikon sadece görsel)

    ps = (
        "$ErrorActionPreference='Stop';"
        "$s=(New-Object -ComObject WScript.Shell);"
        f"$l=$s.CreateShortcut('{hedef_yol}');"
        f"$l.TargetPath='{_pythonw()}';"
        f"$l.Arguments='\"{UI}\"';"
        f"$l.WorkingDirectory='{BURASI}';"
        + (f"$l.IconLocation='{IKON_ICO},0';" if os.path.exists(IKON_ICO) else "") +
        f"$l.Description='{aciklama}';"
        "$l.WindowStyle=1;"
        "$l.Save();"
    )
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                            "-Command", ps], capture_output=True, text=True, timeout=90)
        return os.path.exists(hedef_yol) or r.returncode == 0
    except Exception as e:
        say(f"     ⚠️  PowerShell kısayolu oluşturamadı: {e}", "warn")
        return False


def _win_vbs(yol):
    """Yedek yöntem: ikonsuz .vbs kısayolu (PowerShell engelliyse)."""
    try:
        with open(yol, "w", encoding="utf-8", newline="\r\n") as f:
            f.write('Set sh = CreateObject("WScript.Shell")\r\n')
            f.write(f'sh.CurrentDirectory = "{BURASI}"\r\n')
            f.write(f'sh.Run """{_pythonw()}"" ""{UI}""", 1, False\r\n')
        return True
    except Exception:
        return False


def _win_ekle():
    yapilan = []
    masa = _masaustu()
    if masa:
        lnk = os.path.join(masa, "GhostPilot.lnk")
        if _win_kisayol(lnk):
            yapilan.append(("Masaüstü", lnk))
        elif _win_vbs(os.path.join(masa, "GhostPilot.vbs")):
            yapilan.append(("Masaüstü (yedek)", os.path.join(masa, "GhostPilot.vbs")))
    # Başlat menüsü
    appdata = os.environ.get("APPDATA") or os.path.join(HOME, "AppData", "Roaming")
    baslat = os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs")
    if os.path.isdir(baslat):
        lnk = os.path.join(baslat, "GhostPilot.lnk")
        if _win_kisayol(lnk, "GhostPilot — menü"):
            yapilan.append(("Başlat menüsü", lnk))
    # Görev çubuğuna sabitleme ipucu
    return yapilan


# ===========================================================================
#  LINUX — .desktop
# ===========================================================================
def _desktop_dosyasi(yol, simge_yolu):
    icerik = f"""[Desktop Entry]
Type=Application
Name=GhostPilot
Comment=Bilgisayarınız için sessiz yardımcı
Exec={PY} "{KUR}"
Path={BURASI}
Icon={simge_yolu}
Terminal=true
Categories=Utility;Development;
StartupNotify=false
"""
    with open(yol, "w", encoding="utf-8") as f:
        f.write(icerik)
    os.chmod(yol, 0o755)


def _linux_ekle():
    yapilan = []
    simge = IKON_PNG
    # ikonu simge temasına da kopyala (menüde görünmesi için)
    tema = os.path.join(HOME, ".local", "share", "icons", "hicolor", "256x256", "apps")
    try:
        os.makedirs(tema, exist_ok=True)
        kopya = os.path.join(tema, "ghostpilot.png")
        if os.path.exists(IKON_PNG):
            shutil.copy2(IKON_PNG, kopya)
            simge = "ghostpilot"
    except Exception:
        pass
    # uygulama menüsü
    uyg = os.path.join(HOME, ".local", "share", "applications")
    try:
        os.makedirs(uyg, exist_ok=True)
        yol = os.path.join(uyg, "ghostpilot.desktop")
        _desktop_dosyasi(yol, simge)
        try:
            subprocess.run(["update-desktop-database", uyg], capture_output=True, timeout=20)
        except Exception:
            pass
        yapilan.append(("Uygulama menüsü", yol))
    except Exception:
        pass
    # masaüstü
    masa = _masaustu()
    if masa:
        yol = os.path.join(masa, "GhostPilot.desktop")
        try:
            _desktop_dosyasi(yol, simge)
            # GNOME masaüstünde "güvenilir" işaretle (yoksa çift tık çalışmaz)
            try:
                subprocess.run(["gio", "set", yol, "metadata::trusted", "true"],
                               capture_output=True, timeout=15)
            except Exception:
                pass
            yapilan.append(("Masaüstü", yol))
        except Exception:
            pass
    return yapilan


# ===========================================================================
#  macOS — masaüstü .command + Dock ipucu
# ===========================================================================
def _mac_ekle():
    yapilan = []
    masa = _masaustu()
    if masa:
        yol = os.path.join(masa, "GhostPilot.command")
        try:
            with open(yol, "w", encoding="utf-8") as f:
                f.write("#!/bin/bash\n")
                f.write(f'cd "{BURASI}" || exit 1\n')
                f.write(f'"{PY}" "{KUR}"\n')
            os.chmod(yol, 0o755)
            # özel ikon (Finder) — varsa
            if os.path.exists(IKON_PNG):
                try:
                    subprocess.run(["sips", "-i", IKON_PNG, yol], capture_output=True, timeout=30)
                except Exception:
                    pass
            yapilan.append(("Masaüstü", yol))
        except Exception:
            pass
    # Uygulamalar klasörüne kısayol
    try:
        uyg = os.path.join(HOME, "Applications")
        os.makedirs(uyg, exist_ok=True)
        hedef = os.path.join(uyg, "GhostPilot.command")
        yuk = f"""#!/bin/bash
cd "{BURASI}" || exit 1
exec "{PY}" "{KUR}"
"""
        with open(hedef, "w", encoding="utf-8") as f:
            f.write(yuk)
        os.chmod(hedef, 0o755)
        yapilan.append(("~/Applications", hedef))
    except Exception:
        pass
    return yapilan


# ===========================================================================
#  ANA
# ===========================================================================
def ekle(sessiz=False):
    if IS_WIN:
        y = _win_ekle()
    elif IS_MAC:
        y = _mac_ekle()
    else:
        y = _linux_ekle()
    if not sessiz:
        if y:
            say("  ✅ Kısayollar hazır:", "ok")
            for etiket, yol in y:
                say(f"     • {etiket}: {yol}")
            if IS_WIN:
                say("     (Görev çubuğuna sabitlemek için kısayola sağ tık → 'Görev çubuğuna sabitle')")
            if not IS_WIN and not IS_MAC:
                say("     (Masaüstünde çift tıklama çalışmazsa: sağ tık → 'İzin ver / Güvenilir yap')")
        else:
            say("  ⚠️  Kısayol oluşturulamadı (masaüstü klasörü bulunamadı).", "warn")
    return y


def kaldir(sessiz=False):
    hedefler = []
    masa = _masaustu()
    for ad in ("GhostPilot.lnk", "GhostPilot.vbs", "GhostPilot.desktop",
               "GhostPilot.command", "GhostPilot"):
        if masa:
            hedefler.append(os.path.join(masa, ad))
    appdata = os.environ.get("APPDATA") or os.path.join(HOME, "AppData", "Roaming")
    hedefler += [os.path.join(appdata, "Microsoft", "Windows", "Start Menu",
                              "Programs", "GhostPilot.lnk"),
                 os.path.join(HOME, ".local", "share", "applications", "ghostpilot.desktop"),
                 os.path.join(HOME, "Applications", "GhostPilot.command")]
    sayilan = 0
    for h in hedefler:
        try:
            if os.path.isdir(h):
                shutil.rmtree(h)
                sayilan += 1
            elif os.path.exists(h):
                os.remove(h)
                sayilan += 1
        except Exception:
            pass
    if not sessiz:
        say(f"  ✅ {sayilan} kısayol kaldırıldı." if sayilan else "  ℹ️  Kısayol yoktu.")
    return sayilan


def durum():
    masa = _masaustu()
    bulundu = []
    for ad in ("GhostPilot.lnk", "GhostPilot.vbs", "GhostPilot.desktop", "GhostPilot.command"):
        if masa and os.path.exists(os.path.join(masa, ad)):
            bulundu.append(f"Masaüstü: {ad}")
    for ad in (os.path.join(HOME, ".local", "share", "applications", "ghostpilot.desktop"),
               os.path.join(HOME, "Applications", "GhostPilot.command")):
        if os.path.exists(ad):
            bulundu.append(ad)
    say("\n  Masaüstü kısayolları:")
    if bulundu:
        for b in bulundu:
            say(f"    ✅ {b}", "ok")
    else:
        say("    ❌ yok — kurmak için: python kur.py kisayol")
    return bulundu


def var_mi():
    """Sessiz kontrol: masaüstü/menü kısayolu var mı? (yazdırmaz)"""
    masa = _masaustu()
    for ad in ("GhostPilot.lnk", "GhostPilot.vbs", "GhostPilot.desktop", "GhostPilot.command"):
        if masa and os.path.exists(os.path.join(masa, ad)):
            return True
    for ad in (os.path.join(HOME, ".local", "share", "applications", "ghostpilot.desktop"),
               os.path.join(HOME, "Applications", "GhostPilot.command")):
        if os.path.exists(ad):
            return True
    return False


def main():
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "ekle").lower()
    if cmd in ("ekle", "kur", "add", "olustur", "oluştur"):
        ekle()
        return 0
    if cmd in ("kaldir", "sil", "remove"):
        kaldir()
        return 0
    if cmd in ("durum", "status", "goster", "göster"):
        durum()
        return 0
    say("Kullanım: python kisayol.py ekle | kaldir | durum")
    return 1


if __name__ == "__main__":
    sys.exit(main())

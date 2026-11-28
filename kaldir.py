#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — kaldir.py  ·  KALDIRMA (Windows / Linux / macOS)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Windows : "Programlar ve Özellikler" (Ayarlar → Uygulamalar) listesine kaydolur
#            ve oradan kaldırılabilir.  KALDIR.bat da aynı işi yapar.
#  Linux   : uygulama menüsü + masaüstü kısayolları silinir
#  macOS   : masaüstü/~/Applications kısayolları silinir
#
#  GÜVENLİK KİLİDİ: bir klasörün "kurulu GhostPilot" sayılması için içinde
#  şu dosyaların OLMASI gerekir: ghostpilot.py + lisans.py + kur.py.
#  Sadece kaldir.py kopyalanmış bir klasör ASLA silinmez (geliştirici kazası).
#
#  Kullanım:
#    python kaldir.py            → sorularak kaldır (güvenli)
#    python kaldir.py --tum      → ayarlar + lisans dahil HER ŞEYİ sil
#    python kaldir.py --sessiz   → soru sormadan (Programlar'daki Kaldır)
#    python kaldir.py kaydet     → "Programlar" listesine kayıt (kurulumda çağrılır)
#    python kaldir.py durum      → ne kurulu, ne kayıtlı?
# ============================================================================

import os
import platform
import shutil
import subprocess
import sys
import time

BURASI = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
CFG_DIR = os.path.join(HOME, ".ghostpilot")
SISTEM = platform.system()
IS_WIN = SISTEM == "Windows"
IS_MAC = SISTEM == "Darwin"

KAYIT_YOLU = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\GhostPilot"
AD = "GhostPilot"
# Kurulu sayılmak için ZORUNLU dosyalar
KURULU_ISARETLERI = ("ghostpilot.py", "lisans.py", "kur.py")

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def say(s="", c=""):
    kod = {"ok": "\033[92m", "warn": "\033[93m", "err": "\033[91m", "dim": "\033[2m"}.get(c, "")
    print(f"{kod}{s}\033[0m" if kod else s)


def kurulu_mu(yol=None):
    """Bu klasör gerçekten kurulu bir GhostPilot mu? (silme güvenlik kilidi)"""
    yol = yol or BURASI
    if not os.path.isdir(yol):
        return False
    return all(os.path.exists(os.path.join(yol, f)) for f in KURULU_ISARETLERI)


def _surum():
    try:
        sys.path.insert(0, BURASI)
        import ghostpilot as G
        return G.VERSION
    except Exception:
        return "5.11.0"


def _boyut():
    t = 0
    for kok, _, dos in os.walk(BURASI):
        for d in dos:
            try:
                t += os.path.getsize(os.path.join(kok, d))
            except Exception:
                pass
    return max(1, int(t / 1024))


# ===========================================================================
#  WINDOWS — "Programlar ve Özellikler" kaydı
# ===========================================================================
def kaydet(sessiz=False):
    if not IS_WIN:
        if not sessiz:
            say("  ℹ️  Bu işletim sisteminde kayıt gerekmez.")
        return False
    if not kurulu_mu():
        if not sessiz:
            say("  ⚠️  Bu klasör kurulu bir GhostPilot değil — kayıt yapılmadı.", "warn")
        return False
    try:
        import winreg
        ikon = os.path.join(BURASI, "GhostPilot.ico")
        py = sys.executable
        if not py.lower().endswith(".exe"):
            cand = shutil.which("pythonw") or shutil.which("python")
            py = cand or py
        kaldirici = os.path.join(BURASI, "kaldir.py")
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, KAYIT_YOLU, 0,
                                winreg.KEY_WRITE) as k:
            for ad, d in [
                ("DisplayName", f"{AD} — bilgisayarınız için sessiz yardımcı"),
                ("DisplayVersion", _surum()),
                ("Publisher", "BTM Code"),
                ("DisplayIcon", ikon if os.path.exists(ikon) else py),
                ("InstallLocation", BURASI),
                ("InstallDate", time.strftime("%Y%m%d")),
                ("EstimatedSize", _boyut()),
                ("UninstallString", f'"{py}" "{kaldirici}" --sessiz'),
                ("QuietUninstallString", f'"{py}" "{kaldirici}" --sessiz --tum'),
                ("URLInfoAbout", "https://btmcode.vercel.app"),
                ("HelpLink", "https://github.com/Btmcode/Ghost-Pilot"),
                ("NoModify", 1),
                ("NoRepair", 1),
            ]:
                tip = winreg.REG_DWORD if isinstance(d, int) else winreg.REG_SZ
                winreg.SetValueEx(k, ad, 0, tip, d)
        if not sessiz:
            say("  ✅ 'Programlar ve Özellikler' listesine kaydedildi.", "ok")
            say("     Ayarlar → Uygulamalar → GhostPilot → Kaldır")
        return True
    except Exception as e:
        if not sessiz:
            say(f"  ⚠️  Kayıt yapılamadı: {e}", "warn")
        return False


def kayit_sil(sessiz=False):
    if not IS_WIN:
        return False
    try:
        import winreg
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, KAYIT_YOLU)
        if not sessiz:
            say("  ✅ 'Programlar' listesi kaydı silindi.", "ok")
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        if not sessiz:
            say(f"  ⚠️  Kayıt silinemedi: {e}", "warn")
        return False


def kayit_var():
    if not IS_WIN:
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KAYIT_YOLU):
            return True
    except Exception:
        return False


# ===========================================================================
#  KALDIRMA ADIMLARI
# ===========================================================================
def _calistir(args, zaman=120):
    try:
        return subprocess.run(args, capture_output=True, text=True,
                              timeout=zaman).returncode
    except Exception:
        return 1


def _venv_py():
    aday = (os.path.join(BURASI, ".venv", "Scripts", "python.exe") if IS_WIN
            else os.path.join(BURASI, ".venv", "bin", "python3"))
    return aday if os.path.exists(aday) else sys.executable


def sunucuyu_durdur():
    ok = False
    try:
        if _calistir([_venv_py(), os.path.join(BURASI, "kur.py"), "kapat"]) == 0:
            ok = True
    except Exception:
        pass
    # bekçinin ısrar etmemesi için bayrak (kaldırmada şart)
    try:
        os.makedirs(CFG_DIR, exist_ok=True)
        open(os.path.join(CFG_DIR, "stopped"), "w").close()
    except Exception:
        pass
    # kalan süreçler
    try:
        if IS_WIN:
            subprocess.run(["taskkill", "/F", "/FI", "WINDOWTITLE eq GhostPilot*"],
                           capture_output=True)
        else:
            subprocess.run(["pkill", "-f", "ghostpilot.py"], capture_output=True)
    except Exception:
        pass
    say("  ✅ Sunucu ve bekçi durduruldu." if ok else "  ℹ️  Sunucu zaten kapalıydı.")
    return True


def otomatik_baslatma_sil():
    silinen = []
    try:
        appdata = os.environ.get("APPDATA") or os.path.join(HOME, "AppData", "Roaming")
        bas = os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs",
                           "Startup")
        for ad in ("GhostPilot.vbs", "GhostPilot.lnk"):
            p = os.path.join(bas, ad)
            if os.path.exists(p):
                os.remove(p)
                silinen.append(p)
    except Exception:
        pass
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run",
                            0, winreg.KEY_ALL_ACCESS) as k:
            winreg.DeleteValue(k, AD)
            silinen.append("Run\\GhostPilot")
    except Exception:
        pass
    try:
        p = os.path.join(HOME, ".config", "autostart", "ghostpilot.desktop")
        if os.path.exists(p):
            os.remove(p)
            silinen.append(p)
    except Exception:
        pass
    try:
        p = os.path.join(HOME, "Library", "LaunchAgents", "com.btmcode.ghostpilot.plist")
        if os.path.exists(p):
            subprocess.run(["launchctl", "unload", p], capture_output=True, timeout=20)
            os.remove(p)
            silinen.append(p)
    except Exception:
        pass
    say(f"  ✅ Otomatik başlatma kaldırıldı ({len(silinen)} kayıt)." if silinen
        else "  ℹ️  Otomatik başlatma kaydı yoktu.")
    return silinen


def kisayollari_sil():
    try:
        import kisayol
        n = kisayol.kaldir(sessiz=True)
        say(f"  ✅ {n} kısayol silindi." if n else "  ℹ️  Kısayol yoktu.")
        return n
    except Exception as e:
        say(f"  ℹ️  Kısayol temizliği: {e}")
        return 0


def sanalortam_sil():
    p = os.path.join(BURASI, ".venv")
    if os.path.isdir(p):
        shutil.rmtree(p, ignore_errors=True)
        say("  ✅ Sanal ortam (.venv) silindi.")
        return True
    return False


def ayarlari_sil():
    n = 0
    for p in (CFG_DIR, os.path.join(HOME, ".ghostpilot_kayit")):
        try:
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
                n += 1
            elif os.path.exists(p):
                os.remove(p)
                n += 1
        except Exception:
            pass
    say(f"  ✅ Ayarlar ve lisans bilgisi silindi ({n})." if n
        else "  ℹ️  Silinecek ayar bulunamadı.")
    return n


def klasoru_sil():
    """Kurulum klasörünü siler — KURULU DEĞİLSE ASLA SİLMEZ."""
    if not kurulu_mu():
        say("  🛑 GÜVENLİK: bu klasör kurulu bir GhostPilot değil — silinmedi.", "err")
        say(f"     Klasör: {BURASI}")
        say("     (Silmeniz gerekiyorsa elle silin.)", "dim")
        return False
    if os.path.abspath(BURASI) in ("/", "/home", "/root", os.path.expanduser("~")):
        say("  🛑 GÜVENLİK: kök klasör silinemez.", "err")
        return False
    if IS_WIN:
        gecici = os.path.join(os.environ.get("TEMP") or "C:\\Windows\\Temp",
                              "gp_kaldir.bat")
        try:
            with open(gecici, "w", encoding="utf-8", newline="\r\n") as f:
                f.write("@echo off\r\n")
                f.write("timeout /t 3 /nobreak >nul\r\n")
                f.write(f'rmdir /s /q "{BURASI}" 2>nul\r\n')
                f.write('del "%~f0" >nul 2>nul\r\n')
            subprocess.Popen(["cmd", "/c", gecici],
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            say("  ✅ Kurulum klasörü siliniyor (3 saniye içinde).")
            return True
        except Exception as e:
            say(f"  ⚠️  Otomatik silinemedi: {e}", "warn")
            say(f"     Elle silin: {BURASI}")
            return False
    try:
        gecici = os.path.join("/tmp", "gp_kaldir.sh")
        with open(gecici, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\nsleep 2\n")
            f.write(f'rm -rf "{BURASI}"\n')
            f.write('rm -f "$0"\n')
        os.chmod(gecici, 0o755)
        subprocess.Popen(["/bin/sh", gecici], start_new_session=True)
        say("  ✅ Kurulum klasörü siliniyor.")
        return True
    except Exception as e:
        say(f"  ⚠️  Silinemedi: {e}", "warn")
        say(f"     Elle silin: rm -rf \"{BURASI}\"")
        return False


# ===========================================================================
#  ANA
# ===========================================================================
def durum():
    print()
    print("  👻 GhostPilot — kaldırma durumu")
    print("  " + "─" * 56)
    print(f"  Kurulum klasörü : {BURASI}")
    print(f"  Kurulu mu       : {'EVET ✓' if kurulu_mu() else 'HAYIR (bu bir kurulum değil)'}")
    print(f"  Ayarlar         : {CFG_DIR} {'(var)' if os.path.isdir(CFG_DIR) else '(yok)'}")
    print(f"  Sanal ortam     : {'var' if os.path.isdir(os.path.join(BURASI,'.venv')) else 'yok'}")
    if IS_WIN:
        print(f"  Program listesi : {'KAYITLI ✓' if kayit_var() else 'kayıtlı değil'}")
    try:
        import kisayol
        print(f"  Kısayol         : {'var' if kisayol.var_mi() else 'yok'}")
    except Exception:
        pass
    print()
    return 0


def kaldir(tum=False, sessiz=False):
    if not kurulu_mu():
        say("\n  🛑 Bu klasör kurulu bir GhostPilot değil — kaldırma iptal edildi.", "err")
        say(f"     {BURASI}")
        say("     Bu koruma, yanlış klasörün silinmesini engeller.", "dim")
        return 1
    if not sessiz:
        print()
        say("  👻 GhostPilot kaldırılıyor", "ok")
        say("  " + "─" * 56)
    sunucuyu_durdur()
    otomatik_baslatma_sil()
    kisayollari_sil()
    if IS_WIN:
        kayit_sil(sessiz=True)
    sanalortam_sil()
    for kok, dirs, _ in os.walk(BURASI):
        for d in list(dirs):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(kok, d), ignore_errors=True)
                dirs.remove(d)
    if not tum and not sessiz:
        try:
            c = input("\n  Ayarlar ve lisans bilgisi de silinsin mi? (e/H): ")
        except (EOFError, KeyboardInterrupt):
            c = ""
        tum = c.strip().lower() in ("e", "y", "evet", "yes")
    if tum:
        ayarlari_sil()
    else:
        say("  ℹ️  Ayarlar korundu (~/.ghostpilot) — yeniden kurarsanız lisans durur.")
    if not sessiz:
        try:
            c = input("\n  Kurulum klasörü de silinsin mi? (e/H): ")
        except (EOFError, KeyboardInterrupt):
            c = ""
        if c.strip().lower() in ("e", "y", "evet", "yes"):
            klasoru_sil()
        else:
            say(f"  ℹ️  Klasör korundu: {BURASI}")
    else:
        klasoru_sil()
    say("\n  ✅ GhostPilot kaldırıldı. İyi günler! 👋\n", "ok")
    return 0


def main():
    arg = [a.lower() for a in sys.argv[1:]]
    if "kaydet" in arg or "register" in arg:
        return 0 if kaydet() else 1
    if "durum" in arg or "status" in arg:
        return durum()
    if "kayit-sil" in arg:
        return 0 if kayit_sil() else 1
    return kaldir(tum=("--tum" in arg or "--all" in arg),
                  sessiz=("--sessiz" in arg or "--quiet" in arg))


if __name__ == "__main__":
    sys.exit(main())

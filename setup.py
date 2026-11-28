#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — setup.py   ·   TEK KURULUM BEYNİ (Windows / Linux / macOS)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Bu dosya hangi işletim sisteminde olduğunu KENDİSİ anlar ve eksikleri
#  kendisi kurar. Giriş dosyaları yalnızca birer "kapı"dır:
#      KURULUM.bat   → Windows  (çift tık)
#      kurulum.sh    → Linux / macOS (çift tık / ./kurulum.sh)
#      python setup.py  → üçünde de elle
#
#  Adımlar: 0 algıla · 1 Python · 2 pip+Pillow · 3 tünel · 4 yapılandırma
#           5 sunucu · 6 otomatik başlatma · 7 özet
# ============================================================================

import os
import platform
import shutil
import subprocess
import sys
import time

# Windows konsolu cp1254 kullanır; emoji yazınca UnicodeEncodeError çöker.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

BURASI = os.path.dirname(os.path.abspath(__file__))
KUR = os.path.join(BURASI, "kur.py")
HOME = os.path.expanduser("~")
SISTEM = platform.system()               # Windows | Linux | Darwin
IS_WIN = SISTEM == "Windows"
IS_MAC = SISTEM == "Darwin"
IS_LINUX = SISTEM == "Linux"

PY_MIN = (3, 8)
PY_SURUM = "3.13.7"
URL = {
    "py_win": f"https://www.python.org/ftp/python/{PY_SURUM}/python-{PY_SURUM}-amd64.exe",
    "py_mac": f"https://www.python.org/ftp/python/{PY_SURUM}/python-{PY_SURUM}-macos11.pkg",
    "pip": "https://bootstrap.pypa.io/get-pip.py",
}
GECICI = os.environ.get("TEMP") or os.environ.get("TMPDIR") or "/tmp"

C = {"ok": "\033[92m", "warn": "\033[93m", "err": "\033[91m", "dim": "\033[2m",
     "bas": "\033[1m", "end": "\033[0m"}
if IS_WIN and not os.environ.get("WT_SESSION"):
    C = {k: "" for k in C}


def say(s="", c=""):
    print(f"{C.get(c,'')}{s}{C['end']}")


def head(s):
    say("\n" + "═" * 64, "dim")
    say(f"  {s}", "bas")
    say("═" * 64, "dim")


def adim(n, s):
    say(f"\n  [{n}] {s}", "ok")


def bekle(sn):
    time.sleep(sn)


# ===========================================================================
#  0 · SİSTEMİ TANIMA
# ===========================================================================
def sistem_bilgi():
    m = platform.machine().lower()
    mimari = "arm64" if m in ("arm64", "aarch64") else ("x64" if "64" in m else m or "?")
    ad = {"Windows": "Windows", "Darwin": "macOS", "Linux": "Linux"}.get(SISTEM, SISTEM)
    say(f"\n  🖥️  Sistem algılandı: {ad} · {mimari} · Python {platform.python_version()}")
    if not (IS_WIN or IS_MAC or IS_LINUX):
        say(f"  ⚠️  {SISTEM} test edilmedi — yine de deneyeceğim.", "warn")
    return {"os": SISTEM, "ad": ad, "mimari": mimari,
            "linux_paket": _linux_paket_yoneticisi()}


def _linux_paket_yoneticisi():
    for a, ad in (("apt-get", "debian"), ("dnf", "fedora"), ("yum", "rhel"),
                  ("pacman", "arch"), ("zypper", "suse"), ("apk", "alpine")):
        if shutil.which(a):
            return ad
    return ""


# ===========================================================================
#  1 · PYTHON
# ===========================================================================
def python_surum():
    adaylar = [[sys.executable or "python3"]]
    if IS_WIN:
        adaylar += [["py", "-3"], ["python"], ["python3"]]
    else:
        adaylar += [["python3"], ["python"]]
    for cmd in adaylar:
        try:
            r = subprocess.run(cmd + ["-c", "import sys;print('%d.%d.%d' % sys.version_info[:3])"],
                               capture_output=True, text=True, timeout=20)
            out = (r.stdout or "").strip()
            if r.returncode == 0 and out.count(".") == 2:
                if tuple(int(x) for x in out.split(".")) >= PY_MIN:
                    return {"ok": True, "surum": out, "yol": cmd}
        except Exception:
            pass
    return {"ok": False, "surum": "", "yol": []}


def _sudo(cmd):
    """Gerekirse sudo ile çalıştır (Linux)."""
    if os.name == "posix" and os.geteuid() != 0 and shutil.which("sudo"):
        return subprocess.run(["sudo"] + cmd, timeout=1800)
    return subprocess.run(cmd, timeout=1800)


def python_kur(s):
    say("     Python yok → otomatik kurulum başlıyor…", "warn")
    if IS_WIN:
        hedef = os.path.join(GECICI, "gpython-setup.exe")
        try:
            _indir(URL["py_win"], hedef, 25)
            say("     ⚙️  kuruluyor — Windows izin penceresi çıkarsa 'Evet' deyin…")
            subprocess.run([hedef, "/passive", "InstallAllUsers=0", "PrependPath=1",
                            "Include_pip=1", "Include_launcher=1", "Include_test=0",
                            "Shortcuts=0"], timeout=1800)
            _sil(hedef)
            return python_surum()["ok"]
        except Exception as e:
            say(f"     ❌ {e}", "err")
            return False

    if IS_MAC:
        try:
            hedef = os.path.join(GECICI, "gpython.pkg")
            _indir(URL["py_mac"], hedef, 45)
            say("     ⚙️  kuruluyor — macOS parolanızı sorabilir…")
            _sudo(["installer", "-pkg", hedef, "-target", "/"])
            _sil(hedef)
            for p in ("/usr/local/bin/python3", "/Library/Frameworks/Python.framework/Versions/Current/bin/python3"):
                if os.path.exists(p):
                    return True
            return python_surum()["ok"]
        except Exception as e:
            say(f"     ❌ {e}", "err")
            say("     Elle: https://www.python.org/downloads/macos/", "warn")
            return False

    # Linux
    pk = s.get("linux_paket") or ""
    komutlar = {
        "debian": [["apt-get", "update", "-y"], ["apt-get", "install", "-y", "python3", "python3-pip", "python3-venv"]],
        "fedora": [["dnf", "install", "-y", "python3", "python3-pip"]],
        "rhel": [["yum", "install", "-y", "python3", "python3-pip"]],
        "arch": [["pacman", "-Sy", "--noconfirm", "python", "python-pip"]],
        "suse": [["zypper", "install", "-y", "python3", "python3-pip"]],
        "alpine": [["apk", "add", "python3", "py3-pip"]],
    }.get(pk, [])
    for cmd in komutlar:
        try:
            say(f"     ⚙️  {' '.join(cmd)}")
            _sudo(cmd)
        except Exception as e:
            say(f"     ⚠️  {e}", "warn")
    if python_surum()["ok"]:
        return True
    if shutil.which("brew"):
        try:
            subprocess.run(["brew", "install", "python3"], timeout=1800)
            return python_surum()["ok"]
        except Exception:
            pass
    say("     Elle: paket yöneticinizden python3 kurun (sudo apt install python3)", "warn")
    return False


# ===========================================================================
#  2 · pip + Pillow
# ===========================================================================
def pip_kur(py_cmd):
    try:
        if subprocess.run([py_cmd, "-m", "pip", "--version"], capture_output=True,
                          text=True, timeout=60).returncode == 0:
            return True
    except Exception:
        pass
    say("     pip yok → kuruluyor…", "warn")
    try:
        gp = os.path.join(GECICI, "get-pip.py")
        _indir(URL["pip"], gp, 2)
        subprocess.run([py_cmd, gp, "--quiet", "--disable-pip-version-check"], timeout=600)
        _sil(gp)
        return subprocess.run([py_cmd, "-m", "pip", "--version"], capture_output=True,
                              text=True, timeout=60).returncode == 0
    except Exception as e:
        say(f"     ⚠️  pip kurulamadı: {e}", "warn")
        return False


def pillow_kur(py_cmd):
    try:
        r = subprocess.run([py_cmd, "-c", "import PIL;print(PIL.__version__)"],
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    if not pip_kur(py_cmd):
        return ""
    say("     ekran görüntüsü için Pillow kuruluyor (~3 MB)…", "dim")
    for ek in ([], ["--user"], ["--break-system-packages"]):
        try:
            subprocess.run([py_cmd, "-m", "pip", "install", "--quiet",
                            "--disable-pip-version-check"] + ek + ["pillow"], timeout=600)
            r = subprocess.run([py_cmd, "-c", "import PIL;print(PIL.__version__)"],
                               capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                return r.stdout.strip()
        except Exception:
            continue
    say("     ⚠️  Pillow kurulamadı — ekran görüntüsü sınırlı çalışır.", "warn")
    return ""


# ===========================================================================
#  3 · TÜNEL (ssh — ek program yok)
# ===========================================================================
# ===========================================================================
#  yardımcılar
# ===========================================================================
def _indir(url, hedef, mb=None):
    import urllib.request
    etiket = f" (~{mb} MB)" if mb else ""
    say(f"     ⬇️  indiriliyor{etiket}")
    try:
        with urllib.request.urlopen(url, timeout=120) as r, open(hedef, "wb") as f:
            toplam = int(r.headers.get("Content-Length") or 0)
            inen = 0
            son = 0
            while True:
                parca = r.read(262144)
                if not parca:
                    break
                f.write(parca)
                inen += len(parca)
                if toplam and time.time() - son > 2:
                    son = time.time()
                    say(f"\r        %{100*inen/toplam:.0f}  ({inen/1048576:.1f} MB)", "dim")
    except Exception as e:
        raise RuntimeError(f"indirme başarısız: {e}")
    return hedef


def _sil(yol):
    try:
        os.remove(yol)
    except Exception:
        pass


def _internet(host="www.python.org"):
    import socket
    try:
        socket.create_connection((host, 443), timeout=8).close()
        return True
    except Exception:
        return False


def _py_caliştir(args):
    """kur.py'yi doğru Python ile çağır."""
    p = python_surum()
    cmd = (p["yol"] if p["ok"] else [sys.executable]) + [KUR] + args
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1",
               GP_SETUP_TARAFINDAN="1", GP_VENV_PY=sys.executable)
    return subprocess.call(cmd, env=env)


# ===========================================================================
#  ANA AKIŞ
# ===========================================================================
def main(argv=None):
    argv = argv or sys.argv[1:]
    elle = "--elle" in argv          # elle adım adım (isteğe bağlı)
    say("")
    say("  👻  G h o s t P i l o t   ·   Tek Tık Kurulum", "bas")
    say("  Bilgisayarınız için sessiz yardımcı. Sizden teknik bilgi istemez.")

    s = sistem_bilgi()

    if not _internet():
        say("\n  ❌ İnternet bağlantısı yok. Bağlanıp tekrar çalıştırın.", "err")
        return 2

    basarili = True
    TOPLAM = 7

    # 1 — Python
    adim("1", "Python")
    p = python_surum()
    if not p["ok"]:
        python_kur(s)
        p = python_surum()
    if not p["ok"]:
        say("  ❌ Python kurulamadı.", "err")
        if IS_WIN:
            say("     Bilgisayarı kapatıp açın, KURULUM.bat'a tekrar çift tıklayın.", "warn")
        else:
            say("     Elle kurun: https://www.python.org/downloads/", "warn")
        return 1
    py = p["yol"][0]
    say(f"     ✅ Python {p['surum']}", "ok")

    # 2 — Sanal ortam (sistem Python'u kirlenmesin)
    adim("2", "Sanal ortam (.venv)")
    venv_py = ""
    try:
        import sanalortam
        venv_py = sanalortam.olustur(sessiz=True)
    except Exception as e:
        say(f"     ⚠️  {e}", "warn")
    if venv_py:
        say(f"     ✅ izole kurulum: {venv_py}", "ok")
        py = venv_py                      # bundan sonra venv Python'u kullanılır
    else:
        say("     ℹ️  sanal ortam kurulamadı — sistem Python'u kullanılacak", "warn")

    # 3 — pip + Pillow
    adim("3", "Gerekli ek paketler (pip · Pillow)")
    ok_pip = pip_kur(py)
    pv = pillow_kur(py) if ok_pip else ""
    say(f"     {'✅' if ok_pip else '⚠️ '} pip  ·  "
        f"{'✅ Pillow ' + pv if pv else '⚠️  Pillow yok'}", "ok" if (ok_pip and pv) else "warn")

    # 3 — Tünel (ssh; ek program GEREKMEZ)
    adim("4", "HTTPS tüneli (ssh — ek program gerekmez)")
    import shutil as _sh
    if _sh.which("ssh"):
        say("     hazır — tünel kurulum sonrası tek komutla açılır", "ok")
    else:
        say("     ssh yok — yerel ağ (192.168.x.x) kullanılabilir", "warn")

    # 4 — Yapılandırma + erişim anahtarı (kur.py yapar)
    adim("5", "Yapılandırma · sunucu · otomatik başlatma")
    rc = _py_caliştir(["oto"])
    if rc != 0:
        basarili = False

    # 5-7 kur.py oto() içinde; burada kapanış özeti
    # "Programlar ve Özellikler" listesine kayıt (kaldırma için)
    try:
        import kaldir as _KAL
        if _KAL.kaydet(sessiz=True):
            say("  🗑️  Kaldırma kaydı: Ayarlar → Uygulamalar → GhostPilot", "ok")
    except Exception:
        pass

    # masaüstü kısayolu (kur.py yapmış olabilir; yoksa burada kurulur)
    try:
        import kisayol as _KS
        if not _KS.var_mi():
            y = _KS.ekle(sessiz=True)
            if y:
                say(f"  🖥️  Masaüstü kısayolu: {y[0][1]}", "ok")
        else:
            say("  🖥️  Masaüstü kısayolu hazır", "ok")
    except Exception as e:
        say(f"  ⚠️  kısayol: {e}", "warn")

    ozet = os.path.join(BURASI, "KURULUM-OZET.txt")
    say("")
    say("═" * 64, "dim")
    if os.path.exists(ozet):
        say("  ✅ KURULUM TAMAM — ChatGPT'ye eklenecek bilgiler:", "ok")
        say("═" * 64, "dim")
        try:
            for satir in open(ozet, encoding="utf-8").read().splitlines():
                if satir.strip() and not satir.startswith("="):
                    say("  " + satir)
        except Exception:
            pass
        say("")
        say(f"  📄 Aynı bilgiler: {ozet}", "dim")
    else:
        say("  ℹ️  Durum özeti:", "warn")
        _py_caliştir(["durum"])
        say("")
        say("  Eksik varsa yukarıda yazıyor. Bu dosyayı tekrar çalıştırmak", "dim")
        say("  güvenlidir — ayarlarınız ve anahtarınız SİLİNMEZ.", "dim")
        basarili = False
    say("═" * 64, "dim")
    say("")
    if IS_WIN:
        say("  Menü: BASLA.bat   ·   Panel: PANEL.bat")
    else:
        say("  Menü: ./basla.sh   ·   Panel: python kur.py panel")
    say("  Kullanım:      python kur.py kota")
    say("")
    return 0 if basarili else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        say("\n  İptal edildi. Hiçbir değişiklik yapılmadı.", "warn")
        sys.exit(130)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — kur.py  (Windows / Linux / macOS)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Ne yapar?  Sohbet asistanı programını bilgisayarınıza bağlar. Tek komut.
#
#    python kur.py            → arayüz (menü)
#    python kur.py claude     → Claude Desktop'a kendini kaydeder
#    python kur.py chatgpt    → ChatGPT / tarayıcı AI için uzak köprü
#    python kur.py doctor     → denetim
#    python kur.py token      → yeni erişim anahtarı
#    python kur.py kaldir     → kaydı geri alır
# ============================================================================

import json
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

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "ghostpilot.py")
OS_NAME = platform.system()
IS_WIN = OS_NAME == "Windows"
HOME = os.path.expanduser("~")
PY = (os.environ.get("GP_VENV_PY")
      or (sys.executable if sys.executable else ("python" if IS_WIN else "python3")))

STOP_FILE = os.path.join(HOME, ".ghostpilot", "stopped")
C = {"ok": "\033[92m", "warn": "\033[93m", "err": "\033[91m", "dim": "\033[2m", "end": "\033[0m"}
if IS_WIN and not os.environ.get("WT_SESSION"):
    C = {k: "" for k in C}


def say(s="", c=""):
    print(f"{C.get(c,'')}{s}{C['end']}")


_SETUP_ALT = bool(os.environ.get("GP_SETUP_TARAFINDAN"))


def head(s):
    if _SETUP_ALT:                      # setup.py zaten başlık attı
        say("")
        return
    say("\n" + "=" * 60, "dim")
    say(f"  {s}")
    say("=" * 60, "dim")


def step(n, s):
    if _SETUP_ALT:                      # "1/7" yerine sade madde işareti
        say(f"\n     • {s}", "ok")
        return
    say(f"\n  {n}  {s}", "ok")


def py(args, capture=True):
    """ghostpilot.py'yi çalıştırır. Çıktı BOŞSA hatayı da yazdırır (sessiz çökme olmasın)."""
    cmd = [PY, SERVER] + args
    if not capture:
        return subprocess.Popen(cmd)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=180, env=env)
    except subprocess.TimeoutExpired:
        return type("R", (), {"returncode": 1, "stdout": "",
                              "stderr": "zaman aşımı (180 sn)"})()
    out = (r.stdout or "").strip()
    if not out:
        err = (r.stderr or "").strip()
        return type("R", (), {"returncode": r.returncode, "stdout": (
            "\n  ⚠️  ghostpilot.py çıktı vermedi.\n"
            f"     komut    : {' '.join(cmd)}\n"
            f"     çıkış kodu: {r.returncode}\n"
            f"     hata     : {err[:800] or '(hata metni yok)'}\n"
        ), "stderr": err})()
    return r


# ============================================================================
#  GEREKSİNİMLER — eksikse KENDİSİ İNDİRİP KURAR
#  Python · pip · Pillow · Tailscale
#  Hiçbir adımda kullanıcıdan terminal bilgisi istenmez.
# ============================================================================

PY_MIN = (3, 8)
PY_SURUM = "3.13.7"          # Windows'ta kurulacak sürüm
TS_INDIRME = "https://tailscale.com/download/windows"
TS_MSI = "https://pkgs.tailscale.com/stable/tailscale-setup-latest-amd64.msi"


def _internet_var(host="www.python.org", port=443, sn=6):
    try:
        import socket
        socket.create_connection((host, port), timeout=sn).close()
        return True
    except Exception:
        return False


def python_surum():
    """>{{'ok':bool,'surum':str,'yol':str}} — çalışan Python yeterli mi? (Windows'ta py -3 de denenir)"""
    adaylar = []
    if PY:
        adaylar.append([PY])
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
                u = tuple(int(x) for x in out.split("."))
                if u >= PY_MIN + (0,):
                    return {"ok": True, "surum": out, "yol": " ".join(cmd)}
        except Exception:
            continue
    return {"ok": False, "surum": "", "yol": ""}


def python_kur(sessiz=True):
    """Python yoksa indirip kurar. Windows: python.org amd64 exe (PATH'e ekler)."""
    say("     Python bulunamadı — otomatik kurulum başlıyor…", "warn")
    if not _internet_var():
        say("     ❌ İnternet yok. https://python.org/downloads adresinden kurun.", "err")
        return False
    if IS_WIN:
        hedef = os.path.join(os.environ.get("TEMP") or "/tmp", "gpython-setup.exe")
        url = f"https://www.python.org/ftp/python/{PY_SURUM}/python-{PY_SURUM}-amd64.exe"
        try:
            import urllib.request
            say(f"     ⬇️  indiriliyor: Python {PY_SURUM} (~25 MB, 1-2 dakika)")
            urllib.request.urlretrieve(url, hedef)
            say("     ⚙️  kuruluyor (pencere açılırsa 'Install Now' deyin)…")
            args = [hedef, "/passive", "InstallAllUsers=0", "PrependPath=1",
                    "Include_pip=1", "Include_launcher=1", "Include_test=0",
                    "AssociateFiles=1", "Shortcuts=0"]
            r = subprocess.run(args, timeout=900)
            try:
                os.remove(hedef)
            except Exception:
                pass
            if python_surum()["ok"]:
                say(f"     ✅ Python kuruldu: {python_surum()['surum']}", "ok")
                return True
            say("     ⚠️  Kurulum bitti ama Python hâlâ görünmüyor. "
                "Bilgisayarı kapatıp açın, sonra tekrar çalıştırın.", "warn")
            return False
        except Exception as e:
            say(f"     ❌ Otomatik kurulum olmadı: {e}", "err")
            say("     Elle: https://python.org/downloads → 'Add python.exe to PATH' işaretle.", "warn")
            return False
    # macOS / Linux
    if OS_NAME == "Darwin":
        if shutil.which("brew"):
            subprocess.run(["brew", "install", "python3"], timeout=1800)
            return python_surum()["ok"]
        say("     Elle: https://python.org/downloads", "warn")
        return False
    for cmd in (["apt-get", "install", "-y", "python3"], ["dnf", "install", "-y", "python3"],
                ["pacman", "-S", "--noconfirm", "python"]):
        if shutil.which(cmd[0]):
            try:
                subprocess.run(["sudo"] + cmd if os.geteuid() != 0 else cmd, timeout=900)
                return python_surum()["ok"]
            except Exception:
                pass
    return False


def pip_kur(py_cmd=None):
    """pip yoksa get-pip.py ile kurar."""
    py_cmd = py_cmd or PY
    try:
        r = subprocess.run([py_cmd, "-m", "pip", "--version"], capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            return True
    except Exception:
        pass
    say("     pip yok — kuruluyor…", "warn")
    try:
        import urllib.request
        gp = os.path.join(os.environ.get("TEMP") or "/tmp", "get-pip.py")
        urllib.request.urlretrieve("https://bootstrap.pypa.io/get-pip.py", gp)
        subprocess.run([py_cmd, gp, "--quiet"], timeout=600)
        try:
            os.remove(gp)
        except Exception:
            pass
        r = subprocess.run([py_cmd, "-m", "pip", "--version"], capture_output=True, text=True, timeout=60)
        return r.returncode == 0
    except Exception as e:
        say(f"     ⚠️  pip kurulamadı: {e}", "warn")
        return False


def pillow_kur(py_cmd=None):
    """Pillow (ekran görüntüsü için) yoksa kurar."""
    py_cmd = py_cmd or PY
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
    for args in (["-m", "pip", "install", "--quiet", "--disable-pip-version-check", "pillow"],
                 ["-m", "pip", "install", "--quiet", "--user", "--disable-pip-version-check", "pillow"]):
        try:
            subprocess.run([py_cmd] + args, timeout=600)
            r = subprocess.run([py_cmd, "-c", "import PIL;print(PIL.__version__)"],
                               capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                return r.stdout.strip()
        except Exception:
            continue
    say("     ⚠️  Pillow kurulamadı — ekran görüntüsü özelliği sınırlı çalışır.", "warn")
    return ""


def tailscale_kur():
    """Tailscale yoksa indirip kurar (yalnız Windows'ta tam otomatik)."""
    if tailscale_bin():
        return True
    say("     Tailscale yok (ChatGPT bağlantısı bunu kullanır) — kuruluyor…", "warn")
    if not _internet_var("pkgs.tailscale.com"):
        say("     ❌ İnternet yok.", "err")
        return False
    if IS_WIN:
        hedef = os.path.join(os.environ.get("TEMP") or "/tmp", "tailscale-setup.msi")
        try:
            import urllib.request
            say("     ⬇️  indiriliyor: Tailscale (~40 MB)")
            urllib.request.urlretrieve(TS_MSI, hedef)
            say("     ⚙️  kuruluyor (Windows izin penceresi çıkabilir → 'Evet')…")
            subprocess.run(["msiexec", "/i", hedef, "/qn", "/norestart"], timeout=900)
            try:
                os.remove(hedef)
            except Exception:
                pass
            if tailscale_bin():
                say("     ✅ Tailscale kuruldu", "ok")
                say("     🔑 Tarayıcı açılacak: Google/Microsoft hesabıyla giriş yapın.", "warn")
                try:
                    subprocess.Popen([tailscale_bin(), "up"])
                except Exception:
                    pass
                return True
            say("     ⚠️  Tailscale kurulumu tamamlanmadı (yönetici izni gerekebilir).", "warn")
            say(f"         Elle: {TS_INDIRME}", "warn")
            return False
        except Exception as e:
            say(f"     ❌ {e}", "err")
            say(f"         Elle: {TS_INDIRME}", "warn")
            return False
    say(f"     Elle kurun: https://tailscale.com/download ({OS_NAME})", "warn")
    return False


def gereksinimler(sessiz=False):
    """Tüm gereksinimleri tek tek kontrol eder, eksiği kurar. Özet döner."""
    sonuc = {"python": False, "pip": False, "pillow": "", "tailscale": False}
    if not sessiz:
        head("Gereksinimler — eksik olan otomatik kurulur")

    # 1) Python
    p = python_surum()
    if not p["ok"]:
        python_kur()
        p = python_surum()
    sonuc["python"] = p["ok"]
    if not sessiz:
        say("     ✅ Python %s (%s)" % (p["surum"], p["yol"]) if p["ok"]
            else "     ❌ Python kurulamadı", "ok" if p["ok"] else "err")

    pyy = (p["yol"].split() or [PY])
    # 2) pip + 3) Pillow
    sonuc["pip"] = pip_kur(pyy[0]) if sonuc["python"] else False
    sonuc["pillow"] = pillow_kur(pyy[0]) if sonuc["pip"] else ""
    if not sessiz:
        say("     ✅ pip hazır" if sonuc["pip"] else "     ⚠️  pip yok", "ok" if sonuc["pip"] else "warn")
        say("     ✅ Pillow %s" % sonuc["pillow"] if sonuc["pillow"] else
            "     ⚠️  Pillow yok (ekran görüntüsü sınırlı)", "ok" if sonuc["pillow"] else "warn")

    # 4) Tailscale
    sonuc["tailscale"] = bool(tailscale_bin()) or tailscale_kur()
    if not sessiz and not sonuc["tailscale"]:
        say("     ⚠️  Tailscale yok — ChatGPT bağlantısı kurulamaz (Claude/Cursor çalışır)", "warn")
    return sonuc


def otomatik_kur():
    """Kullanıcının çift tıklayacağı TEK yol: her şeyi sırayla kurar."""
    head("GhostPilot — tek tık kurulum")
    say("  Hiçbir şey yapmanıza gerek yok. Eksikler kendiliğinden kurulur.")
    g = gereksinimler()
    if not g["python"]:
        say("\n  ❌ Python kurulamadı. Kurulumu buradan yapıp tekrar deneyin:", "err")
        say("     https://python.org/downloads", "warn")
        return 1
    # Python kurulduysa kur.py'yi onunla yeniden başlat (PATH tazelensin)
    p = python_surum()
    if p["ok"] and os.path.abspath(p["yol"].split()[0]).lower() != os.path.abspath(PY).lower():
        try:
            say("  🔄 Yeni Python ile devam ediliyor…")
            subprocess.call(p["yol"].split() + [os.path.abspath(__file__), "oto"])
            return 0
        except Exception:
            pass
    return oto()


# ============================================================================
#  CLAUDE DESKTOP / CURSOR / VS CODE  → stdio
# ============================================================================

def claude_config_paths():
    """Claude Desktop ayar dosyasının olası yolları."""
    if IS_WIN:
        base = os.environ.get("APPDATA") or os.path.join(HOME, "AppData", "Roaming")
        return [os.path.join(base, "Claude", "claude_desktop_config.json")]
    if OS_NAME == "Darwin":
        return [os.path.join(HOME, "Library", "Application Support", "Claude",
                             "claude_desktop_config.json")]
    return [
        os.path.join(HOME, ".config", "Claude", "claude_desktop_config.json"),
        os.path.join(HOME, ".config", "claude-desktop",
                     "claude_desktop_config.json"),
    ]


CLIENTS = {
    "claude": {
        "label": "Claude Desktop",
        "paths_fn": claude_config_paths,
        "key": "mcpServers",
    },
    "cursor": {
        "label": "Cursor",
        "paths_fn": lambda: [os.path.join(HOME, ".cursor", "mcp.json")],
        "key": "mcpServers",
    },
    "vscode": {
        "label": "VS Code (Copilot / Continue)",
        "paths_fn": lambda: [
            os.path.join(HOME, ".vscode", "mcp.json"),
            os.path.join(os.environ.get("APPDATA", HOME), "Code", "User", "mcp.json"),
        ],
        "key": "servers",
    },
}


def mcp_entry():
    return {"command": PY, "args": [SERVER, "bridge"]}


def install_client(cid):
    c = CLIENTS[cid]
    head(f"{c['label']} — bağlantı kurulumu")
    paths = c["paths_fn"]()
    target = None
    for p in paths:
        if os.path.exists(p):
            target = p
            break
    if not target:
        target = paths[0]
        say(f"  ℹ️  {c['label']} ayar dosyası bulunamadı; oluşturulacak:")
        say(f"     {target}", "dim")

    data = {}
    if os.path.exists(target):
        try:
            data = json.load(open(target, "r", encoding="utf-8")) or {}
        except Exception:
            bak = target + f".bak-{int(time.time())}"
            shutil.copy2(target, bak)
            say(f"  ⚠️  Mevcut dosya okunamadı, yedeklendi: {bak}", "warn")
            data = {}
        else:
            bak = target + ".bak"
            try:
                shutil.copy2(target, bak)
            except Exception:
                pass

    key = c["key"]
    data.setdefault(key, {})
    data[key]["ghostpilot"] = mcp_entry()

    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    say(f"\n  ✅ Yazıldı: {target}")
    say("\n  Eklenen blok:", "dim")
    say(json.dumps({key: {"ghostpilot": mcp_entry()}}, indent=2, ensure_ascii=False), "dim")
    say(f"\n  Sıradaki adım: {c['label']}'ı tamamen kapat ve yeniden aç.", "ok")
    say("  Sonra sohbette şunu yaz:  'ghostpilot_status aracını çalıştır'")
    return 0


def uninstall_clients():
    head("Kayıtları geri al")
    for cid, c in CLIENTS.items():
        for p in c["paths_fn"]():
            if not os.path.exists(p):
                continue
            try:
                data = json.load(open(p, "r", encoding="utf-8")) or {}
                if c["key"] in data and "ghostpilot" in data[c["key"]]:
                    del data[c["key"]]["ghostpilot"]
                    json.dump(data, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
                    say(f"  ✅ {c['label']}: kayıt silindi ({p})")
            except Exception as e:
                say(f"  ⚠️  {c['label']}: {e}", "warn")
    say("\n  Ayar klasörü (~/.ghostpilot) duruyor — silmek için elle kaldırın.", "dim")
    return 0


# ============================================================================
#  CHATGPT / TARAYICI AI  → HTTPS relay
# ============================================================================

def tailscale_bin():
    p = shutil.which("tailscale")
    if p:
        return p
    if IS_WIN:
        for c in (r"C:\Program Files\Tailscale\tailscale.exe",
                  r"C:\Program Files (x86)\Tailscale\tailscale.exe"):
            if os.path.exists(c):
                return c
    if OS_NAME == "Darwin" and os.path.exists("/Applications/Tailscale.app/Contents/MacOS/Tailscale"):
        return "/Applications/Tailscale.app/Contents/MacOS/Tailscale"
    return None


def chatgpt_setup():
    head("ChatGPT / tarayıcıdaki AI — bağlantı kurulumu")
    say("""
  Ne olacak?
    1) Bu bilgisayarda küçük bir sunucu açılır (GhostPilot köprüsü)
    2) Tailscale bu sunucuyu HTTPS ile internete açar (size özel adres)
    3) ChatGPT'ye o adresi 'Connector' olarak eklersiniz
    4) ChatGPT sizin bilgisayarınızda komut çalıştırır, dosya okur/yazar
""")

    ts = tailscale_bin()
    if not ts:
        say("  ❌ Tailscale bulunamadı — ChatGPT için gerekli (ücretsiz)", "err")
        say("     https://tailscale.com/download adresinden kurun, giriş yapın.")
        say("\n  Tailscale istemiyorsanız alternatifler:", "warn")
        say("     • Claude Desktop  → python kur.py claude      (tünel GEREKMEZ)")
        say("     • Cursor / VS Code → python kur.py cursor")
        say("     • Aynı ağdaki cihaz → python ghostpilot.py relay --port 17381")
        say("       ve 192.168.x.x:17381/mcp adresini kullanın.")
        return 1

    say(f"  ✅ Tailscale: {ts}", "ok")

    # port
    port = 17381
    try:
        cfg_p = os.path.join(HOME, ".ghostpilot", "config.json")
        if os.path.exists(cfg_p):
            port = json.load(open(cfg_p, encoding="utf-8")).get("port", port) or port
    except Exception:
        pass

    # tünel aç
    step("1/3", f"HTTPS tüneli açılıyor (port {port})…")
    try:
        r = subprocess.run([ts, "funnel", "--bg", str(port)],
                           capture_output=True, text=True, timeout=90)
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode != 0 and "already" not in out.lower():
            say(f"  ⚠️  {out.strip()[:300]}", "warn")
    except Exception as e:
        say(f"  ⚠️  tünel: {e}", "warn")

    # URL
    url = ""
    try:
        r = subprocess.run([ts, "status", "--json"], capture_output=True,
                           text=True, timeout=30)
        dns = (json.loads(r.stdout or "{}").get("Self") or {}).get("DNSName") or ""
        if dns:
            url = "https://" + dns.rstrip(".") + "/mcp"
    except Exception:
        pass
    if not url:
        say("  ⚠️  Özel adres okunamadı. 'tailscale status --json' çıktısına bakın.", "warn")

    step("2/3", "Erişim anahtarı")
    tok = ""
    tok_path = os.path.join(HOME, ".ghostpilot", "token")
    try:
        tok = open(tok_path, encoding="utf-8").read().strip()
    except Exception:
        pass
    if len(tok) < 24:
        py(["token"])
        try:
            tok = open(tok_path, encoding="utf-8").read().strip()
        except Exception:
            tok = "(okunamadı — python ghostpilot.py token)"

    step("3/3", "Şimdi sunucuyu başlatın")
    say("""
  YENİ bir terminal açın (bu pencereyi kapatmayın) ve şunu çalıştırın:

      python kur.py sunucu

  O pencere AÇIK KALMALI. Kapatırsanız ChatGPT bağlantısı kesilir.
  Sonra kontrol:  python kur.py test
""", "dim")

    # ChatGPT'nin yeni ekranında API anahtarı seçeneği YOK.
    # Bu yüzden token'ı URL'ye sorgu parametresi olarak gömüyoruz.
    url_with_token = (url + "?token=" + tok) if (url and tok) else url

    say("\n" + "─" * 60)
    say("  ChatGPT → Özel MCP sunucusu ekle", "ok")
    say("")
    say("  Ad            : GhostPilot")
    say("  Bağlantı      : Sunucu URL'si")
    say(f"  Sunucu URL'si : {url_with_token or 'https://<makine>.tailXXXX.ts.net/mcp?token=...'}")
    say("  Kimlik doğr.  : Kimlik doğrulama yok")
    say('  ☑ "Anladım ve devam etmek istiyorum"')
    say("")
    say("  ⚠️  Anahtar URL'nin içinde — bu yüzden ekran görüntüsü/ekran paylaşımı")
    say("      yaparken URL'yi gizleyin. Anahtar yenilenince URL de değişir:")
    say("      python kur.py token  →  yeni URL'yi kopyalayın.", "warn")
    say("")
    say("  Kaydettikten sonra YENİ sohbet açıp yazın:")
    say('     "ghostpilot_status aracını çalıştır ve ne yapabildiğini özetle"', "dim")
    say("─" * 60)
    say("\n  Arena / başka tarayıcı AI: aynı URL + Bearer anahtarı.", "dim")
    say("  Güvenlik: anahtar yalnız sizde; tüneli kapatmak için:")
    say(f"     {ts} funnel --bg=false {port}", "dim")
    return 0


# ============================================================================
#  İZİNLER — klasör ekle / listele
# ============================================================================

def cfg_path():
    return os.path.join(HOME, ".ghostpilot", "config.json")


def load_cfg_file():
    p = cfg_path()
    try:
        if os.path.exists(p):
            return json.load(open(p, encoding="utf-8")) or {}
    except Exception:
        pass
    return {}


def save_cfg_file(d):
    p = cfg_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    try:
        os.chmod(p, 0o600)
    except Exception:
        pass


def norm(p):
    p = os.path.abspath(os.path.expanduser(p))
    return p.rstrip("\\/") or p


def izin(args):
    """python kur.py izin D:\\AiProjelerim [--sadece-oku]"""
    head("Klasör izinleri")
    d = load_cfg_file()
    d.setdefault("read_roots", [HOME])
    d.setdefault("write_roots", [HOME, os.path.join(HOME, "Desktop"), os.path.join(HOME, "Documents")])

    if not args:
        say("\n  Okuma izni (read_roots):")
        for r in d["read_roots"]:
            say(f"     • {r}", "dim")
        say("\n  Yazma izni (write_roots):")
        for r in d["write_roots"]:
            say(f"     • {r}", "dim")
        say("""
  Klasör eklemek için:
     python kur.py izin "D:\\AiProjelerim"
     python kur.py izin "D:\\Yedekler" --sadece-oku
""", "dim")
        return 0

    target = args[0]
    ro = "--sadece-oku" in args
    if not os.path.exists(target):
        say(f"  ⚠️  Klasör şu an yok: {target}", "warn")
        say("     Yine de eklenecek (sonra oluşturursanız çalışır).")
    t = norm(target)
    changed = False
    if t not in [norm(x) for x in d["read_roots"]]:
        d["read_roots"].append(t)
        changed = True
    if not ro and t not in [norm(x) for x in d["write_roots"]]:
        d["write_roots"].append(t)
        changed = True
    save_cfg_file(d)

    say(f"\n  ✅ Eklendi: {t}")
    say(f"     okuma: var · yazma: {'yok' if ro else 'var'}")
    if changed:
        say("\n  ⚠️  Değişikliğin geçerli olması için sunucuyu yeniden başlatın:", "warn")
        say("     (sunucu penceresinde Ctrl+C, sonra: python kur.py sunucu)")
    return 0


def izin_sil(args):
    if not args:
        return izin([])
    head("İzin kaldır")
    d = load_cfg_file()
    t = norm(args[0])
    for k in ("read_roots", "write_roots"):
        d[k] = [x for x in (d.get(k) or []) if norm(x) != t]
    save_cfg_file(d)
    say(f"  ✅ Kaldırıldı: {t}")
    say("  Sunucuyu yeniden başlatın.", "dim")
    return 0


# ============================================================================
#  OTOMATİK BAŞLATMA — sunucu bilgisayar açılınca çalışsın
# ============================================================================

def pythonw():
    """Pencere açmayan Python yorumlayıcısı."""
    if IS_WIN:
        cand = os.path.join(os.path.dirname(PY), "pythonw.exe")
        if os.path.exists(cand):
            return cand
    return PY


def startup_dir():
    if IS_WIN:
        return os.path.join(os.environ.get("APPDATA", os.path.join(HOME, "AppData", "Roaming")),
                            "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    if OS_NAME == "Darwin":
        return os.path.join(HOME, "Library", "LaunchAgents")
    return os.path.join(HOME, ".config", "autostart")


def otomatik(kapat=False):
    head("Otomatik başlatma" + (" — kaldır" if kapat else ""))
    sd = startup_dir()
    port = load_cfg_file().get("port", 17381) or 17381

    if IS_WIN:
        link = os.path.join(sd, "GhostPilot.vbs")
        if kapat:
            if os.path.exists(link):
                os.remove(link)
                say(f"  ✅ Kaldırıldı: {link}")
            else:
                say("  ℹ️  Kayıt yoktu.")
            return 0
        os.makedirs(sd, exist_ok=True)
        vbs = (
            'Set sh = CreateObject("WScript.Shell")\r\n'
            'sh.CurrentDirectory = "' + HERE + '"\r\n'
            'sh.Run """' + pythonw() + '"" "' + SERVER + '" watchdog --port ' + str(port) + '", 0, False\r\n'
        )
        open(link, "w", encoding="utf-8", newline="").write(vbs)
        say(f"  ✅ Kuruldu: {link}")
        say("  Bilgisayar açılınca BEKÇİ sessizce (pencere yok) başlar;")
        say("  sunucu çökerse kendisi yeniden ayağa kaldırır.")
        say("  Kaldırmak için:  python kur.py otomatik-kaldir")
        return 0

    if OS_NAME == "Darwin":
        link = os.path.join(sd, "com.btmcode.ghostpilot.plist")
        if kapat:
            if os.path.exists(link):
                os.remove(link)
                subprocess.run(["launchctl", "unload", link], capture_output=True, timeout=20)
                say(f"  ✅ Kaldırıldı: {link}")
            return 0
        os.makedirs(sd, exist_ok=True)
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.btmcode.ghostpilot</string>
  <key>ProgramArguments</key><array>
    <string>{PY}</string><string>{SERVER}</string><string>watchdog</string>
    <string>--port</string><string>{port}</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict></plist>"""
        open(link, "w", encoding="utf-8").write(plist)
        subprocess.run(["launchctl", "load", link], capture_output=True, timeout=20)
        say(f"  ✅ Kuruldu: {link}")
        return 0

    link = os.path.join(sd, "ghostpilot.desktop")
    if kapat:
        if os.path.exists(link):
            os.remove(link)
            say(f"  ✅ Kaldırıldı: {link}")
        return 0
    os.makedirs(sd, exist_ok=True)
    open(link, "w", encoding="utf-8").write(
        "[Desktop Entry]\nType=Application\nName=GhostPilot\n"
        f"Exec={PY} {SERVER} watchdog --port {port}\nX-GNOME-Autostart-enabled=true\n")
    say(f"  ✅ Kuruldu: {link}")
    return 0


# ============================================================================
#  SUNUCU + UÇTAN UCA TEST
# ============================================================================

def tailscale_url(port):
    ts = tailscale_bin()
    if not ts:
        return ""
    try:
        r = subprocess.run([ts, "status", "--json"], capture_output=True, text=True, timeout=30)
        dns = (json.loads(r.stdout or "{}").get("Self") or {}).get("DNSName") or ""
        if dns:
            return "https://" + dns.rstrip(".") + "/mcp"
    except Exception:
        pass
    return ""


def start_relay():
    head("Sunucuyu başlat")
    say("  Bu pencere AÇIK KALMALI. Kapatırsanız ChatGPT bağlantısı kesilir.")
    say("  Durdurmak için: Ctrl+C\n")
    return subprocess.call([PY, SERVER, "relay"])


def run_test():
    """Uçtan uca test: tünel + token + araç listesi."""
    head("Uçtan uca test")
    port = 17381
    try:
        cfg_p = os.path.join(HOME, ".ghostpilot", "config.json")
        if os.path.exists(cfg_p):
            port = json.load(open(cfg_p, encoding="utf-8")).get("port", port) or port
    except Exception:
        pass

    import urllib.request
    import urllib.error

    # 1) yerel sunucu
    say("\n  1) Yerel sunucu")
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as r:
            d = json.load(r)
        say(f"     ✅ çalışıyor — {d.get('service')} v{d.get('version')}, {d.get('tools')} araç", "ok")
    except Exception:
        say("     ❌ çalışmıyor", "err")
        say("     → AYRI bir terminalde:  python ghostpilot.py relay")
        say("       (bu pencere açık kalmalı)")
        return 1

    # 2) token
    say("\n  2) Erişim anahtarı")
    tok = ""
    try:
        tok = open(os.path.join(HOME, ".ghostpilot", "token"), encoding="utf-8").read().strip()
    except Exception:
        pass
    if tok:
        say(f"     ✅ {tok[:6]}…{tok[-4:]}", "ok")
    else:
        say("     ❌ okunamadı → python ghostpilot.py token", "err")
        return 1

    # 3) yerel MCP
    say("\n  3) Yerel MCP (araç listesi)")
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/mcp",
            data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + tok})
        with urllib.request.urlopen(req, timeout=10) as r:
            n = len(json.load(r)["result"]["tools"])
        say(f"     ✅ {n} araç döndü", "ok")
    except Exception as e:
        say(f"     ❌ {e}", "err")
        return 1

    # 4) tünel
    say("\n  4) Tailscale tüneli")
    url = tailscale_url(port)
    if not url:
        say("     ⚠️  özel adres okunamadı (Tailscale girişi?)", "warn")
        return 0
    say(f"     {url}", "dim")
    public = url.replace("/mcp", "/health")
    try:
        with urllib.request.urlopen(public, timeout=15) as r:
            json.load(r)
        say("     ✅ internetten erişilebiliyor", "ok")
    except urllib.error.HTTPError as e:
        say(f"     ❌ HTTP {e.code}", "err")
        say("     → funnel kapalı olabilir:  tailscale funnel --bg " + str(port))
        return 1
    except Exception as e:
        say(f"     ❌ {e}", "err")
        say("     → funnel açık mı?  tailscale funnel --bg " + str(port))
        return 1

    say("\n" + "─" * 60)
    say("  ✅ HER ŞEY HAZIR — ChatGPT'ye ekleyin:", "ok")
    say("     Sunucu URL'si : " + url + "?token=" + tok, "dim")
    say("     Kimlik doğr.  : Kimlik doğrulama yok")
    say("─" * 60)
    return 0


# ============================================================================
#  TEK TUŞ — tam otomatik kurulum
# ============================================================================

def port_cfg():
    return int(load_cfg_file().get("port", 17381) or 17381)


def relay_running(port=None):
    import urllib.request
    port = port or port_cfg()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=3) as r:
            return json.load(r)
    except Exception:
        return None


def start_relay_bg():
    """Bekçiyi (watchdog) arka planda başlatır — sunucu HEP ayakta kalır."""
    port = port_cfg()
    if relay_running(port):
        return True, "zaten çalışıyor"
    try:
        kw = {}
        if IS_WIN:
            kw["creationflags"] = (getattr(subprocess, "CREATE_NO_WINDOW", 0) |
                                   getattr(subprocess, "DETACHED_PROCESS", 0))
            exe = pythonw()
        else:
            exe = PY
            kw["start_new_session"] = True
        subprocess.Popen([exe, SERVER, "watchdog", "--port", str(port)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         cwd=HERE, **kw)
        for _ in range(25):
            time.sleep(0.4)
            if relay_running(port):
                return True, "bekçi çalışıyor (sunucu izleniyor)"
    except Exception as e:
        return False, str(e)
    return False, "başlatılamadı"


def ts_state():
    """(tailscale_yolu, durum, dns_adı)"""
    ts = tailscale_bin()
    if not ts:
        return None, "yok", ""
    dns, state = "", ""
    try:
        r = subprocess.run([ts, "status", "--json"], capture_output=True,
                           text=True, timeout=25)
        d = json.loads(r.stdout or "{}")
        state = (d.get("BackendState") or "").lower()
        dns = (d.get("Self") or {}).get("DNSName") or ""
    except Exception:
        pass
    return ts, state, dns


def oto():
    head("Tek tuş kurulum — her şey otomatik")
    ok_all = True

    # 1) Gereksinimler (Python · pip · Pillow · Tailscale) — eksikse KURAR
    step("1/7", "Gereksinimler (Python · pip · Pillow · Tailscale)")
    # setup.py ile çağrıldıysa gereksinimler zaten kurulmuş; tekrar indirmeyelim.
    g = ({"python": True, "pip": True, "pillow": "kurulu", "tailscale": bool(tailscale_bin())}
         if os.environ.get("GP_SETUP_TARAFINDAN") else gereksinimler(sessiz=True))
    if not g["python"]:
        say("     ❌ Python yok ve kurulamadı.", "err")
        say("        https://python.org/downloads → 'Add python.exe to PATH' işaretleyin.", "warn")
        return 1
    pv = python_surum()
    say(f"     ✅ Python {pv['surum']}", "ok")
    say(f"     {'✅' if g['pip'] else '⚠️ '} pip · "
        f"{'✅ Pillow ' + g['pillow'] if g['pillow'] else '⚠️  Pillow yok'} · "
        f"{'✅ Tailscale' if g['tailscale'] else '⚠️  Tailscale yok'}",
        "ok" if (g["pip"] and g["pillow"] and g["tailscale"]) else "warn")

    # 2) Dosyalar
    step("2/7", "Dosyalar")
    eksik = [f for f in ("ghostpilot.py", "screen.py") if not os.path.exists(os.path.join(HERE, f))]
    if eksik:
        say(f"     ❌ eksik: {eksik}", "err")
        return 1
    say("     ✅ ghostpilot.py · screen.py", "ok")

    # 3) Yapılandırma + anahtar
    step("3/7", "Yapılandırma ve erişim anahtarı")
    d = load_cfg_file()
    d.setdefault("port", 17381)
    d.setdefault("read_roots", [HOME])
    d.setdefault("write_roots", [HOME, os.path.join(HOME, "Desktop"), os.path.join(HOME, "Documents")])
    save_cfg_file(d)

    # Mevcut anahtar VARSA KORUNUR. Yenilemek ChatGPT'deki URL'yi geçersiz
    # kılar; kurulumun işi bağlantıyı bozmak değil, kurmaktır.
    tok = ""
    tok_path = os.path.join(HOME, ".ghostpilot", "token")
    try:
        tok = open(tok_path, encoding="utf-8").read().strip()
    except Exception:
        pass
    if len(tok) >= 24:
        say(f"     ✅ mevcut anahtar korundu: {tok[:6]}…{tok[-4:]}", "ok")
    else:
        py(["token"])
        try:
            tok = open(tok_path, encoding="utf-8").read().strip()
        except Exception:
            pass
        if len(tok) < 24:
            say("     ❌ anahtar üretilemedi", "err")
            return 1
        say(f"     ✅ yeni anahtar üretildi: {tok[:6]}…{tok[-4:]}", "ok")

    # 4) Bulunan istemciler
    step("4/7", "Sohbet programları")
    found = []
    for cid, c in CLIENTS.items():
        for pth in c["paths_fn"]():
            if os.path.exists(os.path.dirname(pth) or "."):
                found.append(cid)
                break
    if found:
        import io as _io
        import contextlib
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            for cid in found:
                install_client(cid)
        for cid in found:
            say(f"     ✅ {CLIENTS[cid]['label']} — bağlandı", "ok")
    else:
        say("     ℹ️  Claude/Cursor kurulu görünmüyor — atlandı (ChatGPT için gerek yok).")

    # 5) Tailscale + tünel
    step("5/7", "Tailscale ve HTTPS tüneli")
    port = port_cfg()
    ts, state, dns = ts_state()
    url = ""
    if not ts:
        say("     ⚠️  Tailscale yok — ChatGPT bağlantısı kurulamaz.", "warn")
        say("         https://tailscale.com/download → kur, giriş yap, sonra tekrar çalıştır.")
        ok_all = False
    elif state not in ("running", "starting"):
        say(f"     ⚠️  Tailscale giriş yapmamış (durum: {state or 'bilinmiyor'}).", "warn")
        say("         Şunu çalıştırın:  tailscale up")
        ok_all = False
    else:
        try:
            r = subprocess.run([ts, "funnel", "--bg", str(port)],
                               capture_output=True, text=True, timeout=90)
            out = ((r.stdout or "") + (r.stderr or "")).strip()
            if r.returncode == 0 or "already" in out.lower():
                say(f"     ✅ tünel açık (port {port})", "ok")
            else:
                say(f"     ⚠️  {out[:200]}", "warn")
                ok_all = False
        except Exception as e:
            say(f"     ⚠️  {e}", "warn")
            ok_all = False
        if dns:
            url = "https://" + dns.rstrip(".") + "/mcp"

    # 6) Sunucu (arka planda)
    step("6/7", "Sunucu")
    ok, msg = start_relay_bg()
    if ok:
        say(f"     ✅ {msg} — http://127.0.0.1:{port}", "ok")
    else:
        say(f"     ❌ {msg}", "err")
        ok_all = False

    # 7) Otomatik başlatma + masaüstü kısayolu
    step("7/7", "Bilgisayar açılınca otomatik başlat + masaüstü kısayolu")
    try:
        otomatik_sessiz()
        say("     ✅ kuruldu (pencere açılmaz)", "ok")
    except Exception as e:
        say(f"     ⚠️  {e}", "warn")
    # masaüstü kısayolu (hayalet ikonlu)
    try:
        import kisayol as _KS
        y = _KS.ekle(sessiz=True)
        if y:
            say(f"     ✅ masaüstü kısayolu: {y[0][1]}", "ok")
        else:
            say("     ⚠️  masaüstü kısayolu oluşturulamadı", "warn")
    except Exception as e:
        say(f"     ⚠️  kısayol: {e}", "warn")

    # ---- ÖZET ----
    d2 = load_cfg_file()
    if url:
        # OAuth keşif adreslerinin doğru (https) üretilmesi için
        d2["public_base"] = url[:-4] if url.endswith("/mcp") else url
    d2["require_token"] = True
    save_cfg_file(d2)
    need = True
    full = url or ""
    say("\n" + "═" * 62)
    if ok_all and full:
        say("  ✅ KURULUM TAMAM — ChatGPT'ye eklemek için:", "ok")
    else:
        say("  ⚠️  Kurulum kısmen tamam. Eksikler yukarıda.", "warn")
    say("═" * 62)
    say("")
    say("  ChatGPT → Ayarlar → Bağlayıcılar → Özel MCP sunucusu ekle")
    say("")
    say("  Ad             : GhostPilot")
    say("  Bağlantı       : Sunucu URL'si")
    say(f"  Sunucu URL'si  : {full or '(Tailscale gerekli)'}")
    say("  Kimlik doğr.   : OAuth")
    say("")
    say("  Kaydet'e basınca ChatGPT sizi GhostPilot'un KENDİ onay ekranına")
    say("  gönderir. Orada 'İzin ver' deyin — bağlantı kurulur.")
    say("")
    say("  🔒 Başkası bu URL'yi bilse bile izin ekranını geçemez;", "ok")
    say("     erişim yalnız onayladığınız istemciye verilir (PKCE + 30 gün).", "ok")
    say("")
    say(f"  (Elle test için Bearer: {tok[:8]}…{tok[-4:]})", "dim")
    say("")
    if full:
        ozet = os.path.join(HERE, "KURULUM-OZET.txt")
        try:
            open(ozet, "w", encoding="utf-8").write(
                "GhostPilot — ChatGPT bağlantı bilgileri\n"
                "========================================\n\n"
                "Ad            : GhostPilot\n"
                "Sunucu URL'si : " + full + "\n"
                "Kimlik dogr. : OAuth\n"
                "Simge         : chatgpt-icon-256.png (klasordeki dosya)\n\n"
                "Not: Bu dosyayı kimseyle paylaşmayın (anahtar içinde).\n"
                "Anahtar yenilenirse URL değişir: python kur.py token\n")
            say(f"  📄 Bu bilgiler kaydedildi: {ozet}", "dim")
        except Exception:
            pass
    say("\n  Denetim: python kur.py test")
    say("═" * 62 + "\n")
    return 0 if ok_all else 1


_AUTOSTART_QUIET = {"on": False}


def otomatik_sessiz():
    """otomatik() ile aynı iş, ama çıktıyı bastırmadan."""
    import io as _io
    import contextlib
    buf = _io.StringIO()
    with contextlib.redirect_stdout(buf):
        otomatik()
    return buf.getvalue()


def guvenlik(args):
    """python kur.py guvenlik [ac|kapat] — URL anahtarı zorunlu mu?"""
    head("Bağlantı güvenliği")
    d = load_cfg_file()
    cur = bool(d.get("require_token", True))
    mode = (args[0] if args else "").lower()

    if mode in ("ac", "on", "1"):
        d["require_token"] = True
        save_cfg_file(d)
        say("  ✅ Anahtar ZORUNLU yapıldı.")
        say("     Uzak URL'ye ?token=... eklenmeli, yoksa bağlantı reddedilir.")
    elif mode in ("kapat", "off", "0"):
        d["require_token"] = False
        save_cfg_file(d)
        say("  ✅ Anahtar KAPATILDI.")
        say("     Tek tıkla bağlanılır; URL'ye anahtar gerekmez.")
    else:
        say(f"  Şu anki durum: {'AÇIK — OAuth veya token zorunlu' if cur else 'KAPALI — herkes girebilir (!)'}")
        say("""
  Değiştirmek için:
     python kur.py guvenlik ac       → token zorunlu
     python kur.py guvenlik kapat    → token gerekmez (tek tık kolaylığı)

  Sadece kendi bilgisayarınızda ve Tailscale ağınızda kullanıyorsanız
  kapalı bırakmak pratiktir. Açık bırakırsanız URL'yi bilen herkes erişemez.
""", "dim")
        return 0
    say("  Sunucuyu yeniden başlatın.", "dim")
    return 0


def durum():
    head("Sunucu durumu")
    port = port_cfg()
    h = relay_running(port)
    if h:
        say(f"  🟢 ÇALIŞIYOR — {h.get('service')} v{h.get('version')} · {h.get('tools')} araç", "ok")
        say(f"     http://127.0.0.1:{port}", "dim")
    else:
        say("  🔴 ÇALIŞMIYOR", "err")
        say("     Başlatmak için: python kur.py sunucu")
    # Bekçi gerçekten yaşıyor mu? pid dosyası + canlılık kontrolü
    bekci = False
    try:
        pid_f = os.path.join(HOME, ".ghostpilot", "watchdog.pid")
        if os.path.exists(pid_f):
            pid = int(open(pid_f).read().strip() or 0)
            if pid:
                if IS_WIN:
                    import subprocess as sp
                    r = sp.run(["tasklist", "/FI", "PID eq %d" % pid],
                               capture_output=True, text=True, timeout=10)
                    bekci = str(pid) in (r.stdout or "")
                else:
                    os.kill(pid, 0)
                    bekci = True
    except Exception:
        bekci = False
    say("  " + ("🛡️  Bekçi aktif — çökerse kendisi geri getirir" if bekci else
                "⚠️  Bekçi yok — çökerse geri gelmez (python kur.py sunucu)"),
        "ok" if bekci else "warn")
    url = tailscale_url(port)
    if url:
        say(f"  🌐 ChatGPT adresi: {url}", "dim")
        say("     Kimlik doğrulama: OAuth")
    else:
        say("  ⚠️  Tailscale tüneli yok (ChatGPT bağlantısı için gerekli)", "warn")
    return 0


def _pkill(pattern):
    """Satırda `pattern` geçen python süreçlerini öldürür.

    wmic yeni Windows'ta yok → önce PowerShell, sonra taskkill, sonra wmic.
    ÖNEMLİ: yalnız PYTHON süreçlerini öldürür — başka programlara dokunmaz.
    """
    import subprocess as sp
    if IS_WIN:
        # 1) PowerShell (Windows 10/11'de her zaman var)
        ps = (
            "Get-CimInstance Win32_Process | "
            "Where-Object { $_.Name -like 'python*' -and "
            "$_.CommandLine -like '*" + pattern + "*' } | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force "
            "-ErrorAction SilentlyContinue }"
        )
        try:
            r = sp.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-Command", ps], capture_output=True, text=True, timeout=40)
            if r.returncode == 0:
                return True
        except Exception:
            pass
        # 2) wmic (eski Windows)
        try:
            r = sp.run(["wmic", "process", "where",
                        "commandline like '%" + pattern + "%'", "delete"],
                       capture_output=True, text=True, timeout=40)
            return r.returncode == 0
        except Exception:
            return False
    return sp.run(["pkill", "-9", "-f", pattern],
                  capture_output=True, text=True).returncode == 0


def _pkill_pid(pid):
    """Bilinen bir PID'i öldür (kayıtlı pid dosyası)."""
    import subprocess as sp
    try:
        pid = int(pid)
    except Exception:
        return False
    if pid <= 0:
        return False
    try:
        if IS_WIN:
            sp.run(["taskkill", "/F", "/PID", str(pid)],
                   capture_output=True, text=True, timeout=20)
        else:
            os.kill(pid, 9)
        return True
    except Exception:
        return False


def pid_dosyasi_oldur(ad="relay.pid"):
    """~/.ghostpilot/<ad> içindeki PID'i öldürür (varsa)."""
    p = os.path.join(HOME, ".ghostpilot", ad)
    try:
        with open(p, encoding="utf-8") as f:
            pid = (f.read() or "").strip()
        if pid:
            _pkill_pid(pid)
        os.remove(p)
        return True
    except Exception:
        return False


def durdur(sessiz=False):
    """Sunucuyu ve bekçiyi durdurur. Bekçi geri getirmez (durma bayrağı)."""
    if not sessiz:
        head("Sunucuyu durdur")
    # 1) Bekçiye "dur" bayrağı koy — yoksa çökerttiğimiz sunucuyu geri getirir
    try:
        os.makedirs(os.path.dirname(STOP_FILE), exist_ok=True)
        open(STOP_FILE, "w").write(str(int(time.time())))
    except Exception:
        pass
    # 2) Önce bekçiyi, sonra relay'i öldür
    _pkill("ghostpilot.py watchdog")
    pid_dosyasi_oldur("watchdog.pid")
    time.sleep(0.4)
    _pkill("ghostpilot.py relay")
    pid_dosyasi_oldur("relay.pid")
    _pkill("ghostpilot.py --port")          # olası varyantlar
    _pkill("ghostpilot.py bridge")          # stdio köprü açık kaldıysa
    time.sleep(1.2)
    alive = bool(relay_running())
    # 3) hâlâ yanıt veriyorsa son bir kez daha, geniş desenle dene
    if alive:
        _pkill("ghostpilot.py")
        time.sleep(1.0)
        alive = bool(relay_running())
    if not sessiz:
        if alive:
            say("  ⚠️  Hâlâ yanıt veriyor — elle kapatmanız gerekebilir.", "warn")
        else:
            say("  ✅ DURDURULDU — sunucu ve bekçi kapandı.", "ok")
            say("     ChatGPT bağlantısı artık çalışmaz.", "dim")
        say("")
        say("  Yeniden başlatmak için:  python kur.py basla")
        say("  Açılışta hiç başlamasın: python kur.py otomatik-kaldir", "dim")
    return 0 if not alive else 1


def basla(sessiz=False):
    """Durma bayrağını kaldırır ve bekçiyi başlatır."""
    if not sessiz:
        head("Sunucuyu başlat")
    try:
        if os.path.exists(STOP_FILE):
            os.remove(STOP_FILE)
    except Exception:
        pass
    if relay_running():
        say("  ℹ️  Zaten çalışıyor.", "dim")
        return 0
    ok, msg = start_relay_bg()
    say(f"  {'✅' if ok else '❌'} {msg}", "ok" if ok else "err")
    if ok:
        say(f"     http://127.0.0.1:{port_cfg()}", "dim")
    return 0 if ok else 1


def tam_kapat():
    """Durdur + otomatik başlatmayı kaldır + Tailscale tünelini kapat."""
    head("Tamamen kapat")
    say("  Yapılacaklar:")
    say("    1) Sunucu ve bekçi durdurulacak")
    say("    2) Açılışta otomatik başlatma kaldırılacak")
    say("    3) Tailscale HTTPS tüneli kapatılacak  (ChatGPT erişimi kesilir)")
    say("")
    try:
        if input("  Devam? (e/H): ").strip().lower() != "e":
            say("  İptal edildi.")
            return 0
    except (EOFError, KeyboardInterrupt):
        print()
        return 0
    durdur(sessiz=True)
    say("  ✅ Sunucu ve bekçi durduruldu.")
    try:
        otomatik_sessiz_kapat()
        say("  ✅ Otomatik başlatma kaldırıldı.")
    except Exception as e:
        say(f"  ⚠️  Otomatik başlatma: {e}", "warn")
    ts = tailscale_bin()
    port = port_cfg()
    if ts:
        try:
            r = subprocess.run([ts, "funnel", "--bg=false", str(port)],
                               capture_output=True, text=True, timeout=60)
            say("  ✅ Tailscale tüneli kapatıldı." if r.returncode == 0
                else "  ⚠️  Tünel kapatılamadı (elle: tailscale funnel --bg=false %d)" % port,
                "ok" if r.returncode == 0 else "warn")
        except Exception as e:
            say(f"  ⚠️  Tailscale: {e}", "warn")
    else:
        say("  ℹ️  Tailscale yok — kapatılacak tünel yok.", "dim")
    say("")
    say("  🔒 Artık hiçbir sohbet programı bilgisayarınıza erişemez.", "ok")
    say("     Yeniden açmak için: python kur.py basla")
    return 0


def otomatik_sessiz_kapat():
    import contextlib
    import io as _io
    with contextlib.redirect_stdout(_io.StringIO()):
        otomatik(kapat=True)


def oauth_durum():
    head("OAuth — izin verilen istemciler")
    p = os.path.join(HOME, ".ghostpilot", "oauth.json")
    if not os.path.exists(p):
        say("  ℹ️  Henüz OAuth izni yok.")
        say("     ChatGPT'de bağlantı kurulunca burada görünür.")
        return 0
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        say(f"  ❌ okunamadı: {e}", "err")
        return 1
    toks = d.get("tokens") or {}
    ist = d.get("clients") or {}
    if not toks:
        say("  ℹ️  Aktif erişim anahtarı yok.")
    for t, r in toks.items():
        kalan = max(0, int((r.get("expires_at", 0) - time.time()) / 86400))
        say(f"  • {r.get('client_id') or '(bilinmiyor)'}  ·  {kalan} gün kaldı  ·  "
            f"{t[:6]}…{t[-4:]}")
    if ist:
        say("\n  Kayıtlı istemciler:")
        for cid, c in ist.items():
            say(f"    - {c.get('name') or cid}", "dim")
    say("\n  Hepsini iptal etmek için: python kur.py oauth-sil", "dim")
    return 0


def oauth_sil():
    head("OAuth izinlerini iptal et")
    p = os.path.join(HOME, ".ghostpilot", "oauth.json")
    if not os.path.exists(p):
        say("  ℹ️  Zaten izin yok.")
        return 0
    try:
        d = json.load(open(p, encoding="utf-8"))
        n = len(d.get("tokens") or {})
        d["tokens"] = {}
        d["codes"] = {}
        d["refresh"] = {}
        json.dump(d, open(p, "w", encoding="utf-8"), indent=1)
        say(f"  ✅ {n} erişim anahtarı iptal edildi.")
        say("  ChatGPT bağlantısı artık çalışmaz; yeniden izin vermeniz gerekir.", "warn")
    except Exception as e:
        say(f"  ❌ {e}", "err")
        return 1
    return 0



# ============================================================================
#  v5.0.0 — panel, güncelleme, mod, görev, telegram, makine adı
# ============================================================================

def _cfg_oku():
    p = os.path.join(HOME, ".ghostpilot", "config.json")
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}


def _cfg_yaz(d):
    p = os.path.join(HOME, ".ghostpilot", "config.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(d, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def panel():
    """Yerel paneli açar (tarayıcıda durum + DURDUR + onay)."""
    head("Yerel panel")
    d = _cfg_oku()
    port = int(d.get("port") or 17381)
    url = f"http://127.0.0.1:{port}/panel"
    r = py(["doctor"])
    if "Sunucu çalışıyor" not in (r.stdout or ""):
        say("  Sunucu kapalı — önce başlatılıyor…", "warn")
        basla()
    say(f"\n  Panel adresi : {url}")
    say("  Yalnız bu bilgisayardan açılır.", "dim")
    try:
        import webbrowser
        webbrowser.open(url)
        say("  ✅ Tarayıcıda açıldı.")
    except Exception:
        say("  Tarayıcı açılamadı; adresi elle yapıştırın.", "warn")
    return 0


def mod(deger=""):
    """Salt-okunur / okuma+yazma / onay modu."""
    head("Çalışma modu")
    d = _cfg_oku()
    v = (deger or "").lower()
    if v in ("salt-okunur", "salt", "readonly", "read-only", "ro"):
        d["read_only"] = True
        _cfg_yaz(d)
        say("  ✅ SALT OKUNUR: yazma, silme, terminal ve fare/klavye KAPALI.")
        say("     Yalnız okuma, listeleme, ekran görüntüsü ve belge okuma çalışır.")
    elif v in ("yazma", "write", "rw", "normal"):
        d["read_only"] = False
        _cfg_yaz(d)
        say("  ✅ Okuma + yazma modu açık.")
    elif v in ("onay-hepsi", "hepsi"):
        d["onay"] = "hepsi"
        _cfg_yaz(d)
        say("  ✅ HER işlem panelden onay ister.")
    elif v in ("onay-riskli", "riskli"):
        d["onay"] = "riskli"
        _cfg_yaz(d)
        say("  ✅ Riskli işlemler (sil/terminal/yaz) onay ister. (varsayılan)")
    elif v in ("onay-kapali", "serbest"):
        d["onay"] = "kapali"
        _cfg_yaz(d)
        say("  ⚠️  Onay KAPALI — AI hiç sormadan işlem yapar.", "warn")
    else:
        say(f"  Şu an: salt-okunur={'AÇIK' if d.get('read_only') else 'kapalı'} · "
            f"onay={d.get('onay') or 'riskli'}")
        say("""
  Kullanım:
    python kur.py mod salt-okunur     (yalnız bak, hiç dokunma)
    python kur.py mod yazma           (okuma + yazma)
    python kur.py mod onay-hepsi      (her işlem onay bekler)
    python kur.py mod onay-riskli     (varsayılan)
    python kur.py mod onay-kapali     (hiç sorma — dikkat)
""")
    sunucuyu_yenile()
    return 0


def sunucuyu_yenile():
    """Ayar değiştiyse sunucuyu sessizce yeniden başlat (çalışıyorsa)."""
    try:
        r = py(["doctor"])
        if "Sunucu çalışıyor" in (r.stdout or ""):
            durdur(sessiz=True)
            time.sleep(1)
            basla(sessiz=True)
            say("  ↻ Sunucu yeni ayarla yeniden başlatıldı.", "dim")
    except TypeError:
        pass
    except Exception:
        pass


def guncelle(kontrol_only=False):
    head("Güncelleme")
    try:
        import guncelle as G
    except Exception as e:
        say(f"  ❌ guncelle.py bulunamadı: {e}", "err")
        return 1
    try:
        import ghostpilot
        mevcut = ghostpilot.VERSION
    except Exception:
        mevcut = "0.0.0"
    say(f"  Kurulu sürüm : {mevcut}")
    tag, url, notlar = G.son_surum()
    if not tag:
        say(f"  ❌ {notlar}", "err")
        return 1
    say(f"  Son sürüm    : {tag}")
    if not G.surum_coz(tag) > G.surum_coz(mevcut):
        say("  ✅ Güncelsiniz.")
        return 0
    if kontrol_only:
        say("  ⬆️  Güncelleme var. Kurmak için: python kur.py guncelle")
        return 0
    say("  ⬇️  İndiriliyor…")
    r = G.indir_ve_kur(HERE)
    if not r.get("ok"):
        say(f"  ❌ {r.get('error')}", "err")
        return 1
    say(f"  ✅ {r.get('version')} kuruldu ({len(r.get('files') or [])} dosya).")
    say(f"  Yedek: {r.get('backup')}", "dim")
    sunucuyu_yenile()
    return 0


def gorev(*args):
    """Zamanlanmış görevler: ekle / liste / sil."""
    head("Zamanlanmış görevler")
    try:
        import ghostpilot as G
    except Exception as e:
        say(f"  ❌ {e}", "err")
        return 1
    alt = (args[0].lower() if args else "liste")
    if alt in ("liste", "list", "ls"):
        lst = G._gorev_yukle()
        if not lst:
            say("  Kayıtlı görev yok.")
            say("""
  Örnek:
    python kur.py gorev ekle yedek "robocopy D:\\Proje E:\\Yedek /MIR" 09:30
    python kur.py gorev ekle saat "echo selam" 30        (30 dakikada bir)
""")
            return 0
        for g in lst:
            ne = g.get("when") or f"her {int((g.get('every') or 0)/60)} dk"
            son = time.strftime("%d.%m %H:%M", time.localtime(g["last_run"])) if g.get("last_run") else "hiç"
            say(f"  • {g['name']:14s} {ne:14s} son: {son:12s} "
                f"{'✅' if g.get('last_ok') else ('❌' if g.get('last_ok') is False else '·')}")
        return 0
    if alt in ("sil", "remove", "delete") and len(args) > 1:
        r = G.t_gorev_sil({"name": args[1]})
        say(f"  {'✅ Silindi' if r.get('ok') else '⚠️  Bulunamadı'} (kalan: {r.get('remaining')})")
        return 0
    if alt in ("ekle", "add") and len(args) >= 3:
        ad, cmd = args[1], args[2]
        zaman = args[3] if len(args) > 3 else ""
        a = {"name": ad, "command": cmd}
        if ":" in zaman:
            a["at"] = zaman
        else:
            a["every_minutes"] = int(zaman or 60)
        r = G.t_gorev_ekle(a)
        if r.get("ok"):
            say(f"  ✅ Eklendi: {ad} → {a.get('at') or str(a.get('every_minutes')) + ' dk'}")
        else:
            say(f"  ❌ {r.get('error')}", "err")
        return 0
    say("  Kullanım: python kur.py gorev [liste|ekle|sil] …")
    return 0


def telegram(*args):
    """Telegram bildirimini aç/kapat."""
    head("Telegram bildirimi (isteğe bağlı)")
    d = _cfg_oku()
    if not args:
        st = "AÇIK" if d.get("telegram_enabled") else "kapalı"
        say(f"  Durum: {st}")
        say("""
  Açmak için:
    python kur.py telegram <bot_token> <chat_id>
  Kapatmak için:
    python kur.py telegram kapat

  Not: Yalnızca GİDEN bildirim gönderir. Telegram'dan komut ALMAZ.
""")
        return 0
    if args[0].lower() in ("kapat", "off", "sil"):
        d["telegram_enabled"] = False
        d["telegram_token"] = ""
        d["telegram_chat"] = ""
        _cfg_yaz(d)
        say("  ✅ Telegram bildirimi kapatıldı.")
        return 0
    if len(args) < 2:
        say("  ❌ Bot token ve chat_id gerekli.", "err")
        return 1
    d["telegram_token"] = args[0].strip()
    d["telegram_chat"] = args[1].strip()
    d["telegram_enabled"] = True
    _cfg_yaz(d)
    say("  ✅ Açıldı. Test mesajı gönderiliyor…")
    try:
        import ghostpilot as G
        G.CFG.update(d)
        r = G.telegram_gonder("GhostPilot bağlandı 👻 Bu bir test mesajıdır.")
        say("  ✅ Telegram'a ulaştı." if r.get("ok") else f"  ❌ {r.get('error')}", "ok" if r.get("ok") else "err")
    except Exception as e:
        say(f"  ❌ {e}", "err")
    sunucuyu_yenile()
    return 0


def makine(ad=""):
    """Bu bilgisayara bir ad ver (birden çok makinede ayırt etmek için)."""
    head("Makine adı")
    d = _cfg_oku()
    if not ad:
        import platform
        say(f"  Şu anki ad: {d.get('machine_name') or platform.node()}")
        say("  Değiştirmek için: python kur.py makine ev-pc")
        return 0
    d["machine_name"] = ad
    _cfg_yaz(d)
    say(f"  ✅ Makine adı: {ad}")
    sunucuyu_yenile()
    return 0



def ajan(deger=""):
    """Görünür ajan imlecini/şeridini aç-kapat ve test et."""
    head("Görünür ajan (hayalet imleç + şerit)")
    d = _cfg_oku()
    v = (deger or "").lower()
    if v in ("kapat", "kapa", "off", "gizle"):
        d["show_agent"] = False
        _cfg_yaz(d)
        say("  ✅ Görsel katman KAPALI — ajan yine çalışır, sadece ekranda görünmez.")
        sunucuyu_yenile()
        return 0
    if v in ("ac", "aç", "on", "goster"):
        d["show_agent"] = True
        _cfg_yaz(d)
        say("  ✅ Görsel katman AÇIK.")
        sunucuyu_yenile()
        return 0
    durum = d.get("show_agent", True)
    say(f"  Şu an: {'AÇIK' if durum else 'kapalı'}")
    try:
        import goverlay
        ok = goverlay.start(3)
        st = goverlay.status()
        say(f"  Test: {'✅ çalışıyor' if ok else '❌ açılamadı'} {st.get('reason') or ''}")
        if ok:
            goverlay.ghost_glide(120, 120, label="GhostPilot — ben ajan imleci")
            goverlay.click_ring(120, 120, label="ekranınızda böyle görünürüm")
            say("  Şerit ve imleç ekranda göründüyse hazır.", "dim")
    except Exception as e:
        say(f"  ❌ Görsel katman yok: {e}", "err")
        say("  Not: tkinter gerekir (Windows Python'da hazırdır).", "dim")
    say("""
  Aç / kapat:
    python kur.py ajan ac
    python kur.py ajan kapat
""")
    return 0



def simge():
    """İkonu gösterir — ChatGPT formuna yüklenecek dosyayı hazırlar."""
    head("GhostPilot simgesi")
    adaylar = [
        ("ChatGPT formu için (≤10 KB)", "chatgpt-icon-256.png"),
        ("Claude / tarayıcı favicon", "favicon.ico"),
        ("Panel / web simgesi", "icon.png"),
        ("Vektör (her boyut)", "icon.svg"),
    ]
    bulunan = []
    for etiket, ad in adaylar:
        yol = os.path.join(HERE, ad)
        if os.path.exists(yol):
            kb = os.path.getsize(yol) / 1024
            say(f"  {etiket:28s} {ad:22s} {kb:6.2f} KB")
            bulunan.append(yol)
        else:
            say(f"  {etiket:28s} {ad:22s} (yok — 'python simge_uret.py' çalıştırın)", "warn")

    if not bulunan:
        return 1

    say("""
  ChatGPT'ye ekleme:
    1) chatgpt.com → Ayarlar → Bağlayıcılar (Apps) → Ekle
    2) "Simge / Icon" alanına şu dosyayı yükleyin:
""")
    say(f"       {os.path.join(HERE, 'chatgpt-icon-256.png')}")
    say("""
    Not: Bağlayıcı zaten ekliyse simge değişmez — SİLİP yeniden ekleyin.
  Panelde: tarayıcı sekmesindeki simge kendiliğinden görünür.
  Claude: sunucunun favicon'unu otomatik alır (/favicon.ico).
""")
    try:
        import webbrowser
        hedef = os.path.join(HERE, "chatgpt-icon-256.png")
        if os.path.exists(hedef):
            webbrowser.open("file://" + hedef.replace("\\", "/"))
            say("  ✅ Simge görüntüleyicide açıldı.", "dim")
    except Exception:
        pass
    return 0



def paketler():
    """Free / PRO karşılaştırması — fiyat tek yerden (paketler.py)."""
    head("Paketler — ücretsiz ve destek paketi")
    try:
        import paketler as PK
        say(PK.satir_metinleri())
        say("")
        say("  Destek olmak için:", "dim")
        say(f"    {PK.BAGIS_URL}")
        say("")
        say("  Anahtar aldıktan sonra:", "dim")
        say("    python kur.py lisans GP-...        (etkinleştir)")
        say("    python kur.py lisans               (durumu göster)")
    except Exception as e:
        say(f"  ❌ {e}", "err")
    say("")
    return 0


def lisans(anahtar=""):
    """GhostPilot Pro lisansını göster / etkinleştir."""
    head("GhostPilot Pro — lisans")
    try:
        import ghostpilot as G
    except Exception as e:
        say(f"  ❌ {e}", "err")
        return 1
    if not anahtar:
        kd = G.kota_durum()
        say(f"  Plan        : {'PRO (sınırsız)' if kd['pro'] else 'Ücretsiz'}")
        if kd.get("lisans"):
            b = G.lisans_bilgi(kd["lisans"])
            say(f"  Paket       : {b.get('plan_adi', '—')}")
            say(f"  Bitiş       : {b.get('bitis', '?')}  (kalan {b.get('kalan_gun', '?')} gün)")
            say(f"  Lisans no   : {b.get('id', '?')} · {b.get('bagli_metin', '—')}")
            say(f"  Bu makine   : {G.makine_kimligi()}")
            if b.get("yenile"):
                say("  ⏳ Süre dolmak üzere — yenilemek için destek sayfası:", "warn")
                say(f"     {G.BAGIS_URL}", "warn")
        try:
            import paketler as PK
            say(f"  PRO fiyatı  : {PK.PARA_BIRIMI}{PK.AYLIK_FIYAT}{PK.m('ay')}"
                f"  →  {PK.BAGIS_URL}", "dim")
        except Exception:
            pass
        say(f"  Bu ay       : {kd['kullanilan']:,} / {kd['limit']:,} çağrı")
        say(f"  Kalan       : {kd['kalan']:,}")
        if kd["kurcalandi"]:
            say("  ⚠️  Kota dosyası kurcalanmış görünüyor.", "warn")
        if kd.get("pro_iptal"):
            say(f"  ⛔ Paket sona erdi: {kd.get('pro_iptal_neden', '')}", "err")
            say(f"     Yenilemek için: {G.BAGIS_URL}")
            say("     Yeni anahtar:  python kur.py lisans <yeni-anahtar>")
        if kd["pro"]:
            say("  ✅ Sınırsız kullanım açık.", "ok")
            try:
                b2 = G.lisans_bilgi(kd.get("lisans") or "")
                say(f"  📱 Bu bilgisayar: {G.makine_kimligi()[:12]}…  "
                    f"(anahtar: {b2.get('id','?')})", "dim")
            except Exception:
                pass
        else:
            say("")
            say("  GhostPilot ücretsiz ve açık kaynak.")
            say("  Sınırsız kullanım için BTM Code'dan bir DESTEK anahtarı isteyin:")
            say("    https://buymeacoffee.com/btmcode")
            say("  Anahtarınız varsa:  python kur.py lisans <anahtar>")
        return 0
    r = G.lisans_ayarla(anahtar)
    say(("  ✅ " + r.get("message", "")) if r.get("ok") else f"  ❌ {r.get('error')}",
        "ok" if r.get("ok") else "err")
    sunucuyu_yenile()
    return 0 if r.get("ok") else 1


def kota():
    """Bu ayın kullanımını göster."""
    head("Aylık kullanım")
    try:
        import ghostpilot as G
        kd = G.kota_durum()
    except Exception as e:
        say(f"  ❌ {e}", "err")
        return 1
    dolu = int(round(kd["yuzde"] / 5))
    cubuk = "█" * dolu + "░" * (20 - dolu)
    say(f"  {kd['ay']}   {cubuk}  {kd['yuzde']}%")
    say(f"  {kd['kullanilan']:,} / {kd['limit']:,} çağrı  ·  kalan {kd['kalan']:,}")
    if kd["pro"]:
        say("  ✅ Pro — sınırsız", "ok")
    elif kd["asis"]:
        say("  ⛔ Sınır doldu. Görsel katman kapandı; Pro ile açılır.", "err")
    else:
        say("  ℹ️  Ücretsiz plan.", "dim")
    return 0


# ============================================================================
#  MENÜ
# ============================================================================

def menu():
    while True:
        head("GhostPilot — bilgisayarınız için sessiz yardımcı")
        say("""
  1) Claude Desktop'a bağla        (en kolay, tünel gerekmez)
  2) ChatGPT / tarayıcı AI'ya bağla (Tailscale ile HTTPS tünel)
  3) Cursor / VS Code'a bağla
  4) Kurulumu denetle (doctor)
  5) Yeni erişim anahtarı
  6) Kayıtları geri al
  7) Sunucuyu başlat (ChatGPT bağlantısı için açık kalmalı)
  8) Uçtan uca test
  9) Klasör izni ekle (örn. D:\\AiProjelerim)
 10) Bilgisayar açılınca otomatik başlat
 11) ⚡ TEK TUŞ — her şeyi otomatik kur
 12) Bağlantı güvenliği (URL anahtarı aç/kapat)
 13) OAuth izinlerini göster / iptal et
 14) Sunucu durumu (çalışıyor mu, bekçi var mı)
 15) Sunucuyu durdur (bekçi de durur)
 16) ⛔ TAMAMEN KAPAT (sunucu + otomatik başlatma + tünel)
 17) Sunucuyu yeniden başlat
 18) 🌐 Yerel panel (tarayıcıda DURDUR + onay)
 19) 👁 Mod: salt okunur / yazma / onay
 20) ⬆️  Güncelleme var mı
 21) ⏰ Zamanlanmış görevler
 22) 📨 Telegram bildirimi
 23) 👻 Görünür ajan (imleç testi)
 24) 🖼️  Simge (ChatGPT'ye yüklenecek dosya)
 25) 💎 Lisans / Pro (aylık kullanım)
 26) 🧹 Aylık sayacı sıfırla (lisans korunur)
 27) 📱 Bu bilgisayarın kimliği
 28) 🧰 Eksikleri kur / onar (Python · Pillow · Tailscale)
 29) 🖥️  Masaüstü kısayolu oluştur
 30) 🪟 Program arayüzü (pencere)
 31) 🌍 Dil değiştir (TR/EN/DE/ES)
 32) 📦 Sanal ortam (.venv) durumu
 33) 🗑️  GhostPilot'u kaldır (uninstall)
 34) ☁️  Lisans sunucusu (çevrimiçi doğrulama)
 35) 💎 Paketler ve fiyat (ücretsiz / PRO 10$)
  0) Çıkış
""")
        try:
            sec = input("  Seçim: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if sec == "1":
            install_client("claude")
        elif sec == "2":
            chatgpt_setup()
        elif sec == "3":
            install_client("cursor")
            install_client("vscode")
        elif sec == "4":
            r = py(["doctor"])
            print(r.stdout)
            if getattr(r, "stderr", "") and r.returncode != 0:
                say(f"  stderr: {r.stderr[:400]}", "warn")
        elif sec == "5":
            print(py(["token"]).stdout)
        elif sec == "6":
            uninstall_clients()
        elif sec == "7":
            start_relay()
        elif sec == "8":
            run_test()
        elif sec == "9":
            try:
                yol = input("  Klasör yolu (örn. D:\\AiProjelerim): ").strip().strip('"')
            except (EOFError, KeyboardInterrupt):
                yol = ""
            if yol:
                izin([yol])
        elif sec == "10":
            otomatik()
        elif sec == "11":
            oto()
        elif sec == "12":
            guvenlik([])
        elif sec == "14":
            durum()
        elif sec == "15":
            durdur()
        elif sec == "16":
            tam_kapat()
        elif sec == "17":
            basla()
        elif sec == "18":
            panel()
        elif sec == "19":
            mod()
        elif sec == "20":
            guncelle(kontrol_only=True)
        elif sec == "21":
            gorev()
        elif sec == "22":
            telegram()
        elif sec == "23":
            ajan()
        elif sec == "24":
            simge()
        elif sec == "25":
            lisans()
        elif sec == "26":
            import ghostpilot as G
            say("  " + G.kota_sifirla()["mesaj"], "ok")
        elif sec == "27":
            import ghostpilot as G
            say(f"  {G.makine_kimligi()}")
        elif sec == "28":
            gereksinimler()
        elif sec == "29":
            import kisayol as _KS
            _KS.ekle()
        elif sec == "30":
            import ui as _UI
            _UI.main()
        elif sec == "31":
            import diller as _DI
            say("  Diller: " + " · ".join(f"{i+1}) {k.upper()} {v}" for i, (k, v) in
                                          enumerate(_DI.DILLER.items())))
            try:
                sec2 = input("  Seçim (1-4): ").strip()
                kod = list(_DI.DILLER)[int(sec2) - 1]
                _DI.dil_sec(kod)
                say(f"  ✅ Dil: {_DI.DILLER[kod]}", "ok")
            except (ValueError, IndexError, EOFError, KeyboardInterrupt):
                pass
        elif sec == "34":
            say("  " + (__import__("lisans_online").sunucu_url() or "(tanımlı değil)"))
            try:
                u = input("  Adres (boş = durum): ").strip()
            except (EOFError, KeyboardInterrupt):
                u = ""
            if u:
                import lisans_online as _LO
                d = load_cfg_file()
                d["lisans_url"] = u.rstrip("/")
                save_cfg_file(d)
                say(f"  ✅ {d['lisans_url']}", "ok")
        elif sec == "35":
            paketler()
            try:
                input("  Devam etmek için Enter… ")
            except (EOFError, KeyboardInterrupt):
                pass
        elif sec == "33":
            import kaldir as _KAL
            return _KAL.kaldir()
        elif sec == "32":
            import sanalortam as _SO
            b = _SO.bilgi()
            say(f"  {'✅' if b['var'] else '❌'} sanal ortam: {b['yol'] or 'yok'}"
                + (f" (Python {b['surum']})" if b['var'] else ""))
        elif sec == "13":
            oauth_durum()
            try:
                if input("\n  Tüm izinler iptal edilsin mi? (e/H): ").strip().lower() == "e":
                    oauth_sil()
            except (EOFError, KeyboardInterrupt):
                print()
        elif sec == "0":
            return 0
        try:
            input("\n  Enter ile menüye dön…")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0


def main():
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
    if not os.path.exists(SERVER):
        say(f"  ❌ ghostpilot.py bulunamadı: {SERVER}", "err")
        return 1
    if cmd in ("paketler", "paket", "plans", "fiyat", "pricing"):
        return paketler()
    if cmd in ("lisans", "license", "pro"):
        return lisans(sys.argv[2] if len(sys.argv) > 2 else "")
    if cmd in ("kota", "quota", "kullanim"):
        return kota()
    if cmd in ("kota-sifirla", "kota-temizle", "sifirla"):
        import ghostpilot as G
        r = G.kota_sifirla()
        say(f"  ✅ {r['mesaj']} (lisans korundu)", "ok")
        return 0
    if cmd in ("lisans-kaldir", "lisans-iptal", "pro-kaldir"):
        import ghostpilot as G
        r = G.lisans_iptal()
        say(f"  ✅ {r['mesaj']}", "ok")
        return 0
    if cmd in ("lisans-sunucu", "lisans-url", "sunucu-lisans"):
        import lisans_online as _LO
        alt = (sys.argv[2] if len(sys.argv) > 2 else "").strip()
        d = load_cfg_file()
        if alt in ("", "durum", "goster"):
            say(f"  Lisans sunucusu : {_LO.sunucu_url() or '(tanımlı değil — çevrimdışı mod)'}")
            try:
                d2 = _LO._oku()
                say(f"  Son sorgu       : {time.strftime('%Y-%m-%d %H:%M', time.localtime(float(d2.get('t') or 0)))}")
                say(f"  Son sonuç       : {'geçerli' if d2.get('ok') else 'reddedildi'} · {d2.get('mesaj','')}")
            except Exception:
                pass
            say("  Ayarlamak için  : python kur.py lisans-sunucu https://sizin-adres")
            say("  Kaldırmak için  : python kur.py lisans-sunucu sil")
            return 0
        if alt in ("sil", "kaldir", "off"):
            d.pop("lisans_url", None)
            save_cfg_file(d)
            say("  ✅ Lisans sunucusu kaldırıldı — çevrimdışı moda dönüldü.", "ok")
            return 0
        d["lisans_url"] = alt.rstrip("/")
        save_cfg_file(d)
        say(f"  ✅ Lisans sunucusu: {d['lisans_url']}", "ok")
        say("     Şimdi her açılışta/6 saatte bir oraya sorulur.")
        try:
            import lisans_online as _LO2
            r = _LO2._sor("AYLIKX8F5196", _LO2._makine(), d["lisans_url"])
            say(f"     Bağlantı testi: {'✅ çalışıyor' if r is not None else '⚠️  ulaşılamadı'}")
        except Exception:
            pass
        return 0
    if cmd in ("kaldir", "uninstall", "sil"):
        import kaldir as _KAL
        alt = sys.argv[2:] if len(sys.argv) > 2 else []
        if "--tum" in alt or "--all" in alt:
            return _KAL.kaldir(tum=True)
        if "--sessiz" in alt:
            return _KAL.kaldir(sessiz=True)
        if "durum" in alt:
            return _KAL.durum()
        return _KAL.kaldir()
    if cmd in ("ui", "arayuz", "arayüz", "pencere", "gui"):
        import ui as _UI
        return _UI.main()
    if cmd in ("dil", "language", "lang"):
        import diller as _DI
        alt = (sys.argv[2] if len(sys.argv) > 2 else "")
        if alt in _DI.DILLER:
            _DI.dil_sec(alt)
            say(f"  ✅ Dil: {_DI.DILLER[alt]}", "ok")
        else:
            say("  Diller: " + " · ".join(f"{k}={v}" for k, v in _DI.DILLER.items()))
            say(f"  Şu an: {_DI.DILLER.get(_DI.dil(), _DI.dil())}")
        return 0
    if cmd in ("venv", "sanalortam", "sanal-ortam"):
        import sanalortam as _SO
        alt = (sys.argv[2] if len(sys.argv) > 2 else "durum")
        return 0 if _SO.main.__call__ and (subprocess.call(
            [sys.executable, os.path.join(HERE, "sanalortam.py"), alt]) == 0) else 1
    if cmd in ("kisayol", "masaustu", "shortcut"):
        import kisayol as _KS
        alt = (sys.argv[2] if len(sys.argv) > 2 else "ekle").lower()
        if alt in ("kaldir", "sil"):
            _KS.kaldir()
        elif alt in ("durum", "goster"):
            _KS.durum()
        else:
            _KS.ekle()
        return 0
    if cmd in ("cihaz", "makine-kimlik", "device"):
        import ghostpilot as G
        head("Bu bilgisayarın kimliği")
        say(f"  {G.makine_kimligi()}")
        say("  (Lisans ve aylık sayaç bu kimliğe bağlıdır.)", "dim")
        return 0
    if cmd in ("simge", "icon", "logo", "ikon"):
        return simge()
    if cmd in ("ajan", "overlay", "gorunur", "imlec"):
        return ajan(sys.argv[2] if len(sys.argv) > 2 else "")
    if cmd in ("panel", "web", "arayuz"):
        return panel()
    if cmd in ("mod", "mode", "salt-okunur", "readonly"):
        return mod(sys.argv[2] if len(sys.argv) > 2 else
                   ("salt-okunur" if cmd == "salt-okunur" else ""))
    if cmd in ("guncelle", "update", "yukselt"):
        return guncelle(kontrol_only="--kontrol" in sys.argv)
    if cmd in ("gorev", "gorevler", "schedule", "cron"):
        return gorev(*sys.argv[2:])
    if cmd in ("telegram", "tg", "bildirim"):
        return telegram(*sys.argv[2:])
    if cmd in ("makine", "machine", "isim"):
        return makine(sys.argv[2] if len(sys.argv) > 2 else "")
    if cmd in ("", "menu", "kur", "install"):
        return menu()
    if cmd in CLIENTS:
        return install_client(cmd)
    if cmd in ("chatgpt", "uzak", "relay"):
        return chatgpt_setup()
    if cmd == "doctor":
        print(py(["doctor"]).stdout)
        return 0
    if cmd == "token":
        print(py(["token"]).stdout)
        return 0
    if cmd in ("durum", "status"):
        return durum()
    if cmd in ("durdur", "stop"):
        return durdur()
    if cmd in ("kapat", "tam-kapat", "off"):
        return tam_kapat()
    if cmd in ("basla", "start", "ac"):
        return basla()
    if cmd in ("oauth", "oauth-durum"):
        return oauth_durum()
    if cmd in ("oauth-sil", "oauth-iptal"):
        return oauth_sil()
    if cmd == "guvenlik":
        return guvenlik(sys.argv[2:])
    if cmd in ("oto", "otomatik-kurulum", "auto", "ful"):
        return oto()
    if cmd in ("onar", "gereksinim", "gereksinimler", "hazirla", "setup", "repair"):
        return 0 if otomatik_kur() == 0 else 1
    if cmd in ("python-kur", "pythonkur"):
        return 0 if python_kur() else 1
    if cmd in ("tailscale-kur", "tailscalekur"):
        return 0 if tailscale_kur() else 1
    if cmd == "izin":
        return izin(sys.argv[2:])
    if cmd in ("izin-sil",):
        return izin_sil(sys.argv[2:])
    if cmd in ("otomatik", "autostart"):
        return otomatik()
    if cmd in ("otomatik-kaldir", "noautostart"):
        return otomatik(kapat=True)
    if cmd in ("sunucu", "server", "relay", "baslat"):
        return start_relay()
    if cmd in ("test", "tani"):
        return run_test()
    if cmd in ("kaldir", "uninstall", "remove"):
        return uninstall_clients()
    say(f"  Bilinmeyen komut: {cmd}", "err")
    say("  Geçerli: oto | claude | chatgpt | cursor | vscode | sunucu | test | doctor\n"
        "           token | izin <yol> | izin-sil <yol> | otomatik | otomatik-kaldir | kaldir")
    return 1


if __name__ == "__main__":
    sys.exit(main())

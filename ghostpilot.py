# lis an.py'nin SHA-256 özeti (paketlenirken `simge_uret.py` benzeri bir adımda
# yazılır). Boşsa kontrol atlanır. Amaç: dosyayı değiştirip doğrulamayı
# kaldırmayı fark etmek — caydırıcı, kırılmaz değil.
LISANS_DOSYA_OZETI = "470540540a73079ccdc9753668e389d3565c9985d7a3b8fdbea13e0c4575401d"


def _lisans_butunluk():
    try:
        if not LISANS_DOSYA_OZETI:
            return True
        import hashlib
        yol = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lisans.py")
        with open(yol, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest() == LISANS_DOSYA_OZETI
    except Exception:
        return False


def lisans_dogrula(anahtar):
    """Ed25519 imza doğrulaması — sır BURADA DEĞİL, yalnız açık anahtar.

    Kod açık kaynak olsa bile kimse geçerli anahtar üretemez; üretmek için
    BTM Code'un özel anahtarı gerekir.
    """
    if not _lisans_butunluk():
        audit("lisans-butunluk", "lisans.py değiştirilmiş", ok=False)
        return False, ("lisans doğrulama dosyası değiştirilmiş görünüyor — "
                       "kurulumu yeniden yapın")
    try:
        import lisans as _L
        return _L.dogrula(anahtar)
    except Exception as e:
        return False, f"lisans modülü yüklenemedi: {e}"


def lisans_bilgi(anahtar):
    try:
        import lisans as _L
        return _L.bilgi(anahtar)
    except Exception as e:
        return {"ok": False, "error": str(e)}


def lisans_ayarla(anahtar):
    b = lisans_bilgi(anahtar)
    if not b.get("ok"):
        return {"ok": False, "error": f"Geçersiz lisans: {b.get('error')}"}
    with KOTA_KILIT:
        d = _kota_yukle()
        d["pro"] = True
        d["lisans"] = anahtar.strip()
        d["son"] = time.time()
        _kota_yaz(d)
    audit("lisans", f"etkinleştirildi ({b.get('id')}) — {b.get('bagli_metin','')}")
    return {"ok": True, "pro": True, "id": b.get("id"),
            "message": (f"GhostPilot Pro etkinleştirildi ({b.get('bitis')}). "
                        f"Kilit: {b.get('bagli_metin', '—')}.")}


def kota_sifirla():
    """Sayacı temizler (yanlış kurcalama alarmı için). Lisans korunur."""
    with KOTA_KILIT:
        d = _kota_yukle()
        yeni = _kota_bos()
        yeni["pro"] = bool(d.get("pro"))
        yeni["lisans"] = d.get("lisans") or ""
        _kota_yaz(yeni)
        _kayit_yaz({"ay": yeni["ay"], "kullanilan": 0, "toplam": 0,
                    "_b": _kayit_butunluk(yeni["ay"], 0, 0),
                    "_makine": makine_kimligi()})
        try:
            os.remove(KOTA_AUDIT_ISARET)
        except Exception:
            pass
    audit("kota-sifirla", "sayaç sıfırlandı")
    return {"ok": True, "mesaj": "Aylık sayaç sıfırlandı."}


def lisans_iptal():
    """Pro'yu kaldırır (anahtar başka makineye taşınacaksa)."""
    with KOTA_KILIT:
        d = _kota_yukle()
        d["pro"] = False
        d["lisans"] = ""
        _kota_yaz(d)
    audit("lisans-iptal", "pro kaldırıldı")
    return {"ok": True, "mesaj": "Lisans kaldırıldı — ücretsiz plana dönüldü."}


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot MCP v3.0.0 — tek dosya, sıfır bağımlılık
#  Copyright (c) 2026 BTM Code — MIT License
#  https://btmcode.vercel.app  ·  https://github.com/Btmcode/Ghost-Pilot
#
#  Bilgisayarınıza şu 3 şeyi verir:
#    1) Köprü (bridge)  : stdio          → Claude Desktop / Cursor / VS Code
#    2) Uzak (relay)    : HTTPS + token  → ChatGPT / Arena / tarayıcıdaki her AI
#    3) Araçlar         : dosya, terminal, ekran
#
#  Kullanım:
#    python ghostpilot.py            → ne yapacağını söyler
#    python ghostpilot.py doctor     → kurulumu denetler (İLK BUNU ÇALIŞTIRIN)
#    python ghostpilot.py bridge     → stdio MCP sunucusu
#    python ghostpilot.py relay      → HTTPS köprüsü (ChatGPT için)
#    python ghostpilot.py token      → yeni erişim anahtarı
#    python ghostpilot.py tools      → 24 aracı listeler
# ============================================================================

import base64
import hashlib
import io as _io
import json
import os
import platform
import re
import secrets
import shutil
import socket
import ssl
import subprocess
import sys
import threading
import time


# Windows'ta alt süreçler konsol penceresi açmasın (pythonw.exe yanıp sönmesin)
SESSIZ = {}
if sys.platform.startswith("win"):
    SESSIZ["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

VERSION = "5.23.0"

# Windows konsolu varsayılan olarak cp1254/cp1252 kullanır ve emoji yazınca
# UnicodeEncodeError ile çöker. Hem kendimiz hem alt süreçler için UTF-8'e geç.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
OS_NAME = platform.system()  # "Windows" | "Linux" | "Darwin"
IS_WIN = OS_NAME == "Windows"
HOME = os.path.expanduser("~")
CFG_DIR = os.path.join(HOME, ".ghostpilot")
CFG_FILE = os.path.join(CFG_DIR, "config.json")
TOKEN_FILE = os.path.join(CFG_DIR, "token")
DEFAULT_PORT = 17381
MAX_FILE_BYTES = 2 * 1024 * 1024      # 2 MB — dosya okuma sınırı
MAX_OUTPUT = 40_000                    # komut çıktısı karakter sınırı

# ============================================================================
#  AYARLAR
# ============================================================================

DEFAULT_CFG = {
    "port": DEFAULT_PORT,
    "read_roots": [HOME],
    "write_roots": [HOME, os.path.join(HOME, "Desktop"), os.path.join(HOME, "Documents")],
    "blocked_paths": [],
    "allow_shell": True,
    "allow_screen": True,
    "shell_timeout": 60,
    "log": True,
    # GÜVENLİK: varsayılan olarak kimlik doğrulama ZORUNLU.
    # - OAuth (ChatGPT'nin "OAuth" seçeneği) birincil yol
    # - Bearer / ?token= ikincil yol (Claude Desktop, curl, elle test)
    # Kapatmak için: python kur.py guvenlik kapat   (ÖNERİLMEZ)
    "require_token": True,
    # Salt-okunur mod: yazma/silme/terminal/girdi KAPALI, yalnız bakılabilir
    "read_only": False,
    # Onay: "riskli" (sil/terminal/yaz varsayılan), "hepsi", "kapali"
    "onay": "riskli",
    # Ajan ekranda görünsün mü (hayalet imleç + şerit)
    "show_agent": True,
    # Telegram bildirimi — varsayılan KAPALI
    "telegram_enabled": False,
    "telegram_token": "",
    "telegram_chat": "",
    # ChatGPT'nin istemci kimliği önceden yazılabilir; boşsa otomatik kayıt
    # (Dynamic Client Registration) devreye girer.
    "oauth_client_id": "",
    "oauth_client_secret": "",
}


def _mkdir(p):
    try:
        os.makedirs(p, mode=0o700, exist_ok=True)
    except Exception:
        pass


def load_cfg():
    _mkdir(CFG_DIR)
    cfg = dict(DEFAULT_CFG)
    try:
        if os.path.exists(CFG_FILE):
            with open(CFG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f) or {})
    except Exception:
        pass
    return cfg


def save_cfg(cfg):
    _mkdir(CFG_DIR)
    try:
        with open(CFG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        try:
            os.chmod(CFG_FILE, 0o600)
        except Exception:
            pass
    except Exception as e:
        print(f"[uyarı] ayar yazılamadı: {e}", file=sys.stderr)


def load_token(create=True):
    env = (os.environ.get("GHOSTPILOT_TOKEN") or "").strip()
    if env:
        return env
    _mkdir(CFG_DIR)
    try:
        if os.path.exists(TOKEN_FILE):
            t = open(TOKEN_FILE, "r", encoding="utf-8").read().strip()
            if len(t) >= 24:
                return t
        if not create:
            return ""
        t = secrets.token_urlsafe(32)
        fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(t)
        return t
    except Exception:
        return secrets.token_urlsafe(32)


CFG = load_cfg()
TOKEN = load_token()
AUDIT_LOCK = threading.Lock()


def audit(action, detail, ok=True):
    if not CFG.get("log"):
        return
    try:
        line = json.dumps({
            "t": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "action": action, "ok": bool(ok), "detail": str(detail)[:300],
        }, ensure_ascii=False)
        with AUDIT_LOCK:
            with open(os.path.join(CFG_DIR, "audit.log"), "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception:
        pass


# ============================================================================
#  GÜVENLİK — yol ve komut denetimi
# ============================================================================

SHELL_BLOCKLIST = [
    # geri dönüşü olmayan / sistem bozucu komutlar
    "rm -rf /", "rm -rf /*", "rmdir /s /q c:\\", "format c:", "del /f /s /q c:\\",
    "mkfs", "dd if=", ":(){", "shutdown", "reboot", "poweroff", "halt ",
    "diskpart", "bcdedit", "vssadmin delete", "cipher /w",
    # kimlik bilgisi sızdırma
    "mimikatz", "reg save hklm\\sam", "reg save hklm\\system",
]


def check_command(cmd):
    low = cmd.lower().strip()
    for bad in SHELL_BLOCKLIST:
        if bad in low:
            return False, f"Engellendi: geri dönüşü olmayan komut içeriyor ('{bad}')."
    return True, ""


def _real(p):
    try:
        return os.path.realpath(os.path.expanduser(os.path.expandvars(str(p))))
    except Exception:
        return ""


def _inside(path, roots):
    rp = _real(path)
    if not rp:
        return False
    for r in roots:
        rr = _real(r)
        if not rr:
            continue
        try:
            if os.path.commonpath([rp, rr]) == rr:
                return True
        except ValueError:
            continue
    return False


def _sanal():
    try:
        import sanaldunya
        return sanaldunya
    except Exception:
        return None


def check_read(path):
    sd = _sanal()
    if sd and sd.acik(CFG):
        # SANAL BİLGİSAYAR: her yer serbest (yalnız sanal kök içinde)
        if _inside(path, sd.kokler()):
            return True, ""
        # sanal kök dışına çıkmak istenirse sanal köke yönlendir
        return False, ("Sanal bilgisayar modu açık — yalnız sanal klasörde "
                       "çalışılır: %s" % sd.kok_klasor())
    if _inside(path, CFG.get("blocked_paths") or []):
        return False, "Bu yol engelli listesinde."
    if not _inside(path, CFG.get("read_roots") or [HOME]):
        return False, "Bu yol okuma izni verilen klasörlerin dışında."
    return True, ""


def check_write(path):
    sd = _sanal()
    if sd and sd.acik(CFG):
        if _inside(path, sd.kokler()):
            return True, ""
        return False, ("Sanal bilgisayar modu açık — yalnız sanal klasörde "
                       "yazılabilir: %s" % sd.kok_klasor())
    if _inside(path, CFG.get("blocked_paths") or []):
        return False, "Bu yol engelli listesinde."
    if not _inside(path, CFG.get("write_roots") or [HOME]):
        return False, "Bu yol yazma izni verilen klasörlerin dışında."
    return True, ""


# ============================================================================
#  YETENEKLER — ne yapabildiğimizi dürüstçe bildirir
# ============================================================================

def caps():
    sd = _sanal()
    c = {
        "os": OS_NAME,
        "virtual_computer": bool(sd and sd.acik(CFG)),
        "virtual_root": (sd.kok_klasor() if sd and sd.acik(CFG) else ""),
        "files": True,
        "shell": bool(CFG.get("allow_shell")),
        "screen": False,
        "input": False,
        "screen_backend": None,
        "input_backend": None,
        "requires_cursor": False,
        "note": "",
    }
    if not CFG.get("allow_screen"):
        c["note"] = "Ekran kontrolü ayarlardan kapatılmış."
        return c
    try:
        import screen  # aynı klasördeki modül
        info = screen.capabilities()
        c.update({
            "screen": bool(info.get("screen")),
            "input": bool(info.get("input")),
            "screen_backend": info.get("screen_backend"),
            "input_backend": info.get("input_backend"),
            "requires_cursor": bool(info.get("requires_cursor")),
            "screen_size": info.get("size"),
            "note": info.get("note", ""),
        })
    except Exception as e:
        c["note"] = f"Ekran modülü yüklenemedi: {e}"
    return c


# ============================================================================
#  ARAÇLAR
# ============================================================================

def t_status(_a):
    c = caps()
    return {
        "ok": True,
        "version": VERSION,
        "host": socket.gethostname(),
        "user": os.environ.get("USERNAME") or os.environ.get("USER") or "",
        "os": OS_NAME,
        "capabilities": c,
        "config": {
            "read_roots": CFG.get("read_roots"),
            "write_roots": CFG.get("write_roots"),
            "allow_shell": CFG.get("allow_shell"),
            "allow_screen": CFG.get("allow_screen"),
            "shell_timeout": CFG.get("shell_timeout"),
        },
        "uptime_s": round(time.time() - START_TIME),
    }


def t_ls(a):
    path = a.get("path") or HOME
    ok, why = check_read(path)
    if not ok:
        return {"ok": False, "error": why}
    if not os.path.isdir(path):
        return {"ok": False, "error": "Klasör değil veya yok."}
    show_hidden = bool(a.get("hidden"))
    items = []
    try:
        for name in sorted(os.listdir(path), key=str.lower):
            if not show_hidden and name.startswith("."):
                continue
            full = os.path.join(path, name)
            try:
                st = os.stat(full)
                items.append({
                    "name": name,
                    "type": "dir" if os.path.isdir(full) else "file",
                    "size": None if os.path.isdir(full) else st.st_size,
                    "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)),
                })
            except OSError:
                continue
            if len(items) >= 500:
                break
    except PermissionError:
        return {"ok": False, "error": "Erişim reddedildi (yönetici izni gerekli)."}
    return {"ok": True, "path": _real(path), "count": len(items), "items": items}


def t_read(a):
    path = a.get("path") or ""
    if not path:
        return {"ok": False, "error": "path gerekli."}
    ok, why = check_read(path)
    if not ok:
        return {"ok": False, "error": why}
    if not os.path.isfile(path):
        return {"ok": False, "error": "Dosya yok."}
    size = os.path.getsize(path)
    if size > MAX_FILE_BYTES:
        return {"ok": False, "error": f"Dosya çok büyük ({size} bayt > {MAX_FILE_BYTES})."}
    try:
        head = open(path, "rb").read(2048)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    if b"\x00" in head:
        return {"ok": False, "error": "İkili (binary) dosya — metin olarak okunamaz. "
                                      "Görsel ise screenshot/read değil, dosya yolu ile işleyin."}
    try:
        txt = open(path, "r", encoding="utf-8", errors="replace").read()
    except Exception as e:
        return {"ok": False, "error": str(e)}
    truncated = False
    if len(txt) > MAX_OUTPUT:
        txt = txt[:MAX_OUTPUT]
        truncated = True
    return {"ok": True, "path": _real(path), "bytes": size,
            "truncated": truncated, "content": txt}


def t_write(a):
    path = a.get("path") or ""
    content = a.get("content", "")
    mode = (a.get("mode") or "overwrite").lower()
    if not path:
        return {"ok": False, "error": "path gerekli."}
    ok, why = check_write(path)
    if not ok:
        return {"ok": False, "error": why}
    try:
        os.makedirs(os.path.dirname(_real(path)) or ".", exist_ok=True)
        if mode == "append":
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "path": _real(path), "bytes": os.path.getsize(path), "mode": mode}


def t_edit(a):
    path = a.get("path") or ""
    old = a.get("old", "")
    new = a.get("new", "")
    if not path or not old:
        return {"ok": False, "error": "path ve old gerekli."}
    ok, why = check_read(path)
    if not ok:
        return {"ok": False, "error": why}
    ok, why = check_write(path)
    if not ok:
        return {"ok": False, "error": why}
    try:
        s = open(path, "r", encoding="utf-8", errors="replace").read()
    except Exception as e:
        return {"ok": False, "error": str(e)}
    n = s.count(old)
    if n == 0:
        return {"ok": False, "error": "Aranan metin bulunamadı."}
    if n > 1 and not a.get("all"):
        return {"ok": False, "error": f"Metin {n} kez geçiyor. Daha uzun bir parça verin veya all=true."}
    s = s.replace(old, new) if a.get("all") else s.replace(old, new, 1)
    try:
        open(path, "w", encoding="utf-8").write(s)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "path": _real(path), "replaced": n}


def t_glob(a):
    import fnmatch
    root = a.get("path") or HOME
    pat = a.get("pattern") or "*"
    ok, why = check_read(root)
    if not ok:
        return {"ok": False, "error": why}
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        if len(hits) >= 300:
            break
        if not a.get("hidden"):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for fn in filenames:
            if fnmatch.fnmatch(fn.lower(), pat.lower()):
                hits.append(os.path.join(dirpath, fn))
                if len(hits) >= 300:
                    break
    return {"ok": True, "root": _real(root), "count": len(hits), "files": hits}


def t_grep(a):
    import re as _re
    pat = a.get("pattern") or ""
    root = a.get("path") or HOME
    if not pat:
        return {"ok": False, "error": "pattern gerekli."}
    ok, why = check_read(root)
    if not ok:
        return {"ok": False, "error": why}
    try:
        rx = _re.compile(pat, _re.I)
    except _re.error as e:
        return {"ok": False, "error": f"Geçersiz düzenli ifade: {e}"}
    hits, scanned = [], 0
    exts = a.get("extensions") or []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in
                       ("node_modules", "__pycache__", ".git", "venv", ".venv")]
        for fn in filenames:
            if exts and not any(fn.lower().endswith(e.lower()) for e in exts):
                continue
            full = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(full) > 512_000:
                    continue
                scanned += 1
                with open(full, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if rx.search(line):
                            hits.append({"file": full, "line": i, "text": line.strip()[:200]})
                            if len(hits) >= 150:
                                return {"ok": True, "hits": hits, "scanned": scanned,
                                        "truncated": True}
            except Exception:
                continue
    return {"ok": True, "hits": hits, "scanned": scanned, "truncated": False}


def t_info(a):
    path = a.get("path") or ""
    if not path:
        return {"ok": False, "error": "path gerekli."}
    ok, why = check_read(path)
    if not ok:
        return {"ok": False, "error": why}
    if not os.path.exists(path):
        return {"ok": False, "error": "Yol yok."}
    st = os.stat(path)
    return {"ok": True, "path": _real(path), "type": "dir" if os.path.isdir(path) else "file",
            "size": st.st_size,
            "created": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_ctime)),
            "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)),
            "readable": os.access(path, os.R_OK), "writable": os.access(path, os.W_OK)}


def t_mkdir(a):
    path = a.get("path") or ""
    if not path:
        return {"ok": False, "error": "path gerekli."}
    ok, why = check_write(os.path.join(path, "x"))
    if not ok:
        return {"ok": False, "error": why}
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "path": _real(path)}


def t_move(a):
    src, dst = a.get("src") or "", a.get("dst") or ""
    if not src or not dst:
        return {"ok": False, "error": "src ve dst gerekli."}
    for p in (src, dst):
        ok, why = check_write(p)
        if not ok:
            return {"ok": False, "error": why}
    try:
        shutil.move(src, dst)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "src": _real(src), "dst": _real(dst)}


def t_copy(a):
    src, dst = a.get("src") or "", a.get("dst") or ""
    if not src or not dst:
        return {"ok": False, "error": "src ve dst gerekli."}
    ok, why = check_read(src)
    if not ok:
        return {"ok": False, "error": why}
    ok, why = check_write(dst)
    if not ok:
        return {"ok": False, "error": why}
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "src": _real(src), "dst": _real(dst)}


def t_delete(a):
    path = a.get("path") or ""
    if not path:
        return {"ok": False, "error": "path gerekli."}
    ok, why = check_write(path)
    if not ok:
        return {"ok": False, "error": why}
    if not a.get("confirm"):
        return {"ok": False, "error": "Silme için confirm=true gerekli (yanlışlıkla silmeyi önler).",
                "hint": "Önce t_info ile ne olduğunu kontrol edin."}
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    audit("delete", path)
    return {"ok": True, "deleted": _real(path)}


def t_shell(a):
    cmd = a.get("command") or ""
    cwd = a.get("cwd") or HOME
    if not cmd.strip():
        return {"ok": False, "error": "command gerekli."}
    if not CFG.get("allow_shell"):
        return {"ok": False, "error": "Terminal erişimi ayarlardan kapatılmış."}
    ok, why = check_command(cmd)
    if not ok:
        return {"ok": False, "error": why}
    ok, why = check_read(cwd)
    if not ok:
        return {"ok": False, "error": why}
    tmo = int(a.get("timeout") or CFG.get("shell_timeout") or 60)
    tmo = max(5, min(tmo, 300))
    t0 = time.time()
    try:
        kwargs = dict(cwd=_real(cwd), shell=True, capture_output=True, timeout=tmo)
        if IS_WIN:
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        p = subprocess.run(cmd, **kwargs)
        out = (p.stdout or b"").decode("utf-8", "replace")
        err = (p.stderr or b"").decode("utf-8", "replace")
        trunc = False
        if len(out) > MAX_OUTPUT:
            out, trunc = out[:MAX_OUTPUT], True
        if len(err) > 8000:
            err = err[:8000]
        audit("shell", cmd, p.returncode == 0)
        return {"ok": p.returncode == 0, "exit": p.returncode,
                "stdout": out, "stderr": err, "truncated": trunc,
                "seconds": round(time.time() - t0, 2)}
    except subprocess.TimeoutExpired:
        audit("shell_timeout", cmd, False)
        return {"ok": False, "error": f"Komut {tmo} saniyede bitmedi (zaman aşımı)."}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def t_apps(a):
    """Çalışan uygulamalar / pencereler."""
    items = []
    try:
        if IS_WIN:
            p = subprocess.run(
                ["tasklist", "/fo", "csv", "/nh"], capture_output=True, timeout=20,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            for line in (p.stdout or b"").decode("utf-8", "replace").splitlines():
                parts = [x.strip('"') for x in line.split('","')]
                if len(parts) >= 2:
                    items.append({"name": parts[0], "pid": parts[1]})
        else:
            p = subprocess.run(["ps", "-eo", "comm="], capture_output=True, timeout=20)
            from collections import Counter
            for name, n in Counter((p.stdout or b"").decode("utf-8", "replace").split()).items():
                items.append({"name": name, "count": n})
    except Exception as e:
        return {"ok": False, "error": str(e)}
    seen, uniq = set(), []
    for it in items:
        if it["name"] not in seen:
            seen.add(it["name"])
            uniq.append(it)
    return {"ok": True, "count": len(uniq), "apps": uniq[:120]}


def t_open(a):
    target = a.get("target") or ""
    if not target:
        return {"ok": False, "error": "target gerekli (uygulama adı, dosya yolu veya URL)."}
    try:
        if IS_WIN:
            os.startfile(target)  # noqa
            return {"ok": True, "opened": target}
        if OS_NAME == "Darwin":
            subprocess.Popen(["open", target])
            return {"ok": True, "opened": target}
        exe = shutil.which(target)
        if exe:
            subprocess.Popen([exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"ok": True, "opened": exe}
        subprocess.Popen(["xdg-open", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"ok": True, "opened": target}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def t_notify(a):
    title = a.get("title") or "GhostPilot"
    msg = a.get("message") or ""
    try:
        if IS_WIN:
            ps = ("[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
                  "ContentType=WindowsRuntime] > $null; $t=[Windows.UI.Notifications."
                  "ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications."
                  "ToastTemplateType]::ToastText02); $x=$t.GetElementsByTagName('text'); "
                  "$x.Item(0).AppendChild($t.CreateTextNode('" + title.replace("'", "") +
                  "')) > $null; $x.Item(1).AppendChild($t.CreateTextNode('" +
                  msg.replace("'", "") + "')) > $null; [Windows.UI.Notifications."
                  "ToastNotificationManager]::CreateToastNotifier('GhostPilot').Show($t)")
            subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, timeout=15,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        elif OS_NAME == "Darwin":
            subprocess.run(["osascript", "-e",
                            f'display notification "{msg}" with title "{title}"'],
                           capture_output=True, timeout=15)
        else:
            if shutil.which("notify-send"):
                subprocess.run(["notify-send", title, msg], capture_output=True, timeout=15)
            else:
                return {"ok": False, "error": "notify-send yok."}
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---- ekran / girdi: screen.py varsa ----

def _screen_mod():
    try:
        import screen
        return screen
    except Exception:
        return None


_SHOT_CACHE = {"anahtar": None, "veri": None, "t": 0.0}
_SHOT_KILIT = threading.Lock()


def t_shot(a):
    m = _screen_mod()
    if not m or not CFG.get("allow_screen"):
        return {"ok": False, "error": "Ekran yakalama bu makinede kullanılamıyor.",
                "hint": "python ghostpilot.py doctor → neden gösterilir."}
    mw = int(a.get("max_width") or 1280)
    anahtar = (str(a.get("region")), mw, str(a.get("monitor")))
    # HIZ: 1.2 saniye içinde aynı istek gelirse tekrar yakalama (ağ/motor yükü azalır)
    simdi = time.time()
    with _SHOT_KILIT:
        if (_SHOT_CACHE["anahtar"] == anahtar and
                simdi - _SHOT_CACHE["t"] < 1.2 and _SHOT_CACHE["veri"]):
            d = dict(_SHOT_CACHE["veri"])
            d["cached"] = True
            return d
    r = m.screenshot(region=a.get("region"), max_width=mw,
                     monitor=a.get("monitor"))
    if isinstance(r, dict) and r.get("ok"):
        with _SHOT_KILIT:
            _SHOT_CACHE.update({"anahtar": anahtar, "veri": dict(r), "t": time.time()})
    return r


def _guard_input(fn, *args, force=False, restore=True, wait_for_user=False,
                 label=""):
    """Girdi işlemini çalıştırır.

    VARSAYILAN (v5.1): BEKLEMEZ — kullanıcıyla AYNI ANDA çalışır.
      · Ekranda hayalet imleç + şerit görünür (goverlay).
      · Gerçek imleç korunur (CursorRestore / arka plan PostMessage).
    Eski davranış için: wait_for_user=true (kullanıcı meşgulse bekler).
    """
    try:
        import goverlay
        if label:
            goverlay.hud(label)
    except Exception:
        pass
    if wait_for_user:
        try:
            import input_bg
            input_bg.wait_until_user_idle(force=force)
        except Exception as e:
            if type(e).__name__ == "Busy":
                return {"ok": False, "busy": True, "error": str(e)}
    try:
        return fn(*args)
    finally:
        try:
            import goverlay
            goverlay.ghost_hide()
        except Exception:
            pass


def _sanal_sinir(x, y):
    """Sanal modda koordinat sınır dışındaysa uyarı döner."""
    sd = _sanal()
    if not sd or not sd.acik(CFG):
        return None
    if sd.sinir_icinde(x, y):
        return None
    s = sd.ekran_siniri() or (0, 0, 0, 0)
    return {"ok": False, "virtual_boundary": True,
            "error": ("Sanal bilgisayar modu: ajan yalnız kendi ekran alanında "
                      "çalışır (x 0-%d, y 0-%d). Gerçek imlecinize dokunmaz."
                      % (s[2], s[3]))}


def t_click(a):
    """Tıklar — SİZİNLE AYNI ANDA; gerçek imleciniz oynatılmaz."""
    x, y = int(a.get("x", 0)), int(a.get("y", 0))
    hata = _sanal_sinir(x, y)
    if hata:
        return hata
    etiket = a.get("label") or "tıklıyorum"
    try:
        import input_bg
        return input_bg.bg_click(x, y, button=a.get("button") or "left",
                                 double=bool(a.get("double")),
                                 visible=not bool(a.get("sessiz")),
                                 label=etiket)
    except Exception as e:
        m = _screen_mod()
        if not m or not CFG.get("allow_screen"):
            return {"ok": False, "error": f"Girdi denetimi kullanılamıyor: {e}"}
        return _guard_input(lambda: m.click(x, y, button=a.get("button") or "left",
                                            double=bool(a.get("double"))),
                            label=etiket)


def t_move_mouse(a):
    """Fareyi taşır (dosya taşımak için: t_move)."""
    hata = _sanal_sinir(int(a.get("x", 0)), int(a.get("y", 0)))
    if hata:
        return hata
    m = _screen_mod()
    if not m or not CFG.get("allow_screen"):
        return {"ok": False, "error": "Girdi denetimi kullanılamıyor."}
    return _guard_input(lambda: m.move(int(a.get("x", 0)), int(a.get("y", 0))))


def t_drag(a):
    m = _screen_mod()
    if not m or not CFG.get("allow_screen"):
        return {"ok": False, "error": "Girdi denetimi kullanılamıyor."}
    return _guard_input(lambda: m.drag(int(a.get("x1", 0)), int(a.get("y1", 0)),
                                       int(a.get("x2", 0)), int(a.get("y2", 0))))


def t_scroll(a):
    m = _screen_mod()
    if not m or not CFG.get("allow_screen"):
        return {"ok": False, "error": "Girdi denetimi kullanılamıyor."}
    return _guard_input(lambda: m.scroll(int(a.get("amount", -3))))


def t_type(a):
    """Yazar — gerçek imleciniz yerinde kalır, siz de yazabilirsiniz."""
    metin = str(a.get("text", ""))
    try:
        import input_bg
        # HIZ: varsayılan gecikme 0 — ajan kelimeyi tek nefeste yazar.
        # İsterseniz delay ile yavaşlatın (insan gibi yazsın).
        return input_bg.bg_type(metin, visible=not bool(a.get("sessiz")),
                                delay=float(a.get("delay") or 0))
    except Exception as e:
        m = _screen_mod()
        if not m or not CFG.get("allow_screen"):
            return {"ok": False, "error": f"Girdi denetimi kullanılamıyor: {e}"}
        return _guard_input(lambda: m.type_text(metin), label="yazıyorum")


def t_key(a):
    """Kısayol tuşu — arka planda pencereye gönderilir."""
    kombo = str(a.get("combo", ""))
    try:
        import input_bg
        return input_bg.bg_key(kombo)
    except Exception as e:
        m = _screen_mod()
        if not m or not CFG.get("allow_screen"):
            return {"ok": False, "error": f"Girdi denetimi kullanılamıyor: {e}"}
        return _guard_input(lambda: m.key(kombo), label=f"tuş: {kombo}")


def _overlay_status():
    try:
        import goverlay
        return goverlay.status()
    except Exception as e:
        return {"ready": False, "reason": str(e)[:120]}


def _overlay_up():
    """Görsel katmanı arka planda başlat (sunucu açılışında)."""
    if not CFG.get("show_agent", True):
        return False
    try:
        import goverlay
        return goverlay.start(2.0)
    except Exception:
        return False


def t_sanal_durum(a):
    sd = _sanal()
    if not sd:
        return {"ok": False, "error": "sanaldunya modülü yok."}
    d = sd.durum()
    d["ok"] = True
    return d


def t_sanal_mod(a):
    sd = _sanal()
    if not sd:
        return {"ok": False, "error": "sanaldunya modülü yok."}
    if a.get("acik") is False:
        sd.kapat()
        return {"ok": True, "sanal": False,
                "not": "Sanal mod kapandı — gerçek bilgisayar kuralları geçerli."}
    if not sd.ac():
        return {"ok": False, "error": "Açılamadı."}
    return {"ok": True, "sanal": True, "kok": sd.kok_klasor(),
            "not": ("Sanal bilgisayar açık: ajan yalnız bu klasörde çalışır, "
                    "kendi imleci ve kendi ekran alanı var.")}


def t_ui_click(a):
    """Bir pencerede metni/düğmeyi bulup tıklar — tek adımda.

    Ekran görüntüsü → yazı bul (OCR yoksa pencerede metin arama) →
    merkeze tıkla. Koordinat hesaplamak için 3-4 tur sohbet gerekmez.
    """
    hedef = str(a.get("text") or "").strip()
    if not hedef:
        return {"ok": False, "error": "text parametresi gerekli (ör. 'Kaydet')."}
    try:
        import ui_bul
    except Exception:
        return {"ok": False, "error": "ui_bul modülü yok."}
    return ui_bul.bul_ve_tikla(hedef, pencere=a.get("window"),
                               bolge=a.get("region"))


def t_ghost(a):
    """Ekranda görünür imleç / şerit (işlemin nerede olduğunu görün)."""
    try:
        import goverlay
    except Exception as e:
        return {"ok": False, "error": f"görsel katman yok: {e}"}
    islem = (a.get("action") or "goster").lower()
    if islem in ("gizle", "hide"):
        goverlay.ghost_hide()
        goverlay.hud_off()
        return {"ok": True, "visible": False}
    if islem in ("serit", "hud", "mesaj"):
        goverlay.hud(a.get("text") or a.get("label") or "çalışıyorum",
                     seconds=float(a.get("seconds") or 4))
        return {"ok": True, "hud": True}
    ok = goverlay.start(2.5)
    if not ok:
        return {"ok": False, "error": goverlay.status().get("reason") or
                "Görsel katman bu makinede açılamıyor (tkinter/ekran yok)."}
    x, y = int(a.get("x", 0)), int(a.get("y", 0))
    if a.get("glide", True) and (x or y):
        goverlay.ghost_glide(x, y, label=a.get("label") or "")
    else:
        goverlay.ghost_show(x, y, label=a.get("label") or "")
    return {"ok": True, "visible": True, "x": x, "y": y,
            "status": goverlay.status()}


def t_hud(a):
    """Ekranın altında 'şu an ne yapıyorum' şeridi gösterir."""
    try:
        import goverlay
        goverlay.hud(a.get("text") or "", seconds=float(a.get("seconds") or 4))
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---- belge / pano / pencere / monitör / arka plan işler ----

def t_doc(a):
    yol = a.get("path") or ""
    _ok, _ = check_read(yol) if yol else (True, "")
    if yol and not _ok:
        return {"ok": False, "error":
                f"Bu yol okuma izni verilen klasörlerin dışında: {yol}",
                "hint": "İzin vermek için: python kur.py izin \"" + os.path.dirname(yol) + "\"",
                "read_roots": CFG.get("read_roots") or []}
    return _t_doc(a)


def _t_doc(a):
    path = a.get("path") or ""
    if not path:
        return {"ok": False, "error": "path gerekli."}
    ok, why = check_read(path)
    if not ok:
        return {"ok": False, "error": why}
    try:
        import belge
    except Exception as e:
        return {"ok": False, "error": f"belge modülü yok: {e}"}
    return belge.read_document(path)


def t_clip_get(_a):
    import input_bg
    return input_bg.clipboard_get()


def t_clip_set(a):
    import input_bg
    return input_bg.clipboard_set(a.get("text", ""))


def t_windows(_a):
    import input_bg
    return {"ok": True, "active": input_bg.active_window(),
            "windows": input_bg.window_list()}


def t_focus(a):
    import input_bg
    m = a.get("match") or ""
    if not m:
        return {"ok": False, "error": "match gerekli (pencere başlığından parça)."}
    return input_bg.window_focus(m)


def t_minimize(a):
    import input_bg
    m = a.get("match") or ""
    if not m:
        return {"ok": False, "error": "match gerekli."}
    return input_bg.window_minimize(m)


def t_monitors(_a):
    import input_bg
    mons = input_bg.monitors()
    return {"ok": bool(mons), "count": len(mons), "monitors": mons,
            "cursor": input_bg.cursor_pos(),
            "user_idle_s": round(input_bg.last_input_age(), 2)}


def t_user_busy(_a):
    import input_bg
    age = input_bg.last_input_age()
    return {"ok": True, "user_idle_s": round(age, 2),
            "user_using_computer": age < 0.45,
            "note": "Ajan, siz bilgisayarı kullanırken bekler (force=true ile zorlanabilir).",
            "stats": input_bg.stats()}


# ---- arka plan komutları ----

JOBS = {}
JOB_LOCK = threading.Lock()


def _job_run(job_id, cmd, cwd, timeout):
    try:
        kw = dict(cwd=cwd, shell=True, stdout=subprocess.PIPE,
                  stderr=subprocess.STDOUT, text=True, errors="replace")
        if IS_WIN:
            kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        p = subprocess.Popen(cmd, **kw)
        with JOB_LOCK:
            JOBS[job_id]["pid"] = p.pid
        try:
            out, _ = p.communicate(timeout=timeout)
            code = p.returncode
        except subprocess.TimeoutExpired:
            p.kill()
            out, _ = p.communicate()
            code = -9
        with JOB_LOCK:
            JOBS[job_id].update({
                "done": True, "exit": code,
                "output": (out or "")[-MAX_OUTPUT:],
                "finished": time.time(),
            })
    except Exception as e:
        with JOB_LOCK:
            JOBS[job_id].update({"done": True, "exit": -1, "output": f"HATA: {e}",
                                 "finished": time.time()})


def t_job_start(a):
    cmd = a.get("command") or ""
    cwd = a.get("cwd") or HOME
    if not cmd.strip():
        return {"ok": False, "error": "command gerekli."}
    ok, why = check_command(cmd)
    if not ok:
        return {"ok": False, "error": why}
    ok, why = check_read(cwd)
    if not ok:
        return {"ok": False, "error": why}
    timeout = max(10, min(int(a.get("timeout") or 3600), 24 * 3600))
    jid = "job-" + secrets.token_hex(4)
    with JOB_LOCK:
        JOBS[jid] = {"command": cmd, "cwd": _real(cwd), "started": time.time(),
                     "done": False, "exit": None, "output": "", "pid": None,
                     "timeout": timeout}
    threading.Thread(target=_job_run, args=(jid, cmd, _real(cwd), timeout),
                     daemon=True).start()
    return {"ok": True, "job_id": jid, "command": cmd,
            "hint": "job_status ile ilerlemeyi izleyin; bitince job_output."}


def t_job_status(a):
    jid = a.get("job_id") or ""
    with JOB_LOCK:
        j = JOBS.get(jid)
        if not j:
            return {"ok": False, "error": f"İş bulunamadı: {jid}",
                    "jobs": list(JOBS.keys())[-10:]}
        snap = dict(j)
    return {"ok": True, "job_id": jid, "done": snap["done"], "exit": snap["exit"],
            "pid": snap["pid"], "elapsed_s": round(time.time() - snap["started"], 1),
            "command": snap["command"],
            "output_tail": (snap["output"] or "")[-1200:]}


def t_job_output(a):
    jid = a.get("job_id") or ""
    with JOB_LOCK:
        j = JOBS.get(jid)
        if not j:
            return {"ok": False, "error": f"İş bulunamadı: {jid}"}
        snap = dict(j)
    return {"ok": True, "job_id": jid, "done": snap["done"], "exit": snap["exit"],
            "elapsed_s": round(time.time() - snap["started"], 1),
            "output": snap["output"] or ""}


def t_job_kill(a):
    jid = a.get("job_id") or ""
    with JOB_LOCK:
        j = JOBS.get(jid)
        if not j:
            return {"ok": False, "error": "İş yok."}
        pid = j.get("pid")
    if not pid:
        return {"ok": False, "error": "PID henüz yok."}
    try:
        if IS_WIN:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                           capture_output=True, timeout=15,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        else:
            os.kill(pid, 15)
        return {"ok": True, "killed": pid}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def t_jobs(_a):
    with JOB_LOCK:
        return {"ok": True, "count": len(JOBS),
                "jobs": [{"job_id": k, "command": v["command"],
                          "done": v["done"], "exit": v["exit"],
                          "elapsed_s": round(time.time() - v["started"], 1)}
                         for k, v in list(JOBS.items())[-20:]]}



# ============================================================================
#  TELEGRAM BİLDİRİMİ — varsayılan KAPALI
#  Açmak: python kur.py telegram <bot_token> <chat_id>
#  Yalnız GİDEN mesaj gönderir; Telegram'dan komut ALMAZ (güvenlik).
# ============================================================================

def _telegram_ayar():
    t = (CFG.get("telegram_token") or "").strip()
    c = (CFG.get("telegram_chat") or "").strip()
    return (t, c) if (t and c and CFG.get("telegram_enabled")) else (None, None)


def telegram_gonder(metin):
    tok, chat = _telegram_ayar()
    if not tok:
        return {"ok": False, "error": "Telegram kapalı. Açmak için: python kur.py telegram <token> <chat_id>"}
    import urllib.parse
    import urllib.request
    data = urllib.parse.urlencode({"chat_id": chat, "text": str(metin)[:3900],
                                   "disable_web_page_preview": "true"}).encode()
    try:
        with urllib.request.urlopen(
                f"https://api.telegram.org/bot{tok}/sendMessage", data=data, timeout=15) as r:
            j = json.load(r)
        ok = bool(j.get("ok"))
        audit("telegram", "ok" if ok else "hata")
        return {"ok": ok, "detail": "" if ok else str(j.get("description"))[:200]}
    except Exception as e:
        return {"ok": False, "error": f"Gönderilemedi: {e}"}


def t_bildir(a):
    metin = a.get("message") or a.get("text") or ""
    if not metin:
        return {"ok": False, "error": "message gerekli."}
    return telegram_gonder(metin)


def t_makine(a):
    """Hangi bilgisayardayız? Çoklu makine kurulumunda ayırt etmek için."""
    import platform
    return {"ok": True,
            "machine": CFG.get("machine_name") or platform.node(),
            "user": os.environ.get("USERNAME") or os.environ.get("USER") or "?",
            "os": f"{platform.system()} {platform.release()}",
            "version": VERSION, "port": CFG.get("port") or DEFAULT_PORT,
            "read_only": bool(CFG.get("read_only")),
            "approval": CFG.get("onay") or "riskli"}


# ============================================================================
#  ZAMANLANMIŞ GÖREVLER — "her gün 09:00'da şunu yap" gibi
#  Kayıt: ~/.ghostpilot/tasks.json   Zamanlayıcı: sunucu ayaktayken çalışır
# ============================================================================

GOREV_DOSYA = os.path.join(CFG_DIR, "tasks.json")
GOREV_KILIT = threading.Lock()


def _gorev_yukle():
    try:
        return json.load(open(GOREV_DOSYA, encoding="utf-8"))
    except Exception:
        return []


def _gorev_kaydet(lst):
    os.makedirs(CFG_DIR, exist_ok=True)
    tmp = GOREV_DOSYA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(lst, f, ensure_ascii=False, indent=1)
    os.replace(tmp, GOREV_DOSYA)


def _gorev_zamani_geldi(g):
    """Saatlik/dakikalık zamanlamayı kontrol eder."""
    simdi = time.localtime()
    son = g.get("last_run") or 0
    # 1) "HH:MM" → her gün o saatte
    if ":" in str(g.get("when", "")):
        try:
            hh, mm = [int(x) for x in str(g["when"]).split(":")[:2]]
        except Exception:
            return False
        if time.time() - son < 3600:
            return False
        return simdi.tm_hour == hh and abs(simdi.tm_min - mm) <= 1
    # 2) saniye cinsinden aralık
    try:
        ara = max(60, int(g.get("every") or 0))
    except Exception:
        return False
    return time.time() - son >= ara


def _durduruldu_bayragi():
    """Kullanıcı 'durdur' dediyse arka plan döngüleri durmalı."""
    try:
        return os.path.exists(os.path.join(CFG_DIR, "stopped"))
    except Exception:
        return False


def gorev_dongu(durdur_flag=None):
    """Sunucu içinde arka planda çalışan zamanlayıcı."""
    while True:
        try:
            # 'durdur' adli bir gorev varsa o da kapanis istegi sayilir
            if durdur_flag is not None and callable(durdur_flag):
                try:
                    if durdur_flag("durdur") or durdur_flag("stop"):
                        return
                except TypeError:
                    if durdur_flag():
                        return
            if _durduruldu_bayragi():
                return
            with GOREV_KILIT:
                lst = _gorev_yukle()
                degisti = False
                for g in lst:
                    if not g.get("enabled", True):
                        continue
                    if _gorev_zamani_geldi(g):
                        r = call_tool("shell", {"command": g.get("command", ""),
                                                "_onaylandi": True})
                        g["last_run"] = time.time()
                        g["last_ok"] = bool(r.get("ok"))
                        g["last_out"] = (r.get("stdout") or r.get("error") or "")[:300]
                        degisti = True
                        audit("gorev", f"{g.get('name')} → {'ok' if r.get('ok') else 'hata'}")
                if degisti:
                    _gorev_kaydet(lst)
        except Exception as e:
            audit("gorev-hata", str(e)[:150])
        time.sleep(20)


def t_gorev_ekle(a):
    ad = (a.get("name") or "").strip() or "gorev"
    cmd = a.get("command") or ""
    if not cmd:
        return {"ok": False, "error": "command gerekli."}
    g = {"name": ad, "command": cmd, "enabled": True, "last_run": 0,
         "last_ok": None, "last_out": ""}
    if a.get("at"):
        g["when"] = a["at"]
    elif a.get("every_minutes"):
        g["every"] = max(1, int(a["every_minutes"])) * 60
    else:
        return {"ok": False, "error": "at='09:30' veya every_minutes=30 vermelisiniz."}
    with GOREV_KILIT:
        lst = [x for x in _gorev_yukle() if x.get("name") != ad]
        lst.append(g)
        _gorev_kaydet(lst)
    audit("gorev-ekle", ad)
    return {"ok": True, "task": g, "count": len(lst)}


def t_gorev_liste(a):
    lst = _gorev_yukle()
    for g in lst:
        if g.get("last_run"):
            g["last_run_insan"] = time.strftime("%d.%m %H:%M", time.localtime(g["last_run"]))
    return {"ok": True, "tasks": lst, "count": len(lst)}


def t_gorev_sil(a):
    ad = a.get("name") or ""
    with GOREV_KILIT:
        lst = _gorev_yukle()
        yeni = [x for x in lst if x.get("name") != ad]
        _gorev_kaydet(yeni)
    audit("gorev-sil", ad)
    return {"ok": len(yeni) < len(lst), "remaining": len(yeni)}


def t_kota(args):
    """Ne kadar kullanım hakkı kaldı? (sohbetten sorulabilir — rakip standardı)"""
    kd = kota_durum()
    lb = kd.get("lisans_bilgi") or {}
    satir = []
    if kd.get("pro"):
        satir.append("Destek anahtarı etkin — çağrılar sınırsız.")
        if lb.get("plan_adi"):
            satir.append(f"Paket: {lb['plan_adi']}"
                         + (f" · bitiş {lb['bitis']}" if lb.get("bitis") else ""))
    else:
        satir.append(f"Bu ay kullanılan: {kd['kullanilan']:,} / {kd['limit']:,}"
                     .replace(",", "."))
        satir.append(f"Kalan: {kd['kalan']:,} çağrı".replace(",", "."))
        satir.append(f"Doluluk: %{int(round(kd['yuzde']))}")
        if kd.get("uyari_mesaji"):
            satir.append(kd["uyari_mesaji"])
        satir.append(f"Sıfırlanma: {kd.get('sifirlanma')}")
        satir.append(f"Destek anahtarı (sınırsız): {BAGIS_URL}")
    satir.append("")
    satir.append("Sayım kuralı: yalnız GERÇEK araç çalışmaları sayılır. "
                 "Bağlantı kopması, zaman aşımı ve reddedilen çağrılar sayılmaz.")
    return {"ok": True, "text": "\n".join(satir), **kd}


TOOLS = {
    "ghostpilot_status": (t_status, "GhostPilot'un bu bilgisayarda ne yapabildiğini gösterir.", {}),
    "kota_durumu": (t_kota, "Bu ay ne kadar kullanım hakkı kaldığını, sıfırlanma tarihini ve paket durumunu söyler.", {}),
    "ls": (t_ls, "Klasör içeriğini listeler.", {"path": {"type": "string", "description": "Klasör yolu (boş = ev dizini)"}, "hidden": {"type": "boolean", "description": "Gizli dosyaları da göster"}}),
    "read": (t_read, "Bir metin dosyasını okur (en fazla 2 MB).", {"path": {"type": "string", "description": "Dosya yolu"}}, ["path"]),
    "write": (t_write, "Dosya yazar veya üzerine ekler.", {"path": {"type": "string"}, "content": {"type": "string"}, "mode": {"type": "string", "enum": ["overwrite", "append"]}}, ["path", "content"]),
    "edit": (t_edit, "Dosyada metin parçası değiştirir.", {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}, "all": {"type": "boolean"}}, ["path", "old", "new"]),
    "glob": (t_glob, "Dosya adı desenine göre arama yapar (*.txt gibi).", {"pattern": {"type": "string"}, "path": {"type": "string"}}, ["pattern"]),
    "grep": (t_grep, "Dosya içinde metin/düzenli ifade arar.", {"pattern": {"type": "string"}, "path": {"type": "string"}, "extensions": {"type": "array", "items": {"type": "string"}}}, ["pattern"]),
    "info": (t_info, "Dosya/klasör bilgisi verir.", {"path": {"type": "string"}}, ["path"]),
    "mkdir": (t_mkdir, "Klasör oluşturur.", {"path": {"type": "string"}}, ["path"]),
    "move": (t_move, "Dosya/klasör taşır veya yeniden adlandırır.", {"src": {"type": "string"}, "dst": {"type": "string"}}, ["src", "dst"]),
    "copy": (t_copy, "Dosya/klasör kopyalar.", {"src": {"type": "string"}, "dst": {"type": "string"}}, ["src", "dst"]),
    "delete": (t_delete, "Dosya/klasör siler (confirm=true gerekir).", {"path": {"type": "string"}, "confirm": {"type": "boolean"}}, ["path"]),
    "shell": (t_shell, "Terminal komutu çalıştırır ve çıktısını döndürür.", {"command": {"type": "string"}, "cwd": {"type": "string"}, "timeout": {"type": "integer"}}, ["command"]),
    "apps": (t_apps, "Çalışan uygulamaları/süreçleri listeler.", {}),
    "open": (t_open, "Uygulama, dosya veya URL açar.", {"target": {"type": "string"}}, ["target"]),
    "notify": (t_notify, "Masaüstü bildirimi gösterir.", {"title": {"type": "string"}, "message": {"type": "string"}}, ["message"]),
    "telegram": (t_bildir, "Telegram'a bildirim gönderir (kullanıcı açtıysa).", {"message": {"type": "string"}}, ["message"]),
    "machine": (t_makine, "Hangi bilgisayarda olduğumuzu, sürümü ve modları söyler.", {}),
    "schedule_add": (t_gorev_ekle, "Zamanlanmış görev ekler: her gün belirli saatte veya belirli aralıkla komut çalıştırır.", {"name": {"type": "string"}, "command": {"type": "string"}, "at": {"type": "string", "description": "\"09:30\" gibi günlük saat"}, "every_minutes": {"type": "integer", "description": "kaç dakikada bir"}}),
    "schedule_list": (t_gorev_liste, "Zamanlanmış görevleri listeler.", {}),
    "schedule_remove": (t_gorev_sil, "Zamanlanmış görevi siler.", {"name": {"type": "string"}}),
    "ghost": (t_ghost, "Ekranda görünür imleç/işaret gösterir — işlemin nerede olduğunu görürsünüz.", {"action": {"type": "string", "description": "goster | gizle | serit"}, "x": {"type": "integer"}, "y": {"type": "integer"}, "label": {"type": "string"}, "text": {"type": "string"}, "glide": {"type": "boolean"}, "seconds": {"type": "number"}}),
    "hud": (t_hud, "Ekranın altında 'şu an ne yapıyorum' şeridi gösterir.", {"text": {"type": "string"}, "seconds": {"type": "number"}}),
    "sanal_durum": (t_sanal_durum, "Sanal bilgisayar modunun durumunu gösterir: "
                                  "açık mı, sanal klasör nerede, ekran alanı ne?",
                    {}),
    "sanal_mod": (t_sanal_mod, "Sanal bilgisayar modunu açar/kapatır. Açıkken ajan "
                               "yalnız sanal klasörde çalışır, kendi imlecini kullanır.",
                  {"acik": {"type": "boolean"}}),
    "ui_click": (t_ui_click, "Bir penceredeki düğmeyi/metni bulup tıklar; "
                              "koordinat bilmeye gerek yok.", {"text": {"type": "string"}, "window": {"type": "string"}}),
    "screenshot": (t_shot, "Ekranı JPEG olarak yakalar (base64).", {"region": {"type": "object", "description": "{x,y,w,h}"}, "max_width": {"type": "integer"}, "monitor": {"type": "integer", "description": "1 = birincil, 2 = ikinci ekran…"}}),
    "click": (t_click, "Tıklar — SİZİNLE AYNI ANDA; gerçek imleciniz oynamaz, ekranda hayalet imleç görünür.", {"x": {"type": "integer"}, "y": {"type": "integer"}, "button": {"type": "string", "enum": ["left", "right", "middle"]}, "double": {"type": "boolean"}, "label": {"type": "string", "description": "ekranda görünecek açıklama"}, "sessiz": {"type": "boolean", "description": "hayalet imleci gösterme"}}, ["x", "y"]),
    "move_mouse": (t_move_mouse, "Fareyi koordinata taşır.", {"x": {"type": "integer"}, "y": {"type": "integer"}}, ["x", "y"]),
    "drag": (t_drag, "Fareyi sürükler (dosya taşıma, metin seçme).", {"x1": {"type": "integer"}, "y1": {"type": "integer"}, "x2": {"type": "integer"}, "y2": {"type": "integer"}}, ["x1", "y1", "x2", "y2"]),
    "scroll": (t_scroll, "Tekerlek kaydırır (negatif = aşağı).", {"amount": {"type": "integer"}, "x": {"type": "integer"}, "y": {"type": "integer"}}),
    "type_text": (t_type, "Yazar — SİZİNLE AYNI ANDA; imleciniz yerinde kalır.", {"text": {"type": "string"}, "delay": {"type": "number"}, "sessiz": {"type": "boolean"}}, ["text"]),
    "press_key": (t_key, "Kısayol tuşu basar (ctrl+c, enter, alt+tab) — arka planda.", {"combo": {"type": "string"}}, ["combo"]),
    "doc_read": (t_doc, "Belge okur: .docx .xlsx .pptx .pdf .csv .json .html .md (sıfır bağımlılık).",
                 {"path": {"type": "string", "description": "Belge yolu"}}, ["path"]),
    "clipboard_get": (t_clip_get, "Panodaki metni okur.", {}),
    "clipboard_set": (t_clip_set, "Panoya metin yazar.", {"text": {"type": "string"}}, ["text"]),
    "windows": (t_windows, "Açık pencereleri ve etkin pencereyi listeler.", {}),
    "window_focus": (t_focus, "Başlığa göre pencereyi öne getirir (ajan doğru pencereye yazsın).",
                     {"match": {"type": "string"}}, ["match"]),
    "window_minimize": (t_minimize, "Başlığa göre pencereyi küçültür.",
                        {"match": {"type": "string"}}, ["match"]),
    "monitors": (t_monitors, "Monitörleri, imleç konumunu ve kullanıcı boşta mı gösterir.", {}),
    "user_busy": (t_user_busy, "Siz bilgisayarı kullanıyor musunuz? Ajan buna göre bekler.", {}),
    "job_start": (t_job_start, "Uzun komutu ARKA PLANDA başlatır (derleme, sunucu, yedekleme).",
                  {"command": {"type": "string"}, "cwd": {"type": "string"},
                   "timeout": {"type": "integer"}}, ["command"]),
    "job_status": (t_job_status, "Arka plan işinin durumunu gösterir.",
                   {"job_id": {"type": "string"}}, ["job_id"]),
    "job_output": (t_job_output, "Arka plan işinin tüm çıktısını verir.",
                   {"job_id": {"type": "string"}}, ["job_id"]),
    "job_kill": (t_job_kill, "Arka plan işini durdurur.",
                 {"job_id": {"type": "string"}}, ["job_id"]),
    "jobs": (t_jobs, "Çalışan/biten arka plan işlerini listeler.", {}),
}
TOOL_ORDER = list(TOOLS.keys())


def schemas():
    out = []
    for name in TOOL_ORDER:
        _fn, desc, props, *req = TOOLS[name]
        out.append({
            "name": name,
            "description": desc,
            "inputSchema": {"type": "object", "properties": props,
                            "required": req[0] if req else []},
        })
    return out


YAZAN_ARACLAR = {
    "write", "edit", "mkdir", "move", "copy", "delete", "shell",
    "click", "move_mouse", "drag", "scroll", "type_text", "press_key",
    "open", "job_start", "job_kill", "clipboard_set", "window_focus",
    "window_minimize",
}


def call_tool(name, args):
    if name not in TOOLS:
        return {"ok": False, "error": f"Bilinmeyen araç: {name}"}
    if _onay_gerekli(name) and not args.get("_onaylandi"):
        engel = onay_iste(name, args)
        if engel:
            return engel
    # ---- KOTA: ücretsiz 20.000 çağrı/ay ----
    # Kota SAYIM KURALI (rakip standardı): yalnız gerçek çalışmalar sayılır.
    # Küçük/sorgu araçları (durum, kota, okuma amaçlı hızlı bilgiler) ve
    # zaman aşımına uğrayan çağrılar sayılmaz → kullanıcı mağdur olmaz.
    _SAYILMAYAN = {"ghostpilot_status", "kota_durumu", "machine", "schedule_list"}
    if not CFG.get("kota_kapali") and name not in _SAYILMAYAN:
        if not kota_say():
            kd = kota_durum()
            return {"ok": False, "kota_asildi": True,
                    "kullanilan": kd["kullanilan"], "limit": kd["limit"],
                    "error": KOTA_ASIM_MESAJ.format(kullanilan=kd["kullanilan"],
                                                    limit=kd["limit"],
                                                    bagis=BAGIS_URL),
                    "bagis_url": BAGIS_URL}
    if CFG.get("read_only") and name in YAZAN_ARACLAR:
        return {"ok": False, "read_only": True,
                "error": f"SALT OKUNUR MOD açık — '{name}' değişiklik yapar, reddedildi.",
                "hint": "Kapatmak için: python kur.py mod yazma"}
    fn = TOOLS[name][0]
    try:
        r = fn(args or {})
        if not isinstance(r, dict):
            r = {"ok": True, "result": r}
        audit("tool", name, r.get("ok", True))
        # zaman aşımı sayılmaz → sayaç geri alınır (adil kota)
        if isinstance(r, dict) and r.get("timeout"):
            _kota_geri_al()
        return r
    except TimeoutError as e:
        _kota_geri_al()
        audit("tool_error", f"{name}: timeout", False)
        return {"ok": False, "timeout": True, "error": f"Zaman aşımı: {e}"}
    except Exception as e:
        audit("tool_error", f"{name}: {e}", False)
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}



# ============================================================================
#  SİMGE (ikon) — ChatGPT/Claude eklenti listesinde ve panelde görünür
#  · MCP serverInfo.icons → istemci ikonu alabilir
#  · /icon.png · /favicon.ico · /apple-touch-icon.png → tarayıcı/favicon
#  · /simge.svg · /manifest.json → web uygulaması simgesi
#  Dosyalar yoksa gömülü SVG kullanılır (tek dosya çalışsın diye).
# ============================================================================

GOMULU_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#0e1628"/><stop offset="1" stop-color="#080d1a"/>
</linearGradient></defs>
<rect width="256" height="256" rx="56" fill="url(#g)"/>
<rect x="3" y="3" width="250" height="250" rx="53" fill="none" stroke="#263654" stroke-width="2"/>
<circle cx="128" cy="128" r="86" fill="none" stroke="#22d3ee" stroke-opacity=".66" stroke-width="4.6"/>
<path d="M65 190 L65 116 A63 63 0 0 1 191 116 L191 190
Q167 214 143 190 Q119 214 95 190 Q71 214 65 190 Z" fill="#f59e0b" stroke="#fdc860" stroke-width="3"/>
<ellipse cx="111" cy="112" rx="10.7" ry="12.3" fill="#0c1220"/>
<ellipse cx="145" cy="112" rx="10.7" ry="12.3" fill="#0c1220"/>
<ellipse cx="128" cy="215" rx="47" ry="5" fill="none" stroke="#22d3ee" stroke-opacity=".6" stroke-width="3"/>
</svg>"""

_SIMGE_CACHE = {}
_ISTEM_BASE = ""       # istekte bulunulan taban adres (handler doldurur)


def _simge_dosya(ad):
    """SIMGE dizininden dosya oku (yol geçişi engelli)."""
    if ad in _SIMGE_CACHE:
        return _SIMGE_CACHE[ad]
    kok = os.path.dirname(os.path.abspath(__file__))
    yol = os.path.join(kok, os.path.basename(ad))
    try:
        with open(yol, "rb") as f:
            veri = f.read()
    except Exception:
        veri = None
    _SIMGE_CACHE[ad] = veri
    return veri


def _simge_b64(ad="icon-256.png"):
    import base64
    veri = _simge_dosya(ad)
    if not veri:
        return None
    return base64.b64encode(veri).decode()


def _simge_svg_b64():
    import base64
    veri = _simge_dosya("icon.svg")
    if not veri:
        veri = GOMULU_SVG.encode("utf-8")
    return base64.b64encode(veri).decode()


def _eklenti_kimlik():
    """eklenti.json varsa oradan oku — tek kaynak. Yoksa gömülü değerler."""
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "eklenti.json"), encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def server_info(base=""):
    """MCP serverInfo — isim, sürüm ve SİMGE."""
    ikonlar = []
    b64svg = _simge_svg_b64()
    ikonlar.append({"src": "data:image/svg+xml;base64," + b64svg,
                    "mimeType": "image/svg+xml", "sizes": ["any"]})
    b64png = _simge_b64("icon-256.png")
    if b64png:
        ikonlar.append({"src": "data:image/png;base64," + b64png,
                        "mimeType": "image/png", "sizes": ["256x256"]})
    if base:
        ikonlar.append({"src": base.rstrip("/") + "/icon.png",
                        "mimeType": "image/png", "sizes": ["256x256"]})
    _e = _eklenti_kimlik()
    return {
        "name": "ghostpilot",
        "title": _e.get("title") or "GhostPilot",
        "version": VERSION,
        # ---- mağaza/eklenti kartında görünen alanlar
        "description": _e.get("description") or (
            "Your real computer, not a sandbox. 44 tools — files, "
            "terminal, screen, scheduling. No cloud, no telemetry."),
        "developer": _e.get("developer") or GELISTIRICI,
        "author": {"name": GELISTIRICI, "email": GELISTIRICI_EPOSTA,
                   "url": GITHUB_PROFIL},
        "icons": ikonlar,
        "websiteUrl": SITE_URL,
        "repositoryUrl": REPO_URL,
        "homepage": SITE_URL,
        "supportUrl": DESTEK_URL,
        "donateUrl": DESTEK_URL,
        "privacyPolicyUrl": GIZLILIK_URL,
        "termsOfServiceUrl": KOSUL_URL,
        "license": "MIT",
        "_meta": {
            "com.ghostpilot/developer": GELISTIRICI,
            "com.ghostpilot/donate": DESTEK_URL,
            "com.ghostpilot/source": REPO_URL,
        },
    }



# ============================================================================
#  LİSANS / KOTA — aylık ücretsiz araç çağrısı sınırı
#
#  · Ücretsiz: ayda 20.000 araç çağrısı
#  · Pro: aylık 15 USD (lisans anahtarı ile açılır)
#  · Sahip (siz): lisans anahtarı olmadan, sınırsız
#
#  Güvenlik katmanları (hacking'i zorlaştırır — TAMAMEN imkânsız değildir):
#    1. Sayaç, kimlik doğrulaması geçtikten SONRA tutulur (istemci tarafı
#       manipülasyonu işe yaramaz; sunucu kendi sayar).
#    2. Sayaç +1 kilitli yazma + atomik replace; her çağrıda diske işlenir.
#       Süreç öldürülse bile sayaç korunur.
#    3. Aynı veri dosyanın SONUNA HMAC-SHA256 imza yazılır. Dosya elle
#       değiştirilirse imza tutmaz → sayaç sıfırlanmaz, "kurcalanmış" işaretlenir.
#    4. Çoklu yedek: ~/.ghostpilot/kota.json + config.json içinde gizli kopya +
#       audit.log'daki saatlik damga. Üçü karşılaştırılır, EN YÜKSEK olan geçerli.
#    5. Saat geri alma koruması: son görülen tarihten önceki tarih kabul edilmez.
#    6. Lisans anahtarı sunucudan doğrulanır (HMAC; anahtar yalnız sunucuda).
#  NOT: Kullanıcı kendi bilgisayarının yöneticisidir; kaynağı değiştirip
#  sayacı kaldırabilir. Hiçbir yerel yazılım bunu tamamen engelleyemez.
#  Gerçek koruma sunucu taraflı imza doğrulamasıdır (lisans).
# ============================================================================

KOTA_DOSYA = os.path.join(CFG_DIR, "kota.json")
KOTA_AUDIT_ISARET = os.path.join(CFG_DIR, ".kota_isaret")
KOTA_KAYIT = os.path.join(HOME, ".ghostpilot_kayit")   # makineye bağlı defter
KOTA_KILIT = threading.Lock()

KOTA_UCRETSIZ = 20000          # aylık ücretsiz çağrı
KOTA_FIYAT = "bağış"           # satış yok — destek bağışla
BAGIS_URL = "https://buymeacoffee.com/btmcode"
KOTA_ASIM_MESAJ = (
    "Aylık ücretsiz sınır doldu ({kullanilan:,}/{limit:,}).\n"
    "\n"
    "GhostPilot ücretsiz ve açık kaynak. Sınırsız kullanım için BTM Code'dan\n"
    "bir DESTEK anahtarı isteyebilirsiniz (katkı karşılığı verilir):\n"
    "  → {bagis}\n"
    "Anahtarınız varsa:  python kur.py lisans <anahtar>"
)

# NOT: Lisans doğrulaması `lisans.py` içinde, yalnız AÇIK ANAHTARLA yapılır.
# Anahtar üretmek için BTM Code'un özel anahtarı gerekir — bu kodda yoktur.
# (Eski HMAC sürümünde sır burada duruyordu; herkes anahtar üretebiliyordu.)
def _lisans_hmac_yok(*a, **k):
    raise RuntimeError("Lisans imzası artık Ed25519 ile, satıcı tarafında yapılır.")


KOTA_TUZU = "ghostpilot-kota-v1"
KASA_PAROLA_ISARETI = "ghostpilot-kasa-v1"     # lisans kasasıyla AYNI tuz (satıcı tarafı)


def makine_kimligi():
    """Bu bilgisayarı tanıtan 16 haneli kimlik.

    TEK kaynak lisans.py'dir: kullanıcı bu numarayı satıcıya bildirir,
    satıcı anahtarı bu numaraya kilitler. İki yerde farklı üretilmemeli.
    """
    try:
        import lisans as _L
        return _L.makine_kimligi()
    except Exception:
        import platform
        return hashlib.sha256(("GP-MAKINE|" + (platform.node() or "?").lower()).encode()).hexdigest()[:16]


MUHUR_DOSYA = os.path.join(CFG_DIR, ".muhur")


def _muhur_butunluk(ay, kullanilan):
    return hashlib.sha256((KOTA_TUZU + "|muhur|" + f"{ay}|{kullanilan}").encode()).hexdigest()[:40]


def _muhur_yaz(d):
    """Haftada bir, sayaç durumunu imzalı mühür olarak yazar."""
    ay, k = d.get("ay"), int(d.get("kullanilan") or 0)
    try:
        eski = json.load(open(MUHUR_DOSYA, encoding="utf-8"))
        if eski.get("ay") == ay and int(eski.get("k") or 0) >= k \
                and time.time() - float(eski.get("t") or 0) < 7 * 86400:
            return
    except Exception:
        pass
    try:
        os.makedirs(CFG_DIR, exist_ok=True)
        with open(MUHUR_DOSYA, "w", encoding="utf-8") as f:
            json.dump({"ay": ay, "k": k, "t": time.time(), "_b": _muhur_butunluk(ay, k),
                       "_makine": makine_kimligi()}, f)
    except Exception:
        pass


def _muhur_oku():
    """(ay, en_az_kullanim, bozuk_mu) — dosya silinmişse (None, 0, False)."""
    try:
        d = json.load(open(MUHUR_DOSYA, encoding="utf-8"))
    except Exception:
        return None, 0, False
    ok = d.get("_b") == _muhur_butunluk(d.get("ay"), int(d.get("k") or 0))
    return d.get("ay"), int(d.get("k") or 0), (not ok)


def _bütünlük(veri):
    """Kota dosyası bütünlük özeti (kurcalama tespiti).

    Sır DEĞİL — amacı gizlilik değil, kazara/elle düzenlemeyi yakalamak.
    Gerçek güvenlik sunucu tarafı sayım + üçlü yedekten gelir.
    """
    import hashlib
    return hashlib.sha256((KOTA_TUZU + veri).encode()).hexdigest()[:32]


def _ay_baslangic(t=None):
    import datetime
    d = datetime.date.today() if t is None else datetime.date.fromtimestamp(t)
    return f"{d.year}-{d.month:02d}"


def _kota_bos():
    return {"ay": _ay_baslangic(), "kullanilan": 0, "son": time.time(),
            "kurcalandi": False, "pro": False, "lisans": ""}


def _kota_dogrula(d):
    """Dosya imzasını doğrular; bozulmuşsa None döner."""
    try:
        imza = d.pop("_imza", None)
        if not imza:
            return None
        beklenen = _bütünlük(json.dumps(d, sort_keys=True, ensure_ascii=False))
        return d if imza == beklenen else None
    except Exception:
        return None


def _kota_yaz(d):
    """Atomik yazma + HMAC imzası + gizli kopya."""
    try:
        os.makedirs(CFG_DIR, exist_ok=True)
        gövde = dict(d)
        gövde["_imza"] = _bütünlük(json.dumps(d, sort_keys=True, ensure_ascii=False))
        gecici = KOTA_DOSYA + ".tmp"
        with open(gecici, "w", encoding="utf-8") as f:
            json.dump(gövde, f, ensure_ascii=False, indent=1)
            f.flush()
            os.fsync(f.fileno())
        os.replace(gecici, KOTA_DOSYA)
        # gizli kopya (config içinde) — biri silinse diğeri kalır
        c = _cfg_oku_raw()
        c["_kota_kopya"] = {"ay": d.get("ay"), "kullanilan": d.get("kullanilan"),
                            "son": d.get("son"), "pro": d.get("pro")}
        _cfg_yaz_raw(c)
        # makineye bağlı kayıt: dosya silinse bile geçmiş korunur
        esk = _kayit_oku()
        _kayit_yaz({
            "ay": d.get("ay"),
            "kullanilan": max(int(esk.get("kullanilan") or 0) if esk.get("ay") == d.get("ay") else 0,
                              int(d.get("kullanilan") or 0)),
            "toplam": max(int(esk.get("toplam") or 0), int(d.get("toplam") or 0)),
            "_b": _kayit_butunluk(d.get("ay"), int(d.get("kullanilan") or 0),
                                  int(d.get("toplam") or 0)),
            "_makine": makine_kimligi(),
        })
        return True
    except Exception:
        return False


def _kayit_butunluk(ay, kullanilan, toplam):
    return hashlib.sha256(f"{KOTA_TUZU}|{ay}|{kullanilan}|{toplam}".encode()).hexdigest()[:32]


def _kayit_oku():
    try:
        d = json.load(open(KOTA_KAYIT, encoding="utf-8"))
        if d.get("_b") != _kayit_butunluk(d.get("ay"), int(d.get("kullanilan") or 0),
                                          int(d.get("toplam") or 0)):
            d["_bozuk"] = True
        return d
    except Exception:
        return {}


def _kayit_yaz(d):
    try:
        os.makedirs(CFG_DIR, exist_ok=True)
        tmp = KOTA_KAYIT + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tmp, KOTA_KAYIT)
        return True
    except Exception:
        return False


def _cfg_oku_raw():
    try:
        return json.load(open(os.path.join(CFG_DIR, "config.json"), encoding="utf-8"))
    except Exception:
        return {}


def _cfg_yaz_raw(d):
    try:
        p = os.path.join(CFG_DIR, "config.json")
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tmp, p)
        return True
    except Exception:
        return False


def _kota_yukle():
    """Beş kaynaktan EN YÜKSEK sayacı al; kurcalama/saat hilesi varsa işaretle."""
    ay = _ay_baslangic()
    adaylar = []
    kurcalandi = False
    try:
        saat_geri, _ileri = _saat_kontrol()
    except Exception:
        saat_geri = False
    if saat_geri:
        kurcalandi = True
        audit("saat-geri", "sistem saati geriye alınmış (deneme uzatma denemesi)", ok=False)

    # 1) ana dosya (imzalı)
    try:
        with open(KOTA_DOSYA, encoding="utf-8") as f:
            ham = json.load(f)
        d = _kota_dogrula(dict(ham))
        if d is None:
            kurcalandi = True
            # imza yok/bozuk → içindeki sayacı yine de "en az bu kadar" say
            d = {"ay": ham.get("ay") or ay,
                 "kullanilan": int(ham.get("kullanilan") or 0),
                 "son": float(ham.get("son") or 0),
                 "pro": bool(ham.get("pro")),
                 "lisans": ham.get("lisans") or ""}
        adaylar.append(d)
    except Exception:
        pass

    # 2) config içindeki gizli kopya
    c = _cfg_oku_raw()
    kopya = c.get("_kota_kopya")
    if isinstance(kopya, dict):
        adaylar.append({"ay": kopya.get("ay") or ay,
                        "kullanilan": int(kopya.get("kullanilan") or 0),
                        "son": float(kopya.get("son") or 0),
                        "pro": bool(kopya.get("pro")),
                        "lisans": ""})

    # 3) audit.log'daki saatlik damga
    try:
        with open(KOTA_AUDIT_ISARET, encoding="utf-8") as f:
            isaret = json.load(f)
        if isaret.get("ay") == ay:
            adaylar.append({"ay": ay, "kullanilan": int(isaret.get("kullanilan") or 0),
                            "son": float(isaret.get("son") or 0), "pro": False,
                            "lisans": ""})
    except Exception:
        pass

    # 4) makineye bağlı defter (dosyalar silinse bile burada durur)
    k = _kayit_oku()
    if k and not k.get("_bozuk"):
        adaylar.append({"ay": k.get("ay") or ay,
                        "kullanilan": int(k.get("kullanilan") or 0),
                        "son": float(k.get("son") or 0), "pro": bool(k.get("pro")),
                        "lisans": ""})
    elif k.get("_bozuk"):
        kurcalandi = True
        adaylar.append({"ay": k.get("ay") or ay,
                        "kullanilan": int(k.get("kullanilan") or 0),
                        "son": 0, "pro": False, "lisans": ""})

    # 5) imzalı cihaz mührü — dosyaların hepsi silinse bile "en az bu kadar"
    m_ay, m_k, m_bozuk = _muhur_oku()
    if m_ay == ay and m_k:
        adaylar.append({"ay": ay, "kullanilan": m_k, "son": 0, "pro": False, "lisans": ""})
    if m_bozuk:
        kurcalandi = True

    if not adaylar:
        return _kota_bos()

    # ay değiştiyse sayaç sıfırlanır
    secili = _kota_bos()
    for a in adaylar:
        if a.get("ay") != ay:
            continue
        if a.get("kullanilan", 0) > secili.get("kullanilan", 0):
            secili = {**_kota_bos(), **a, "ay": ay}
        if a.get("pro"):
            secili["pro"] = True
        if a.get("lisans"):
            secili["lisans"] = a["lisans"]

    # saat geri alma: son görülen tarih ileride olamaz
    sonlar = [a.get("son", 0) for a in adaylar if a.get("son")]
    if sonlar:
        secili["son"] = max(secili.get("son", 0), max(sonlar))

    # ---- SAAT HİLESİ: süre uzatma denemesi görülürse Pro kapanır ----
    if secili.get("kurcalandi"):
        secili["pro"] = False
        secili["pro_iptal"] = True
        secili["pro_iptal_neden"] = secili.get("pro_iptal_neden") or (
            "sayaç/saat doğrulaması başarısız — paket tarihleri güvenilir değil")

    # ---- PRO KARARI: bayrak yetmez, imzalı ve SÜRESİ GEÇMEMİŞ anahtar gerekir ----
    if secili.get("pro") and not secili.get("kurcalandi"):
        if not _pro_gecerli_mi(secili.get("lisans")):
            # anahtar geçersiz VEYA süresi doldu → Pro kendiliğinden kapanır
            secili["pro"] = False
            b = {}
            try:
                b = lisans_bilgi(secili.get("lisans") or "")
            except Exception:
                pass
            secili["pro_iptal"] = True
            secili["pro_iptal_neden"] = (b.get("error") or "lisans geçersiz")

    # %80 uyarı bayrağı yalnız AYNI ay için geçerli (yeni ayda tekrar uyarılır)
    for a in adaylar:
        if a.get("ay") == ay and a.get("uyardi80"):
            secili["uyardi80"] = True
            break

    secili["kurcalandi"] = kurcalandi or bool(secili.get("kurcalandi"))
    if kurcalandi:
        audit("kota-kurcalama", "kota.json imzası bozuk")
    return secili


_PRO_ONBELLEK = {"anahtar": "", "sonuc": False, "t": 0}

SAAT_DOSYA = os.path.join(CFG_DIR, ".saat")
SAAT_TOLERANS = 6 * 3600          # 6 saat: saat dilimi/uçuş payı
SAAT_GERI_ESIK = 24 * 3600        # 24 saatden fazla geri alma → hile say


def _saat_kontrol():
    """Sistem saati geriye alınmış mı? (deneme süresini uzatma hilesi)

    Son görülen zaman 5 yerde tutulur (saat dosyası, kota, defter, mühür,
    audit). Sistem saati bunlardan 24 saatten fazla geriyse hile işaretlenir;
    ileri alınmışsa sorun değil ama hemen "son" damgası yazılır.
    Döner: (geri_alindi: bool, ileri_atladi: bool)
    """
    simdi = time.time()
    onceki = []
    try:
        with open(SAAT_DOSYA, encoding="utf-8") as f:
            onceki.append(float((f.read() or "0").strip() or 0))
    except Exception:
        pass
    try:
        d = _kota_yukle_raw()
        onceki.append(float(d.get("son") or 0))
    except Exception:
        pass
    try:
        k = _kayit_oku()
        onceki.append(float(k.get("son") or 0))
    except Exception:
        pass
    try:
        with open(KOTA_AUDIT_ISARET, encoding="utf-8") as f:
            onceki.append(float((json.load(f) or {}).get("son") or 0))
    except Exception:
        pass
    en_buyuk = max([x for x in onceki if x > 0] or [0])
    geri = bool(en_buyuk and simdi < en_buyuk - SAAT_GERI_ESIK)
    ileri = bool(en_buyuk and simdi > en_buyuk + SAAT_TOLERANS)
    # her durumda ileriyi kaydet (kullanıcı saati ileri alıp geri almasın)
    try:
        os.makedirs(CFG_DIR, exist_ok=True)
        with open(SAAT_DOSYA, "w", encoding="utf-8") as f:
            f.write(str(max(simdi, en_buyuk)))
    except Exception:
        pass
    return geri, ileri


def _kota_yukle_raw():
    """Saat kontrolü için ham (doğrulamasız) okuma — özyineleme yok."""
    try:
        return json.load(open(KOTA_DOSYA, encoding="utf-8"))
    except Exception:
        return {}


def _pro_gecerli_mi(lisans_anahtari):
    """Pro durumu DOSYADAKİ BAYRAKTAN değil, imzalı anahtardan doğrulanır.

    Böylece kota.json içine "pro": true yazmak işe yaramaz: bayrak True olsa
    bile anahtar geçersizse (ya da başka makineye kilitliyse) Pro kapalıdır.
    60 saniyelik önbellek yalnız hız içindir.
    """
    k = (lisans_anahtari or "").strip()
    if not k:
        return False
    simdi = time.time()
    if _PRO_ONBELLEK["anahtar"] == k and simdi - _PRO_ONBELLEK["t"] < 60:
        return _PRO_ONBELLEK["sonuc"]
    try:
        ok, _neden = lisans_dogrula(k)
    except Exception:
        ok = False
    # ---- SUNUCU TARAFLI KONTROL (tanımlıysa) ----
    if ok:
        try:
            import lisans_online as _LO
            if _LO.sunucu_url():
                ok2, neden2, kaynak = _LO.dogrula_online(k, yerel_ok=True)
                if not ok2:
                    audit("lisans-sunucu", f"reddedildi ({kaynak}): {neden2}", ok=False)
                ok = ok2
        except Exception:
            pass                      # ağ hatası → yerel karar geçerli
    _PRO_ONBELLEK.update({"anahtar": k, "sonuc": bool(ok), "t": simdi})
    return bool(ok)


def _lisans_bilgi_guvenli(anahtar):
    if not anahtar:
        return {}
    try:
        b = lisans_bilgi(anahtar)
        return b if b.get("ok") else {"error": b.get("error")}
    except Exception:
        return {}



def _kota_geri_al():
    """Zaman aşımına uğrayan çağrıyı geri al — kullanıcı çalışmayan iş için ödemesin."""
    try:
        with KOTA_KILIT:
            d = _kota_yukle()
            if d.get("kullanilan", 0) > 0:
                d["kullanilan"] -= 1
                _kota_yaz(d)
                audit("kota", "zaman aşımı geri alındı")
    except Exception:
        pass

def kota_durum():
    """Panel/CLI için özet."""
    with KOTA_KILIT:
        d = _kota_yukle()
    kalan = max(0, KOTA_UCRETSIZ - d.get("kullanilan", 0))
    kull = d.get("kullanilan", 0)
    yuzde = round(100 * kull / KOTA_UCRETSIZ, 1) if KOTA_UCRETSIZ else 0
    return {
        "ay": d.get("ay"), "kullanilan": kull,
        "limit": KOTA_UCRETSIZ, "kalan": kalan,
        "yuzde": yuzde,
        # ---- rakip (Desktop Commander) standardı: %80 uyarısı + ay sıfırlaması
        "uyari_seviyesi": ("sinir" if kull >= KOTA_UCRETSIZ
                           else "uyari" if yuzde >= 80 else "normal"),
        "uyari_mesaji": ("" if d.get("pro") else
                         (f"Bu ay {kull:,} çağrının {int(yuzde)}%'ini kullandınız."
                          .replace(",", ".")
                          if yuzde >= 80 and kull < KOTA_UCRETSIZ else
                          "Aylık ücretsiz sınır doldu." if kull >= KOTA_UCRETSIZ else "")),
        "sifirlanma": "Her ayın 1'inde 00:00 UTC",
        "pro": bool(d.get("pro")), "sinirsiz": bool(d.get("pro")),
        "fiyat": KOTA_FIYAT, "bagis": BAGIS_URL,
        "lisans": d.get("lisans") or "",
        "lisans_bilgi": (lambda b: {
            "id": b.get("id"), "plan": b.get("plan"), "plan_adi": b.get("plan_adi"),
            "bitis": b.get("bitis"), "kalan_gun": b.get("kalan_gun"),
            "yenile": b.get("yenile"), "bagli_metin": b.get("bagli_metin")})(_lisans_bilgi_guvenli(d.get("lisans") or "")),
        "pro_iptal": bool(d.get("pro_iptal")),
        "pro_iptal_neden": d.get("pro_iptal_neden") or "",
        "kurcalandi": bool(d.get("kurcalandi")),
        "makine": makine_kimligi(),
        "asis": (not d.get("pro")) and (
            d.get("kullanilan", 0) >= KOTA_UCRETSIZ or bool(d.get("kurcalandi"))),
    }


def kota_say():
    """Bir araç çağrısı say. False → sınır aşıldı, çağrı reddedilmeli.

    Kurcalama tespit edilirse ücretsiz kota KAPALI davranır (fail-closed):
    sayacı silip/bozup sıfırdan başlamanın faydası olmaz — destek anahtarı
    gerekir. Bu bilinçli bir tercih: yanlış alarm olursa kullanıcı
    `python kur.py kota-sifirla` ile temizleyebilir.
    """
    global _KOTA_ONBELLEK
    with KOTA_KILIT:
        d = _kota_yukle()
        if d.get("pro"):
            d["kullanilan"] = d.get("kullanilan", 0) + 1
            d["son"] = time.time()
            _kota_yaz(d)
            return True
        if d.get("kullanilan", 0) >= KOTA_UCRETSIZ or d.get("kurcalandi"):
            return False
        d["kullanilan"] = d.get("kullanilan", 0) + 1
        # %80 uyarısı: ayda 1 kez, kullanıcıyı haberdar et (sürpriz olmasın)
        try:
            yuz = 100 * d["kullanilan"] / KOTA_UCRETSIZ
            if yuz >= 80 and not d.get("uyardi80"):
                d["uyardi80"] = True
                d["uyari80_t"] = int(time.time())
                audit("kota", f"%80 uyarı ({d['kullanilan']}/{KOTA_UCRETSIZ})")
        except Exception:
            pass
        d["son"] = time.time()
        _kota_yaz(d)
        _KOTA_ONBELLEK = d["kullanilan"]
        # sunucuya günlük kalp atışı (admin panelde görünmek için)
        try:
            import lisans_online as _LO
            if _LO.sunucu_url():
                _LO.kalp_at(kullanim=d["kullanilan"])
        except Exception:
            pass
        # haftalık cihaz mührü — dosyalar silinse bile "en az bu kadar" korunur
        try:
            _muhur_yaz(d)
        except Exception:
            pass
        # saatlik damga (audit)
        try:
            if int(time.time()) % 3600 < 2 or not os.path.exists(KOTA_AUDIT_ISARET):
                with open(KOTA_AUDIT_ISARET, "w", encoding="utf-8") as f:
                    json.dump({"ay": d["ay"], "kullanilan": d["kullanilan"],
                               "son": d["son"]}, f)
        except Exception:
            pass
        return True


_KOTA_ONBELLEK = 0


def lisans_dogrula(anahtar):
    """Ed25519 imza doğrulaması — sır BURADA DEĞİL, yalnız açık anahtar.

    Kod açık kaynak olsa bile kimse geçerli anahtar üretemez; üretmek için
    BTM Code'un özel anahtarı (gizli_anahtar.pem) gerekir.
    """
    try:
        import lisans as _L
        return _L.dogrula(anahtar)
    except Exception as e:
        return False, f"lisans modülü yüklenemedi: {e}"


def lisans_bilgi(anahtar):
    try:
        import lisans as _L
        return _L.bilgi(anahtar)
    except Exception as e:
        return {"ok": False, "error": str(e)}


def lisans_ayarla(anahtar):
    b = lisans_bilgi(anahtar)
    if not b.get("ok"):
        return {"ok": False, "error": f"Geçersiz lisans: {b.get('error')}"}
    with KOTA_KILIT:
        d = _kota_yukle()
        d["pro"] = True
        d["lisans"] = anahtar.strip()
        d["son"] = time.time()
        _kota_yaz(d)
    audit("lisans", f"etkinleştirildi ({b.get('id')})")
    return {"ok": True, "pro": True,
            "message": f"GhostPilot Pro etkinleştirildi ({b.get('bitis')})."}


# ============================================================================
#  MCP — JSON-RPC
# ============================================================================

def rpc(req):
    method = req.get("method")
    rid = req.get("id")
    params = req.get("params") or {}

    def ok(result):
        return {"jsonrpc": "2.0", "id": rid, "result": result}

    def err(code, msg):
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": msg}}

    if method == "initialize":
        return ok({
            "protocolVersion": "2025-06-18",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": server_info(_ISTEM_BASE or ""),
        })
    if method in ("notifications/initialized", "initialized"):
        return None
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": schemas()})
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        result = call_tool(name, args)
        content = []
        # Ekran görüntüsü → modelin GERÇEKTEN gördüğü görsel içerik
        b64 = result.get("base64") if isinstance(result, dict) else None
        if b64 and result.get("ok"):
            mime = "image/jpeg" if (result.get("format") or "jpeg") == "jpeg" else "image/png"
            content.append({"type": "image", "data": b64, "mimeType": mime})
            meta = {k: v for k, v in result.items() if k != "base64"}
            content.append({"type": "text",
                            "text": json.dumps(meta, ensure_ascii=False, indent=1)})
        else:
            content.append({"type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=1)})
        return ok({"content": content, "isError": not result.get("ok", True)})
    if method == "resources/list":
        return ok({"resources": []})
    if method == "prompts/list":
        return ok({"prompts": []})
    return err(-32601, f"Bilinmeyen metot: {method}")


def run_bridge():
    """stdio MCP sunucusu (Claude Desktop, Cursor, VS Code)."""
    sys.stderr.write(f"[GhostPilot] stdio köprü v{VERSION} — {len(TOOLS)} araç hazır\n")
    sys.stderr.flush()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        resp = rpc(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()



# ============================================================================
#  OAUTH 2.1 — ChatGPT'nin "OAuth" seçeneği için
#  Akış: keşif (/.well-known) → /authorize (onay ekranı) → kod → /token
#  Kodlar ve erişim anahtarları diske yazılır; sunucu yeniden başlasa da geçerli.
# ============================================================================

OAUTH_FILE = os.path.join(CFG_DIR, "oauth.json")
OAUTH_TTL = 30 * 24 * 3600           # erişim anahtarı 30 gün
CODE_TTL = 300                        # yetkilendirme kodu 5 dakika


def _oauth_load():
    try:
        if os.path.exists(OAUTH_FILE):
            return json.load(open(OAUTH_FILE, encoding="utf-8")) or {}
    except Exception:
        pass
    return {"clients": {}, "tokens": {}, "codes": {}}


def _oauth_save(d):
    _mkdir(CFG_DIR)
    try:
        with open(OAUTH_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
        try:
            os.chmod(OAUTH_FILE, 0o600)
        except Exception:
            pass
    except Exception:
        pass


def _pkce_s256(verifier: str) -> str:
    h = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(h).decode().rstrip("=")


def _iso(ts):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


ONAY_HTML = """<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GhostPilot — Erişim izni</title>
<style>
 :root{color-scheme:dark}
 *{box-sizing:border-box}
 body{margin:0;min-height:100vh;display:grid;place-items:center;
   font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
   background:#0b1120;color:#e2e8f0;padding:24px}
 .kart{max-width:460px;width:100%;background:#111a2e;border:1px solid #1e2d4a;
   border-radius:18px;padding:28px;box-shadow:0 20px 60px #0008}
 h1{margin:0 0 6px;font-size:20px;display:flex;gap:10px;align-items:center}
 .alt{color:#8b9bb4;font-size:13px;margin:0 0 18px}
 .istemci{background:#0d1626;border:1px solid #1e2d4a;border-radius:12px;
   padding:12px 14px;margin-bottom:16px;font-size:13px;color:#b8c6dc}
 .istemci b{color:#e2e8f0}
 ul{margin:0 0 20px;padding-left:18px;font-size:13px;color:#b8c6dc}
 li{margin:3px 0}
 .adim{display:flex;gap:14px;padding:14px 0;border-top:1px solid var(--cizgi)}
.adim:first-of-type{border-top:0}
.adim-no{flex:0 0 30px;height:30px;border-radius:50%;background:#1e2d4a;
 color:#c9d5e8;font-weight:700;font-size:14px;display:flex;align-items:center;
 justify-content:center}
.adim-govde{flex:1;min-width:0}
.adim-bas{font-weight:700;font-size:14px;margin-bottom:8px}
.dugme-link{display:inline-block;background:#1e2d4a;color:#c9d5e8;font-weight:600;
 padding:10px 15px;border-radius:10px;text-decoration:none;font-size:13px}
.kopya-kutu{background:#0d1626;border:1px dashed #3b5075;border-radius:10px;
 padding:12px;font-size:12px;white-space:pre-wrap;word-break:break-all;
 cursor:pointer;margin:0;color:#a5d6ff}
.form-tablo td{padding:8px 10px}
.form-tablo th{width:170px;vertical-align:top}
.form-tablo tr.vurgu{background:#2a1c0d}
.form-tablo tr.vurgu td{color:#f0c07a}
.kirmizi{color:#f87171;font-weight:700}
.mini{background:#1e2d4a;color:#9fb3d1;border:0;border-radius:6px;
 font-size:11px;padding:3px 8px;margin-left:6px;cursor:pointer}
.btn-destek{display:inline-block;background:#ffdd00;color:#0b1120;
 font-weight:700;padding:12px 18px;border-radius:11px;text-decoration:none;
 font-size:14px;margin:0 8px 8px 0}
.btn-gh{display:inline-block;background:#1e2d4a;color:#c9d5e8;font-weight:600;
 padding:12px 16px;border-radius:11px;text-decoration:none;font-size:14px;margin:0 8px 8px 0}
.btn-anahtar{display:inline-block;background:#22c55e;color:#06240f;font-weight:700;
 padding:12px 16px;border-radius:11px;text-decoration:none;font-size:14px;margin:0 8px 8px 0}
.uyari{background:#2a1c0d;border:1px solid #5b3d10;border-radius:10px;
   padding:10px 12px;font-size:12.5px;color:#f0c07a;margin-bottom:20px}
 .dug{margin-top:8px}
 button{width:100%;padding:13px;border-radius:11px;border:0;font-size:15px;
   font-weight:600;cursor:pointer;margin-bottom:9px}
 .onayla{background:#f59e0b;color:#1a1206}
 .reddet{background:#1e2d4a;color:#c9d5e8}
 button:active{transform:translateY(1px)}
 footer{margin-top:14px;font-size:11.5px;color:#64748b;text-align:center}
</style></head><body>
<div class="kart">
  <h1>👻 GhostPilot</h1>
  <p class="alt">Bu bilgisayara erişim izni isteniyor</p>
  <div class="istemci">İsteyen: <b>__CLIENT__</b><br>Bilgisayar: <b>__HOST__</b></div>
  <ul>
    <li>Dosya okuma ve yazma (izin verilen klasörler)</li>
    <li>Terminal komutu çalıştırma</li>
    <li>Ekran görüntüsü alma, fare ve klavye</li>
    <li>Uygulama açma, bildirim gösterme</li>
  </ul>
  <div class="uyari">Yalnızca kendi başlattığınız bir bağlantıysa onaylayın.
    Bu ekranı siz açmadıysanız <b>Reddet</b>.</div>
  <form method="post" action="/oauth/authorize">
    <input type="hidden" name="sid" value="__SID__">
    <div class="dug">
      <button class="onayla" name="karar" value="onayla">✅ İzin ver</button>
      <button class="reddet" name="karar" value="reddet">Reddet</button>
    </div>
  </form>
  <footer>İzni geri almak için: <code>python kur.py oauth-sil</code></footer>
</div></body></html>"""


def oauth_metadata(base, include_auth_methods=False):
    """OAuth 2.1 yetkilendirme sunucusu üst verisi.

    ÖNEMLİ: registration_endpoint AÇIKÇA duyurulmalı — yoksa ChatGPT
    "Dinamik istemci kaydı (DCR) kullanılamıyor" der ve kullanıcıdan
    elle istemci kimliği/gizli anahtar ister (istemiyoruz).
    """
    d = {
        "issuer": base,
        "authorization_endpoint": base + "/oauth/authorize",
        "token_endpoint": base + "/oauth/token",
        "registration_endpoint": base + "/oauth/register",
        "response_types_supported": ["code"],
        "response_modes_supported": ["query"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256", "plain"],
        "scopes_supported": ["ghostpilot"],
        # ChatGPT'nin istemci kaydı yöntemleri (spec 2025-11-25)
        "client_registration_approaches_supported": [
            "dynamic_client_registration",
        ],
        "service_documentation": "https://github.com/Btmcode/Ghost-Pilot",
    }
    if include_auth_methods:
        d["token_endpoint_auth_methods_supported"] = ["none",
                                                      "client_secret_post",
                                                      "client_secret_basic"]
        d["registration_endpoint_auth_methods_supported"] = ["none"]
    return d


def oauth_scope_ok(header_value):
    """Authorization: Bearer <oauth_token> geçerli mi?"""
    if not header_value:
        return False
    t = header_value.replace("Bearer ", "").strip()
    if not t:
        return False
    d = _oauth_load()
    rec = (d.get("tokens") or {}).get(t)
    if not rec:
        return False
    if rec.get("expires_at", 0) and rec["expires_at"] < time.time():
        return False
    return True





# ============================================================================
#  ONAY MEKANİZMASI — riskli işler panelde onay bekler
#  Kullanıcı panelden "Onayla" demezse iş YAPILMAZ (varsayılan: RET).
# ============================================================================

ONAY_BEKLEYEN = {}          # id -> {"tool","args","t","sonuc"}
ONAY_KILIT = threading.Lock()
ONAY_SURESI = 120           # saniye; sonra otomatik RET
RISKLI_ARACLAR = {"delete", "move", "shell", "job_start", "write", "edit"}


def _onay_gerekli(name):
    """Onay zorunlu mu? config: onay = "riskli" (varsayılan) | "hepsi" | "kapali".

    SANAL BİLGİSAYAR: ajan zaten kendi kutusunda çalışıyor → onay sorulmaz.
    Gerçek makinede davranış değişmez.
    """
    sd = _sanal()
    if sd and sd.acik(CFG):
        return False
    mode = (CFG.get("onay") or "riskli").lower()
    if mode == "kapali":
        return False
    if mode == "hepsi":
        return True
    return name in RISKLI_ARACLAR



def _onay_ekrani_var():
    """Onay ekranı (masaüstü paneli veya tarayıcı paneli) gerçekten açık mı?

    ÖNEMLİ: relay/watchdog pid dosyaları SAYILMAZ — onlar sunucunun kendisidir,
    onay isteğini gösteremezler. Onay ekranı = /panel/veri adresini düzenli
    çağıran bir arayüz (masaüstü paneli 3 sn'de bir, tarayıcı 2 sn'de bir).
    """
    # 1) Masaüstü arayüzü son 10 sn içinde veri çekti mi?
    if _arayuz_canli():
        return True
    # 2) Tarayıcı paneli açık mı? (.panel_goruldu damgası her /panel/veri çağrısında yazılır)
    try:
        t = int(open(os.path.join(CFG_DIR, ".panel_goruldu"),
                     encoding="utf-8").read().strip() or 0)
        if (time.time() - t) <= 12:
            return True
    except Exception:
        pass
    return False


def onay_iste(name, args):
    """İşi kuyruğa al, kullanıcı panelden karar verene kadar bekle."""
    import uuid
    oid = uuid.uuid4().hex[:10]
    entry = {"tool": name, "args": {k: str(v)[:200] for k, v in args.items()},
             "t": time.strftime("%H:%M:%S"), "sonuc": None}
    with ONAY_KILIT:
        ONAY_BEKLEYEN[oid] = entry
    audit("onay-bekle", f"{name} ({oid})")
    # Onay ekranı gerçekten açık mı? Kapalıysa 120 sn beklemek yerine
    # hemen anlaşılır bir hata dön — kullanıcı boş yere beklemesin.
    if not _onay_ekrani_var():
        with ONAY_KILIT:
            ONAY_BEKLEYEN.pop(oid, None)
        audit("onay-yok", f"{name}: onay ekranı çalışmıyor", ok=False)
        return {"ok": False, "onay_yok": True, "engine": "approval_unavailable",
                "error": "Bu işlem ONAY gerektiriyor ama onay ekranı açık değil. "
                         "İşlem YAPILMADI.",
                "hint": "GhostPilot panelini açın (python kur.py panel) veya "
                        "onay modunu değiştirin (python kur.py mod onay riskli)"}
    bitis = time.time() + ONAY_SURESI
    while time.time() < bitis:
        if entry["sonuc"] is not None:
            break
        time.sleep(0.25)
    with ONAY_KILIT:
        karar = entry["sonuc"]
        ONAY_BEKLEYEN.pop(oid, None)
    if karar == "onay":
        audit("onay-verildi", f"{name} ({oid})")
        return None                      # devam et
    audit("onay-red", f"{name} ({oid})")
    return {"ok": False, "denied": True,
            "error": "Kullanıcı bu işlemi ONAYLAMADI (veya 120 sn içinde yanıt gelmedi). "
                     "İşlem yapılmadı.",
            "hint": "Kullanıcı panelden onaylamalı: http://127.0.0.1:<port>/panel"}


def onay_karar(oid, karar):
    with ONAY_KILIT:
        e = ONAY_BEKLEYEN.get(oid)
        if not e:
            return False
        e["sonuc"] = "onay" if karar in ("onay", "onayla", "evet", "ok") else "ret"
    return True


def onay_listesi():
    with ONAY_KILIT:
        return {k: dict(v) for k, v in ONAY_BEKLEYEN.items()}



# ============================================================================
#  DESTEK / KATKI — tek yerden yönetilir
#  GhostPilot ücretsiz ve açık kaynak (MIT). İsteyen bağış yapabilir.
# ============================================================================

# --- geliştirici kimliği (mağaza/eklenti kartlarında görünen bilgi) ---
GELISTIRICI = "BtmCode"
GELISTIRICI_EPOSTA = "devcloudpy@gmail.com"

DESTEK_URL = "https://buymeacoffee.com/btmcode"      # donate / bağış
SITE_URL = "https://btmcode.vercel.app"
BLOG_URL = "https://mnemark.blogspot.com"
REPO_URL = "https://github.com/Btmcode/Ghost-Pilot"
GITHUB_PROFIL = "https://github.com/Btmcode"
KOSUL_URL = "https://github.com/Btmcode/Ghost-Pilot/blob/main/KOSULLAR.md"
GIZLILIK_URL = "https://github.com/Btmcode/Ghost-Pilot/blob/main/GIZLILIK.md"
DESTEK_ANAHTAR_URL = "https://buymeacoffee.com/btmcode"   # destek anahtarı isteği


def _islem_sayaci():
    """Denetim kaydından toplam işlem sayısını sayar (bağış kutusu için)."""
    try:
        p = os.path.join(CFG_DIR, "audit.log")
        with open(p, "rb") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def _paket_html():
    """Web panelindeki Free / PRO karşılaştırma kutusu (fiyat: paketler.py)."""
    try:
        import paketler as PK
        satir = ""
        for i, (anahtar, ucretsizde) in enumerate(PK.OZELLIKLER):
            bg = " style=\"background:#16281a\"" if True else ""
            satir += (
                f'<tr><td style="padding:5px 0;color:#8b9bb4">{PK.m(anahtar)}</td>'
                f'<td style="text-align:center;color:{"#22c55e" if ucretsizde else "#3d4a5f"}">'
                f'{"✓" if ucretsizde else "—"}</td>'
                f'<td style="text-align:center;background:#16281a;color:#22c55e">✓</td></tr>')
        return f"""<div class="bolum">
  <h2>{PK.m('baslik')}</h2>
  <p class="alt" style="margin:0 0 12px">{PK.m('alt')}</p>
  <table style="width:100%;border-collapse:collapse;font-size:13px">
    <tr>
      <th style="text-align:left"></th>
      <th style="text-align:center;color:#e2e8f0;padding-bottom:6px">{PK.m('ucretsiz')}
        <div style="color:#f59e0b;font-size:16px">0 {PK.PARA_BIRIMI}</div></th>
      <th style="text-align:center;background:#16281a;border-radius:8px 8px 0 0;padding:6px">
        <div style="color:#22c55e;font-size:10px;letter-spacing:.5px">{PK.m('en_cok')}</div>
        <div style="color:#22c55e">PRO</div>
        <div style="color:#f59e0b;font-size:16px">{PK.PARA_BIRIMI}{PK.AYLIK_FIYAT}{PK.m('ay')}</div></th>
    </tr>
    {satir}
  </table>
  <p class="alt" style="margin:12px 0 0;font-size:12px">{PK.m('fiyat_not')}</p>
  <a href="{PK.BAGIS_URL}" target="_blank" rel="noopener"
     style="display:inline-block;margin-top:11px;background:#22c55e;color:#06240f;
            font-weight:700;padding:11px 18px;border-radius:11px;text-decoration:none">
    💛 {PK.m('katil')}</a>
</div>"""
    except Exception:
        return ""


PANEL_DESTEK = """<div class="bolum" id="destekBolum">
  <h2>Destek · bağış · bağlantılar</h2>
  <p class="alt" style="margin:0 0 12px">
    GhostPilot <b>ücretsiz, açık kaynak (MIT)</b>. Satış yok — sürdürmek için
    tek yol bağış. İşinize yaradıysa bir kahve ısmarlayabilirsiniz.
  </p>
  <a href="%s" target="_blank" rel="noopener" class="btn-destek">
    ☕ Bağış yap (Buy me a coffee)
  </a>
  <a href="%s" target="_blank" rel="noopener" class="btn-gh">
    ⭐ GitHub deposu
  </a>
  <a href="%s" target="_blank" rel="noopener" class="btn-anahtar">
    🔑 Destek anahtarı iste
  </a>

  <table style="margin-top:16px">
    <tr><th style="width:170px">Geliştirici</th><td><b>%s</b></td></tr>
    <tr><th>Web sitesi</th><td><a href="%s" target="_blank">%s</a></td></tr>
    <tr><th>Kaynak kodu</th><td><a href="%s" target="_blank">%s</a></td></tr>
    <tr><th>GitHub profili</th><td><a href="%s" target="_blank">%s</a></td></tr>
    <tr><th>Bağış</th><td><a href="%s" target="_blank">%s</a></td></tr>
    <tr><th>Gizlilik</th><td><a href="%s" target="_blank">Gizlilik politikası</a></td></tr>
    <tr><th>Koşullar</th><td><a href="%s" target="_blank">Kullanım koşulları</a></td></tr>
    <tr><th>Blog</th><td><a href="%s" target="_blank">%s</a></td></tr>
    <tr><th>İletişim</th><td><a href="mailto:%s">%s</a></td></tr>
  </table>
</div>""" % (DESTEK_URL, REPO_URL, DESTEK_ANAHTAR_URL,
             GELISTIRICI,
             SITE_URL, SITE_URL.replace("https://", ""),
             REPO_URL, REPO_URL.replace("https://", ""),
             GITHUB_PROFIL, GITHUB_PROFIL.replace("https://", ""),
             DESTEK_URL, DESTEK_URL.replace("https://", ""),
             GIZLILIK_URL, KOSUL_URL,
             BLOG_URL, BLOG_URL.replace("https://", ""),
             GELISTIRICI_EPOSTA, GELISTIRICI_EPOSTA)


# ============================================================================
#  YEREL PANEL — tarayıcıdan durum, izinler, denetim kaydı, DURDUR
#  Adres: http://127.0.0.1:<port>/panel   (yalnız bu bilgisayardan)
# ============================================================================

PANEL_HTML = """<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GhostPilot — Panel</title>
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="/icon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#0b1120">
<meta name="apple-mobile-web-app-title" content="GhostPilot">
<style>
:root{color-scheme:dark;--bg:#0b1120;--kart:#121c2f;--cizgi:#1e2d4a;
 --metin:#e2e8f0;--soluk:#8b9bb4;--amber:#f59e0b;--yesil:#22c55e;--kirmizi:#ef4444}
*{box-sizing:border-box}
body{margin:0;font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
 background:var(--bg);color:var(--metin);padding:22px}
.wrap{max-width:900px;margin:0 auto}
h1{font-size:20px;margin:0 0 4px;display:flex;align-items:center;gap:9px}
.alt{color:var(--soluk);font-size:13px;margin:0 0 20px}
.izgara{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-bottom:18px}
.kart{background:var(--kart);border:1px solid var(--cizgi);border-radius:14px;padding:14px 16px}
.kart .b{font-size:12px;color:var(--soluk);text-transform:uppercase;letter-spacing:.4px}
.kart .d{font-size:17px;font-weight:600;margin-top:3px}
.ok{color:var(--yesil)} .no{color:var(--kirmizi)} .uy{color:var(--amber)}
.bolum{background:var(--kart);border:1px solid var(--cizgi);border-radius:14px;
 padding:16px 18px;margin-bottom:14px}
.bolum h2{font-size:14px;margin:0 0 10px;color:var(--soluk);text-transform:uppercase;
 letter-spacing:.5px;font-weight:600}
button{border:0;border-radius:11px;padding:11px 16px;font-size:14px;font-weight:600;
 cursor:pointer;margin:0 8px 8px 0}
.dur{background:var(--kirmizi);color:#fff;font-size:15px;padding:14px 22px}
.gri{background:#1e2d4a;color:#c9d5e8}
.amber{background:var(--amber);color:#1a1206}
pre{background:#0d1626;border:1px solid var(--cizgi);border-radius:10px;padding:12px;
 overflow:auto;max-height:260px;font-size:12.5px;margin:0;white-space:pre-wrap;word-break:break-all}
code{background:#0d1626;padding:2px 6px;border-radius:6px;font-size:12.5px}
table{width:100%;border-collapse:collapse;font-size:13px}
td,th{text-align:left;padding:6px 8px;border-bottom:1px solid var(--cizgi)}
th{color:var(--soluk);font-weight:600;font-size:12px}
.uyari{background:#2a1c0d;border:1px solid #5b3d10;border-radius:10px;padding:11px 14px;
 font-size:12.5px;color:#f0c07a;margin-bottom:16px}
</style></head><body><div class="wrap">
<h1><img src="/icon.svg" width="34" height="34" alt=""
     style="border-radius:9px;flex:0 0 auto"> GhostPilot
     <span id="surum" class="alt" style="margin:0;pointer-events:none"></span>
     <span id="aiDurum" style="margin-left:auto;font-size:11.5px;font-weight:700;
       padding:4px 11px;border-radius:99px;background:#1e2d4a;color:#c9d5e8;
       pointer-events:none">KONTROL EDİLİYOR…</span></h1>
<p class="alt">{KAPSAM_YAZI}</p>

<div class="uyari">{KAPSAM_UYARI}</div>

<div class="izgara">
  <div class="kart"><div class="b">Sunucu</div><div class="d" id="durum">—</div></div>
  <div class="kart"><div class="b">Bekçi</div><div class="d" id="bekci">—</div></div>
  <div class="kart"><div class="b">Araç</div><div class="d" id="arac">—</div></div>
  <div class="kart"><div class="b">Mod</div><div class="d" id="mod">—</div></div>
  <div class="kart"><div class="b">izin</div><div class="d" id="oauth">—</div></div>
  <div class="kart"><div class="b">İşlem imleci</div><div class="d" id="ajan">—</div></div>
  <div class="kart" style="grid-column:1/-1">
    <div class="b">Bu ayki kullanım</div>
    <div class="d" id="kotaMetin">—</div>
    <div style="height:8px;background:#1e2d4a;border-radius:6px;margin-top:9px;overflow:hidden">
      <div id="kotaBar" style="height:100%;width:0%;background:#22c55e;transition:width .4s"></div>
    </div>
    <div class="alt" id="kotaAlt" style="font-size:12px;margin-top:7px"></div>
  </div>
</div>

<div class="bolum" id="onayBolum" style="display:none">
  <h2>⚠️ Onay bekleyen işlemler</h2>
  <div id="onayListe"></div>
</div>

<div class="bolum">
  <h2>Acil durdurma</h2>
  <button type="button" class="dur" id="btnDur" onclick="eylem('durdur',this)">⛔ UZAKTAN ERİŞİMİ DURDUR</button>
  <button type="button" class="gri" id="btnBasla" onclick="eylem('basla',this)">▶ Yeniden başlat</button>
  <button type="button" class="gri" style="font-size:12px;padding:8px 12px"
          onclick="if(confirm('Sunucu tamamen kapanacak. Pencereyi açmak için masaüstündeki kısayolu kullanmanız gerekir. Devam?'))eylem('sunucu-kapat',this)">
    🔌 Sunucuyu tamamen kapat</button>
  <div id="sonuc" class="alt" style="margin:10px 0 0"></div>
</div>

<div class="bolum" id="baglaBolum">
  <h2>🔌 ChatGPT'ye bağla — 4 adım</h2>

  <div class="adim">
    <div class="adim-no">1</div>
    <div class="adim-govde">
      <div class="adim-bas">Bağlantı adresini hazırla</div>
      <button type="button" class="amber" onclick="eylem('bagla',this)">🔗 Adresi hazırla</button>
      <button type="button" class="gri" onclick="kopyalaUrl(this)">📋 Adresi kopyala</button>
      <div id="baglaSonuc" class="alt" style="margin-top:8px"></div>
      <div id="baglaKutu" style="display:none;margin-top:10px">
        <pre id="baglaUrl" class="kopya-kutu" onclick="kopyalaUrl(this)"
             title="Kopyalamak için tıklayın"></pre>
      </div>
    </div>
  </div>

  <div class="adim">
    <div class="adim-no">2</div>
    <div class="adim-govde">
      <div class="adim-bas">ChatGPT'de Eklentiler sayfasını aç</div>
      <a class="dugme-link" href="https://chatgpt.com/plugins" target="_blank" rel="noopener">
        ↗ chatgpt.com/plugins
      </a>
      <div class="alt" style="margin-top:6px">
        Sol menüden <b>Eklentiler</b> de buraya açılır. Sağ üstteki
        <b>Ekle</b> düğmesine bas, sonra <b>Özel MCP sunucusu</b>nu seç.
      </div>
    </div>
  </div>

  <div class="adim">
    <div class="adim-no">3</div>
    <div class="adim-govde">
      <div class="adim-bas">Açılan formu böyle doldur</div>
      <table class="form-tablo">
        <tr><th>Simge</th><td><code>chatgpt-icon-256.png</code>
            <span class="alt">(klasördeki dosya · 9.9 KB)</span></td></tr>
        <tr><th>Ad</th><td><code>GhostPilot</code>
            <button class="mini" onclick="kopyalaMetin('GhostPilot',this)">kopyala</button></td></tr>
        <tr><th>Açıklama</th><td><code>Bilgisayarımdaki dosyalar ve komutlar</code>
            <button class="mini" onclick="kopyalaMetin('Bilgisayarımdaki dosyalar ve komutlar',this)">kopyala</button></td></tr>
        <tr><th>Bağlantı</th><td><b>Sunucu URL'si</b> seçili kalsın</td></tr>
        <tr><th>Sunucu URL'si</th><td><code id="formUrl">— adres hazır olunca burada —</code>
            <button class="mini" onclick="kopyalaUrl(this)">kopyala</button></td></tr>
        <tr class="vurgu"><th>Kimlik doğrulama</th>
            <td><b>Yok</b> seç · <span class="kirmizi">OAuth'a DOKUNMA</span>
            <div class="alt">Anahtar adresin içinde geliyor. OAuth seçilirse bağlanmaz.</div></td></tr>
        <tr><th>Onay kutusu</th><td><b>"Anladım ve devam etmek istiyorum"</b>u işaretle</td></tr>
      </table>
    </div>
  </div>

  <div class="adim">
    <div class="adim-no">4</div>
    <div class="adim-govde">
      <div class="adim-bas">Oluştur'a bas ve deneyin</div>
      <div class="alt">
        Yeni bir sohbet aç → sohbette <b>+</b> → <b>GhostPilot</b> → yaz:
        <code>ghostpilot_status</code>
      </div>
    </div>
  </div>
</div>

<div class="bolum">
  <h2>Mod</h2>
  <button class="gril" onclick="eylem('salt-okunur')" id="bSalt">👁 Salt okunur</button>
  <button class="amber" onclick="eylem('yazma')">✍️ Okuma + yazma</button>
  <button class="gri" onclick="eylem('oauth-sil')">🔑 Tüm izinleri iptal et</button>
</div>

<div class="bolum">
  <h2>İzin verilen klasörler</h2>
  <table id="klasorler"></table>
  <p class="alt" style="margin:10px 0 0">Eklemek için:
    <code>python kur.py izin "D:\\Proje"</code></p>
</div>

""" + _paket_html() + PANEL_DESTEK + """

<div class="bolum">
  <h2>Son işlemler (denetim kaydı)</h2>
  <pre id="kayit">yükleniyor…</pre>
</div>

</div><script>
let sonHata = '';
function durumYaz(){
  const e = document.getElementById('aiDurum');
  const kapali = document.body.dataset.ai === 'kapali';
  e.textContent = kapali ? '⛔ ERİŞİM KAPALI' : '✅ ERİŞİM AÇIK';
  e.style.background = kapali ? '#3a1010' : '#0d2f1f';
  e.style.color = kapali ? '#f87171' : '#4ade80';
}
let sonUrl = '';
function kopyalaUrl(btn){
  if(!sonUrl){ eylem('bagla', btn); return; }
  (navigator.clipboard ? navigator.clipboard.writeText(sonUrl) : Promise.reject())
    .then(function(){ document.getElementById('baglaSonuc').textContent = '✅ Adres kopyalandi.'; })
    .catch(function(){ window.prompt('Adresi kopyalayin (Ctrl+C):', sonUrl); });
}
async function yukle(){
  try{
    const r = await fetch('/panel/veri', {cache:'no-store'});
    if(!r.ok) throw new Error('HTTP '+r.status);
    const d = await r.json();
    document.body.dataset.ai = d.ai_kapali ? 'kapali' : 'acik';
    durumYaz();
    document.getElementById('surum').textContent = 'v'+d.version;
    const st=document.getElementById('durum');
    st.textContent = d.running ? 'ÇALIŞIYOR' : 'KAPALI';
    st.className = 'd ' + (d.running?'ok':'no');
    const bk=document.getElementById('bekci');
    bk.textContent = d.watchdog ? 'aktif' : 'yok';
    bk.className = 'd ' + (d.watchdog?'ok':'uy');
    document.getElementById('arac').textContent = d.tools;
    const md=document.getElementById('mod');
    md.textContent = d.read_only ? 'Salt okunur' : 'Okuma+yazma';
    md.className='d '+(d.read_only?'uy':'ok');
    document.getElementById('oauth').textContent = d.oauth_tokens;
    const aj=document.getElementById('ajan');
    aj.textContent = (d.agent_visible && d.agent_visible.ready) ? 'açık' : 'kapalı';
    aj.className='d '+((d.agent_visible && d.agent_visible.ready)?'ok':'uy');
    document.getElementById('klasorler').innerHTML =
      '<tr><th>Tür</th><th>Klasör</th></tr>' +
      d.read_roots.map(x=>'<tr><td>okuma</td><td><code>'+x+'</code></td></tr>').join('') +
      d.write_roots.map(x=>'<tr><td>yazma</td><td><code>'+x+'</code></td></tr>').join('');
    const ob=document.getElementById('onayBolum'), ol=document.getElementById('onayListe');
    const ids=Object.keys(d.onay||{});
    if(ids.length){
      ob.style.display='block';
      // nested tırnak YOK: data-* özniteliği + addEventListener
      ol.innerHTML = ids.map(function(id){
        const o=d.onay[id];
        return '<div style="border:1px solid #5b3d10;background:#2a1c0d;border-radius:10px;'+
          'padding:11px 13px;margin-bottom:9px">'+
          '<div style="font-size:13.5px;margin-bottom:7px"><b>'+o.tool+'</b> '+
          '<span class="alt">('+o.t+')</span><br><code style="font-size:11.5px">'+
          JSON.stringify(o.args).slice(0,160)+'</code></div>'+
          '<button type="button" class="amber" data-karar="onay" data-id="'+id+'">✔ Onayla</button>'+
          '<button type="button" class="gri" data-karar="ret" data-id="'+id+'">✖ Reddet</button></div>';
      }).join('');
      ol.querySelectorAll('button[data-karar]').forEach(function(b){
        b.addEventListener('click', function(){
          eylem(b.dataset.karar + ':' + b.dataset.id, b);
        });
      });
    } else { ob.style.display='none'; }
    const k=d.kota||{};
    const bar=document.getElementById('kotaBar');
    const yuz=Math.min(100, k.yuzde||0);
    bar.style.width = yuz+'%';
    bar.style.background = k.pro ? '#22d3ee' : (yuz>=100 ? '#ef4444' : yuz>=80 ? '#f59e0b' : '#22c55e');
    const lb=k.lisans_bilgi||{};
    const paketAd = lb.plan_adi ? (lb.plan_adi+(lb.kalan_gun!=null?' · '+lb.kalan_gun+' gün kaldı':'')) : '';
    document.getElementById('kotaMetin').textContent = k.pro
      ? ('PRO · sınırsız' + (paketAd ? ('  ·  '+paketAd) : ''))
      : (k.kullanilan||0).toLocaleString('tr-TR')+' / '+(k.limit||20000).toLocaleString('tr-TR')+' çağrı';
    document.getElementById('kotaAlt').innerHTML = k.pro
      ? (lb.yenile
          ? '<span style="color:#f59e0b">⏳ Paket bitiyor ('+lb.kalan_gun+' gün). Yenile → <a href="'+((k.bagis)||'https://buymeacoffee.com/btmcode')+'" target="_blank" style="color:#22d3ee">destek ol</a></span>'
          : 'Paket: '+paketAd+' — teşekkürler 💛')
      : (k.pro_iptal
          ? '<span style="color:#ef4444">Paket sona erdi ('+((k.pro_iptal_neden)||'')+'). Yenile → <a href="'+((k.bagis)||'https://buymeacoffee.com/btmcode')+'" target="_blank" style="color:#22d3ee">destek ol</a></span>'
          : (k.asis
          ? '<span style="color:#ef4444">Sınır doldu. Sınırsız için destek anahtarı → <a href="'+((k.bagis)||'https://buymeacoffee.com/btmcode')+'" target="_blank" style="color:#22d3ee">destek ol</a></span>'
          : 'Kalan: '+(k.kalan||0).toLocaleString('tr-TR')+' çağrı · sınırsız için destek anahtarı'));
    document.getElementById('kayit').textContent = d.audit || '(kayıt yok)';
    sonHata = '';
  }catch(e){
    sonHata = String(e && e.message || e);
    const st = document.getElementById('durum');
    if(st){ st.textContent='bağlantı yok'; st.className='d no'; }
    const e2 = document.getElementById('aiDurum');
    if(e2){ e2.textContent='⚠️ BAĞLANTI YOK'; e2.style.background='#3a2a08';
            e2.style.color='#fbbf24'; }
  }
}
async function eylem(k, btn){
  const out = document.getElementById('sonuc');
  try{
    if(btn){ btn.disabled = true; btn.style.opacity = 0.6; }
    if(out){ out.textContent = '⏳ işleniyor…'; out.style.color = '#8b9bb4'; }
    const r = await fetch('/panel/eylem?k='+encodeURIComponent(k), {method:'POST'});
    const d = await r.json();
    const msg = String(d.message || 'tamam');
    if(k === 'bagla'){
      const box = document.getElementById('baglaSonuc');
      const kutu = document.getElementById('baglaKutu');
      if(msg.indexOf('BAGLANDI|') === 0){
        const p = msg.split('|');
        sonUrl = p[2] || '';
        document.getElementById('baglaUrl').textContent = sonUrl;
        var fu = document.getElementById('formUrl');
        if(fu){ fu.textContent = sonUrl; }
        kutu.style.display = 'block';
        box.textContent = '✅ Adres hazir (' + p[1] + '). Kopyalayip ChatGPT ekranina yapistirin.';
        box.style.color = '#22c55e';
      } else if(msg.indexOf('TUNEL_KAPATILDI') === 0){
        sonUrl = ''; kutu.style.display = 'none';
        box.textContent = 'Tunel kapatildi.'; box.style.color = '#8b9bb4';
      } else {
        box.textContent = '⚠️ ' + msg.replace('TUNEL_YOK|','');
        box.style.color = '#f59e0b';
      }
      if(btn){ btn.disabled = false; btn.style.opacity = 1; }
      if(out){ out.textContent = ''; }
      return;
    }
    if(out){
      out.textContent = (d.ok === false ? '⚠️ ' : '✅ ') + (d.message || 'tamam');
      out.style.color = d.ok === false ? '#ef4444' : '#22c55e';
    }
    if(k === 'durdur'){
      document.body.dataset.ai = 'kapali'; durumYaz();
      if(btn){ btn.disabled = false; btn.style.opacity = 1; }
      setTimeout(yukle, 500);
      return;
    }
    if(k === 'basla'){
      document.body.dataset.ai = 'acik'; durumYaz();
      if(btn){ btn.disabled = false; btn.style.opacity = 1; }
      setTimeout(yukle, 500);
      return;
    }
    setTimeout(yukle, 400);
  }catch(e){
    if(out){
      out.textContent = '⚠️ Sunucu kapandı — uzaktan erişim artık KAPALI. '
                      + 'Yeniden açmak için masaüstündeki GhostPilot kısayoluna çift tıkla.';
      out.style.color = '#f59e0b';
    }
    document.body.dataset.ai = 'kapali'; durumYaz();
  }finally{
    if(btn && k !== 'durdur'){ btn.disabled = false; btn.style.opacity = 1; }
  }
}
yukle(); setInterval(yukle, 4000);
</script></body></html>"""


def _panel_kapsam_metni():
    """Panelin başlık/uyarı metnini bağlandığı arayüze göre üret.

    Yalnız 127.0.0.1 → 'bu bilgisayardan erişilir'
    0.0.0.0 / ::     → 'ağdan erişilebilir' + erişim anahtarı uyarısı
    """
    disari = RELAY_HOST in ("0.0.0.0", "::", "")
    if disari:
        alt = "Panel — erişim anahtarıyla korunur"
        uyari = ("Bu panel tüm ağ arayüzlerine açık. Adresi bilen herkes bağlanabilir; "
                 "her istek <b>erişim anahtarı</b> ile doğrulanır. Kesmek için "
                 "aşağıdaki <b>UZAKTAN ERİŞİMİ DURDUR</b> düğmesini kullanın.")
    else:
        alt = "Yerel panel — yalnız bu bilgisayardan erişilir"
        uyari = ("Bu panel yalnız <b>127.0.0.1</b> üzerinde açılır. Telefonunuzdan veya "
                 "başka bir cihazdan erişilemez. Uzaktan erişimi tamamen kesmek için "
                 "aşağıdaki <b>DURDUR</b> düğmesini kullanın.")
    return (PANEL_HTML.replace("{KAPSAM_YAZI}", alt)
                      .replace("{KAPSAM_UYARI}", uyari))


def _audit_tail(n=25):
    try:
        p = os.path.join(CFG_DIR, "audit.log")
        with open(p, "r", encoding="utf-8") as f:
            lines = f.readlines()[-n:]
        out = []
        for ln in lines:
            try:
                d = json.loads(ln)
                out.append(f"{d.get('t','')}  {d.get('action',''):12s} "
                           f"{'ok' if d.get('ok') else 'HATA'}  {d.get('detail','')[:60]}")
            except Exception:
                out.append(ln.strip()[:100])
        return "\n".join(out)
    except Exception:
        return "(kayıt yok)"


def _watchdog_alive():
    try:
        pid_f = os.path.join(CFG_DIR, "watchdog.pid")
        if not os.path.exists(pid_f):
            return False
        pid = int(open(pid_f).read().strip() or 0)
        if not pid:
            return False
        if IS_WIN:
            r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                               capture_output=True, text=True, timeout=10,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            return str(pid) in (r.stdout or "")
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _oauth_token_count():
    try:
        d = json.load(open(OAUTH_FILE, encoding="utf-8"))
        live = [t for t, r in (d.get("tokens") or {}).items()
                if not r.get("expires_at") or r["expires_at"] > time.time()]
        return len(live)
    except Exception:
        return 0


SON_GORUNTU = os.path.join(CFG_DIR, ".arayuz_goruldu")


def _arayuz_isaretle():
    """Arayüz her veri çekişinde buraya zaman yazar → onay ekranı açık mı anlaşılır."""
    try:
        with open(SON_GORUNTU, "w", encoding="utf-8") as f:
            f.write(str(int(time.time())))
    except Exception:
        pass


def _arayuz_canli(esik=10):
    """Arayüz son 10 saniye içinde veri çektiyse açık sayılır (3 sn'de bir yenileniyor)."""
    try:
        t = int(open(SON_GORUNTU, encoding="utf-8").read().strip() or 0)
        return (time.time() - t) <= esik
    except Exception:
        return False


def panel_payload():
    try:
        import input_bg
        busy = input_bg.last_input_age() < 0.45
    except Exception:
        busy = False
    _arayuz_isaretle()
    return {
        "version": VERSION,
        "running": True,
        "watchdog": _watchdog_alive(),
        "tools": len(TOOLS),
        "read_only": bool(CFG.get("read_only")),
        "oauth_tokens": _oauth_token_count(),
        "user_busy": busy,
        "read_roots": CFG.get("read_roots") or [],
        "write_roots": CFG.get("write_roots") or [],
        "agent_visible": _overlay_status(),
        "concurrent": True,
        "kota": kota_durum(),
        "onay": onay_listesi(),
        "onay_modu": CFG.get("onay") or "riskli",
        "audit": _audit_tail(),
        "ai_kapali": bool(CFG.get("ai_kapali")),
        "stopped": os.path.exists(os.path.join(CFG_DIR, "stopped")),
    }


# ============================================================================
#  UZAK KÖPRÜ — ChatGPT / tarayıcıdaki her AI
# ============================================================================

class RelayHandler(BaseHTTPRequestHandler):
    server_version = f"GhostPilot/{VERSION}"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    # ---- yardımcılar ----
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type, Authorization, X-GhostPilot-Token, "
                         "Mcp-Session-Id, Accept, Last-Event-ID")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Expose-Headers", "Mcp-Session-Id")

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _binary(self, kod, veri, mime, cache=0):
        try:
            self.send_response(kod)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(veri)))
            if cache:
                self.send_header("Cache-Control", f"public, max-age={cache}")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(veri)
        except Exception:
            pass

    def _md_sayfa(self, tur):
        """Gizlilik / şartlar sayfası — yoksa gömülü özet."""
        kok = os.path.dirname(os.path.abspath(__file__))
        adaylar = (["GIZLILIK.md", "privacy.md"] if tur == "privacy"
                   else ["KOSULLAR.md", "terms.md"])
        govde = ""
        for ad in adaylar:
            try:
                with open(os.path.join(kok, ad), encoding="utf-8") as f:
                    govde = f.read()
                break
            except Exception:
                continue
        if not govde:
            govde = ("# GhostPilot\n\n"
                     "Ayrıntılar: https://github.com/Btmcode/Ghost-Pilot\n\n"
                     "GhostPilot verilerinizi toplamaz; her şey kendi "
                     "bilgisayarınızda kalır.")
        # markdown → basit HTML (başlık, paragraf, liste, kalın, kod)
        import html as _h
        import re as _re
        cikti, liste = [], False
        for satir in govde.split("\n"):
            t = satir.strip()
            if t.startswith(("# ", "## ", "### ")):
                if liste:
                    cikti.append("</ul>"); liste = False
                seviye = len(t) - len(t.lstrip("#"))
                cikti.append(f"<h{seviye+1}>{_h.escape(t.lstrip('# ').strip())}</h{seviye+1}>")
            elif t.startswith(("* ", "- ")):
                if not liste:
                    cikti.append("<ul>"); liste = True
                cikti.append("<li>" + _h.escape(t[2:]) + "</li>")
            elif t.startswith("|"):
                cikti.append("<p style='color:#8b9bb4;font-size:13px'>" +
                             _h.escape(t.strip("|").replace("|", " · ")) + "</p>")
            elif t:
                if liste:
                    cikti.append("</ul>"); liste = False
                gov = _h.escape(t)
                gov = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", gov)
                gov = _re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', gov)
                cikti.append(f"<p>{gov}</p>")
            else:
                if liste:
                    cikti.append("</ul>"); liste = False
        if liste:
            cikti.append("</ul>")
        baslik = "Gizlilik Politikası" if tur == "privacy" else "Kullanım Şartları"
        html_doc = f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GhostPilot — {baslik}</title>
<link rel="icon" href="/favicon.ico"><link rel="icon" type="image/svg+xml" href="/icon.svg">
<style>
:root{{color-scheme:dark}}
body{{margin:0;background:#0b1120;color:#e2e8f0;
 font:15px/1.65 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
main{{max-width:760px;margin:0 auto;padding:34px 22px 70px}}
h1{{font-size:26px;color:#f59e0b;margin:0 0 6px}}
h2{{font-size:19px;margin:28px 0 8px;color:#f59e0b}}
h3{{font-size:16px;margin:20px 0 6px}}
p{{margin:8px 0;color:#c7d2e2}}
a{{color:#22d3ee}}
ul{{margin:8px 0 8px 20px}}
li{{margin:4px 0;color:#c7d2e2}}
img{{border-radius:10px}}
.bas{{display:flex;align-items:center;gap:10px;margin-bottom:22px}}
</style></head><body><main>
<div class="bas"><img src="/icon.svg" width="34" height="34" alt=""><b>GhostPilot</b></div>
{chr(10).join(cikti)}
</main></body></html>"""
        veri = html_doc.encode("utf-8")
        return self._binary(200, veri, "text/html; charset=utf-8", cache=3600)

    def _svg_icon(self):
        veri = _simge_dosya("icon.svg") or GOMULU_SVG.encode("utf-8")
        return self._binary(200, veri, "image/svg+xml", cache=86400)

    def _panel_action(self, k):
        """Panelden gelen eylemler (yalnız 127.0.0.1)."""
        if k == "salt-okunur":
            CFG["read_only"] = True
            save_cfg(CFG)
            return "Salt okunur mod AÇIK — yazma, terminal ve girdi reddedilir."
        if k == "yazma":
            CFG["read_only"] = False
            save_cfg(CFG)
            return "Okuma + yazma modu açık."
        if k == "oauth-sil":
            try:
                d = _oauth_load()
                n = len(d.get("tokens") or {})
                d["tokens"] = {}
                d["codes"] = {}
                d["refresh"] = {}
                _oauth_save(d)
                return f"{n} izin iptal edildi. ChatGPT yeniden izin istemeli."
            except Exception as e:
                return f"Hata: {e}"
        if k.startswith("onay:"):
            oid = k.split(":", 1)[1]
            okk = onay_karar(oid, "onay")
            return "Onaylandı." if okk else "Bu istek artık yok (süresi doldu)."
        if k.startswith("ret:"):
            oid = k.split(":", 1)[1]
            okk = onay_karar(oid, "ret")
            return "Reddedildi." if okk else "Bu istek artık yok."
        if k == "durdur":
            # uzaktan erişimni kes — sunucu AYAKTA kalır ki panelden geri açılabilsin.
            CFG["ai_kapali"] = True
            save_cfg(CFG)
            try:
                d = _oauth_load()
                n = len(d.get("tokens") or {})
                d["tokens"] = {}
                d["codes"] = {}
                d["refresh"] = {}
                _oauth_save(d)
            except Exception:
                n = 0
            try:
                open(os.path.join(CFG_DIR, "stopped"), "w").write(str(int(time.time())))
            except Exception:
                pass
            return (f"⛔ Uzaktan erişim KESİLDİ. {n} izin silindi. Panel açık, "
                    "isterseniz 'Yeniden başlat' ile geri açabilirsiniz.")
        if k == "bagla":
            d = self._tunel_bilgi()
            kapat = (d.get("url") or "") if self._tunel_canli(d) else ""
            if kapat:
                self._tunel_durdur()
                return "TUNEL_KAPATILDI"
            url, tip = self._tunel_baslat()
            if url:
                return "BAGLANDI|" + tip + "|" + url
            if tip == "yok":
                return ("TUNEL_YOK|Bu bilgisayarda tunel araci yok. En kolay yol: "
                        "ChatGPT yerine Claude Desktop kullanmak (tunel gerekmez) — "
                        "python kur.py claude")
            return ("TUNEL_YOK|Adres acilamadi. Tailscale'e giris yapip tekrar deneyin "
                    "(python kur.py tailscale-kur) veya Cloudflare kurun.")
        if k == "mesaj-kopyala":
            return "OK"
        if k == "sunucu-kapat":
            threading.Thread(target=self._panel_stop, daemon=True).start()
            return "Sunucu tamamen kapatılıyor…"
        if k == "basla":
            CFG["ai_kapali"] = False
            save_cfg(CFG)
            try:
                bayrak = os.path.join(CFG_DIR, "stopped")
                if os.path.exists(bayrak):
                    os.remove(bayrak)
            except Exception:
                pass
            if not self._relay_alive():
                try:
                    import kur as K
                    threading.Thread(target=lambda: K.start_relay_bg(),
                                     daemon=True).start()
                except Exception:
                    pass
            return ("✅ Uzaktan erişim yeniden AÇILDI. İstemciyi bir kez "
                    "yenilemeniz gerekebilir.")
        return "Bilinmeyen eylem."

    def _relay_alive(self):
        """Sunucu gerçekten yanıt veriyor mu? (port ayardan okunur)"""
        try:
            import urllib.request
            port = int(CFG.get("port") or DEFAULT_PORT)
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health",
                                        timeout=2) as r:
                return r.status == 200
        except Exception:
            return False

    # ---- disariya acilan gecici tunel (tek dugme) ----
    def _tunel_bilgi(self):
        d = {"url": "", "pid": None, "tip": ""}
        try:
            with open(os.path.join(CFG_DIR, "tunel.json"), encoding="utf-8") as f:
                d.update(json.load(f) or {})
        except Exception:
            pass
        return d

    def _tunel_yaz(self, d):
        try:
            with open(os.path.join(CFG_DIR, "tunel.json"), "w", encoding="utf-8") as f:
                json.dump(d, f)
        except Exception:
            pass

    def _tunel_canli(self, d):
        """Kayitli tunel gercekten ayakta mi? (olu pid / bos url = degil)"""
        pid = d.get("pid")
        if not pid:
            return bool(d.get("url"))  # tailscale: pid yok, adres varsa acik say
        try:
            if os.name == "nt":
                r = subprocess.run(["tasklist", "/FI", "PID eq %s" % pid],
                                   capture_output=True, text=True, timeout=10)
                return str(pid) in (r.stdout or "")
            os.kill(int(pid), 0)
            return True
        except Exception:
            return False

    def _tunel_durdur(self):
        d = self._tunel_bilgi()
        pid = d.get("pid")
        if pid:
            try:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                                   capture_output=True, timeout=15)
                else:
                    try:
                        os.killpg(os.getpgid(int(pid)), 9)
                    except Exception:
                        os.kill(int(pid), 9)
            except Exception:
                pass
        self._tunel_yaz({"url": "", "pid": None, "tip": ""})
        return True

    def _tunel_baslat(self):
        """Disaridan erisilebilir HTTPS adresi acar. Tailscale varsa onu,
        yoksa Cloudflare hizli tuneli dener. Adresi dondurur."""
        port = int(CFG.get("port") or DEFAULT_PORT)
        tok = ""
        try:
            tok = open(os.path.join(CFG_DIR, "token"), encoding="utf-8").read().strip()
        except Exception:
            pass

        # 1) Tailscale (kurulu ve girisli ise en saglam yol)
        try:
            import kur as K
            ts = K.tailscale_bin()
            if ts:
                subprocess.run([ts, "funnel", "--bg", str(port)],
                               capture_output=True, timeout=90)
                r = subprocess.run([ts, "status", "--json"],
                                   capture_output=True, text=True, timeout=30)
                dns = (json.loads(r.stdout or "{}").get("Self") or {}).get("DNSName") or ""
                if dns:
                    url = "https://" + dns.rstrip(".") + "/mcp"
                    if tok:
                        url += "?token=" + tok
                    self._tunel_yaz({"url": url, "pid": None, "tip": "tailscale"})
                    return url, "tailscale"
        except Exception:
            pass

        # 1b) SSH ile ucretsiz tunel (Windows 10/11'de ssh hazir gelir)
        url, tip = self._ssh_tunel(port, tok)
        if url:
            return url, tip

        # 2) Cloudflare hizli tunel (hesap gerekmez)
        exe = shutil.which("cloudflared")
        if not exe and os.name == "nt":
            for c in (os.path.join(os.environ.get("ProgramFiles", ""), "cloudflared", "cloudflared.exe"),
                      os.path.join(os.environ.get("LOCALAPPDATA", ""), "cloudflared", "cloudflared.exe")):
                if os.path.exists(c):
                    exe = c
                    break
        if not exe:
            return "", "yok"
        try:
            logp = os.path.join(CFG_DIR, "tunel.log")
            pr = self._popen_arka(
                [exe, "tunnel", "--url", "http://127.0.0.1:%d" % port, "--no-autoupdate"], logp)
            for _ in range(40):
                time.sleep(1)
                try:
                    with open(logp, encoding="utf-8", errors="replace") as lf:
                        t = lf.read()
                except Exception:
                    t = ""
                m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", t)
                if m:
                    url = m.group(0) + "/mcp"
                    if tok:
                        url += "?token=" + tok
                    self._tunel_yaz({"url": url, "pid": pr.pid, "tip": "cloudflare"})
                    return url, "cloudflare"
                if pr.poll() is not None:
                    break
            try:
                pr.kill()
            except Exception:
                pass
        except Exception:
            pass
        return "", "hata"

    def _popen_arka(self, cmd, logp):
        """Arka planda, kendi surec grubunda calistir (durdururken hepsi olur)."""
        f = open(logp, "w", encoding="utf-8", errors="replace")
        kw = {}
        if os.name == "nt":
            kw["creationflags"] = 0x00000008 | 0x00000200  # DETACHED | NEW_PROCESS_GROUP
        else:
            kw["start_new_session"] = True
        kw.update(SESSIZ)
        return subprocess.Popen(cmd, stdout=f, stderr=f, stdin=subprocess.DEVNULL, **kw)

    def _ssh_tunel(self, port, tok):
        """ssh -R ile ucretsiz HTTPS adres (pinggy / localhost.run). Hesap gerekmez."""
        ssh = shutil.which("ssh") or (r"C:\Windows\System32\OpenSSH\ssh.exe"
                                      if os.path.exists(r"C:\Windows\System32\OpenSSH\ssh.exe") else None)
        if not ssh:
            return "", ""
        secenekler = [ssh, "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=20",
                      "-o", "ExitOnForwardFailure=yes", "-o", "LogLevel=INFO"]
        saglayicilar = [
            ("pinggy", secenekler + ["-p", "443", "-R0:127.0.0.1:%d" % port, "a.pinggy.io"],
             r"https://[a-z0-9-]+\.(?:free\.pinggy\.net|run\.pinggy-free\.link|pinggy\.link)"),
            ("localhost.run", secenekler + ["-R", "80:127.0.0.1:%d" % port, "nokey@localhost.run"],
             r"https://[a-z0-9-]+\.lhr\.life"),
        ]
        for ad, cmd, desen in saglayicilar:
            logp = os.path.join(CFG_DIR, "tunel-%s.log" % ad)
            try:
                pr = self._popen_arka(cmd, logp)
            except Exception:
                continue
            for _ in range(35):
                time.sleep(1)
                try:
                    with open(logp, encoding="utf-8", errors="replace") as lf:
                        t = lf.read()
                except Exception:
                    t = ""
                m = re.search(desen, t)
                if m:
                    url = m.group(0) + "/mcp"
                    if tok:
                        url += "?token=" + tok
                    self._tunel_yaz({"url": url, "pid": pr.pid, "tip": ad})
                    return url, ad
                if pr.poll() is not None:
                    break
            try:
                pr.kill()
            except Exception:
                pass
            try:
                os.remove(os.path.join(CFG_DIR, "tunel.json"))
            except Exception:
                pass
        return "", ""

    def _panel_stop(self):
        time.sleep(0.4)
        try:
            open(os.path.join(CFG_DIR, "stopped"), "w").write(str(int(time.time())))
        except Exception:
            pass
        os._exit(0)

    def _authed(self):
        """Bearer başlığı VEYA ?token= sorgu parametresi.

        ChatGPT'nin yeni 'Özel MCP sunucusu' ekranında API anahtarı seçeneği
        yok (yalnız OAuth / Kimlik doğrulama yok). Bu yüzden anahtarı URL'ye
        sorgu parametresi olarak koyabilmek gerekir:
            https://makine.tailXXXX.ts.net/mcp?token=...
        """
        # 1) OAuth erişim anahtarı (ChatGPT'nin "OAuth" seçeneği)
        if oauth_scope_ok(self.headers.get("Authorization", "")):
            return True
        if not CFG.get("require_token"):
            return True
        if not TOKEN:
            return True
        h = self.headers
        supplied = (h.get("Authorization", "").replace("Bearer ", "").strip()
                    or h.get("X-GhostPilot-Token", "").strip())
        if supplied == TOKEN:
            return True
        try:
            qs = parse_qs(urlparse(self.path).query)
            q = (qs.get("token", [""])[0] or "").strip()
            if q and q == TOKEN:
                return True
        except Exception:
            pass
        return False

    # ---- yönlendirme ----
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _base(self):
        global _ISTEM_BASE
        """Bu sunucunun dışarıdan görünen adresi (Tailscale HTTPS varsa o)."""
        known = (CFG.get("public_base") or "").rstrip("/")
        if known:
            return known
        host = (self.headers.get("X-Forwarded-Host")
                or self.headers.get("Host") or "")
        if not host:
            _ISTEM_BASE = f"http://127.0.0.1:{CFG.get('port') or DEFAULT_PORT}"
            return _ISTEM_BASE
        proto = "http"
        if "ts.net" in host or self.headers.get("X-Forwarded-Proto") == "https":
            proto = "https"
        _ISTEM_BASE = f"{proto}://{host}"
        return _ISTEM_BASE

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        # ---- OAuth keşif (ChatGPT bu adresleri kendisi sorar) ----
        if path in ("/.well-known/oauth-protected-resource",
                    "/.well-known/oauth-protected-resource/mcp"):
            base = self._base()
            return self._json(200, {
                "resource": base + "/mcp",
                "authorization_servers": [base],
                "bearer_methods_supported": ["header"],
                "scopes_supported": ["ghostpilot"],
                "resource_documentation": base + "/",
            })
        if path in ("/.well-known/oauth-authorization-server",
                    "/.well-known/oauth-authorization-server/mcp"):
            return self._json(200, oauth_metadata(self._base(), True))
        if path in ("/.well-known/openid-configuration",
                    "/.well-known/openid-configuration/mcp"):
            return self._json(200, oauth_metadata(self._base(), True))

        # ---- OAuth yetkilendirme ekranı ----
        if path == "/oauth/authorize":
            return self._authorize_page(qs)

        # ---- simge / favicon (herkese açık, kimlik istemez) ----
        if path in ("/favicon.ico", "/icon.ico"):
            veri = _simge_dosya("favicon.ico")
            if veri:
                return self._binary(200, veri, "image/x-icon", cache=86400)
            return self._svg_icon()
        if path in ("/icon.png", "/icon-256.png", "/apple-touch-icon.png"):
            veri = _simge_dosya("icon-256.png") or _simge_dosya("icon.png")
            if veri:
                return self._binary(200, veri, "image/png", cache=86400)
            return self._svg_icon()
        if path in ("/icon-48.png", "/icon-128.png", "/icon-180.png"):
            ad = path.lstrip("/")
            veri = _simge_dosya(ad)
            if veri:
                return self._binary(200, veri, "image/png", cache=86400)
            return self._svg_icon()
        if path in ("/icon.svg", "/simge.svg"):
            return self._svg_icon()
        # ---- gizlilik politikası ve kullanım şartları (herkese açık) ----
        if path in ("/privacy", "/gizlilik", "/privacy.md", "/gizlilik.md"):
            return self._md_sayfa("privacy")
        if path in ("/terms", "/kosullar", "/terms.md", "/kosullar.md"):
            return self._md_sayfa("terms")

        if path in ("/manifest.json", "/site.webmanifest"):
            base = self._base()
            return self._json(200, {
                "name": "GhostPilot", "short_name": "GhostPilot",
                "description": "Bilgisayarınız için sessiz yardımcı",
                "start_url": base + "/panel", "display": "standalone",
                "background_color": "#0b1120", "theme_color": "#f59e0b",
                "icons": [
                    {"src": base + "/icon-256.png", "sizes": "256x256", "type": "image/png"},
                    {"src": base + "/icon-128.png", "sizes": "128x128", "type": "image/png"},
                    {"src": base + "/icon-48.png", "sizes": "48x48", "type": "image/png"},
                ]})

        if path in ("/panel", "/panel/"):
            body = _panel_kapsam_metni().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                self.wfile.write(body)
            except Exception:
                pass
            return
        if path == "/panel/veri":
            try:
                with open(os.path.join(CFG_DIR, ".panel_goruldu"), "w",
                          encoding="utf-8") as _f:
                    _f.write(str(int(time.time())))
            except Exception:
                pass
            return self._json(200, panel_payload())

        if path in ("/", "/health", "/mcp/health"):
            return self._json(200, {
                "ok": True, "service": "ghostpilot-relay", "version": VERSION,
                "os": OS_NAME, "tools": len(TOOLS),
                "capabilities": caps(),
            })
        if path in ("/mcp", "/mcp/sse"):
            if CFG.get("ai_kapali"):
                return self._json(403, {
                    "ok": False, "error": "AI_ERISIMI_KAPALI",
                    "message": ("Uzaktan erişim panelden durduruldu. Açmak için "
                                "GhostPilot panelindeki 'Yeniden başlat' düğmesi."),
                })
            if not self._authed():
                base = self._base()
                return self._json_auth401(base)
            if self.headers.get("Accept", "").find("text/event-stream") >= 0 or path.endswith("sse"):
                return self._sse_open()
            return self._json(200, {"ok": True, "endpoint": "/mcp",
                                    "message": "POST JSON-RPC gönderin."})
        return self._json(404, {"ok": False, "error": "Bulunamadı."})

    def _json_auth401(self, base):
        body = json.dumps({"ok": False, "error": "UNAUTHORIZED",
                           "message": "Kimlik doğrulama gerekli (OAuth veya Bearer token)."},
                          ensure_ascii=False).encode("utf-8")
        self.send_response(401)
        self.send_header("WWW-Authenticate",
                         f'Bearer realm="ghostpilot", '
                         f'resource_metadata="{base}/.well-known/oauth-protected-resource"')
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _sse_open(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self._cors()
        self.end_headers()
        try:
            self.wfile.write(b": ghostpilot stream open\n\n")
            self.wfile.flush()
            for _ in range(600):          # ~5 dk açık tut
                time.sleep(0.5)
                self.wfile.write(b": ping\n\n")
                self.wfile.flush()
        except Exception:
            return

    def _authorize_page(self, qs):
        """Onay ekranını gösterir. Kayıtlı istemci yoksa otomatik kaydeder."""
        client_id = (qs.get("client_id", [""])[0] or "").strip()
        redirect_uri = (qs.get("redirect_uri", [""])[0] or "").strip()
        state = (qs.get("state", [""])[0] or "").strip()
        code_challenge = (qs.get("code_challenge", [""])[0] or "").strip()
        method = (qs.get("code_challenge_method", ["plain"])[0] or "plain").upper()
        scope = (qs.get("scope", ["ghostpilot"])[0] or "ghostpilot")

        if not redirect_uri:
            return self._json(400, {"ok": False,
                                    "error": "redirect_uri gerekli."})

        d = _oauth_load()
        client = (d.get("clients") or {}).get(client_id)
        if client_id and not client:
            # Bilinmeyen istemci → otomatik kaydet (dynamic registration)
            d.setdefault("clients", {})[client_id] = {
                "client_id": client_id, "redirect_uris": [redirect_uri],
                "created": time.time(), "name": "ChatGPT",
            }
            _oauth_save(d)

        sid = secrets.token_urlsafe(24)
        srv = self.server
        if not hasattr(srv, "gp_pending"):
            srv.gp_pending = {}
        srv.gp_pending[sid] = {
            "client_id": client_id, "redirect_uri": redirect_uri, "state": state,
            "code_challenge": code_challenge, "method": method, "scope": scope,
            "created": time.time(),
        }
        html = (ONAY_HTML
                .replace("__CLIENT__", (client or {}).get("name") or client_id or "ChatGPT")
                .replace("__HOST__", socket.gethostname())
                .replace("__SID__", sid))
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self._cors()
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _form(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n).decode("utf-8", "replace") if n else ""
        return {k: v[0] for k, v in parse_qs(raw).items()}

    def _oauth_authorize_submit(self):
        f = self._form()
        sid = f.get("sid", "")
        karar = f.get("karar", "reddet")
        srv = self.server
        pend = getattr(srv, "gp_pending", {}).pop(sid, None)
        if not pend:
            return self._json(400, {"ok": False,
                                    "error": "Oturum süresi doldu. Bağlantıyı ChatGPT'den yeniden başlatın."})
        ru = pend["redirect_uri"]
        sep = "&" if "?" in ru else "?"
        if karar != "onayla":
            loc = f"{ru}{sep}error=access_denied"
            if pend.get("state"):
                loc += "&state=" + pend["state"]
            self.send_response(302)
            self.send_header("Location", loc)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        code = secrets.token_urlsafe(32)
        d = _oauth_load()
        d.setdefault("codes", {})[code] = {
            "client_id": pend["client_id"], "redirect_uri": ru,
            "code_challenge": pend["code_challenge"], "method": pend["method"],
            "scope": pend.get("scope", "ghostpilot"),
            "expires_at": time.time() + CODE_TTL,
        }
        _oauth_save(d)
        audit("oauth_izin", pend.get("client_id", ""))
        loc = f"{ru}{sep}code={code}"
        if pend.get("state"):
            loc += "&state=" + pend["state"]
        self.send_response(302)
        self.send_header("Location", loc)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _oauth_token(self):
        f = self._form()
        grant = f.get("grant_type", "")
        d = _oauth_load()

        def issue(client_id, scope):
            at = secrets.token_urlsafe(40)
            rt = secrets.token_urlsafe(40)
            d.setdefault("tokens", {})[at] = {
                "client_id": client_id, "scope": scope or "ghostpilot",
                "created": time.time(), "expires_at": time.time() + OAUTH_TTL,
                "refresh": rt,
            }
            d.setdefault("refresh", {})[rt] = {
                "client_id": client_id, "scope": scope or "ghostpilot",
                "created": time.time(),
            }
            _oauth_save(d)
            return {
                "access_token": at, "token_type": "Bearer",
                "expires_in": OAUTH_TTL, "refresh_token": rt,
                "scope": scope or "ghostpilot",
            }

        if grant == "authorization_code":
            code = f.get("code", "")
            verifier = f.get("code_verifier", "")
            rec = (d.get("codes") or {}).get(code)
            if not rec:
                return self._json(400, {"error": "invalid_grant",
                                        "error_description": "Kod geçersiz veya kullanılmış."})
            if rec.get("expires_at", 0) < time.time():
                return self._json(400, {"error": "invalid_grant",
                                        "error_description": "Kodun süresi doldu."})
            if rec.get("redirect_uri") and f.get("redirect_uri") and \
                    f["redirect_uri"] != rec["redirect_uri"]:
                return self._json(400, {"error": "invalid_grant",
                                        "error_description": "redirect_uri uyuşmuyor."})
            if rec.get("code_challenge"):
                if (rec.get("method") or "PLAIN").upper() == "S256":
                    if _pkce_s256(verifier) != rec["code_challenge"]:
                        return self._json(400, {"error": "invalid_grant",
                                                "error_description": "PKCE doğrulanamadı."})
                elif verifier != rec["code_challenge"]:
                    return self._json(400, {"error": "invalid_grant",
                                            "error_description": "PKCE doğrulanamadı."})
            d.get("codes", {}).pop(code, None)
            _oauth_save(d)
            return self._json(200, issue(rec.get("client_id", ""), rec.get("scope")))

        if grant == "refresh_token":
            rt = f.get("refresh_token", "")
            rec = (d.get("refresh") or {}).get(rt)
            if not rec:
                return self._json(400, {"error": "invalid_grant",
                                        "error_description": "refresh_token geçersiz."})
            return self._json(200, issue(rec.get("client_id", ""), rec.get("scope")))

        return self._json(400, {"error": "unsupported_grant_type"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/panel/eylem":
            qs = parse_qs(urlparse(self.path).query)
            k = (qs.get("k", [""])[0] or "").lower()
            msg = self._panel_action(k)
            audit("panel", k)
            return self._json(200, {"ok": True, "message": msg})
        if path == "/oauth/authorize":
            return self._oauth_authorize_submit()
        if path == "/oauth/token":
            return self._oauth_token()
        if path == "/oauth/register":
            try:
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(n).decode("utf-8") or "{}") if n else {}
            except Exception:
                body = {}
            cid = "gp-" + secrets.token_urlsafe(12)
            d = _oauth_load()
            d.setdefault("clients", {})[cid] = {
                "client_id": cid, "name": body.get("client_name") or "ChatGPT",
                "redirect_uris": body.get("redirect_uris") or [],
                "created": time.time(),
            }
            _oauth_save(d)
            return self._json(201, {
                "client_id": cid, "client_secret": "",
                "redirect_uris": body.get("redirect_uris") or [],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
            })
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        raw = self.rfile.read(n) if n > 0 else b""
        if path not in ("/mcp", "/mcp/", "/mcp/message"):
            return self._json(404, {"ok": False, "error": "Bulunamadı."})
        if CFG.get("ai_kapali"):
            return self._json(403, {
                "ok": False, "error": "AI_ERISIMI_KAPALI",
                "message": "Uzaktan erişim durduruldu. Panelden 'Yeniden başlat'.",
            })
        if not self._authed():
            base = self._base()
            body401 = json.dumps({
                "ok": False,
                "error": "UNAUTHORIZED",
                "message": "Kimlik doğrulama gerekli (OAuth veya Bearer token).",
            }, ensure_ascii=False).encode("utf-8")
            self.send_response(401)
            self.send_header("WWW-Authenticate",
                             f'Bearer realm="ghostpilot", '
                             f'resource_metadata="{base}/.well-known/oauth-protected-resource"')
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body401)))
            self._cors()
            self.end_headers()
            try:
                self.wfile.write(body401)
            except Exception:
                pass
            return
        try:
            req = json.loads(raw.decode("utf-8") or "{}")
        except Exception as e:
            return self._json(400, {"ok": False, "error": f"Geçersiz JSON: {e}"})
        # toplu istek desteği
        if isinstance(req, list):
            out = [rpc(r) for r in req]
            out = [o for o in out if o is not None]
            return self._json(200, out)
        resp = rpc(req)
        if resp is None:
            self.send_response(202)
            self.send_header("Content-Length", "0")
            self._cors()
            self.end_headers()
            return
        return self._json(200, resp)


def _start_scheduler():
    try:
        th = threading.Thread(target=gorev_dongu, daemon=True)
        th.start()
        return True
    except Exception:
        return False


def _relay_kilidi_al(port):
    """Ayni portta ikinci relay acilmasin. Windows'ta SO_REUSEADDR yuzunden
    ayni porta iki surec baglanabiliyor; bu yuzden ayri bir kilit dosyasi."""
    lp = os.path.join(CFG_DIR, "relay-%s.lock" % port)
    try:
        _mkdir(CFG_DIR)
        f = open(lp, "w")
    except Exception:
        return None
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception:
        return None
    try:
        f.write(str(os.getpid()))
        f.flush()
    except Exception:
        pass
    return f


def run_relay(port=None, host="127.0.0.1"):
    global RELAY_HOST
    RELAY_HOST = host
    port = int(port or CFG.get("port") or DEFAULT_PORT)
    # elle başlatıldıysa "durduruldu" bayrağı anlamsız
    try:
        sf = os.path.join(CFG_DIR, "stopped")
        if os.path.exists(sf):
            os.remove(sf)
    except Exception:
        pass
    _kilit = _relay_kilidi_al(port)
    if _kilit is None:
        # zaten calisan bir sunucu var — sessizce cik (pencereler acilip kapanmasin)
        try:
            import urllib.request
            with urllib.request.urlopen("http://127.0.0.1:%s/health" % port, timeout=2):
                return 0
        except Exception:
            pass
    srv = ThreadingHTTPServer((host, port), RelayHandler)
    srv.daemon_threads = True
    _kapanis_hazirla(srv, port, host)
    _start_scheduler()
    if _overlay_up():
        print("  İşlem imleci  : açık — hayalet imleç + şerit")
    else:
        print("  İşlem imleci  : kapalı (tkinter/ekran yok veya config show_agent=false)")
    c = caps()
    _goster_host = "127.0.0.1" if host in ("0.0.0.0", "", "::") else host
    _host_notu = ("  (tüm arayüzler — dışarıdan erişim AÇIK, erişim anahtarı zorunlu)"
                  if host in ("0.0.0.0", "::") else "  (yalnız bu bilgisayar)")
    print(f"""
  👻 GhostPilot v{VERSION} — uzak köprü açık
  ─────────────────────────────────────────────────────────
  Yerel sağlık   : http://{_goster_host}:{port}/health
  Yerel panel    : http://{_goster_host}:{port}/panel   ← durum + DURDUR + onay
  MCP ucu        : http://{_goster_host}:{port}/mcp
  Bağlandığı yer : {host}:{port}{_host_notu}
  Araç sayısı    : {len(TOOLS)}
  Kimlik doğr.   : OAuth 2.1 + Bearer (izin ekranı) · {"ZORUNLU" if CFG.get("require_token") else "KAPALI (!)"}

  ChatGPT / Arena / tarayıcıdaki AI için:
    1) Bu pencereyi AÇIK BIRAK
    2) Başka bir terminalde: tailscale funnel --bg {port}
    3) Çıkan https://...ts.net adresini kullan

  Yetenekler: dosya={c['files']} terminal={c['shell']} ekran={c['screen']} girdi={c['input']}
  {('Not: ' + c['note']) if c['note'] else ''}
  ─────────────────────────────────────────────────────────
  Durdurmak için: Ctrl+C
""")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  kapatıldı.")
    finally:
        _kapanis_temizle()



# ============================================================================
#  BEKÇİ (watchdog) — sunucu HEP ayakta kalsın
#  Relay çökerse yeniden başlatır; port dolduysa bekler; pencil yok.
# ============================================================================

def _port_free(port):
    try:
        s = socket.socket()
        s.settimeout(0.5)
        free = s.connect_ex(("127.0.0.1", port)) != 0
        s.close()
        return free
    except Exception:
        return True


# ============================================================================
#  TEMİZ KAPANIŞ — Ctrl+C, pencere kapatma, kill: hepsinde süreç bırakmadan çık
# ============================================================================

_PID_DOSYA = None


def _kapanis_hazirla(srv, port, host="127.0.0.1"):
    """Sinyalleri yakala + pid dosyası yaz → arkada süreç kalmaz."""
    global _PID_DOSYA
    try:
        _PID_DOSYA = os.path.join(CFG_DIR, "relay.pid")
        with open(_PID_DOSYA, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        # arayüz hangi adrese bağlandığımızı bilsin (bağla/kapat doğru çalışsın)
        with open(os.path.join(CFG_DIR, "relay-host"), "w", encoding="utf-8") as f:
            f.write(host or "127.0.0.1")
    except Exception:
        _PID_DOSYA = None
    except Exception:
        _PID_DOSYA = None

    def _kapat(signum=None, frame=None):
        print("\n  👻 GhostPilot kapatılıyor…", flush=True)
        try:
            srv.shutdown()
        except Exception:
            pass
        try:
            srv.server_close()
        except Exception:
            pass
        _kapanis_temizle()
        os._exit(0)

    for ad in ("SIGINT", "SIGTERM", "SIGBREAK", "SIGHUP"):
        try:
            import signal as _s
            if hasattr(_s, ad):
                _s.signal(getattr(_s, ad), _kapat)
        except Exception:
            pass
    try:
        import atexit
        atexit.register(_kapanis_temizle)
    except Exception:
        pass


def _kapanis_temizle():
    """PID dosyasını sil (bayat pid kalmasın)."""
    try:
        if _PID_DOSYA and os.path.exists(_PID_DOSYA):
            os.remove(_PID_DOSYA)
    except Exception:
        pass


def run_watchdog(port=None):
    """Relay'i sürekli ayakta tutar. Tek örnek çalışır (kilit dosyası)."""
    port = int(port or CFG.get("port") or DEFAULT_PORT)
    lock = os.path.join(CFG_DIR, "watchdog.pid")
    _mkdir(CFG_DIR)

    # tek örnek — GERÇEK kilit (pid dosyası yarış durumuna açıktı)
    _kilit = _relay_kilidi_al("watchdog")
    if _kilit is None:
        print("[bekçi] zaten çalışıyor — çıkılıyor", flush=True)
        return 0
    try:
        open(lock, "w").write(str(os.getpid()))
    except Exception:
        pass

    stop_file = os.path.join(CFG_DIR, "stopped")

    def durduruldu():
        """Kullanıcı 'durdur' dediyse bekçi ısrar etmemeli."""
        return os.path.exists(stop_file)

    if durduruldu():
        print("[bekçi] 'durduruldu' bayrağı var — başlatılmıyor. "
              "(başlatmak için: python kur.py basla)", flush=True)
        try:
            os.remove(lock)
        except Exception:
            pass
        return 0

    # portta SAĞLIKLI bir sunucu zaten varsa bekçiye gerek yok — sessizce çık
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:%s/health" % port, timeout=2) as _r:
            if _r.status == 200:
                print("[bekçi] sunucu zaten çalışıyor — çıkılıyor", flush=True)
                try:
                    os.remove(lock)
                except Exception:
                    pass
                return 0
    except Exception:
        pass

    print(f"[bekçi] GhostPilot v{VERSION} — port {port} izleniyor", flush=True)
    fails = 0
    child = None
    son_baslangic = 0.0
    try:
        while True:
            if durduruldu():
                print("[bekçi] durdurma bayrağı görüldü — kapanıyor", flush=True)
                if child and child.poll() is None:
                    try:
                        child.terminate()
                    except Exception:
                        pass
                try:
                    os.remove(lock)
                    os.remove(stop_file)
                except Exception:
                    pass
                return 0
            if child is not None and child.poll() is not None:
                code = child.returncode
                # anında olum = gercek sorun. 5 kez ust uste olursa dur.
                hizli = (time.time() - son_baslangic) < 8
                fails = fails + 1 if hizli else 0
                child = None
                if fails >= 5:
                    print("[bekçi] relay üst üste 5 kez hemen kapandı — "
                          "döngü DURDURULDU. Sebep için: python kur.py hata", flush=True)
                    try:
                        os.remove(lock)
                    except Exception:
                        pass
                    return 1
                time.sleep(min(20, 2 ** min(fails, 4)) if fails else 1)

            if child is None and _port_free(port):
                try:
                    kw = {}
                    if IS_WIN:
                        kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    child = subprocess.Popen(
                        [sys.executable, os.path.abspath(__file__), "relay",
                         "--port", str(port)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        **dict(kw, **SESSIZ))
                    son_baslangic = time.time()
                    print(f"[bekçi] relay başladı (pid {child.pid})", flush=True)
                except Exception as e:
                    print(f"[bekçi] başlatılamadı: {e}", flush=True)
                    time.sleep(10)

            time.sleep(5)
    except KeyboardInterrupt:
        print("\n[bekçi] kapatılıyor…")
        if child and child.poll() is None:
            try:
                child.terminate()
            except Exception:
                pass
        try:
            os.remove(lock)
        except Exception:
            pass
        return 0


# ============================================================================
#  DOCTOR — kurulum denetimi
# ============================================================================

def doctor():
    print(f"\n  👻 GhostPilot v{VERSION} — kurulum denetimi\n" + "  " + "─" * 56)
    ok_all = True

    def line(ok, msg, fix=""):
        nonlocal ok_all
        if not ok:
            ok_all = False
        print(f"  {'✅' if ok else '❌'} {msg}")
        if not ok and fix:
            for f in fix.split("\n"):
                print(f"     → {f}")

    line(True, f"Python {platform.python_version()} · {OS_NAME} {platform.release()}")
    line(True, f"Ev dizini: {HOME}")
    line(os.path.isdir(CFG_DIR), f"Ayar dizini: {CFG_DIR}",
         "Otomatik oluşturulur; ilk çalıştırmada izin verin.")

    c = caps()
    line(c["files"], "Dosya araçları hazır")
    line(c["shell"], "Terminal aracı hazır" if c["shell"] else "Terminal kapalı",
         "config.json → allow_shell: true")

    if c["screen"]:
        line(True, f"Ekran yakalama: {c['screen_backend']} {c.get('screen_size')}")
    else:
        line(False, "Ekran yakalama YOK",
             "Windows'ta: pip install pillow (opsiyonel, tek bağımlılık)\n"
             "Alternatif: PowerShell ile yakalama denenir\n"
             "Ekran olmadan da tüm dosya/terminal araçları çalışır.")
    if c["input"]:
        line(True, f"Fare/klavye denetimi: {c['input_backend']}")
    else:
        line(False, "Fare/klavye denetimi YOK",
             "Windows: user32 (yerleşik) — çalışmıyorsa masaüstü oturumunda olduğunuzdan emin olun\n"
             "Linux: X11 XTEST gerekir (Wayland'da sınırlı)\n"
             "macOS: Quartz için Terminal'e 'Erişilebilirlik' izni verin")
    if c["note"]:
        print(f"     ℹ️  {c['note']}")

    line(bool(TOKEN), f"Erişim anahtarı: {TOKEN[:8]}…{TOKEN[-4:] if len(TOKEN) > 12 else ''}")
    port = CFG.get("port") or DEFAULT_PORT
    free = True
    try:
        s = socket.socket()
        s.settimeout(0.4)
        free = s.connect_ex(("127.0.0.1", port)) != 0
        s.close()
    except Exception:
        pass
    line(True, f"Port {port}: {'boş (kullanılabilir)' if free else 'ŞU AN KULLANIMDA (köprü çalışıyor olabilir)'}")

    ts = shutil.which("tailscale")
    if ts:
        line(True, f"Tailscale bulundu: {ts}")
    else:
        line(False, "Tailscale yok — ChatGPT bağlantısı için gerekir",
             "https://tailscale.com/download adresinden ücretsiz kurun\n"
             "Claude Desktop / Cursor kullanacaksanız GEREKMEZ (stdio çalışır)")

    print("  " + "─" * 56)
    if ok_all:
        print("  ✅ Her şey hazır. Sıradaki adım: python ghostpilot.py bridge\n")
    else:
        print("  ⚠️  Yukarıdaki ❌ maddeleri düzeltin. Dosya/terminal araçları")
        print("     bunlardan bağımsız çalışır; ekran isteğe bağlıdır.\n")
    return 0


# ============================================================================
#  CLI
# ============================================================================

START_TIME = time.time()


def print_help():
    print(f"""
  👻 GhostPilot v{VERSION} — bilgisayarınız için sessiz yardımcı
  ────────────────────────────────────────────────────────────────

  python ghostpilot.py doctor     Kurulumu denetle (İLK BUNU YAPIN)
  python ghostpilot.py bridge     stdio köprü → Claude Desktop, Cursor
  python ghostpilot.py relay      HTTPS köprü  → ChatGPT, Arena, tarayıcı AI
  python ghostpilot.py watchdog   Bekçi: relay çökerse yeniden başlatır (HEP açık)
  python ghostpilot.py tools      {len(TOOLS)} aracı listele
  python ghostpilot.py token      Yeni erişim anahtarı üret
  python ghostpilot.py where      Yapılandırma dosyalarının yerini göster

  Kurulum dosyaları: {CFG_DIR}
  Belgeler: https://github.com/Btmcode/Ghost-Pilot
""")


def main():
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
    if cmd in ("", "-h", "--help", "help"):
        print_help()
        return 0
    if cmd == "doctor":
        return doctor()
    if cmd == "bridge":
        run_bridge()
        return 0
    if cmd in ("watchdog", "bekci", "bekçi", "daemon"):
        port = None
        if "--port" in sys.argv:
            try:
                port = int(sys.argv[sys.argv.index("--port") + 1])
            except Exception:
                pass
        return run_watchdog(port)
    if cmd == "relay":
        port = None
        host = "127.0.0.1"
        if "--port" in sys.argv:
            try:
                port = int(sys.argv[sys.argv.index("--port") + 1])
            except Exception:
                pass
        if "--host" in sys.argv:
            try:
                host = sys.argv[sys.argv.index("--host") + 1]
            except Exception:
                pass
        run_relay(port, host)
        return 0
    if cmd == "tools":
        print(f"\n  {len(TOOLS)} araç:\n")
        for n in TOOL_ORDER:
            print(f"   • {n:16s} {TOOLS[n][1]}")
        print()
        return 0
    if cmd == "token":
        t = secrets.token_urlsafe(32)
        _mkdir(CFG_DIR)
        fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(t)
        print(f"\n  ✅ Yeni anahtar: {t}\n     Dosya: {TOKEN_FILE}\n")
        return 0
    if cmd == "where":
        print(f"\n  ayar : {CFG_FILE}\n  token: {TOKEN_FILE}\n  kayıt: {os.path.join(CFG_DIR, 'audit.log')}\n")
        return 0
    print(f"  Bilinmeyen komut: {cmd}")
    print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

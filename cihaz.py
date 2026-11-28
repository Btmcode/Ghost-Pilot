#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — cihaz.py  ·  ÇOKLU CİHAZ (Faz 6)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  NE ÇÖZER
#    Windows Host ile Ubuntu AI-Workstation AYRI ajanlar olarak çalışır;
#    asistan hangi cihazda işlem yapacağını seçer. Tailscale YOK.
#
#  GÜVENLİK (Tailscale yerine)
#    · Her cihazın kendi 256 bit anahtarı (cihazlar.json içinde, 0600)
#    · İstek imzası: HMAC-SHA256(anahtar, cihaz_id|zaman|nonce|gövde)
#    · Saat sapması ±120 sn dışındaysa reddet (replay koruması)
#    · nonce tek kullanımlık (bellekte son 2000 nonce)
#    · Yalnız açıkça izin verilen araçlar uzaktan çağrılabilir
#      (allow_tools) — varsayılan olarak kabuk/silme gibi tehlikeli araçlar
#      KAPALI; açmak bilinçli bir ayar gerektirir.
#
#  YENİDEN BAĞLANMA
#    · Sağlık yoklaması arka planda; üstel geri çekilme (1,2,4,8...60 sn)
#    · Durum: online / offline / connecting / unauthorized
# ============================================================================

import hashlib
import hmac
import json
import os
import platform
import secrets
import threading
import time

CFG_DIR = os.path.join(os.path.expanduser("~"), ".ghostpilot")
CIHAZ_DOSYA = os.path.join(CFG_DIR, "cihazlar.json")
OS_NAME = platform.system()
IS_WIN = OS_NAME == "Windows"

SAPMA_SN = 120            # izin verilen saat sapması
NONCE_HAVUZU = 2000
_KILIT = threading.RLock()
_NONCELAR = {}
_GERI_CEKILME = {}        # device_id → {"deneme": n, "sonra": ts}

# Uzaktan çağrılabilmesi GÜVENLİ varsayılan araçlar (tehlikeliler hariç)
GUVENLI_VARSAYILAN = [
    "status", "list_sessions", "read_process_output", "list_searches",
    "get_more_search_results", "read_multiple_files", "read_file",
    "list_directory", "find_ui_element", "get_window_info",
    "get_recent_tool_calls", "get_usage_stats", "get_audit_log", "nex_hud",
    "screenshot", "gozle",
]


# ============================================================================
#  1 · KAYIT (cihazlar.json)
# ============================================================================
def _mkdir():
    try:
        os.makedirs(CFG_DIR, exist_ok=True)
    except Exception:
        pass


def _yukle():
    try:
        with open(CIHAZ_DOSYA, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _kaydet(d):
    _mkdir()
    gecici = CIHAZ_DOSYA + ".tmp"
    with open(gecici, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(gecici, CIHAZ_DOSYA)
    try:
        os.chmod(CIHAZ_DOSYA, 0o600)   # yalnız sahibi okuyabilir
    except Exception:
        pass


def cihaz_ekle(device_id, url, ad="", anahtar="", allow_tools=None,
               platform_adi=None, etiketler=None):
    """Cihaz kaydet. Anahtar verilmezse 256 bit üretilir (karşı tarafa verilir)."""
    device_id = str(device_id or "").strip()
    if not device_id or not url:
        return {"ok": False, "error": "device_id ve url gerekli."}
    if not str(url).startswith(("http://", "https://")):
        return {"ok": False, "error": "url http(s):// ile başlamalı."}
    anahtar = anahtar or secrets.token_hex(32)
    with _KILIT:
        d = _yukle()
        d[device_id] = {
            "id": device_id,
            "url": str(url).rstrip("/"),
            "ad": ad or device_id,
            "platform": platform_adi or "",
            "anahtar": anahtar,
            "allow_tools": allow_tools or list(GUVENLI_VARSAYILAN),
            "etiketler": etiketler or [],
            "eklendi": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "son_gorulme": "",
            "durum": "connecting",
        }
        _kaydet(d)
    return {"ok": True, "device_id": device_id, "url": d[device_id]["url"],
            "anahtar": anahtar,
            "uyari": ("Bu anahtarı KARŞI CİHAZA verin; başka yerde saklamayın."
                      if not anahtar else "")}


def cihaz_cikar(device_id):
    with _KILIT:
        d = _yukle()
        if device_id not in d:
            return {"ok": False, "error": "Cihaz yok: %s" % device_id}
        d.pop(device_id)
        _kaydet(d)
    return {"ok": True, "silinen": device_id}


def cihaz_listesi():
    d = _yukle()
    out = []
    for cid, c in d.items():
        out.append({
            "device_id": cid, "ad": c.get("ad"), "url": c.get("url"),
            "platform": c.get("platform"), "durum": c.get("durum"),
            "son_gorulme": c.get("son_gorulme"),
            "allow_tools": len(c.get("allow_tools") or []),
            "etiketler": c.get("etiketler"),
            "anahtar_var": bool(c.get("anahtar")),
        })
    return {"ok": True, "sayi": len(out), "cihazlar": out,
            "yerel": {"platform": OS_NAME, "ad": platform.node() or "yerel"}}


# ============================================================================
#  2 · İMZA (HMAC) — istemci ve sunucu aynı işlevi kullanır
# ============================================================================
def imza_uret(anahtar, device_id, zaman, nonce, govde):
    mesaj = "%s|%s|%s|%s" % (device_id, zaman, nonce, govde)
    return hmac.new(str(anahtar).encode("utf-8"),
                    mesaj.encode("utf-8"), hashlib.sha256).hexdigest()


def imza_dogrula(anahtar, device_id, zaman, nonce, govde, imza):
    # 1) saat sapması
    try:
        if abs(time.time() - float(zaman)) > SAPMA_SN:
            return False, "Saat sapması çok büyük (>%d sn) — istek reddedildi." % SAPMA_SN
    except Exception:
        return False, "Geçersiz zaman damgası."
    # 2) imza (nonce TÜKETİLMEDEN önce) — hatalı imza nonce havuzunu
    #    kirletmesin, aksi hâlde saldırgan meşru nonce'ları yakabilir.
    beklenen = imza_uret(anahtar, device_id, zaman, nonce, govde)
    if not hmac.compare_digest(beklenen, str(imza or "")):
        return False, "İmza geçersiz."
    # 3) nonce tekrarı (yalnız imzası DOĞRU istekler için)
    with _KILIT:
        anahtar_n = "%s:%s" % (device_id, nonce)
        if anahtar_n in _NONCELAR:
            return False, "Nonce tekrar kullanılmış (replay) — reddedildi."
        _NONCELAR[anahtar_n] = time.time()
        if len(_NONCELAR) > NONCE_HAVUZU:
            for k in sorted(_NONCELAR, key=_NONCELAR.get)[:len(_NONCELAR) - NONCE_HAVUZU]:
                _NONCELAR.pop(k, None)
    return True, ""


# ============================================================================
#  3 · HTTP İSTEMCİ (imzalı çağrı + sağlık)
# ============================================================================
def _istek(url, govde=None, basliklar=None, timeout=15):
    import urllib.request
    import urllib.error
    veri = None
    b = dict(basliklar or {})
    if govde is not None:
        veri = json.dumps(govde, ensure_ascii=False).encode("utf-8")
        b["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url, data=veri, headers=b,
                                 method="POST" if veri is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ham = r.read().decode("utf-8", "replace")
            try:
                return {"ok": True, "code": r.status, "veri": json.loads(ham)}
            except Exception:
                return {"ok": True, "code": r.status, "veri": {"ham": ham[:2000]}}
    except urllib.error.HTTPError as e:
        try:
            ham = e.read().decode("utf-8", "replace")
            v = json.loads(ham)
        except Exception:
            v = {"error": "HTTP %s" % e.code}
        return {"ok": False, "code": e.code, "veri": v}
    except Exception as e:
        return {"ok": False, "code": 0, "veri": {"error": str(e)[:200]}}


def saglik(device_id):
    """Tek cihazın sağlığını kontrol et ve durumunu kaydet."""
    d = _yukle()
    c = d.get(device_id)
    if not c:
        return {"ok": False, "error": "Cihaz yok: %s" % device_id}
    t0 = time.time()
    r = _istek(c["url"] + "/cihaz/saglik", timeout=8)
    ms = int((time.time() - t0) * 1000)
    durum = "online" if r.get("ok") else "offline"
    if r.get("code") == 401:
        durum = "unauthorized"
    with _KILIT:
        d = _yukle()
        if device_id in d:
            d[device_id]["durum"] = durum
            if durum == "online":
                d[device_id]["son_gorulme"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                _GERI_CEKILME.pop(device_id, None)
            else:
                g = _GERI_CEKILME.setdefault(device_id, {"deneme": 0})
                g["deneme"] += 1
                g["sonra"] = time.time() + min(60, 2 ** min(g["deneme"], 6))
            _kaydet(d)
    return {"ok": r.get("ok", False), "device_id": device_id,
            "durum": durum, "sure_ms": ms,
            "veri": r.get("veri"), "kod": r.get("code")}


def cagri(device_id, tool, args=None, timeout=60):
    """Uzak cihazda bir aracı çalıştır (imzalı istek).

    Güvenlik: tool, cihazın allow_tools listesinde olmalı.
    """
    if device_id in ("local", "yerel", "", None):
        try:
            import ghostpilot
            return ghostpilot.call_tool(tool, args or {})
        except Exception as e:
            return {"ok": False, "error": "Yerel çağrı hatası: %s" % str(e)[:200]}
    d = _yukle()
    c = d.get(device_id)
    if not c:
        return {"ok": False, "error": "Cihaz kayıtlı değil: %s" % device_id,
                "cihazlar": [x["device_id"] for x in cihaz_listesi()["cihazlar"]]}
    izinli = c.get("allow_tools") or []
    if tool not in izinli:
        return {"ok": False, "reddedildi": True, "device_id": device_id,
                "error": ("'%s' bu cihazda uzaktan çağrıya izinli değil. "
                          "İzinli: %s…" % (tool, ", ".join(izinli[:6]))),
                "not": "allow_tools listesini cihaz_ekle ile genişletin."}
    govde = {"tool": tool, "args": args or {}}
    zaman = "%.3f" % time.time()
    nonce = secrets.token_hex(8)
    govde_metin = json.dumps(govde, ensure_ascii=False, sort_keys=True)
    imza = imza_uret(c["anahtar"], device_id, zaman, nonce, govde_metin)
    t0 = time.time()
    r = _istek(c["url"] + "/cihaz/cagri", govde,
               {"X-Cihaz-Id": device_id, "X-Zaman": zaman,
                "X-Nonce": nonce, "X-Imza": imza}, timeout=timeout)
    ms = int((time.time() - t0) * 1000)
    if r.get("ok"):
        with _KILIT:
            d = _yukle()
            if device_id in d:
                d[device_id]["durum"] = "online"
                d[device_id]["son_gorulme"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                _kaydet(d)
        v = r.get("veri") or {}
        v["_device_id"] = device_id
        v["_sure_ms"] = ms
        return v
    return {"ok": False, "device_id": device_id, "sure_ms": ms,
            "kod": r.get("code"), "hata": (r.get("veri") or {}).get("error"),
            "error": "Uzak cihaz hatası: %s" % (r.get("veri") or {}).get("error", "?")}


# ============================================================================
#  4 · SUNUCU (karşı cihazda çalışan uç)
# ============================================================================
def sunucu_yap(device_id, anahtar, cagri_fn, allow_tools=None,
               host="0.0.0.0", port=17382):
    """İmzalı istekleri kabul eden mini HTTP sunucusu (ThreadingHTTPServer)."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    izinli = allow_tools or list(GUVENLI_VARSAYILAN)

    class Isleyici(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _yaz(self, kod, veri):
            govde = json.dumps(veri, ensure_ascii=False).encode("utf-8")
            self.send_response(kod)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(govde)))
            self.end_headers()
            self.wfile.write(govde)

        def do_GET(self):
            if self.path.rstrip("/").endswith("/cihaz/saglik"):
                return self._yaz(200, {
                    "ok": True, "device_id": device_id,
                    "platform": OS_NAME, "ad": platform.node(),
                    "t": time.time(), "tools": len(izinli),
                })
            if self.path.rstrip("/").endswith("/cihaz/bilgi"):
                return self._yaz(200, {
                    "ok": True, "device_id": device_id, "platform": OS_NAME,
                    "hostname": platform.node(), "python": platform.python_version(),
                    "allow_tools": izinli,
                })
            self._yaz(404, {"error": "yol yok"})

        def do_POST(self):
            if not self.path.rstrip("/").endswith("/cihaz/cagri"):
                return self._yaz(404, {"error": "yol yok"})
            try:
                n = int(self.headers.get("Content-Length") or 0)
                ham = self.rfile.read(n).decode("utf-8", "replace")
                govde = json.loads(ham or "{}")
            except Exception:
                return self._yaz(400, {"error": "gövde okunamadı"})
            gid = self.headers.get("X-Cihaz-Id") or ""
            zaman = self.headers.get("X-Zaman") or ""
            nonce = self.headers.get("X-Nonce") or ""
            imza = self.headers.get("X-Imza") or ""
            if gid != device_id:
                return self._yaz(401, {"error": "cihaz kimliği uyuşmuyor"})
            govde_metin = json.dumps(govde, ensure_ascii=False, sort_keys=True)
            gecerli, sebep = imza_dogrula(anahtar, gid, zaman, nonce,
                                          govde_metin, imza)
            if not gecerli:
                return self._yaz(401, {"error": sebep, "reddedildi": True})
            tool = str(govde.get("tool") or "")
            if tool not in izinli:
                return self._yaz(403, {"error": "araç izinli değil: %s" % tool,
                                       "allow_tools": izinli})
            try:
                sonuc = cagri_fn(tool, govde.get("args") or {})
            except Exception as e:
                return self._yaz(500, {"error": "araç hatası: %s" % str(e)[:200]})
            return self._yaz(200, sonuc if isinstance(sonuc, dict) else {"ok": True,
                                                                        "result": sonuc})

    httpd = ThreadingHTTPServer((host, int(port)), Isleyici)
    t = threading.Thread(target=httpd.serve_forever, name="ghostpilot-cihaz",
                         daemon=True)
    t.start()
    return {"ok": True, "host": host, "port": int(port), "device_id": device_id,
            "allow_tools": izinli, "sunucu": httpd}


# ============================================================================
#  5 · SAĞLIK İZLEYİCİ (arka plan, üstel geri çekilme)
# ============================================================================
class SaglikIzleyici(object):
    def __init__(self, aralik=15):
        self.aralik = aralik
        self._dur = False
        self._t = None
        self.gecmis = []

    def basla(self):
        if self._t and self._t.is_alive():
            return {"ok": True, "not": "zaten çalışıyor"}
        self._dur = False
        self._t = threading.Thread(target=self._dongu, daemon=True,
                                   name="ghostpilot-saglik")
        self._t.start()
        return {"ok": True, "aralik_sn": self.aralik}

    def durdur(self):
        self._dur = True
        return {"ok": True}

    def _dongu(self):
        while not self._dur:
            try:
                for c in cihaz_listesi()["cihazlar"]:
                    if self._dur:
                        break
                    r = saglik(c["device_id"])
                    self.gecmis.append({"t": time.strftime("%H:%M:%S"),
                                        "device": c["device_id"],
                                        "durum": r.get("durum")})
                    if len(self.gecmis) > 200:
                        del self.gecmis[:100]
            except Exception:
                pass
            for _ in range(int(self.aralik * 10)):
                if self._dur:
                    return
                time.sleep(0.1)


_IZLEYICI = SaglikIzleyici()


def izleyici_basla(aralik=15):
    _IZLEYICI.aralik = int(aralik)
    return _IZLEYICI.basla()


def izleyici_durdur():
    return _IZLEYICI.durdur()


def izleyici_gecmis():
    return {"ok": True, "kayit": _IZLEYICI.gecmis[-50:],
            "calisiyor": bool(_IZLEYICI._t and _IZLEYICI._t.is_alive())}

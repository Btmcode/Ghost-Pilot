#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — lisans_online.py  ·  SUNUCU TARAFLI DOĞRULAMA (istemci)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  NE YAPAR?  Yerel imza doğrulaması GEÇSE BİLE, lisansın hâlâ geçerli
#  olduğunu SUNUCUYA sorar. Sunucu "hayır" derse Pro kapanır — kullanıcı
#  kodu kurcalasa bile bu karar dışarıda verilir.
#
#  TASARIM KURALLARI (kasıtlı):
#   • Sunucu adresi YOKSA → yerel doğrulama geçerlidir (kimse kırılmaz).
#   • İnternet/sunucu YOKSA → 14 GÜN tolerans (uçakta/çevrimdışı çalışır).
#   • Sunucu "iptal/süre bitti/başka makine" derse → ANINDA kapanır.
#   • Sonuç 6 saat önbelleklenir (sunucuya yük bindirmemek için).
# ============================================================================

import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

BURASI = os.path.dirname(os.path.abspath(__file__))
CFG_DIR = os.path.join(os.path.expanduser("~"), ".ghostpilot")
DURUM_DOSYA = os.path.join(CFG_DIR, "online.json")
ONBELLEK_SN = 6 * 3600          # 6 saat
TOLERANS_SN = 14 * 86400        # sunucuya ulaşılamazsa 14 gün
ZAMAN_ASIMI = 6


def sunucu_url():
    """Lisans sunucusu adresi — config.json veya ortam değişkeni."""
    u = os.environ.get("GP_LISANS_URL", "").strip()
    if u:
        return u.rstrip("/")
    try:
        c = json.load(open(os.path.join(CFG_DIR, "config.json"), encoding="utf-8"))
        return (c.get("lisans_url") or "").strip().rstrip("/")
    except Exception:
        return ""


def _oku():
    try:
        return json.load(open(DURUM_DOSYA, encoding="utf-8"))
    except Exception:
        return {}


def _yaz(d):
    try:
        os.makedirs(CFG_DIR, exist_ok=True)
        tmp = DURUM_DOSYA + ".tmp"
        json.dump(d, open(tmp, "w", encoding="utf-8"))
        os.replace(tmp, DURUM_DOSYA)
    except Exception:
        pass


def _makine():
    try:
        import lisans
        return lisans.makine_kimligi()[:12]
    except Exception:
        return ""


def _sor(aid, makine, url):
    """Sunucuya sorar. Döner: dict veya None (ulaşılamadı)."""
    hedef = f"{url}/v1/dogrula/{aid}?makine={makine}"
    try:
        baglam = ssl.create_default_context()
        istek = urllib.request.Request(hedef, headers={"User-Agent": "GhostPilot/1.0"})
        with urllib.request.urlopen(istek, timeout=ZAMAN_ASIMI, context=baglam) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:                                   # 403 → gövdede neden var
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"ok": False, "durum": f"http-{e.code}", "mesaj": "sunucu reddetti"}
    except Exception:
        return None                            # ağ yok / DNS yok


KALP_DOSYA = os.path.join(CFG_DIR, ".kalp")
KALP_SN = 24 * 3600            # günde en fazla 1 kalp atışı


def kimlik():
    """Sunucuda görünecek kullanıcı kimliği: lisans varsa anahtar kimliği,
    yoksa bu cihazın kimliği (lisanssız kullanıcı da panelde görünür)."""
    try:
        import ghostpilot as G
        kd = G.kota_durum()
        if kd.get("lisans"):
            p = _anahtar_coz_g(kd["lisans"])
            if p:
                return p, True
    except Exception:
        pass
    return "CIHAZ-" + _makine(), False


def _anahtar_coz_g(k):
    try:
        import lisans
        p = lisans._anahtar_coz(k)
        return p.get("govde") if p else ""
    except Exception:
        return ""


def kalp_at(isabetli=False, kullanim=None, surum=""):
    """Sunucuya 'bu kullanıcı var, şu kadar kullandı' bildirir.

    Lisanssız kullanıcılar da bildirir → admin panelde kalan ücretsiz hak görünür.
    Günde 1 kez gönderilir; hata olursa sessizce geçer (kullanıcı etkilenmez).
    """
    url = sunucu_url()
    if not url:
        return False
    simdi = time.time()
    try:
        son = float(open(KALP_DOSYA, encoding="utf-8").read().strip() or 0)
    except Exception:
        son = 0
    if simdi - son < KALP_SN and not isabetli:
        return False
    aid, lisansli = kimlik()
    if not aid:
        return False
    try:
        import ghostpilot as G
        if kullanim is None:
            kullanim = G.kota_durum().get("kullanilan", 0)
        if not surum:
            surum = G.VERSION
        import platform
        q = (f"{url}/v1/kalp/{urllib.parse.quote(str(aid))}"
             f"?makine={_makine()}&surum={surum}&os={platform.system()}"
             f"&lisansli={1 if lisansli else 0}&kullanim={int(kullanim or 0)}"
             f"&ay={time.strftime('%Y%m')}")
        istek = urllib.request.Request(q, headers={"User-Agent": "GhostPilot/1.0"})
        with urllib.request.urlopen(istek, timeout=ZAMAN_ASIMI,
                                    context=ssl.create_default_context()) as r:
            r.read()
        os.makedirs(CFG_DIR, exist_ok=True)
        open(KALP_DOSYA, "w", encoding="utf-8").write(str(simdi))
        return True
    except Exception:
        return False


def dogrula_online(lisans_anahtari, yerel_ok=True):
    """(karar: bool, neden: str, kaynak: str)

    yerel_ok=False ise zaten yerel doğrulama geçmemiştir → False.
    """
    if not yerel_ok:
        return False, "yerel doğrulama başarısız", "yerel"
    url = sunucu_url()
    if not url:
        return True, "çevrimdışı mod (lisans sunucusu tanımlı değil)", "yerel"

    try:
        import lisans
        p = lisans._anahtar_coz(lisans_anahtari) or {}
        aid = p.get("govde", "")
    except Exception:
        aid = ""
    if not aid:
        return True, "anahtar kimliği okunamadı", "yerel"

    makine = _makine()
    simdi = time.time()
    onceki = _oku()

    # 6 saatlik önbellek: aynı anahtar + aynı makine
    if (onceki.get("id") == aid and onceki.get("makine") == makine
            and simdi - float(onceki.get("t") or 0) < ONBELLEK_SN
            and onceki.get("ok") is not None):
        return bool(onceki["ok"]), onceki.get("mesaj", "önbellek"), "önbellek"

    yanit = _sor(aid, makine, url)

    # --- sunucuya ulaşılamadı: 14 gün tolerans
    if yanit is None:
        son_ok = float(onceki.get("son_ok") or onceki.get("t") or 0)
        gecen = simdi - son_ok
        if son_ok and gecen < TOLERANS_SN:
            kalan = int((TOLERANS_SN - gecen) / 86400)
            return True, f"sunucuya ulaşılamadı — {kalan} gün tolerans", "tolerans"
        if not son_ok:
            return True, "sunucuya hiç ulaşılamadı — çevrimdışı kabul", "tolerans"
        _yaz({**onceki, "ok": False, "mesaj": "tolerans süresi doldu", "t": simdi})
        return False, "lisans sunucusuna 14 gündür ulaşılamıyor", "tolerans"

    # --- sunucu yanıtı
    ok = bool(yanit.get("ok"))
    mesaj = yanit.get("mesaj") or yanit.get("durum") or ""
    yeni = {"id": aid, "makine": makine, "t": simdi, "ok": ok, "mesaj": mesaj,
            "durum": yanit.get("durum"), "cevrimdisi": False}
    if ok:
        yeni["son_ok"] = simdi
    _yaz({**onceki, **yeni})
    return ok, mesaj, "sunucu"

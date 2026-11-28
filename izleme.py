#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — izleme.py  ·  AUDIT & GÖZLEMLENEBİLİRLİK (Faz 5)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  NE ÇÖZER
#    Eski kayıt 4 alanlıydı:  {"t","action","ok","detail"}
#    · hangi araç, hangi cihaz, hangi oturum, ne kadar sürdü → YOK
#    · parametreler `detail` içinde serbest metin → TOKEN SIZABİLİR
#
#  BU DOSYA
#    · Her araç çağrısı yapılandırılmış tek satır olarak yazılır:
#        t, tool, device_id, session_id, süre_ms, ok, params (maskeli),
#        sonuç özeti, hata
#    · GİZLİ BİLGİ MASKESİ: token, şifre, anahtar, parola, secret, bearer,
#      ?token=..., Authorization başlığı → [GİZLİ]
#    · Sorgu araçları: get_recent_tool_calls, get_usage_stats, get_audit_log
#    · NEX canlı HUD: hedef cihaz, aktif pencere, imleç, işlem, sonuç
#
#  KURAL: maskeleme "kara liste" ile değil, HEM anahtar adı HEM desen ile
#  yapılır (iki katman) — biri kaçırırsa diğeri tutar.
# ============================================================================

import json
import os
import platform
import re
import threading
import time

OS_NAME = platform.system()
CFG_DIR = os.path.join(os.path.expanduser("~"), ".ghostpilot")
AUDIT_DOSYA = os.path.join(CFG_DIR, "audit.jsonl")
ESKI_AUDIT = os.path.join(CFG_DIR, "audit.log")
HUD_DOSYA = os.path.join(CFG_DIR, "hud.json")

MAX_SATIR_OKU = 5000
MASKE = "[GİZLİ]"
_KILIT = threading.RLock()
_SAYACLAR = {}
_BELLEK = []          # son çağrılar (hızlı erişim, en fazla 300)


# ============================================================================
#  1 · GİZLİ BİLGİ MASKELEME
# ============================================================================
_GIZLI_ANAHTAR = re.compile(
    r"(token|secret|password|parola|şifre|sifre|api[_-]?key|apikey|"
    r"authorization|auth|bearer|cookie|session[_-]?key|private[_-]?key|"
    r"passwd|credential|anahtar)", re.I)

# Değer içinde geçen gizli desenler (anahtar adı ne olursa olsun)
_GIZLI_DESEN = [
    # URL sorgu parametresi: ?token=abc123
    (re.compile(r"([?&](?:token|key|secret|auth|password|parola)=)([^&\s\"']+)", re.I),
     r"\1" + MASKE),
    # Bearer <token>
    (re.compile(r"(Bearer\s+)([A-Za-z0-9\-\._~\+/]{8,})", re.I), r"\1" + MASKE),
    # uzun base64/hex benzeri anahtarlar (32+ karakter, boşluksuz)
    (re.compile(r"\b([A-Za-z0-9_\-]{32,})\b"), MASKE),
    # SSH private key blokları
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
                re.S), "[GİZLİ ANAHTAR BLOĞU]"),
]


def maskele(deger, derinlik=0):
    """Gizli bilgileri [GİZLİ] ile değiştir. Sözlük/liste/metin hepsi."""
    if derinlik > 6:
        return "[derin]"
    if isinstance(deger, dict):
        cikti = {}
        for k, v in deger.items():
            if _GIZLI_ANAHTAR.search(str(k)):
                cikti[k] = "[GİZLİ]"
            else:
                cikti[k] = maskele(v, derinlik + 1)
        return cikti
    if isinstance(deger, (list, tuple)):
        return [maskele(z, derinlik + 1) for z in deger[:50]]
    if deger is None or isinstance(deger, (int, float, bool)):
        return deger
    s = str(deger)
    # anahtar adı gizli ise (değer düz metin olarak geçmişse) tamamen maskele
    for rx, yer in _GIZLI_DESEN:
        try:
            s = rx.sub(yer, s)
        except Exception:
            pass
    return s[:2000]


def maskeleme_testi():
    """Kendi kendini test eden maskeleme (rapora kanıt)."""
    ornekler = {
        "token": "abc123",
        "password": "hunter2",
        "url": "https://x.free.pinggy.net/mcp?token=SUP3RSECRETDEGER123",
        "header": "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.abcdefghijklmnop",
        "normal": "dosya.txt",
        "api_key": "sk-1234567890",
        "derin": {"a": {"b": {"token": "gizli-deger"}}},
        "liste": ["token=a", "normal"],
        "uzun": "a" * 40,
    }
    m = maskele(ornekler)
    s = json.dumps(m, ensure_ascii=False)
    sizinti = []
    for gizli in ("abc123", "hunter2", "SUP3RSECRETDEGER123",
                  "eyJhbGciOiJIUzI1NiJ9", "sk-1234567890", "gizli-deger",
                  "a" * 40):
        if gizli in s:
            sizinti.append(gizli)
    return {"ok": not sizinti, "maskelendi": m,
            "sizan": sizinti or "yok",
            "kural": "%d anahtar deseni, %d değer deseni"
                     % (1, len(_GIZLI_DESEN))}


# ============================================================================
#  2 · KAYIT (JSONL — yapılandırılmış)
# ============================================================================
def _mkdir():
    try:
        os.makedirs(CFG_DIR, exist_ok=True)
    except Exception:
        pass


def yaz(tool, ok=True, params=None, sonuc=None, hata="", sure_ms=None,
        device_id="local", session_id="", ek=None):
    """Tek araç çağrısını yapılandırılmış olarak kaydet (maskeli)."""
    _mkdir()
    kayit = {
        "t": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "ts": round(time.time(), 3),
        "tool": str(tool)[:80],
        "device_id": str(device_id or "local")[:60],
        "session_id": str(session_id or "")[:40],
        "ok": bool(ok),
        "sure_ms": int(sure_ms) if sure_ms is not None else None,
        "params": maskele(params or {}),
        "result": maskele(sonuc) if sonuc is not None else None,
        "error": str(maskele(hata))[:500] if hata else "",
    }
    if ek:
        kayit["extra"] = maskele(ek)
    satir = json.dumps(kayit, ensure_ascii=False)
    try:
        with _KILIT:
            with open(AUDIT_DOSYA, "a", encoding="utf-8") as f:
                f.write(satir + "\n")
    except Exception:
        pass
    # sayaçlar + bellek
    with _KILIT:
        _BELLEK.append(kayit)
        if len(_BELLEK) > 300:
            del _BELLEK[:len(_BELLEK) - 300]
        a = _SAYACLAR.setdefault(tool, {"cagri": 0, "hata": 0, "toplam_ms": 0})
        a["cagri"] += 1
        if not ok:
            a["hata"] += 1
        if kayit["sure_ms"]:
            a["toplam_ms"] += kayit["sure_ms"]
    return kayit


# ============================================================================
#  3 · SORGULAR
# ============================================================================
def _satirlar(son=200):
    """Dosyadan son N kaydı oku (bozuk satırları atla)."""
    if not os.path.exists(AUDIT_DOSYA):
        return []
    try:
        with open(AUDIT_DOSYA, "r", encoding="utf-8", errors="replace") as f:
            hepsi = f.readlines()
    except Exception:
        return []
    out = []
    for satir in hepsi[-int(son) * 3:][-MAX_SATIR_OKU:]:
        satir = satir.strip()
        if not satir:
            continue
        try:
            out.append(json.loads(satir))
        except Exception:
            continue
    return out[-int(son):]


def son_cagrilar(adet=50, tool=None, sadece_hata=False, device_id=None):
    """get_recent_tool_calls — son araç çağrıları."""
    kayitlar = _satirlar(max(int(adet) * 4, 200))
    if tool:
        kayitlar = [k for k in kayitlar if k.get("tool") == tool]
    if sadece_hata:
        kayitlar = [k for k in kayitlar if not k.get("ok")]
    if device_id:
        kayitlar = [k for k in kayitlar if k.get("device_id") == device_id]
    kayitlar = kayitlar[-int(adet):]
    return {"ok": True, "sayi": len(kayitlar), "cagrilar": kayitlar,
            "kaynak": AUDIT_DOSYA}


def kullanim(donem="gun"):
    """get_usage_stats — dönem bazlı kullanım istatistiği."""
    kayitlar = _satirlar(MAX_SATIR_OKU)
    simdi = time.time()
    sinir = {"saat": 3600, "gun": 86400, "hafta": 7 * 86400,
             "ay": 30 * 86400, "hepsi": 10 ** 12}.get(str(donem), 86400)
    secili = [k for k in kayitlar if (simdi - float(k.get("ts") or 0)) <= sinir]
    arac = {}
    toplam_ms = 0
    hata = 0
    for k in secili:
        a = arac.setdefault(k.get("tool") or "?", {"cagri": 0, "hata": 0, "toplam_ms": 0})
        a["cagri"] += 1
        if not k.get("ok"):
            a["hata"] += 1
            hata += 1
        ms = k.get("sure_ms") or 0
        a["toplam_ms"] += ms
        toplam_ms += ms
    for a in arac.values():
        a["ort_ms"] = int(a["toplam_ms"] / a["cagri"]) if a["cagri"] else 0
    en_cok = sorted(arac.items(), key=lambda z: -z[1]["cagri"])[:10]
    return {
        "ok": True,
        "donem": donem,
        "toplam_cagri": len(secili),
        "hata": hata,
        "basarili": len(secili) - hata,
        "basarisiz_oran": round(hata / len(secili) * 100, 1) if secili else 0.0,
        "toplam_sure_ms": toplam_ms,
        "ortalama_ms": int(toplam_ms / len(secili)) if secili else 0,
        "arac_sayisi": len(arac),
        "en_cok_kullanilan": [{"tool": t, **v} for t, v in en_cok],
        "araclar": arac,
        "bellek_sayaci": dict(_SAYACLAR),
    }


def _sizinti_var(metin):
    """Metinde MASKELENMEMİŞ gizli değer var mı?

    Zaten maskelenmiş yer tutucular ([GİZLİ]/<maskeli>) sızıntı SAYILMAZ;
    aksi hâlde maskelemenin kendisi "sızıntı" gibi görünür (yanlış pozitif).
    """
    for rx, _y in _GIZLI_DESEN:
        for m in rx.finditer(metin):
            # yakalanan gizli parça: son dolu grup
            parca = ""
            for g in reversed(m.groups() or ()):
                if g:
                    parca = g
                    break
            if MASKE in parca or "<maskeli>" in parca:
                continue
            return True
    return False


def denetim_kaydi(adet=100, tool=None, sadece_hata=False, arama=None):
    """get_audit_log — ham audit kaydı (maskeli, filtrelenebilir)."""
    kayitlar = _satirlar(max(adet * 4, 200))
    if tool:
        kayitlar = [k for k in kayitlar if k.get("tool") == tool]
    if sadece_hata:
        kayitlar = [k for k in kayitlar if not k.get("ok")]
    if arama:
        q = str(arama).lower()
        kayitlar = [k for k in kayitlar if q in json.dumps(k, ensure_ascii=False).lower()]
    kayitlar = kayitlar[-int(adet):]
    # kendi kendini doğrula: sızmış gizli veri var mı?
    sizinti = [k.get("tool") for k in kayitlar
               if _sizinti_var(json.dumps(k, ensure_ascii=False))]
    return {"ok": True, "sayi": len(kayitlar), "kayitlar": kayitlar,
            "gizli_sizinti_tespit": sizinti[:5] or "yok",
            "dosya": AUDIT_DOSYA}


def dosya_boyut():
    try:
        return {"audit_kb": round(os.path.getsize(AUDIT_DOSYA) / 1024.0, 1)}
    except Exception:
        return {"audit_kb": 0}


# ============================================================================
#  4 · NEX CANLI HUD
# ============================================================================
def hud_guncelle(hedef_cihaz="local", pencere="", islem="", sonuc="",
                 imlec=None, ek=None):
    """NEX canlı durum şeridi — panel ve /hud ucundan okunur."""
    d = {
        "t": time.strftime("%H:%M:%S"),
        "ts": round(time.time(), 3),
        "device": hedef_cihaz or "local",
        "window": str(pencere or "")[:120],
        "action": str(islem or "")[:200],
        "result": str(sonuc or "")[:200],
        "cursor": imlec,
    }
    if ek:
        d["extra"] = maskele(ek)
    try:
        _mkdir()
        gecici = HUD_DOSYA + ".tmp"
        with open(gecici, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
        os.replace(gecici, HUD_DOSYA)
    except Exception:
        pass
    return {"ok": True, "hud": d}


def hud_oku():
    try:
        with open(HUD_DOSYA, "r", encoding="utf-8") as f:
            return {"ok": True, "hud": json.load(f)}
    except Exception:
        return {"ok": True, "hud": {}}


def hud_otomatik(tool, ok, params=None, sonuc=None):
    """Araç çağrısından otomatik HUD satırı üret (hedef pencere/cihaz dahil)."""
    pencere = ""
    if isinstance(params, dict):
        pencere = params.get("window") or params.get("pencere") or params.get("title") or ""
    cihaz = "local"
    if isinstance(params, dict):
        cihaz = params.get("device_id") or params.get("cihaz") or "local"
    islem = tool
    if isinstance(params, dict) and params.get("text"):
        islem = "%s · %s" % (tool, str(params.get("text"))[:40])
    ozet = ""
    if isinstance(sonuc, dict):
        if sonuc.get("error"):
            ozet = "HATA: " + str(sonuc.get("error"))[:120]
        elif sonuc.get("clicked"):
            ozet = "tıklandı"
        elif "okunan" in sonuc:
            ozet = "%s dosya okundu" % sonuc.get("okunan")
        elif "session_id" in sonuc:
            ozet = "oturum %s" % sonuc.get("session_id")
        elif "arama_id" in sonuc:
            ozet = "arama %s" % sonuc.get("arama_id")
    return hud_guncelle(cihaz, pencere, islem,
                        ozet or ("tamam" if ok else "başarısız"))


def temizle(eski_kayit_sayisi=0):
    """Audit dosyasını arşivle (silmez, taşır)."""
    if not os.path.exists(AUDIT_DOSYA):
        return {"ok": True, "not": "dosya yok"}
    try:
        arsiv = AUDIT_DOSYA.replace(".jsonl",
                                    ".%s.jsonl" % time.strftime("%Y%m%d-%H%M%S"))
        os.replace(AUDIT_DOSYA, arsiv)
        return {"ok": True, "arsiv": arsiv}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

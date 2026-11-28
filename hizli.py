#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — hizli.py  ·  TEK ÇAĞRIDA ÇOK İŞ + ÖN-YAKALAMA
#  Copyright (c) 2026 BTM Code — MIT License
#
#  NEDEN
#    Yapay zekâ ile bilgisayar arasındaki asıl gecikme "iş" değil, TUR.
#    Her tur = model düşünür + istek gider + cevap gelir ≈ 1-3 saniye.
#    Bir tıklama 1 ms sürüyor ama 4 tıklama 4 tur = 8 saniye oluyor.
#
#  ÇÖZÜM
#    1. TEK ÇAĞRI, ÇOK ADIM:  sira=[{"yap":"bul_tikla","hedef":"Kaydet"},
#                                    {"yap":"yaz","metin":"..."}, ...]
#       → 10 adımlık iş 1 turda biter. 10 kat hız.
#
#    2. ÖN-YAKALAMA:  Ajan iş yaparken bir iş parçacığı ekranın nesne
#       ağacını ve görüntüsünü hazır tutar. Sıradaki adım istediğinde
#       bekleme olmaz (0 ms).
#
#    3. ADAPTÖR:  Tek adımlı eski araçlar da buradan geçer → hepsi hızlanır.
#
#  DÜRÜST SINIR: Adımlar sırayla çalışır. Bir adım hata verirse o adımda
#  durur ve NE OLDUĞUNU aynen döndürür (sessizce yutmaz).
# ============================================================================

import threading
import time

# --- Ön-yakalama -----------------------------------------------------------
_PREF = {
    "nesne": None,        # goz.ozet sonucu
    "nesne_t": 0.0,
    "goruntu": None,      # screen.screenshot sonucu
    "goruntu_t": 0.0,
}
_PREF_KILIT = threading.Lock()
_PREF_CALISIYOR = threading.Event()
_NESNE_OMUR = 1.0         # saniye — bundan taze veri varsa yeniden sormayız
_GORUNTU_OMUR = 0.8


def _taze(t, omur):
    return t and (time.time() - t) < omur


def on_yakala(blok=False):
    """Arka planda ekran bilgisini hazırla (nesne ağacı + görüntü)."""
    if _PREF_CALISIYOR.is_set():
        if not blok:
            return False
        _PREF_CALISIYOR.wait(3.0)
        return True
    _PREF_CALISIYOR.set()

    def isci():
        try:
            try:
                import goz
                r = goz.ozet(nesne=True)
                with _PREF_KILIT:
                    _PREF["nesne"], _PREF["nesne_t"] = r, time.time()
            except Exception:
                pass
            try:
                import screen
                g = screen.screenshot(max_width=900)
                with _PREF_KILIT:
                    _PREF["goruntu"], _PREF["goruntu_t"] = g, time.time()
            except Exception:
                pass
        finally:
            _PREF_CALISIYOR.clear()

    threading.Thread(target=isci, daemon=True).start()
    if blok:
        _PREF_CALISIYOR.wait(3.0)
    return True


def hazir_nesne():
    """Ön-yakalanmış nesne ağacı — taze ise (0 ms), değilse yenisini üret."""
    with _PREF_KILIT:
        d, t = _PREF["nesne"], _PREF["nesne_t"]
    if d and _taze(t, _NESNE_OMUR):
        return d, True
    try:
        import goz
        d = goz.ozet(nesne=True)
        with _PREF_KILIT:
            _PREF["nesne"], _PREF["nesne_t"] = d, time.time()
        return d, False
    except Exception:
        return None, False


def hazir_goruntu(max_width=900):
    with _PREF_KILIT:
        d, t = _PREF["goruntu"], _PREF["goruntu_t"]
    if d and _taze(t, _GORUNTU_OMUR):
        return d, True
    try:
        import screen
        d = screen.screenshot(max_width=max_width)
        with _PREF_KILIT:
            _PREF["goruntu"], _PREF["goruntu_t"] = d, time.time()
        return d, False
    except Exception:
        return None, False


def durum():
    with _PREF_KILIT:
        return {"nesne_yas": (time.time() - _PREF["nesne_t"]) if _PREF["nesne_t"] else None,
                "goruntu_yas": (time.time() - _PREF["goruntu_t"]) if _PREF["goruntu_t"] else None,
                "calisiyor": _PREF_CALISIYOR.is_set()}


# ============================================================================
#  TEK ÇAĞRIDA ÇOK ADIM
# ============================================================================
#  Adım biçimi:
#    {"yap": "bul_tikla", "hedef": "Kaydet"}        düğmeyi bul + tıkla
#    {"yap": "tikla",     "x": 100, "y": 200}
#    {"yap": "yaz",       "metin": "merhaba"}
#    {"yap": "tus",       "komut": "ctrl+s"}
#    {"yap": "bekle",     "ms": 300}
#    {"yap": "kaydir",    "x":100,"y":200,"miktar":-3}
#    {"yap": "surukle",   "x1":1,"y1":2,"x2":3,"y2":4}
#    {"yap": "resim"}                               ekran görüntüsü
#    {"yap": "gozle"}                               nesne ağacı metni
#    {"yap": "kabuk",     "komut": "echo x"}        terminal
#    {"yap": "dur"}                                 erken bitir
#
#  Her adımın sonucu "adimlar" listesinde döner; kısa tutulur.
_MAX_ADIM = 40


def _kisa(r, sinir=220):
    if not isinstance(r, dict):
        return {"ok": bool(r)}
    d = {k: v for k, v in r.items()
         if k in ("ok", "bulundu", "x", "y", "exit", "bulunamadi", "error",
                  "typed", "chars", "seconds", "cached", "guven", "metin")}
    if "stdout" in r:
        d["stdout"] = str(r.get("stdout") or "")[:sinir]
    if "error" in d:
        d["error"] = str(d["error"])[:sinir]
    return d


def sira_calistir(adimlar, dur_hatada=True, sessiz=False, _tool=None):
    """Adım listesini tek çağrıda çalıştır."""
    if not isinstance(adimlar, list) or not adimlar:
        return {"ok": False, "error": "sira boş — en az bir adım gerekli."}
    if len(adimlar) > _MAX_ADIM:
        return {"ok": False,
                "error": "En fazla %d adım." % _MAX_ADIM,
                "ipucu": "Daha uzun işi birden çok sira çağrısına bölün."}
    t0 = time.time()
    kayit = []
    sonuc = {"ok": True, "adim_sayisi": len(adimlar), "adimlar": kayit}
    for i, adim in enumerate(adimlar, start=1):
        if not isinstance(adim, dict):
            kayit.append({"no": i, "ok": False, "error": "adım sözlük değil"})
            sonuc["ok"] = False
            break
        yap = str(adim.get("yap") or "").strip().lower()
        r = _tek_adim(yap, adim, _tool)
        kayit.append(dict(no=i, yap=yap, **_kisa(r)))
        if not r.get("ok", False):
            sonuc["ok"] = False
            sonuc["durdu"] = i
            sonuc["hata"] = r.get("error") or "adım başarısız"
            if dur_hatada:
                break
        if yap in ("gozle", "resim"):
            sonuc["son_goruntu" if yap == "resim" else "son_goz"] = r
        # tıklama/yazma sonrası ekran değişti → ön-yakalamayı tazele
        if yap in ("tikla", "bul_tikla", "yaz", "tus", "surukle", "kaydir", "kabuk"):
            if i < len(adimlar):
                on_yakala(blok=False)
    sonuc["sure_ms"] = int((time.time() - t0) * 1000)
    return sonuc


def _tek_adim(yap, a, _tool):
    """Tek adımı çalıştır. _tool(name, args) verilirse araç yolu kullanılır."""
    def cagir(ad, arg):
        if _tool:
            return _tool(ad, arg) or {"ok": False, "error": "araç cevapsız"}
        import ghostpilot
        return ghostpilot.call_tool(ad, arg)

    if yap in ("bul_tikla", "tikla_bul", "ui_click"):
        return cagir("ui_click", {"text": a.get("hedef") or a.get("text") or "",
                                  "window": a.get("pencere") or a.get("window")})

    if yap in ("tikla", "tıkla", "click"):
        arg = {"x": int(a.get("x", 0)), "y": int(a.get("y", 0)),
               "button": a.get("button") or a.get("tus") or "left"}
        if a.get("double") or a.get("cift"):
            arg["double"] = True
        return cagir("click", arg)

    if yap in ("yaz", "type"):
        return cagir("type", {"text": a.get("metin") or a.get("text") or "",
                              "sessiz": bool(a.get("sessiz"))})

    if yap in ("tus", "key", "kisayol"):
        return cagir("key", {"combo": a.get("komut") or a.get("combo") or ""})

    if yap in ("kaydir", "scroll"):
        arg = {"x": int(a.get("x", 0)), "y": int(a.get("y", 0)),
               "amount": int(a.get("miktar", a.get("amount", -3)))}
        return cagir("scroll", arg)

    if yap in ("surukle", "drag"):
        return cagir("drag", {"x1": int(a.get("x1", 0)), "y1": int(a.get("y1", 0)),
                              "x2": int(a.get("x2", 0)), "y2": int(a.get("y2", 0))})

    if yap == "bekle":
        ms = max(0, min(int(a.get("ms", 200)), 10000))
        time.sleep(ms / 1000.0)
        return {"ok": True, "beklendi_ms": ms}

    if yap in ("resim", "screenshot", "ekran"):
        d, onbellek = hazir_goruntu(int(a.get("max_width") or 900))
        if not d:
            return cagir("screenshot", {"max_width": int(a.get("max_width") or 900)})
        if onbellek:
            d = dict(d)
            d["cached"] = True
        return d

    if yap in ("gozle", "goz", "bak", "ozet"):
        d, onbellek = hazir_nesne()
        if not d:
            return cagir("gozle", {"pencere": a.get("pencere") or "",
                                   "nesne": True})
        if onbellek:
            d = dict(d)
            d["cached"] = True
        return d

    if yap in ("kabuk", "shell", "terminal", "komut"):
        return cagir("shell", {"command": a.get("komut") or a.get("command") or "",
                               "cwd": a.get("cwd") or "",
                               "timeout": int(a.get("timeout") or 60)})

    if yap in ("oku", "read"):
        return cagir("read", {"path": a.get("yol") or a.get("path") or ""})

    if yap in ("yaz_dosya", "write"):
        return cagir("write", {"path": a.get("yol") or a.get("path") or "",
                               "content": a.get("icerik") or a.get("content") or ""})

    if yap in ("dur", "bitir", "stop"):
        return {"ok": True, "durdu": True}

    return {"ok": False,
            "error": "Bilinmeyen adım: '%s'" % yap,
            "gecerli": ["bul_tikla", "tikla", "yaz", "tus", "kaydir", "surukle",
                        "bekle", "resim", "gozle", "kabuk", "oku", "yaz_dosya",
                        "dur"]}

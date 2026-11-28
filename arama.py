#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — arama.py  ·  ARKA PLAN ARAMA MOTORU
#  Copyright (c) 2026 BTM Code — MIT License
#
#  NE ÇÖZER
#    Eski `glob`/`grep` senkrondur ve SABİT limitte keser:
#      glob 300, grep 150 sonuç. Büyük projede model eksik sonuç gördüğünü
#      BİLMEZ — sessiz kırpma en tehlikeli hatadır.
#
#  BU DOSYA
#    · Arama arka planda bir iş parçacığında yürür (istek bloklanmaz)
#    · Sonuçlar sıra numarasıyla biriktirilir → sayfa sayfa okunur
#    · `kirpildi` / `tamamlandi` / `taranan_dosya` açıkça bildirilir
#    · Durdurma ve çoklu arama desteği
#
#  ARAMA TÜRLERİ
#    isim   : dosya ADI deseni   (*.py, rapor*)
#    icerik : dosya İÇİNDE metin (düz metin veya düzenli ifade)
#    ikisi  : önce isim, sonra içerik
#
#  GÜVENLİK: her arama kökü check_read() ile doğrulanır; sanal kutu dışına
#  çıkılamaz. Atlanan klasörler: .git node_modules __pycache__ .venv venv dist build
# ============================================================================

import fnmatch
import os
import re
import secrets
import threading
import time

CFG_DIR = os.path.join(os.path.expanduser("~"), ".ghostpilot")

MAX_SONUC = 20000          # arama başına tutulacak en fazla sonuç
MAX_DOSYA_BOY = 8 * 1024 * 1024     # 8 MB üstü dosyalarda içerik aranmaz
VARSAYILAN_SAYFA = 50
ATLA_KLASOR = {".git", ".hg", ".svn", "node_modules", "__pycache__",
               ".venv", "venv", "env", "dist", "build", "target",
               ".idea", ".vscode", "$RECYCLE.BIN", "System Volume Information"}

_KILIT = threading.RLock()
_ARAMALAR = {}


class Arama(object):
    def __init__(self, aid, kok, tur, desen, secenekler=None):
        self.d = {
            "arama_id": aid,
            "kok": kok,
            "tur": tur,                    # isim | icerik | ikisi
            "desen": desen,
            "durum": "hazir",              # hazir/calisiyor/bitti/durduruldu/hata
            "basladi": time.time(),
            "bitti": None,
            "sonuc": [],                   # [{"yol","satir","metin","tur"}]
            "seq": 0,
            "taranan_dosya": 0,
            "taranan_klasor": 0,
            "atlanan_buyuk": 0,
            "okunamayan": 0,
            "kirpildi": False,             # sonuç sınırına takıldı mı
            "hata": "",
            "durdur": False,
            "max_sonuc": int((secenekler or {}).get("max") or MAX_SONUC),
            "buyuk_harf": bool((secenekler or {}).get("ignore_case", True)),
        }
        self._kilit = threading.RLock()

    def get(self, k, v=None):
        return self.d.get(k, v)

    def ekle(self, yol, satir=None, metin="", tur="isim"):
        with self._kilit:
            if self.d["durdur"]:
                return False
            if len(self.d["sonuc"]) >= self.d["max_sonuc"]:
                self.d["kirpildi"] = True      # AÇIKÇA bildirilir
                self.d["durdur"] = True
                return False
            self.d["seq"] += 1
            self.d["sonuc"].append({
                "no": self.d["seq"], "yol": yol,
                "satir": satir, "metin": str(metin)[:400], "tur": tur,
            })
            return True

    def ozet(self):
        d = self.d
        return {
            "arama_id": d["arama_id"],
            "kok": d["kok"],
            "tur": d["tur"],
            "desen": d["desen"],
            "durum": d["durum"],
            "sonuc_sayisi": len(d["sonuc"]),
            "taranan_dosya": d["taranan_dosya"],
            "taranan_klasor": d["taranan_klasor"],
            "okunamayan": d["okunamayan"],
            "atlanan_buyuk": d["atlanan_buyuk"],
            "kirpildi": d["kirpildi"],
            "sinir": d["max_sonuc"],
            "hata": d["hata"],
            "gecen_s": round((d["bitti"] or time.time()) - d["basladi"], 2),
        }


def _izinli(yol):
    """Yol okuma izni içinde mi? (sanal kutu sınırı dahil)"""
    try:
        import ghostpilot
        ok, _why = ghostpilot.check_read(yol)
        return ok
    except Exception:
        return True


def _isci(ar):
    d = ar.d
    try:
        d["durum"] = "calisiyor"
        tur = d["tur"]
        desen = d["desen"]
        bayrak = re.I if d["buyuk_harf"] else 0
        rx = None
        if tur in ("icerik", "ikisi"):
            try:
                rx = re.compile(desen, bayrak)
            except re.error as e:
                d["durum"] = "hata"
                d["hata"] = "Geçersiz düzenli ifade: %s" % e
                d["bitti"] = time.time()
                return
        for kok, klasorler, dosyalar in os.walk(d["kok"]):
            if d["durdur"]:
                break
            klasorler[:] = [k for k in klasorler
                            if k not in ATLA_KLASOR and not k.startswith(".")]
            d["taranan_klasor"] += 1
            for ad in dosyalar:
                if d["durdur"]:
                    break
                tam = os.path.join(kok, ad)
                d["taranan_dosya"] += 1
                if tur in ("isim", "ikisi"):
                    if fnmatch.fnmatch(ad.lower(), desen.lower()):
                        ar.ekle(tam, None, ad, "isim")
                if tur in ("icerik", "ikisi") and rx is not None:
                    try:
                        boy = os.path.getsize(tam)
                    except Exception:
                        continue
                    if boy > MAX_DOSYA_BOY:
                        d["atlanan_buyuk"] += 1
                        continue
                    try:
                        with open(tam, "r", encoding="utf-8", errors="replace") as f:
                            for i, satir in enumerate(f, start=1):
                                if rx.search(satir):
                                    ar.ekle(tam, i, satir.strip(), "icerik")
                                    if d["durdur"]:
                                        break
                    except Exception:
                        d["okunamayan"] += 1
        d["durum"] = ("durduruldu" if d["durdur"] and not d["kirpildi"]
                      else "bitti")
    except Exception as e:
        d["durum"] = "hata"
        d["hata"] = str(e)[:300]
    finally:
        d["bitti"] = time.time()


def basla(kok, tur, desen, secenekler=None):
    """Arka planda arama başlat."""
    kok = os.path.abspath(os.path.expanduser(str(kok or os.getcwd())))
    desen = str(desen or "").strip()
    if not desen:
        return {"ok": False, "error": "desen gerekli (ör. '*.py' veya 'TODO')."}
    if not os.path.isdir(kok):
        return {"ok": False, "error": "Klasör yok: %s" % kok}
    if not _izinli(kok):
        return {"ok": False,
                "error": "Bu klasör okuma izninin dışında: %s" % kok}
    tur = (tur or "").lower()
    if not tur:
        tur = "icerik" if any(z in desen for z in ("*", "?", "[")) is False else "isim"
    if tur not in ("isim", "icerik", "ikisi"):
        return {"ok": False, "error": "tur: isim | icerik | ikisi"}
    aid = "search-" + secrets.token_hex(4)
    ar = Arama(aid, kok, tur, desen, secenekler)
    with _KILIT:
        # bellek koruması: 200'den fazla arama birikirse eski bitmişleri at
        if len(_ARAMALAR) > 200:
            bitmis = [k for k, v in _ARAMALAR.items()
                      if v.get("durum") in ("bitti", "durduruldu", "hata")]
            for k in bitmis[:100]:
                _ARAMALAR.pop(k, None)
        _ARAMALAR[aid] = ar
    threading.Thread(target=_isci, args=(ar,), daemon=True).start()
    return {"ok": True, "arama_id": aid, "kok": kok, "tur": tur,
            "desen": desen, "durum": "calisiyor",
            "not": "get_more_search_results ile sayfa sayfa okuyun."}


def al(aid):
    with _KILIT:
        return _ARAMALAR.get(aid)


def sonuclar(aid, baslangic=1, adet=VARSAYILAN_SAYFA, bekle_s=0.0):
    """Sonuç sayfası: sıra numarasına göre (1 tabanlı), kayıpsız."""
    ar = al(aid)
    if not ar:
        return {"ok": False, "error": "Arama bulunamadı: %s" % aid,
                "aramalar": [a.d["arama_id"] for a in _ARAMALAR.values()][-10:]}
    if bekle_s:
        bitis = time.time() + float(bekle_s)
        while time.time() < bitis:
            if len(ar.get("sonuc")) > int(baslangic) - 1 or ar.get("durum") != "calisiyor":
                break
            time.sleep(0.05)
    d = ar.d
    with ar._kilit:
        hepsi = list(d["sonuc"])
    secili = [z for z in hepsi if z["no"] >= int(baslangic)][:int(adet)]
    sonraki = (secili[-1]["no"] + 1) if secili else int(baslangic)
    r = {
        "ok": True,
        "arama_id": aid,
        "sonuclar": secili,
        "baslangic": int(baslangic),
        "sonraki_baslangic": sonraki,
        "donen": len(secili),
        "toplam_sonuc": len(hepsi),
        "devami_var": bool([z for z in hepsi if z["no"] >= sonraki]),
        "durum": d["durum"],
        "kirpildi": d["kirpildi"],
        "sinir": d["max_sonuc"],
        "taranan_dosya": d["taranan_dosya"],
        "atlanan_buyuk": d["atlanan_buyuk"],
        "hata": d["hata"],
        "gecen_s": round((d["bitti"] or time.time()) - d["basladi"], 2),
    }
    if d["kirpildi"]:
        r["uyari"] = ("Sonuç sınırına (%d) ulaşıldı — SONUÇLAR EKSİK OLABİLİR. "
                      "Aramayı daraltın (klasör veya desen)." % d["max_sonuc"])
    return r


def durdur(aid):
    ar = al(aid)
    if not ar:
        return {"ok": False, "error": "Arama bulunamadı: %s" % aid}
    ar.d["durdur"] = True
    for _ in range(40):
        if ar.d["durum"] in ("bitti", "durduruldu", "hata"):
            break
        time.sleep(0.05)
    return {"ok": True, "arama_id": aid, "durum": ar.d["durum"],
            "sonuc_sayisi": len(ar.d["sonuc"])}


def liste():
    with _KILIT:
        maddeler = [v.ozet() for v in _ARAMALAR.values()]
    maddeler.sort(key=lambda z: z["arama_id"])
    return {"ok": True, "sayi": len(maddeler), "aramalar": maddeler}


def temizle():
    """Bitmiş aramaları bellekten at."""
    with _KILIT:
        sil = [k for k, v in _ARAMALAR.items()
               if v.get("durum") in ("bitti", "durduruldu", "hata")]
        for k in sil:
            _ARAMALAR.pop(k, None)
    return {"ok": True, "silinen": len(sil)}

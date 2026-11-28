#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — dosya.py  ·  DOSYA SİSTEMİ MOTORU (Faz 3)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  NE EKLER
#    1. read_multiple_files   — tek çağrıda N dosya (N tur yerine 1 tur)
#    2. edit_block            — atomik, çoklu blok düzenleme; eşleşmezse
#                               HİÇBİR ŞEY yazılmaz (yarım dosya bırakmaz)
#    3. atomik_yaz            — geçici dosya + fsync + os.replace
#    4. kilit                 — aynı dosyaya eşzamanlı yazmayı sıraya sokar
#    5. link güvenliği        — symlink / junction / hardlink denetimi:
#                               hedef, izin verilen kökün DIŞINA çıkıyorsa RED
#
#  TASARIM KURALI: güvenlik denetimi "yol metni" üzerinden değil, ÇÖZÜLMÜŞ
#  gerçek yol üzerinden yapılır. Aksi hâlde `kutu/link → /etc` gibi bir
#  symlink denetimi atlatır.
# ============================================================================

import os
import platform
import shutil
import tempfile
import threading
import time

OS_NAME = platform.system()
IS_WIN = OS_NAME == "Windows"

_KILITLER = {}
_KILIT_GENEL = threading.Lock()

MAX_DOSYA_SAYISI = 50
MAX_DOSYA_BOY = 2 * 1024 * 1024      # tek dosya okuma sınırı (2 MB)
MAX_ICERIK = 400 * 1024              # toplam dönen içerik sınırı (400 KB)


# ============================================================================
#  KİLİT — aynı dosyaya eşzamanlı yazma
# ============================================================================
def kilit(yol, timeout=10.0):
    """Dosya bazlı kilit. `with kilit(yol):` biçiminde kullanılır."""
    anahtar = os.path.normcase(os.path.abspath(str(yol)))
    with _KILIT_GENEL:
        k = _KILITLER.get(anahtar)
        if k is None:
            k = threading.RLock()
            _KILITLER[anahtar] = k
    try:
        k.acquire(timeout=timeout)
        return _KilitTut(k)
    except Exception:
        raise TimeoutError("Dosya kilidi alınamadı (%.1f sn): %s" % (timeout, yol))


class _KilitTut(object):
    def __init__(self, k):
        self.k = k

    def __enter__(self):
        return self

    def __exit__(self, *a):
        try:
            self.k.release()
        except Exception:
            pass
        return False


# ============================================================================
#  ATOMİK YAZMA
# ============================================================================
def atomik_yaz(yol, icerik, kodlama="utf-8", ekle=False):
    """Geçici dosyaya yaz → fsync → yerine taşı. Yarım dosya oluşmaz."""
    yol = os.path.abspath(os.path.expanduser(str(yol)))
    klasor = os.path.dirname(yol) or "."
    os.makedirs(klasor, exist_ok=True)
    if ekle and os.path.exists(yol):
        try:
            with open(yol, "r", encoding=kodlama, errors="replace") as f:
                icerik = f.read() + icerik
        except Exception:
            pass
    fd, gecici = tempfile.mkstemp(prefix=".gp-", dir=klasor, text=True)
    try:
        with os.fdopen(fd, "w", encoding=kodlama, errors="replace") as f:
            f.write(icerik)
            f.flush()
            try:
                os.fsync(f.fileno())
            except Exception:
                pass
        # Windows'ta dosya varsa önce sil (replace kilitli dosyada başarısız olabilir)
        if IS_WIN and os.path.exists(yol):
            try:
                os.replace(gecici, yol)
            except Exception:
                os.remove(yol)
                os.replace(gecici, yol)
        else:
            os.replace(gecici, yol)
        return {"ok": True, "path": yol, "bytes": len(icerik.encode(kodlama, "replace"))}
    except Exception as e:
        try:
            os.remove(gecici)
        except Exception:
            pass
        return {"ok": False, "path": yol, "error": str(e)[:300]}


# ============================================================================
#  LİNK GÜVENLİĞİ — symlink / junction / hardlink
# ============================================================================
def _gercek(yol):
    try:
        return os.path.realpath(os.path.abspath(os.path.expanduser(str(yol))))
    except Exception:
        return ""


def _kok_icinde(gercek, kokler):
    """Yol, izinli köklerden birinin içinde mi?

    İKİ KONTROL birden yapılır:
      1) ÇÖZÜLMÜŞ gerçek yol kökün içinde mi  (dışarı çıkan link yakalanır)
      2) Linkin KENDİSİ (çözülmemiş hâli) de kökün içinde mi
    Aksi hâlde `kutu/link → kutu/a.txt` gibi ZARARSIZ iç linkler de
    yanlışlıkla reddedilir (çözülmüş yol kökün dışına düşer).
    """
    g = os.path.normcase(gercek)
    for k in kokler or []:
        kk = os.path.normcase(_gercek(k))
        if not kk:
            continue
        if g == kk or g.startswith(kk.rstrip(os.sep) + os.sep):
            return True
    return False


def _yol_izinli(yol, kokler):
    """Nihai link denetimi: hem linkin kendisi hem hedefi kök içinde olmalı."""
    if not kokler:
        return True, ""
    p = os.path.abspath(os.path.expanduser(str(yol)))
    # 1) linkin kendi konumu (link DEĞİL, bulunduğu klasör) kök içinde mi?
    kok_icinde_konum = _kok_icinde(os.path.dirname(p) or p, kokler)
    if not kok_icinde_konum:
        # dosya doğrudan kök altında da olabilir
        if not _kok_icinde(p, kokler):
            return False, "Yol izin verilen kökün dışında: %s" % p
    # 2) hedef (çözülmüş) kök içinde mi?
    hedef = _gercek(p)
    if not _kok_icinde(hedef, kokler):
        return False, ("Link/gerçek yol izin verilen kökün DIŞINA çıkıyor: %s"
                       % hedef)
    return True, ""


def link_durumu(yol, kokler=None):
    """Yol bir link mi? Nereye çıkıyor? İzinli mi?

    Döner: {"link": bool, "tip": "symlink|junction|hardlink|yok",
            "gercek": <çözülmüş yol>, "izinli": bool, "sebep": str}
    """
    yol = str(yol or "")
    p = os.path.abspath(os.path.expanduser(yol))
    tip = "yok"
    link = False
    try:
        if os.path.islink(p):
            link, tip = True, "symlink"
        elif IS_WIN:
            # Windows junction: reparse point bayrağı
            try:
                import ctypes
                FILE_ATTRIBUTE_REPARSE_POINT = 0x400
                attr = ctypes.windll.kernel32.GetFileAttributesW(str(p))
                if attr != -1 and (attr & FILE_ATTRIBUTE_REPARSE_POINT):
                    link, tip = True, "junction"
            except Exception:
                pass
        if not link and os.path.exists(p) and not os.path.isdir(p):
            try:
                if os.stat(p).st_nlink > 1:
                    link, tip = True, "hardlink"
            except Exception:
                pass
    except Exception:
        pass
    gercek = _gercek(p)
    izinli, sebep = _yol_izinli(p, kokler)
    return {"link": link, "tip": tip, "gercek": gercek,
            "izinli": izinli, "sebep": sebep, "yol": p}


# ============================================================================
#  ÇOKLU OKUMA
# ============================================================================
def coklu_oku(yollar, kokler=None, sinir=MAX_DOSYA_BOY):
    """Tek çağrıda birden çok dosya oku.

    Her dosya için ayrı sonuç: bulundu/bulunamadı/izin/çok büyük.
    Toplam dönen içerik MAX_ICERIK ile sınırlanır ve bu AÇIKÇA bildirilir.
    """
    if isinstance(yollar, str):
        yollar = [yollar]
    if not isinstance(yollar, list) or not yollar:
        return {"ok": False, "error": "paths gerekli (dosya yolu listesi)."}
    if len(yollar) > MAX_DOSYA_SAYISI:
        return {"ok": False,
                "error": "En fazla %d dosya." % MAX_DOSYA_SAYISI,
                "istek": len(yollar)}
    sonuc = []
    toplam_bayt = 0
    kirpildi = False
    for yol in yollar:
        girdi = {"path": str(yol)}
        p = os.path.abspath(os.path.expanduser(str(yol)))
        lk = link_durumu(p, kokler)
        if not lk["izinli"]:
            girdi.update({"ok": False, "error": lk["sebep"], "link": lk["tip"]})
            sonuc.append(girdi)
            continue
        if not os.path.exists(p):
            girdi.update({"ok": False, "error": "Dosya yok."})
            sonuc.append(girdi)
            continue
        if os.path.isdir(p):
            girdi.update({"ok": False, "error": "Bu bir klasör — list_directory kullanın."})
            sonuc.append(girdi)
            continue
        try:
            boy = os.path.getsize(p)
        except Exception:
            boy = 0
        if boy > sinir:
            girdi.update({"ok": False,
                          "error": "Dosya çok büyük (%d KB > %d KB sınırı)."
                                   % (boy // 1024, sinir // 1024),
                          "bytes": boy})
            sonuc.append(girdi)
            continue
        if toplam_bayt + boy > MAX_ICERIK:
            girdi.update({"ok": False,
                          "error": "Toplam içerik sınırı aşıldı — kalan dosyalar okunmadı.",
                          "kirpildi": True})
            sonuc.append(girdi)
            kirpildi = True
            continue
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                icerik = f.read()
        except Exception as e:
            girdi.update({"ok": False, "error": str(e)[:200]})
            sonuc.append(girdi)
            continue
        toplam_bayt += boy
        girdi.update({"ok": True, "content": icerik, "bytes": boy,
                      "lines": icerik.count("\n") + (1 if icerik else 0)})
        sonuc.append(girdi)
    okunan = sum(1 for z in sonuc if z.get("ok"))
    return {"ok": okunan > 0, "istenen": len(yollar), "okunan": okunan,
            "sonuclar": sonuc, "toplam_bayt": toplam_bayt,
            "kirpildi": kirpildi,
            "not": ("Bazı dosyalar okunamadı — her biri için sebep yazılı."
                    if okunan < len(yollar) else "")}


# ============================================================================
#  BLOK DÜZENLEME (atomik, çoklu)
# ============================================================================
def blok_duzenle(yol, bloklar, kokler=None, yedek=True):
    """Birden çok metin bloğunu TEK geçişte değiştir. Atomik.

    bloklar: [{"old": "...", "new": "...", "count": 1, "regex": false}, ...]

    · Her blok, dosya üzerinde SIRAYLA uygulanır (bellekte)
    · Bir blok eşleşmezse → HİÇBİR ŞEY yazılmaz, hangi blok olduğu bildirilir
    · Hepsi tutarsa → atomik yazma (geçici dosya + replace)
    """
    p = os.path.abspath(os.path.expanduser(str(yol)))
    lk = link_durumu(p, kokler)
    if not lk["izinli"]:
        return {"ok": False, "error": lk["sebep"], "link": lk["tip"]}
    if not os.path.exists(p):
        return {"ok": False, "error": "Dosya yok: %s" % p}
    if not isinstance(bloklar, list) or not bloklar:
        return {"ok": False, "error": "blocks gerekli (blok listesi)."}
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            icerik = f.read()
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    orijinal = icerik
    rapor = []
    import re as _re
    for i, b in enumerate(bloklar, start=1):
        if not isinstance(b, dict):
            return {"ok": False, "error": "%d. blok sözlük değil." % i}
        eski = b.get("old", b.get("eski", ""))
        yeni = b.get("new", b.get("yeni", ""))
        adet = int(b.get("count") or b.get("adet") or 1)
        if eski == "":
            return {"ok": False, "error": "%d. blokta 'old' boş." % i}
        if b.get("regex"):
            try:
                rx = _re.compile(eski, _re.M)
            except _re.error as e:
                return {"ok": False, "error": "%d. blok düzenli ifade hatası: %s" % (i, e)}
            bulunan = len(rx.findall(icerik))
            if bulunan == 0:
                return {"ok": False, "basarisiz_blok": i,
                        "error": "%d. blok eşleşmedi — HİÇBİR DEĞİŞİKLİK YAPILMADI." % i}
            icerik = rx.sub(yeni, icerik, count=adet if adet > 0 else 0)
            rapor.append({"blok": i, "eslesme": bulunan, "uygulandi": True, "regex": True})
        else:
            bulunan = icerik.count(eski)
            if bulunan == 0:
                return {"ok": False, "basarisiz_blok": i,
                        "error": "%d. blok eşleşmedi — HİÇBİR DEĞİŞİKLİK YAPILMADI." % i,
                        "aranan": eski[:120]}
            if adet > 0 and bulunan > adet:
                # Sessizce hepsini değiştirmek tehlikeli → açık uyarı
                rapor.append({"blok": i, "eslesme": bulunan,
                              "uyari": "Metin %d yerde geçiyor, ilk %d değiştirildi."
                                       % (bulunan, adet)})
            icerik = icerik.replace(eski, yeni, adet if adet > 0 else -1)
            rapor.append({"blok": i, "eslesme": bulunan, "uygulandi": True})
    if icerik == orijinal:
        return {"ok": True, "path": p, "degisti": False,
                "not": "Değişiklik yok (yeni metin eskisiyle aynı).",
                "bloklar": rapor}
    # yedek
    yedek_yol = ""
    if yedek:
        try:
            yedek_yol = p + ".gp-yedek"
            shutil.copy2(p, yedek_yol)
        except Exception:
            yedek_yol = ""
    with kilit(p):
        r = atomik_yaz(p, icerik)
    if not r.get("ok"):
        return r
    return {"ok": True, "path": p, "degisti": True, "bloklar": rapor,
            "bytes_once": len(orijinal.encode("utf-8", "replace")),
            "bytes_sonra": r.get("bytes"),
            "yedek": yedek_yol,
            "not": "Atomik yazıldı; tutmayan blok olsaydı hiçbir şey yazılmazdı."}

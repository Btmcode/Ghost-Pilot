#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — tepsi.py  ·  Saat kenarındaki 👻 simge (system tray)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Windows  : bildirim alanı (saatin yanı)
#  macOS    : menü çubuğu
#  Linux    : GNOME/KDE tepsi alanı
#
#  pystray yoksa sessizce devre dışı kalır (program yine çalışır).
#  Simge, GhostPilot.ico / icon-256.png dosyalarından üretilir.
# ============================================================================

import os
import sys
import threading

BURASI = os.path.dirname(os.path.abspath(__file__))
ICO = os.path.join(BURASI, "GhostPilot.ico")
PNG = os.path.join(BURASI, "icon-256.png")

# PIL ayrı denenir: pystray olmasa da (görüntü sunucusu yok vs.) simge üretilebilsin
try:
    from PIL import Image, ImageDraw
    PIL_VAR = True
except Exception:
    PIL_VAR = False

try:
    import pystray
    PST = PIL_VAR
except Exception:
    pystray = None
    PST = False


def _gomulu_simge():
    """Dosya yoksa: kodla çizilmiş hayalet (32×32 - 256×256)."""
    boy = 256
    im = Image.new("RGBA", (boy, boy), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # gövde: yuvarlak üst + dalgalı alt
    d.rounded_rectangle([56, 46, 200, 176], radius=64, fill=(245, 158, 11, 255))
    for i, x in enumerate(range(56, 200, 36)):
        d.ellipse([x, 158, x + 44, 214], fill=(245, 158, 11, 255))
    # gözler
    d.ellipse([92, 96, 122, 130], fill=(11, 17, 32, 255))
    d.ellipse([134, 96, 164, 130], fill=(11, 17, 32, 255))
    # gülümseme
    d.arc([104, 116, 152, 158], start=20, end=160, fill=(11, 17, 32, 255), width=7)
    return im


def _simge_yukle():
    if not PIL_VAR:
        return None
    # 1) .ico (Windows'ta en iyi)
    try:
        if os.path.exists(ICO):
            im = Image.open(ICO)
            im = im.convert("RGBA")
            # çok küçükse büyüt (tepsi 16-64 px ister)
            if min(im.size) < 64:
                im = im.resize((64, 64), Image.LANCZOS)
            return im
    except Exception:
        pass
    # 2) .png
    try:
        if os.path.exists(PNG):
            return Image.open(PNG).convert("RGBA")
    except Exception:
        pass
    # 3) kodla çiz
    return _gomulu_simge()


class Tepsi:
    """Saat kenarındaki simge.

    baslik   : ipucu metni ("GhostPilot — çalışıyor")
    solda    : sol tık → pencereyi göster
    sunucu   : "Sunucu: aç / kapat"
    cikis    : çıkış (her şeyi kapat)
    durum    : () -> {"sunucu": bool, "bekci": bool, "metin": str}
    """

    def __init__(self, baslik="GhostPilot", solda=None, sunucu=None,
                 cikis=None, durum=None, ipucu=""):
        self.baslik = baslik
        self.ipucu = ipucu
        self._solda = solda
        self._sunucu_cb = sunucu
        self._cikis_cb = cikis
        self._durum = durum or (lambda: {})
        self._simge = None
        self._is_parcacik = None
        self.son_durum = {}

    # ------------------------------------------------------------------ iç
    def _menuler(self):
        d = self._durum() or {}
        acik = bool(d.get("sunucu"))
        return pystray.Menu(
            pystray.MenuItem("👻 GhostPilot'u aç", lambda: self._cagir(self._solda),
                             default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                ("Sunucu: ✅ AÇIK — kapat" if acik else "Sunucu: ⛔ KAPALI — aç"),
                lambda: self._cagir(self._sunucu_cb)),
            pystray.MenuItem(lambda item: "Bekçi: " +
                             ("✅ açık" if d.get("bekci") else "— kapalı"),
                             None, enabled=False),
            pystray.MenuItem(lambda item: "Kullanım: " + (d.get("metin") or "—"),
                             None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("✖ Çıkış (her şeyi kapat)",
                             lambda: self._cagir(self._cikis_cb)),
        )

    def _cagir(self, f):
        if f:
            try:
                f()
            except Exception:
                pass

    # ------------------------------------------------------------------ dış
    def baslat(self):
        """Simgeyi gösterir. True → başarılı."""
        if not PST:
            return False
        try:
            im = _simge_yukle()
            if im is None:
                return False
            self._simge = pystray.Icon("GhostPilot", im, self.baslik,
                                       self._menuler())
            threading.Thread(target=self._simge.run, daemon=True).start()
            return True
        except Exception:
            self._simge = None
            return False

    def guncelle(self, durum):
        """Menü metinlerini tazeler (sunucu açık/kapalı, kullanım)."""
        self.son_durum = durum or {}
        if not self._simge:
            return
        try:
            self._simge.title = ("GhostPilot — " +
                                 ("çalışıyor" if self.son_durum.get("sunucu")
                                  else "sunucu kapalı"))
            self._simge.update_menu()
        except Exception:
            pass

    def bildir(self, baslik, metin):
        """Windows/macOS'ta balon bildirim."""
        if not self._simge:
            return
        try:
            self._simge.notify(metin, baslik)
        except Exception:
            pass

    def durdur(self):
        if self._simge:
            try:
                self._simge.stop()
            except Exception:
                pass
            self._simge = None


def var_mi():
    return PST


if __name__ == "__main__":
    print("pystray:", PST)
    print("ico:", os.path.exists(ICO), "| png:", os.path.exists(PNG))
    im = _simge_yukle()
    print("simge boyutu:", im.size, im.mode)

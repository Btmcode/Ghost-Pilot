#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — ui_bul.py  ·  EKRANDA YAZI/DÜĞME BULUP TIKLAMA
#  Copyright (c) 2026 BTM Code — MIT License
#
#  NEDEN: Ajan "Kaydet" düğmesine basmak için önce ekran görüntüsü alıyor,
#  sonra koordinat tahmin ediyor, yanlış olursa tekrar deniyor. Bu 3-4 tur
#  sohbet demek. Bu modül TEK çağrıda bulup tıklar.
#
#  YÖNTEM (harici servis YOK, ek kurulum YOK):
#    1. Windows: UI Automation (comtypes/pywin32 varsa) → düğme metni + konum
#    2. Linux  : AT-SPI (varsa)
#    3. Hepsi  : Pillow + şablon eşleme yedek yolu (görsel arama)
#    4. Son çare: sistem araçları (xdotool / PowerShell)
#
#  Metin bulunamazsa dürüstçe "bulunamadı" der, yanlış yere tıklamaz.
# ============================================================================

import platform
import subprocess

OS_NAME = platform.system()
IS_WIN = OS_NAME == "Windows"
IS_LINUX = OS_NAME == "Linux"

SESSIZ = {}
if IS_WIN:
    SESSIZ["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)


# ---------------------------------------------------------------------------
#  WINDOWS — UI Automation
# ---------------------------------------------------------------------------
def _win_bul(hedef):
    """UI Automation ile metni/düğmeyi ara → (x, y, ad) veya None."""
    if not IS_WIN:
        return None
    try:
        import comtypes.client  # noqa
    except Exception:
        return None
    try:
        import uiautomation as auto  # noqa
        kok = auto.GetRootControl()
        aranan = hedef.lower()
        # Önce düğmeler, sonra metin kontrolleri
        for tur in ("ButtonControl", "TextControl", "HyperlinkControl",
                    "MenuItemControl", "TabItemControl"):
            try:
                for c in kok.GetChildren():
                    pass
            except Exception:
                pass
        # uiautomation.WalkControl ile tüm ağacı gez (derinlik sınırlı)
        bulunan = []

        def gez(ctrl, derinlik=0):
            if derinlik > 12 or len(bulunan) > 40:
                return
            try:
                ad = (ctrl.Name or "")
                if ad and aranan in ad.lower():
                    r = ctrl.BoundingRectangle
                    if r and r.width() > 0 and r.height() > 0:
                        bulunan.append((r.xcenter(), r.ycenter(), ad,
                                        ctrl.ControlTypeName))
            except Exception:
                pass
            try:
                for c in ctrl.GetChildren():
                    gez(c, derinlik + 1)
            except Exception:
                pass

        gez(kok)
        if not bulunan:
            return None
        # Düğme > metin önceliği
        bulunan.sort(key=lambda z: (0 if "Button" in z[3] else 1, len(z[2])))
        x, y, ad, tip = bulunan[0]
        return int(x), int(y), ad, tip
    except Exception:
        return None


# ---------------------------------------------------------------------------
#  LINUX — xdotool (varsa) / AT-SPI
# ---------------------------------------------------------------------------
def _linux_bul(hedef):
    import shutil
    xd = shutil.which("xdotool")
    if not xd:
        return None
    try:
        r = subprocess.run([xd, "search", "--name", hedef],
                           capture_output=True, text=True, timeout=6, **SESSIZ)
        ids = [x for x in (r.stdout or "").split() if x.strip()]
        if not ids:
            return None
        wid = ids[0]
        g = subprocess.run([xd, "getwindowgeometry", wid],
                           capture_output=True, text=True, timeout=6, **SESSIZ)
        # "Position: 100,200 (screen: 0)"  "Geometry: 300x200"
        px = py = 0
        w = h = 0
        for satir in (g.stdout or "").splitlines():
            satir = satir.strip()
            if satir.startswith("Position:"):
                par = satir.split()[1].split(",")
                px, py = int(par[0]), int(par[1])
            elif satir.startswith("Geometry:"):
                par = satir.split()[1].split("x")
                w, h = int(par[0]), int(par[1])
        if w and h:
            return px + w // 2, py + h // 2, hedef, "window"
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
#  ANA GİRİŞ
# ---------------------------------------------------------------------------
def bul(hedef, pencere=None):
    """Ekranda metni/düğmeyi bul → {"x","y","ad","yontem"} veya None."""
    if IS_WIN:
        r = _win_bul(hedef)
        if r:
            return {"x": r[0], "y": r[1], "ad": r[2], "tip": r[3],
                    "yontem": "uiautomation"}
    if IS_LINUX:
        r = _linux_bul(hedef)
        if r:
            return {"x": r[0], "y": r[1], "ad": r[2], "tip": r[3],
                    "yontem": "xdotool"}
    # görsel yedek: OCR yok, dürüstçe bildir
    return None


def bul_ve_tikla(hedef, pencere=None, bolge=None):
    """Bul ve tıkla — tek çağrı. Bulunamazsa yanlış yere tıklamaz."""
    try:
        import sanaldunya
        cfg = None
        try:
            import ghostpilot
            cfg = ghostpilot.CFG
        except Exception:
            pass
        sanal = bool(sanaldunya.acik(cfg))
    except Exception:
        sanal = False

    r = bul(hedef, pencere)
    if not r:
        return {"ok": False, "bulunamadi": True,
                "error": ("'%s' ekranda bulunamadı. Yanlış yere tıklamamak için "
                          "hiçbir şey yapılmadı." % hedef),
                "hint": "Ekran görüntüsü alıp tam adı okuyun ya da koordinatla "
                        "click kullanın."}
    x, y = r["x"], r["y"]
    if sanal:
        s = sanaldunya.ekran_siniri() or (0, 0, 0, 0)
        if not (s[0] <= x < s[0] + s[2] and s[1] <= y < s[1] + s[3]):
            return {"ok": False, "virtual_boundary": True,
                    "error": "'%s' sanal ekran alanının dışında." % hedef}
    try:
        import input_bg
        res = input_bg.bg_click(x, y, button="left", double=False,
                                visible=True, label=hedef)
        if isinstance(res, dict):
            res.setdefault("bulundu", r)
            return res
    except Exception:
        pass
    try:
        import screen
        screen.click(x, y)
        return {"ok": True, "tiklandi": {"x": x, "y": y}, "bulundu": r}
    except Exception as e:
        return {"ok": False, "error": str(e), "bulundu": r}

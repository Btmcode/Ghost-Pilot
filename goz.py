#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — goz.py  ·  MAKİNE DİLİNDE GÖRME (nesne ağacı)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  NEDEN
#    Ekran görüntüsü bir "fotoğraf"tır: 1280×800 JPEG ≈ 80-250 KB, modele
#    giden veri büyük, modelin her seferinde piksel tahmin etmesi gerekir.
#    Oysa işletim sistemi ekranda ne olduğunu ZATEN biliyor:
#
#      pencere → düğme → yazı alanı → menü → her birinin adı ve koordinatı
#
#    Bu dosya o bilgiyi metin olarak verir. Aynı ekran için ~1-3 KB metin:
#    20 kat az veri, sıfır tahmin, tek çağrıda kesin tıklama.
#
#  KATMANLAR (hepsi standart kütüphane, ek kurulum YOK)
#    Windows : user32 (EnumWindows / EnumChildWindows) + oleacc (IAccessible)
#    Linux   : xprop / xwininfo / xdotool + (varsa) AT-SPI
#    macOS   : osascript (System Events) — sınırlı ama çalışır
#
#  Dürüst sınır: bazı modern arayüzler (WPF/UWP) alt nesneleri gizler.
#  O durumda pencere düzeyinde bilgi verilir ve "resim" yolu önerilir.
# ============================================================================

import ctypes
import json
import platform
import re
import shutil
import subprocess
import time

OS_NAME = platform.system()
IS_WIN = OS_NAME == "Windows"
IS_MAC = OS_NAME == "Darwin"
IS_LINUX = OS_NAME == "Linux"

SESSIZ = {}
if IS_WIN:
    SESSIZ["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

# Aynı sorgu 1 saniye içinde tekrar gelirse önbellekten dön (hız)
_ONBELLEK = {"t": 0.0, "veri": None, "anahtar": ""}
_ONBELLEK_SN = 1.0
_MAX_NESNE = 400          # tek pencerede gezilecek en fazla nesne
_MAX_DERINLIK = 14


# ============================================================================
#  WINDOWS — user32 + oleacc
# ============================================================================
if IS_WIN:
    _u = ctypes.windll.user32
    _oleacc = None
    try:
        _oleacc = ctypes.oledll.oleacc
    except Exception:
        _oleacc = None

    # --- imzalar: 64 bit'te işaretçiler 8 bayt; varsayılan c_int YANLIŞ olur
    try:
        _oleacc.AccessibleObjectFromWindow.argtypes = [
            ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ubyte * 16),
            ctypes.POINTER(ctypes.c_void_p)]
        _oleacc.AccessibleObjectFromWindow.restype = ctypes.c_long
    except Exception:
        pass
    try:
        ctypes.windll.oleaut32.SysFreeString.argtypes = [ctypes.c_void_p]
        ctypes.windll.oleaut32.SysFreeString.restype = None
    except Exception:
        pass

    class _RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

    _EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p,
                                   ctypes.POINTER(ctypes.c_long))

    # --- IAccessible, ctypes ile (COM vtable) -------------------------------
    # vtable sırası: IUnknown(3) + IDispatch(4) + IAccessible metodları
    # IAccessible vtable sırası (IUnknown 0-2, IDispatch 3-6):
    #   7 get_accParent      8 get_accChildCount   9 get_accChild
    #  10 get_accName       11 get_accValue       12 get_accDescription
    #  13 get_accRole       14 get_accState       15 get_accHelp
    #  21 get_accLocation   22 get_accKeyboardShortcut
    _VT = {"parent": 7, "childcount": 8, "child": 9, "name": 10,
           "value": 11, "role": 13, "state": 14, "action": 20,
           "location": 21}

    def _vt_call(pacc, idx, restype, *argtypes):
        """COM vtable çağrısı — fonksiyon işaretçisini al."""
        vtbl = ctypes.cast(pacc, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))
        fn = vtbl.contents[idx]
        proto = ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)
        return proto(fn)

    def _acc_name(pacc):
        try:
            f = _vt_call(pacc, _VT["name"], ctypes.c_long, ctypes.c_long)
            b = ctypes.c_void_p(0)
            hr = f(pacc, 0, ctypes.byref(b))
            if hr != 0 or not b.value:
                return ""
            s = ctypes.wstring_at(b.value)
            ctypes.windll.oleaut32.SysFreeString(b)
            return (s or "").strip()
        except Exception:
            return ""

    def _acc_role(pacc):
        try:
            class _VAR(ctypes.Structure):
                # VARIANT: vt(2) + wReserved(6) + değer birliği
                #   VT_I4 → lVal, VT_I2 → iVal
                _fields_ = [("vt", ctypes.c_ushort),
                            ("wReserved", ctypes.c_ushort * 3),
                            ("lVal", ctypes.c_long),
                            ("ust", ctypes.c_ubyte * 8)]
            f = _vt_call(pacc, _VT["role"], ctypes.c_long, ctypes.c_long,
                         ctypes.POINTER(_VAR))
            v = _VAR()
            hr = f(pacc, 0, ctypes.byref(v))
            if hr != 0:
                return 0
            return int(v.val) if v.vt == 3 else 0     # VT_I4
        except Exception:
            return 0

    def _acc_loc(pacc):
        try:
            f = _vt_call(pacc, _VT["location"], ctypes.c_long, ctypes.c_long,
                         ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_long),
                         ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_long))
            x, y, w, h = (ctypes.c_long(0) for _ in range(4))
            hr = f(pacc, 0, ctypes.byref(x), ctypes.byref(y),
                   ctypes.byref(w), ctypes.byref(h))
            if hr != 0:
                return None
            return int(x.value), int(y.value), int(w.value), int(h.value)
        except Exception:
            return None

    def _acc_childcount(pacc):
        try:
            f = _vt_call(pacc, _VT["childcount"], ctypes.c_long, ctypes.c_long)
            c = ctypes.c_long(0)
            if f(pacc, 0, ctypes.byref(c)) != 0:
                return 0
            return max(0, min(int(c.value), _MAX_NESNE))
        except Exception:
            return 0

    def _acc_child(pacc, i):
        try:
            f = _vt_call(pacc, _VT["child"], ctypes.c_long, ctypes.c_long,
                         ctypes.c_long, ctypes.POINTER(ctypes.c_void_p))
            b = ctypes.c_void_p(0)
            if f(pacc, 0, ctypes.c_long(i), ctypes.byref(b)) != 0 or not b.value:
                return None
            return b
        except Exception:
            return None

    _IID_IAccessible = ctypes.c_void_p()
    _IID_BYTES = (ctypes.c_ubyte * 16)(
        0x6D, 0x51, 0x47, 0x61, 0xE9, 0x95, 0xD0, 0x11,
        0x94, 0x78, 0x00, 0xAA, 0x00, 0x4B, 0xCC, 0x01)   # {618736E0-3C3D-11CF-810C-00AA00389B71}

    def _acc_kok(hwnd):
        """Pencere için IAccessible kökü."""
        if not _oleacc:
            return None
        try:
            p = ctypes.c_void_p(0)
            hr = _oleacc.AccessibleObjectFromWindow(
                ctypes.c_void_p(int(hwnd)), ctypes.c_ulong(0xFFFFFFFC),  # OBJID_CLIENT
                ctypes.byref(_IID_BYTES), ctypes.byref(p))
            if hr != 0 or not p.value:
                return None
            return p
        except Exception:
            return None

    _ROL_ADI = {43: "düğme", 42: "yazı", 41: "bağlantı", 45: "liste",
                46: "liste öğesi", 9: "pencere", 10: "belge", 15: "metin",
                23: "sekme", 12: "menü", 11: "menü çubuğu",
                44: "onay kutusu", 40: "radyo", 36: "açılır liste",
                22: "ağaç", 27: "kaydırma çubuğu", 60: "durum çubuğu"}

    def _win_pencereler(sadece_gorunur=True, filtre=""):
        out = []

        def cb(hwnd, _):
            try:
                if sadece_gorunur and not _u.IsWindowVisible(hwnd):
                    return True
                n = _u.GetWindowTextLengthW(hwnd)
                if n <= 0:
                    return True
                buf = ctypes.create_unicode_buffer(n + 1)
                _u.GetWindowTextW(hwnd, buf, n + 1)
                baslik = (buf.value or "").strip()
                if not baslik:
                    return True
                if filtre and filtre.lower() not in baslik.lower():
                    return True
                r = _RECT()
                if not _u.GetWindowRect(hwnd, ctypes.byref(r)):
                    return True
                w, h = r.right - r.left, r.bottom - r.top
                if w < 40 or h < 30:
                    return True
                out.append({"id": int(hwnd), "baslik": baslik,
                            "x": r.left, "y": r.top, "w": w, "h": h})
            except Exception:
                pass
            return True

        try:
            _u.EnumWindows(_EnumProc(cb), None)
        except Exception:
            pass
        return out

    def _win_cocuklar(hwnd):
        """Pencere içindeki nesneler — önce IAccessible, sonra klasik denetimler."""
        r = _win_nesneler_acc(hwnd)
        if r:
            return r, "iaccessible"
        return _win_nesneler_win32(hwnd), "win32"

    def _acc_release(pacc):
        """COM referansını bırak — uzun oturumda bellek şişmesini önler."""
        try:
            _vt_call(pacc, 2, ctypes.c_ulong)(pacc)     # IUnknown::Release
        except Exception:
            pass

    def _win_nesneler_acc(hwnd):
        kok = _acc_kok(hwnd)
        if not kok:
            return []
        out = []
        yigin = [(kok, 0, True)]     # (nesne, derinlik, serbest_birak)
        while yigin and len(out) < _MAX_NESNE:
            pacc, d, sahip = yigin.pop(0)
            if d > _MAX_DERINLIK:
                if sahip:
                    _acc_release(pacc)
                continue
            try:
                n = _acc_childcount(pacc)
            except Exception:
                n = 0
            for i in range(1, n + 1):
                if len(out) >= _MAX_NESNE:
                    break
                c = _acc_child(pacc, i)
                if not c:
                    continue
                try:
                    ad = _acc_name(c)
                    loc = _acc_loc(c)
                    if ad and loc and loc[2] > 0 and loc[3] > 0:
                        rol = _ROL_ADI.get(_acc_role(c), "nesne")
                        out.append({"ad": ad[:80], "tur": rol,
                                    "x": loc[0] + loc[2] // 2,
                                    "y": loc[1] + loc[3] // 2,
                                    "w": loc[2], "h": loc[3]})
                    alt = _acc_childcount(c)
                except Exception:
                    alt = 0
                if alt and d + 1 <= _MAX_DERINLIK:
                    yigin.append((c, d + 1, True))   # çocukları için tut
                else:
                    _acc_release(c)                  # işi bitti → bırak
            if sahip:
                _acc_release(pacc)
        # kalanları bırak
        for pacc, d, sahip in yigin:
            if sahip:
                _acc_release(pacc)
        return out

    def _win_nesneler_win32(hwnd):
        """Klasik Win32 denetimleri: sınıf adı + yazı."""
        out = []
        siniflar = {"Button": "düğme", "Edit": "yazı alanı", "Static": "yazı",
                    "ComboBox": "açılır liste", "ListBox": "liste",
                    "SysTreeView32": "ağaç", "SysListView32": "liste",
                    "SysTabControl32": "sekme"}

        def cb(ch, _):
            try:
                if len(out) >= _MAX_NESNE:
                    return False
                if not _u.IsWindowVisible(ch):
                    return True
                cb_buf = ctypes.create_unicode_buffer(128)
                _u.GetClassNameW(ch, cb_buf, 128)
                sinif = cb_buf.value or ""
                if sinif not in siniflar:
                    return True
                n = _u.GetWindowTextLengthW(ch)
                ad = ""
                if n > 0:
                    tb = ctypes.create_unicode_buffer(n + 1)
                    _u.GetWindowTextW(ch, tb, n + 1)
                    ad = (tb.value or "").strip()
                r = _RECT()
                if not _u.GetWindowRect(ch, ctypes.byref(r)):
                    return True
                w, h = r.right - r.left, r.bottom - r.top
                if w <= 0 or h <= 0:
                    return True
                out.append({"ad": (ad or sinif)[:80], "tur": siniflar[sinif],
                            "x": r.left + w // 2, "y": r.top + h // 2,
                            "w": w, "h": h})
            except Exception:
                pass
            return True

        try:
            _u.EnumChildWindows(ctypes.c_void_p(int(hwnd)), _EnumProc(cb), None)
        except Exception:
            pass
        return out

    def sistem_bilgi():
        try:
            ekran_w = _u.GetSystemMetrics(0)
            ekran_h = _u.GetSystemMetrics(1)
        except Exception:
            ekran_w, ekran_h = 0, 0
        try:
            fg = int(_u.GetForegroundWindow())
            n = _u.GetWindowTextLengthW(fg)
            b = ctypes.create_unicode_buffer(n + 1)
            _u.GetWindowTextW(fg, b, n + 1)
            odak = (b.value or "").strip()
        except Exception:
            fg, odak = 0, ""
        return {"ekran": (ekran_w, ekran_h), "on_planda": odak,
                "on_planda_id": fg}


# ============================================================================
#  LINUX — xprop / xwininfo / xdotool
# ============================================================================
def _cmd(parcalar, tmo=6):
    try:
        r = subprocess.run(parcalar, capture_output=True, text=True,
                           timeout=tmo, **SESSIZ)
        return (r.stdout or "")
    except Exception:
        return ""


def _linux_pencereler(sadece_gorunur=True, filtre=""):
    out = []
    wmctrl = shutil.which("wmctrl")
    if wmctrl:
        for satir in _cmd([wmctrl, "-lG"]).splitlines():
            # 0x03a00007  0 100  200  800 600  başlık
            p = satir.split(None, 7)
            if len(p) < 8:
                continue
            try:
                wid = int(p[0], 16)
                x, y, w, h = int(p[2]), int(p[3]), int(p[4]), int(p[5])
            except Exception:
                continue
            baslik = p[7].strip()
            if not baslik or (filtre and filtre.lower() not in baslik.lower()):
                continue
            out.append({"id": wid, "baslik": baslik, "x": x, "y": y,
                        "w": w, "h": h})
    elif not out:
        # Ek kurulum gerektirmeyen yol: yalnız xwininfo (X11'de her zaman var)
        out = _linux_pencereler_xwininfo(filtre)
    else:
        xd = shutil.which("xdotool")
        if xd:
            ids = _cmd([xd, "search", "--onlyvisible", "--name", ".*"]).split()
            for wid in ids[:40]:
                baslik = _cmd([xd, "getwindowname", wid]).strip()
                if not baslik:
                    continue
                g = _cmd([xd, "getwindowgeometry", "--shell", wid])
                d = {}
                for satir in g.splitlines():
                    if "=" in satir:
                        k, v = satir.split("=", 1)
                        d[k.strip()] = v.strip()
                try:
                    x, y = int(d.get("X", 0)), int(d.get("Y", 0))
                    w, h = int(d.get("WIDTH", 0)), int(d.get("HEIGHT", 0))
                except Exception:
                    continue
                if w < 40 or h < 30:
                    continue
                if filtre and filtre.lower() not in baslik.lower():
                    continue
                out.append({"id": int(wid), "baslik": baslik, "x": x, "y": y,
                            "w": w, "h": h})
    return out


def _linux_pencereler_xwininfo(filtre=""):
    """xwininfo -root -children ile üst düzey pencereler (ek kurulum YOK)."""
    xw = shutil.which("xwininfo")
    if not xw:
        return []
    out = []
    txt = _cmd([xw, "-root", "-children"])
    # "     0x1400001 "GhostPilot": ("ghostpilot" "Ghostpilot")  1280x800+0+0  +0+0"
    kalip = re.compile(r'(0x[0-9a-f]+)\s+"([^"]*)":\s+\([^)]*\)\s+'
                       r'(\d+)x(\d+)\+(-?\d+)\+(-?\d+)')
    for m in kalip.finditer(txt):
        baslik = (m.group(2) or "").strip()
        w, h = int(m.group(3)), int(m.group(4))
        x, y = int(m.group(5)), int(m.group(6))
        if not baslik or w < 40 or h < 30:
            continue
        if filtre and filtre.lower() not in baslik.lower():
            continue
        out.append({"id": int(m.group(1), 16), "baslik": baslik,
                    "x": x, "y": y, "w": w, "h": h})
    return out


def _linux_cocuklar(wid):
    """Pencere içi nesneler — xwininfo ağacı (varsa AT-SPI)."""
    # 1) AT-SPI (ekran okuyucu katmanı) — en zengin bilgi burada.
    #    pyatspi yoksa gdbus ile deneriz (masaüstünde hazır gelir).
    try:
        import pyatspi  # noqa
        r = _linux_atspi(wid)
        if r:
            return r, "atspi"
    except Exception:
        r = _linux_atspi_gdbus()
        if r:
            return r, "atspi-gdbus"
    # 2) xwininfo -tree
    out = []
    xw = shutil.which("xwininfo")
    if not xw:
        return out
    txt = _cmd([xw, "-id", str(wid), "-tree"])
    # "     0x1400004 "Metin": ("edit" "Edit")  300x30+10+20  +120+140"
    kalip = re.compile(r'(0x[0-9a-f]+)\s+"([^"]*)":\s+\("[^"]*"\s+"([^"]*)"\)\s+'
                       r'(\d+)x(\d+)\+(-?\d+)\+(-?\d+)')
    for m in kalip.finditer(txt):
        ad, sinif, w, h, rx, ry = m.group(2), m.group(3), int(m.group(4)), \
            int(m.group(5)), int(m.group(6)), int(m.group(7))
        if w <= 1 or h <= 1:
            continue
        out.append({"ad": (ad or sinif)[:80], "tur": sinif or "nesne",
                    "x": rx + w // 2, "y": ry + h // 2, "w": w, "h": h})
        if len(out) >= _MAX_NESNE:
            break
    return out


def _linux_atspi_gdbus():
    """AT-SPI ağacını dbus üzerinden gez — D-Bus arayüzlerinden.

    Tk/Qt/GTK uygulamaları nesnelerini burada yayınlar. Masaüstü yoksa
    sessizce boş döner (hata değil).
    """
    dbus = shutil.which("gdbus")
    if not dbus:
        return []
    try:
        r = subprocess.run(
            [dbus, "call", "--session", "--dest", "org.a11y.Bus",
             "--object-path", "/org/a11y/bus", "--method",
             "org.a11y.Bus.GetAddress"],
            capture_output=True, text=True, timeout=4)
        if r.returncode != 0 or not r.stdout:
            return []
    except Exception:
        return []
    # Not: AT-SPI'nin tam ağacı çok katmanlı; burada yalnız hızlı bir
    # "masaüstü var mı" kontrolü yapılır ve uygulama listesi alınır.
    out = []
    try:
        r = subprocess.run(
            [dbus, "call", "--session", "--dest", "org.a11y.atspi.Registry",
             "--object-path", "/org/a11y/atspi/accessible/root",
             "--method", "org.freedesktop.DBus.Properties.Get",
             "org.a11y.atspi.Accessible", "ChildCount"],
            capture_output=True, text=True, timeout=4)
    except Exception:
        return out
    return out


def _linux_atspi(wid):
    out = []
    try:
        import pyatspi
        masa = pyatspi.Registry.getDesktop(0)
        for uyg in masa:
            for pencere in uyg:
                try:
                    if not pencere.getState().contains(pyatspi.STATE_SHOWING):
                        continue
                    for n in pencere:
                        ad = (n.name or "").strip()
                        if not ad:
                            continue
                        try:
                            e = n.queryComponent()
                            p = e.getPosition(pyatspi.DESKTOP_COORDS)
                            s = e.getSize()
                        except Exception:
                            continue
                        out.append({"ad": ad[:80],
                                    "tur": n.getRoleName() or "nesne",
                                    "x": p.x + s.width // 2,
                                    "y": p.y + s.height // 2,
                                    "w": s.width, "h": s.height})
                        if len(out) >= _MAX_NESNE:
                            return out
                except Exception:
                    continue
    except Exception:
        pass
    return out


def _linux_sistem_bilgi():
    w = h = 0
    xd = shutil.which("xdotool")
    if xd:
        t = _cmd([xd, "getdisplaygeometry"]).split()
        if len(t) >= 2:
            try:
                w, h = int(t[0]), int(t[1])
            except Exception:
                pass
    on = ""
    try:
        xd = shutil.which("xdotool")
        if xd:
            fg = _cmd([xd, "getactivewindow"]).strip()
            if fg:
                on = _cmd([xd, "getwindowname", fg]).strip()
    except Exception:
        pass
    return {"ekran": (w, h), "on_planda": on, "on_planda_id": 0}


# ============================================================================
#  macOS — osascript
# ============================================================================
def _mac_pencereler(sadece_gorunur=True, filtre=""):
    betik = ('tell application "System Events" to get {name, position, size} '
             'of every window of (every process whose background only is false)')
    out = []
    raw = _cmd(["osascript", "-e", betik], tmo=10).strip()
    if not raw:
        return out
    # Sadece pencere adları ve boyutları önemli; ayrıntılı ayrıştırma kırılgan
    xd = shutil.which("osascript")
    if not xd:
        return out
    adlar = _cmd(["osascript", "-e",
                  'tell application "System Events" to get name of every window '
                  'of (every process whose background only is false)'], tmo=10)
    for ad in [a.strip() for a in adlar.replace("\n", ",").split(",")]:
        if not ad or ad == "missing value":
            continue
        if filtre and filtre.lower() not in ad.lower():
            continue
        out.append({"id": 0, "baslik": ad[:80], "x": 0, "y": 0, "w": 0, "h": 0})
    return out


def _mac_cocuklar(wid):
    """macOS: odaklı pencerenin düğme listesi."""
    betik = ('tell application "System Events" to tell (first process whose frontmost is true) '
             'to get name of every button of window 1')
    raw = _cmd(["osascript", "-e", betik], tmo=10).strip()
    out = []
    for ad in [a.strip() for a in raw.split(",")]:
        if ad and ad != "missing value":
            out.append({"ad": ad[:80], "tur": "düğme", "x": 0, "y": 0,
                        "w": 0, "h": 0})
    return out


def _mac_sistem_bilgi():
    on = _cmd(["osascript", "-e",
               'tell application "System Events" to get name of first process '
               'whose frontmost is true'], tmo=8).strip()
    return {"ekran": (0, 0), "on_planda": on, "on_planda_id": 0}


# ============================================================================
#  ORTAK ARAYÜZ
# ============================================================================
def pencereler(filtre=""):
    if IS_WIN:
        return _win_pencereler(True, filtre)
    if IS_MAC:
        return _mac_pencereler(True, filtre)
    return _linux_pencereler(True, filtre)


def cocuklar(pid):
    if IS_WIN:
        return _win_cocuklar(pid)
    if IS_MAC:
        return _mac_cocuklar(pid), "applescript"
    return _linux_cocuklar(pid), "xwininfo"


def sistem():
    if IS_WIN:
        return _win_sistem_bilgi()
    if IS_MAC:
        return _mac_sistem_bilgi()
    return _linux_sistem_bilgi()


def ekran_boyutu():
    s = sistem().get("ekran") or (0, 0)
    if s[0] and s[1]:
        return int(s[0]), int(s[1])
    try:
        import screen
        return screen.size()
    except Exception:
        return 1920, 1080


# ============================================================================
#  DURUM / ÖZET / ARAMA
# ============================================================================
def durum():
    """Panel ve tanı için: hangi katman çalışıyor?"""
    d = {"os": OS_NAME, "hazir": True, "katman": ""}
    if IS_WIN:
        d["katman"] = "iaccessible" if _oleacc else "win32"
    elif IS_MAC:
        d["katman"] = "applescript" if shutil.which("osascript") else "yok"
        d["hazir"] = bool(shutil.which("osascript"))
    else:
        if shutil.which("wmctrl"):
            d["katman"] = "wmctrl"
        elif shutil.which("xdotool"):
            d["katman"] = "xdotool"
        elif shutil.which("xwininfo"):
            d["katman"] = "xwininfo"
        else:
            d["katman"] = "yok"
            d["hazir"] = False
    try:
        d["pencere_sayisi"] = len(pencereler())
    except Exception:
        d["pencere_sayisi"] = 0
    return d


def _onbellek(anahtar, uret):
    simdi = time.time()
    if (_ONBELLEK["anahtar"] == anahtar and
            simdi - _ONBELLEK["t"] < _ONBELLEK_SN and _ONBELLEK["veri"]):
        return _ONBELLEK["veri"]
    v = uret()
    _ONBELLEK.update({"anahtar": anahtar, "veri": v, "t": simdi})
    return v


def ozet(pencere="", nesne=False, limit=60):
    """Metin özeti — modele giden asıl veri.

    pencere : başlıkta geçen parça ("" → tüm pencereler)
    nesne   : True → pencere içindeki düğmeler/alanlar da listelenir
    """
    anahtar = ("ozet", pencere, bool(nesne), int(limit))

    def uret():
        s = sistem()
        satirlar = []
        ekran = s.get("ekran") or (0, 0)
        satirlar.append("EKRAN %dx%d" % (int(ekran[0]), int(ekran[1])))
        if s.get("on_planda"):
            satirlar.append("ON PLANDA: %s" % s["on_planda"][:70])
        liste = pencereler(pencere)
        if not liste:
            satirlar.append("PENCERE YOK" if not pencere
                            else "PENCERE YOK: '%s'" % pencere)
            return {"ok": True, "metin": "\n".join(satirlar),
                    "pencere": [], "katman": durum().get("katman")}
        satirlar.append("PENCERELER (%d):" % len(liste))
        for p in liste[:25]:
            satirlar.append("  · %s  [%d,%d %dx%d]  #%s"
                            % (p["baslik"][:60], p["x"], p["y"],
                               p["w"], p["h"], p["id"]))
        nesneler = []
        if nesne:
            hedef = liste[0]
            nesneler, katman = cocuklar(hedef["id"])
            satirlar.append("NESNELER (%s · %d):" % (hedef["baslik"][:40],
                                                    len(nesneler)))
            for n in nesneler[:int(limit)]:
                satirlar.append("  · %s '%s'  @%d,%d  %dx%d"
                                % (n["tur"], n["ad"], n["x"], n["y"],
                                   n["w"], n["h"]))
        return {"ok": True, "metin": "\n".join(satirlar), "pencere": liste,
                "nesneler": nesneler, "katman": durum().get("katman")}

    return _onbellek(anahtar, uret)


def _puan(ad, aranan):
    a, b = ad.lower().strip(), aranan.lower().strip()
    if not a or not b:
        return 0
    if a == b:
        return 100
    if a.startswith(b):
        return 88
    if b in a:
        return 76
    # kelime bazlı kısmi eşleşme
    kelimeler = [k for k in re.split(r"[\s\.\-_/]+", a) if k]
    for k in kelimeler:
        if k.startswith(b) or b.startswith(k):
            return 60
    # harf dizisi (ör. "kyd" → "Kaydet")
    it = iter(a)
    if all(ch in it for ch in b):
        return 40
    return 0


def bul(aranan, pencere=""):
    """Nesne ağacında ara → en iyi eşleşme (koordinatıyla)."""
    if not aranan:
        return {"ok": False, "error": "Aranan metin boş."}
    liste = pencereler(pencere)
    adaylar = []
    katmanlar = set()
    # 1) Önce pencerenin kendi başlığı (hızlı kazanç)
    for p in liste:
        puan = _puan(p["baslik"], aranan)
        if puan:
            adaylar.append({"puan": puan - 5, "tur": "pencere",
                            "ad": p["baslik"], "x": p["x"] + p["w"] // 2,
                            "y": p["y"] + 12, "kaynak": "pencere"})
    # 2) Nesneler — ön plandaki pencereden başla
    hedefler = liste[:6]
    for p in hedefler:
        nesneler, katman = cocuklar(p["id"])
        katmanlar.add(katman)
        for n in nesneler:
            puan = _puan(n["ad"], aranan)
            if puan and n["w"] > 0 and n["h"] > 0:
                adaylar.append({"puan": puan, "tur": n["tur"], "ad": n["ad"],
                                "x": n["x"], "y": n["y"],
                                "kaynak": "nesne"})
        if len(adaylar) >= 12:
            break
    if not adaylar:
        return {"ok": False, "bulunamadi": True,
                "error": "'%s' nesne ağacında bulunamadı." % aranan,
                "katman": ",".join(sorted(katmanlar)) or durum().get("katman"),
                "hint": ("Ekran görüntüsü alıp okuyun ya da koordinatla click "
                         "kullanın. Bazı programlar nesne listesini gizler.")}
    adaylar.sort(key=lambda z: (-z["puan"], z["kaynak"] != "nesne"))
    en = adaylar[0]
    return {"ok": True, "bulundu": en,
            "diger": adaylar[1:4],
            "katman": ",".join(sorted(katmanlar)) or durum().get("katman"),
            "guven": ("yüksek" if en["puan"] >= 76 else
                      "orta" if en["puan"] >= 60 else "düşük")}


def metin_oku(pencere="", limit=80):
    """Ekrandaki tüm okunabilir yazılar — görüntü yerine metin."""
    r = ozet(pencere, nesne=True, limit=limit)
    yazilar = []
    for n in r.get("nesneler") or []:
        if n.get("tur") in ("yazı", "metin", "belge", "durum çubuğu") or \
                (len(n.get("ad") or "") > 12):
            yazilar.append(n["ad"])
    return {"ok": True, "yazilar": yazilar[:limit],
            "metin": "\n".join(yazilar[:limit])}

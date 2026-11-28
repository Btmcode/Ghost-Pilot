#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — screen.py
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Ekran yakalama + fare/klavye denetimi.
#  Windows: user32/GDI (yerleşik)   Linux: X11 XTEST (libXtst)   macOS: Quartz
#  Pillow İSTEĞE BAĞLI: varsa daha hızlı ve ölçeklenebilir, yoksa sistem
#  araçlarıyla çalışır. npm/pip zorunlu değildir.
# ============================================================================

import ctypes
import io
import os
import platform
import shutil
import subprocess
import tempfile
import time

OS_NAME = platform.system()
IS_WIN = OS_NAME == "Windows"
IS_MAC = OS_NAME == "Darwin"
IS_LINUX = OS_NAME == "Linux"

_NOTE = []


def _note(msg):
    if msg not in _NOTE:
        _NOTE.append(msg)


# ============================================================================
#  PILLOW (opsiyonel)
# ============================================================================

def _pil():
    try:
        from PIL import Image, ImageGrab  # noqa
        return Image, ImageGrab
    except Exception:
        return None, None


# ============================================================================
#  YAKALAMA
# ============================================================================

def _to_jpeg(img, max_width=None, quality=68):
    """PIL Image → JPEG bytes (ölçeklenmiş).

    HIZ NOTU: optimize=True Huffman tablolarını yeniden hesaplar ve yaklaşık
    %30-40 yavaşlatır. Ekran görüntüsünde boyut farkı küçük olduğu için
    kapalı. LANCZOS yerine BILINEAR: gözle fark yok, 2-3 kat hızlı.
    """
    Image, _ = _pil()
    if max_width and img.width > max_width:
        h = int(img.height * max_width / img.width)
        try:
            img = img.resize((max_width, h), Image.BILINEAR)
        except Exception:
            img = img.resize((max_width, h))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def _monitor_region(index=1):
    """N. monitörün {x,y,w,h} bölgesi (1 = birincil)."""
    try:
        import input_bg
        ms = input_bg.monitors()
        if not ms:
            return None
        i = max(1, int(index)) - 1
        if i >= len(ms):
            i = 0
        m = ms[i]
        return {"x": m["x"], "y": m["y"], "w": m["w"], "h": m["h"]}
    except Exception:
        return None


def _grab_pil(region=None):
    Image, ImageGrab = _pil()
    if not ImageGrab:
        return None
    try:
        box = None
        if region:
            x, y = int(region.get("x", 0)), int(region.get("y", 0))
            w, h = int(region.get("w", 0)), int(region.get("h", 0))
            if w > 0 and h > 0:
                box = (x, y, x + w, y + h)
        # all_screens pahalı; tek monitör varsa hızlı yolu kullan
        try:
            import ctypes
            n = ctypes.windll.user32.GetSystemMetrics(80) if IS_WIN else 1
        except Exception:
            n = 1
        if n and int(n) > 1:
            return ImageGrab.grab(bbox=box, all_screens=True)
        return ImageGrab.grab(bbox=box)
    except TypeError:
        try:
            return ImageGrab.grab(bbox=box)
        except Exception:
            return None
    except Exception:
        return None


def _ps(cmd_list, timeout=25):
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.run(cmd_list, capture_output=True, timeout=timeout, creationflags=flags)


def _grab_windows_ps(region=None):
    """Pillow yoksa: .NET ile ekran görüntüsü al (Windows'ta hazır)."""
    out = os.path.join(tempfile.gettempdir(), f"gp_shot_{os.getpid()}.png")
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms,System.Drawing;"
        "$b=[System.Windows.Forms.SystemInformation]::VirtualScreen;"
        f"$bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height;"
        "$g=[System.Drawing.Graphics]::FromImage($bmp);"
        "$g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size);"
        f"$bmp.Save('{out}',[System.Drawing.Imaging.ImageFormat]::Png);"
        "$g.Dispose();$bmp.Dispose()"
    )
    try:
        _ps(["powershell", "-NoProfile", "-Command", ps])
        if not os.path.exists(out):
            return None
        from PIL import Image  # varsa kırp/ölçekle
        img = Image.open(out)
        if region:
            x, y = int(region.get("x", 0)), int(region.get("y", 0))
            w, h = int(region.get("w", 0)), int(region.get("h", 0))
            if w > 0 and h > 0:
                img = img.crop((x, y, x + w, y + h))
        return img.copy()
    except Exception:
        # Pillow yok → PNG'yi olduğu gibi döndür
        try:
            return ("raw", out)
        except Exception:
            return None


def _grab_linux(region=None):
    if shutil.which("import"):
        out = os.path.join(tempfile.gettempdir(), f"gp_shot_{os.getpid()}.jpg")
        args = ["import", "-window", "root"]
        if region:
            x, y = int(region.get("x", 0)), int(region.get("y", 0))
            w, h = int(region.get("w", 0)), int(region.get("h", 0))
            if w > 0 and h > 0:
                args += ["-crop", f"{w}x{h}+{x}+{y}"]
        args.append(out)
        try:
            subprocess.run(args, capture_output=True, timeout=25)
            if os.path.exists(out):
                return ("raw", out)
        except Exception:
            pass
    return None


def _grab_mac(region=None):
    out = os.path.join(tempfile.gettempdir(), f"gp_shot_{os.getpid()}.jpg")
    args = ["screencapture", "-x", "-t", "jpg"]
    if region:
        x, y = int(region.get("x", 0)), int(region.get("y", 0))
        w, h = int(region.get("w", 0)), int(region.get("h", 0))
        if w > 0 and h > 0:
            args += ["-R", f"{x},{y},{w},{h}"]
    args.append(out)
    try:
        subprocess.run(args, capture_output=True, timeout=25)
        if os.path.exists(out):
            return ("raw", out)
    except Exception:
        pass
    return None


def screenshot(region=None, max_width=1280, monitor=None):
    max_width = int(max_width or 1280)
    if monitor and not region:
        region = _monitor_region(monitor) or None
    # 1) Pillow varsa her platformda en iyi yol
    img = _grab_pil(region)
    if img is not None:
        jpg = _to_jpeg(img, max_width)
        return {"ok": True, "format": "jpeg", "width": img.width, "height": img.height,
                "base64": __import__("base64").b64encode(jpg).decode(),
                "bytes": len(jpg), "backend": "pillow"}

    # 2) Sistem araçları
    if IS_WIN:
        got = _grab_windows_ps(region)
    elif IS_MAC:
        got = _grab_mac(region)
    else:
        got = _grab_linux(region)

    if isinstance(got, tuple) and got[0] == "raw":
        path = got[1]
        try:
            data = open(path, "rb").read()
            if not data:
                return {"ok": False, "error": "Ekran görüntüsü boş döndü."}
            # ölçekleme yalnız Pillow/ImageMagick varsa
            Image, _ = _pil()
            if Image and max_width:
                try:
                    im = Image.open(io.BytesIO(data))
                    jpg = _to_jpeg(im, max_width)
                    return {"ok": True, "format": "jpeg", "width": im.width, "height": im.height,
                            "base64": __import__("base64").b64encode(jpg).decode(),
                            "bytes": len(jpg), "backend": "system+pillow"}
                except Exception:
                    pass
            fmt = "jpeg" if path.endswith(".jpg") else "png"
            return {"ok": True, "format": fmt, "base64": __import__("base64").b64encode(data).decode(),
                    "bytes": len(data), "backend": "system"}
        finally:
            try:
                os.remove(path)
            except Exception:
                pass

    return {"ok": False,
            "error": "Ekran yakalanamadı (görüntü sunucusu yok veya izin eksik).",
            "hint": "Windows: normal masaüstü oturumunda çalıştırın · "
                    "Linux: X11 oturumu gerekir (Wayland'da sınırlı) · "
                    "macOS: Ekran Kaydı izni verin. "
                    "Alternatif: pip install pillow"}


# ============================================================================
#  GİRDİ — Windows (user32 / SendInput)
# ============================================================================

_WIN_READY = False


def _win_init():
    global _WIN_READY
    if _WIN_READY or not IS_WIN:
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    _WIN_READY = True


if IS_WIN:
    ULONG_PTR = ctypes.wintypes.ULONG_PTR if hasattr(ctypes, "wintypes") else ctypes.c_ulonglong

    class _MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                    ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                    ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

    class _KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                    ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

    class _HARDWAREINPUT(ctypes.Structure):
        _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_ushort),
                    ("wParamH", ctypes.c_ushort)]

    class _INPUTUNION(ctypes.Union):
        _fields_ = [("mi", _MOUSEINPUT), ("ki", _KEYBDINPUT), ("hi", _HARDWAREINPUT)]

    class _INPUT(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong), ("u", _INPUTUNION)]

    _VK = {
        "enter": 0x0D, "return": 0x0D, "tab": 0x09, "esc": 0x1B, "escape": 0x1B,
        "space": 0x20, "backspace": 0x08, "delete": 0x2E, "del": 0x2E, "insert": 0x2D,
        "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
        "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
        "ctrl": 0x11, "control": 0x11, "alt": 0x12, "shift": 0x10, "win": 0x5B,
        "printscreen": 0x2C, "capslock": 0x14,
        **{f"f{i}": 0x6F + i for i in range(1, 13)},
    }

    def _win_send_inputs(inputs):
        n = len(inputs)
        arr = (_INPUT * n)(*inputs)
        ctypes.windll.user32.SendInput(n, arr, ctypes.sizeof(_INPUT))

    def _win_unicode_char(ch):
        units = ch.encode("utf-16-le")
        out = []
        for i in range(0, len(units), 2):
            scan = int.from_bytes(units[i:i + 2], "little")
            for flag in (0x0004, 0x0004 | 0x0002):  # KEYDOWN/KEYUP + UNICODE
                inp = _INPUT(type=1)
                inp.u.ki = _KEYBDINPUT(wVk=0, wScan=scan, dwFlags=flag, time=0, dwExtraInfo=None)
                out.append(inp)
        return out

    def _win_mouse(flags, data=0, dx=0, dy=0):
        inp = _INPUT(type=0)
        inp.u.mi = _MOUSEINPUT(dx=dx, dy=dy, mouseData=data,
                               dwFlags=flags, time=0, dwExtraInfo=None)
        _win_send_inputs([inp])


XR_OK, XR_ERR = 0, 1


# ============================================================================
#  GİRDİ — Linux (X11 XTEST)
# ============================================================================

_X = {"ok": None, "dpy": None, "xtst": None, "xlib": None}


def _x11():
    if _X["ok"] is not None:
        return _X["ok"]
    try:
        xlib = ctypes.CDLL("libX11.so.6")
        xtst = ctypes.CDLL("libXtst.so.6")
        xlib.XOpenDisplay.restype = ctypes.c_void_p
        xlib.XOpenDisplay.argtypes = [ctypes.c_char_p]
        dpy = xlib.XOpenDisplay(None)
        if not dpy:
            _X["ok"] = False
            _note("X11 görüntü sunucusuna bağlanılamadı (DISPLAY boş).")
            return False
        _X.update(ok=True, dpy=dpy, xtst=xtst, xlib=xlib)
        return True
    except Exception as e:
        _X["ok"] = False
        _note(f"X11 XTEST yüklenemedi: {e}")
        return False


def _xflush():
    try:
        _X["xlib"].XFlush(ctypes.c_void_p(_X["dpy"]))
    except Exception:
        pass


_XKEYSYM = {
    "enter": 0xFF0D, "return": 0xFF0D, "tab": 0xFF09, "esc": 0xFF1B, "escape": 0xFF1B,
    "space": 0x0020, "backspace": 0xFF08, "delete": 0xFFFF, "del": 0xFFFF,
    "insert": 0xFF63, "up": 0xFF52, "down": 0xFF54, "left": 0xFF51, "right": 0xFF53,
    "home": 0xFF50, "end": 0xFF57, "pageup": 0xFF55, "pagedown": 0xFF56,
    "ctrl": 0xFFE3, "control": 0xFFE3, "alt": 0xFFE9, "shift": 0xFFE1, "super": 0xFFEB,
    "win": 0xFFEB, "printscreen": 0xFF61,
    **{f"f{i}": 0xFFBE + i - 1 for i in range(1, 13)},
}


def _x_keycode(keysym):
    try:
        lib = _X["xlib"]
        lib.XKeysymToKeycode.restype = ctypes.c_ubyte
        lib.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        return int(lib.XKeysymToKeycode(ctypes.c_void_p(_X["dpy"]), ctypes.c_ulong(keysym)))
    except Exception:
        return 0


def _x_press_keycode(kc, down):
    try:
        _X["xtst"].XTestFakeKeyEvent(ctypes.c_void_p(_X["dpy"]),
                                     ctypes.c_uint(kc), ctypes.c_int(1 if down else 0),
                                     ctypes.c_ulong(0))
        _xflush()
    except Exception:
        pass


# ============================================================================
#  GİRDİ — macOS (Quartz)
# ============================================================================

_QC = {"ok": None, "cg": None, "cf": None}


def _quartz():
    if _QC["ok"] is not None:
        return _QC["ok"]
    if not IS_MAC:
        _QC["ok"] = False
        return False
    try:
        cg = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
        cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        cg.CGEventCreateMouseEvent.restype = ctypes.c_void_p
        cg.CGEventCreateKeyboardEvent.restype = ctypes.c_void_p
        cg.CGEventPost.argtypes = [ctypes.c_int, ctypes.c_void_p]
        _QC.update(ok=True, cg=cg, cf=cf)
        return True
    except Exception as e:
        _QC["ok"] = False
        _note(f"Quartz yüklenemedi: {e}")
        return False


class _CGPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


_MAC_VK = {
    "enter": 0x24, "return": 0x24, "tab": 0x30, "esc": 0x35, "escape": 0x35,
    "space": 0x31, "backspace": 0x33, "delete": 0x75, "del": 0x75,
    "left": 0x7B, "right": 0x7C, "down": 0x7D, "up": 0x7E,
    "home": 0x73, "end": 0x77, "pageup": 0x74, "pagedown": 0x79,
    "ctrl": 0x3B, "alt": 0x3A, "shift": 0x38, "cmd": 0x37, "win": 0x37,
    **{f"f{i}": 0x7A + i - 1 for i in range(1, 13)},
}
_MAC_FLAGS = {"shift": 1 << 17, "ctrl": 1 << 18, "alt": 1 << 19, "cmd": 1 << 20, "win": 1 << 20}


# ============================================================================
#  ORTAK API
# ============================================================================

def _parse_combo(combo):
    parts = [p.strip().lower() for p in str(combo).replace(" ", "").split("+") if p.strip()]
    if not parts:
        return [], ""
    return parts[:-1], parts[-1]


def move(x, y):
    x, y = int(x), int(y)
    if IS_WIN:
        _win_init()
        ctypes.windll.user32.SetCursorPos(x, y)
        return {"ok": True, "x": x, "y": y, "backend": "user32"}
    if IS_MAC and _quartz():
        cg = _QC["cg"]
        ev = cg.CGEventCreateMouseEvent(None, 5, _CGPoint(x, y), 0)
        cg.CGEventPost(0, ev)
        return {"ok": True, "x": x, "y": y, "backend": "quartz"}
    if IS_LINUX and _x11():
        try:
            _X["xtst"].XTestFakeMotionEvent(ctypes.c_void_p(_X["dpy"]), ctypes.c_int(-1),
                                            ctypes.c_int(x), ctypes.c_int(y), ctypes.c_ulong(0))
            _xflush()
            return {"ok": True, "x": x, "y": y, "backend": "xtest"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    return {"ok": False, "error": "Fare denetimi bu makinede kullanılamıyor."}


def click(x, y, button="left", double=False):
    btn = 1 if button == "left" else 3 if button == "right" else 2
    if IS_WIN:
        _win_init()
        ctypes.windll.user32.SetCursorPos(int(x), int(y))
        flags = {"left": (0x0002, 0x0004), "right": (0x0008, 0x0010),
                 "middle": (0x0020, 0x0040)}[button]
        for _ in range(2 if double else 1):
            _win_mouse(flags[0])
            _win_mouse(flags[1])
            if double:
                time.sleep(0.01)
        return {"ok": True, "x": int(x), "y": int(y), "button": button,
                "double": bool(double), "backend": "user32"}
    if IS_MAC and _quartz():
        cg = _QC["cg"]
        down, up = {"left": (1, 2), "right": (3, 4), "middle": (25, 26)}[button]
        cg.CGEventPost(0, cg.CGEventCreateMouseEvent(None, 5, _CGPoint(x, y), 0))
        for _ in range(2 if double else 1):
            cg.CGEventPost(0, cg.CGEventCreateMouseEvent(None, down, _CGPoint(x, y), btn - 1))
            cg.CGEventPost(0, cg.CGEventCreateMouseEvent(None, up, _CGPoint(x, y), btn - 1))
            time.sleep(0.05)
        return {"ok": True, "x": int(x), "y": int(y), "button": button,
                "double": bool(double), "backend": "quartz"}
    if IS_LINUX and _x11():
        move(x, y)
        try:
            for _ in range(2 if double else 1):
                _X["xtst"].XTestFakeButtonEvent(ctypes.c_void_p(_X["dpy"]),
                                                ctypes.c_uint(btn), ctypes.c_int(1),
                                                ctypes.c_ulong(0))
                _X["xtst"].XTestFakeButtonEvent(ctypes.c_void_p(_X["dpy"]),
                                                ctypes.c_uint(btn), ctypes.c_int(0),
                                                ctypes.c_ulong(0))
                _xflush()
                if double:
                    time.sleep(0.02)
            return {"ok": True, "x": int(x), "y": int(y), "button": button,
                    "double": bool(double), "backend": "xtest"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    return {"ok": False, "error": "Tıklama bu makinede kullanılamıyor."}


def drag(x1, y1, x2, y2):
    move(x1, y1)
    time.sleep(0.05)
    if IS_WIN:
        _win_mouse(0x0002)
        for i in range(1, 9):
            nx = int(x1 + (x2 - x1) * i / 8)
            ny = int(y1 + (y2 - y1) * i / 8)
            ctypes.windll.user32.SetCursorPos(nx, ny)
            time.sleep(0.006)
        _win_mouse(0x0004)
        return {"ok": True, "from": [int(x1), int(y1)], "to": [int(x2), int(y2)],
                "backend": "user32"}
    if IS_MAC and _quartz():
        cg = _QC["cg"]
        cg.CGEventPost(0, cg.CGEventCreateMouseEvent(None, 1, _CGPoint(x1, y1), 0))
        for i in range(1, 21):
            nx = x1 + (x2 - x1) * i / 20
            ny = y1 + (y2 - y1) * i / 20
            cg.CGEventPost(0, cg.CGEventCreateMouseEvent(None, 6, _CGPoint(nx, ny), 0))
            time.sleep(0.012)
        cg.CGEventPost(0, cg.CGEventCreateMouseEvent(None, 2, _CGPoint(x2, y2), 0))
        return {"ok": True, "from": [int(x1), int(y1)], "to": [int(x2), int(y2)],
                "backend": "quartz"}
    if IS_LINUX and _x11():
        try:
            _X["xtst"].XTestFakeButtonEvent(ctypes.c_void_p(_X["dpy"]), ctypes.c_uint(1),
                                            ctypes.c_int(1), ctypes.c_ulong(0))
            _xflush()
            for i in range(1, 21):
                nx = int(x1 + (x2 - x1) * i / 20)
                ny = int(y1 + (y2 - y1) * i / 20)
                _X["xtst"].XTestFakeMotionEvent(ctypes.c_void_p(_X["dpy"]), ctypes.c_int(-1),
                                                ctypes.c_int(nx), ctypes.c_int(ny),
                                                ctypes.c_ulong(0))
                _xflush()
                time.sleep(0.012)
            _X["xtst"].XTestFakeButtonEvent(ctypes.c_void_p(_X["dpy"]), ctypes.c_uint(1),
                                            ctypes.c_int(0), ctypes.c_ulong(0))
            _xflush()
            return {"ok": True, "from": [int(x1), int(y1)], "to": [int(x2), int(y2)],
                    "backend": "xtest"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    return {"ok": False, "error": "Sürükleme kullanılamıyor."}


def scroll(amount=-3, x=0, y=0):
    amount = int(amount)
    if x or y:
        move(x, y)
    if IS_WIN:
        _win_init()
        _win_mouse(0x0800, data=ctypes.c_ulong(amount * 120).value & 0xFFFFFFFF)
        return {"ok": True, "amount": amount, "backend": "user32"}
    if IS_MAC and _quartz():
        cg = _QC["cg"]
        cg.CGEventCreateScrollWheelEvent.restype = ctypes.c_void_p
        ev = cg.CGEventCreateScrollWheelEvent(None, 1, 1, ctypes.c_int32(amount))
        cg.CGEventPost(0, ev)
        return {"ok": True, "amount": amount, "backend": "quartz"}
    if IS_LINUX and _x11():
        btn = 4 if amount > 0 else 5
        try:
            for _ in range(abs(amount)):
                for down in (1, 0):
                    _X["xtst"].XTestFakeButtonEvent(ctypes.c_void_p(_X["dpy"]),
                                                    ctypes.c_uint(btn), ctypes.c_int(down),
                                                    ctypes.c_ulong(0))
                _xflush()
                time.sleep(0.02)
            return {"ok": True, "amount": amount, "backend": "xtest"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    return {"ok": False, "error": "Kaydırma kullanılamıyor."}


def type_text(text):
    text = str(text)
    if not text:
        return {"ok": True, "typed": 0}
    if IS_WIN:
        _win_init()
        inputs = []
        for ch in text:
            if ch == "\n":
                inputs += _win_key_vk("enter")
            elif ch == "\t":
                inputs += _win_key_vk("tab")
            else:
                inputs += _win_unicode_char(ch)
        if inputs:
            _win_send_inputs(inputs)
        return {"ok": True, "typed": len(text), "backend": "user32-sendinput"}
    if IS_MAC and _quartz():
        cg, cf = _QC["cg"], _QC["cf"]
        for ch in text:
            kc = _MAC_VK.get("enter") if ch == "\n" else None
            ev = cg.CGEventCreateKeyboardEvent(None, kc or 0, True)
            if not kc:
                buf = ctypes.create_string_buffer(ch.encode("utf-16-be"))
                cf.CFStringCreateWithBytes.restype = ctypes.c_void_p
                s = cf.CFStringCreateWithBytes(None, buf, len(ch.encode("utf-16-be")), 0x0100, False)
                cg.CGEventKeyboardSetUnicodeString(ev, ctypes.c_long(1),
                                                   ctypes.byref(ctypes.c_ushort(ord(ch))))
            cg.CGEventPost(0, ev)
            cg.CGEventPost(0, cg.CGEventCreateKeyboardEvent(None, kc or 0, False))
            time.sleep(0.004)
        return {"ok": True, "typed": len(text), "backend": "quartz"}
    if IS_LINUX and _x11():
        ok = 0
        for ch in text:
            ks = 0x0000 + ord(ch) if ord(ch) < 0x100 else 0x01000000 + ord(ch)
            kc = _x_keycode(ks)
            if not kc:
                kc = _x_keycode(ord(ch) if ord(ch) < 128 else 0)
            if kc:
                _x_press_keycode(kc, True)
                _x_press_keycode(kc, False)
                ok += 1
                # HIZ: tek karakterde bile bekleme yok; X sunucusu sırayı korur
        _xflush()
        return {"ok": ok > 0, "typed": ok, "backend": "xtest",
                **({} if ok else {"error": "Karakterler tuş eşlemesine çevrilemedi (klavye düzeni?)."})}
    return {"ok": False, "error": "Metin yazma kullanılamıyor."}


def _win_key_vk(name):
    vk = _VK.get(str(name).lower())
    if not vk:
        return []
    out = []
    for flag in (0, 0x0002):
        inp = _INPUT(type=1)
        inp.u.ki = _KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flag, time=0, dwExtraInfo=None)
        out.append(inp)
    return out


def key(combo):
    mods, main = _parse_combo(combo)
    if not main:
        return {"ok": False, "error": "Tuş belirtilmedi (örn. ctrl+c)."}
    if IS_WIN:
        _win_init()
        seq = []
        for m in mods:
            seq += [_INPUT(type=1) for _ in _win_key_vk(m)]
        vk_main = _VK.get(main)
        if not vk_main:
            if len(main) == 1:
                seq += _win_unicode_char(main)
            else:
                return {"ok": False, "error": f"Bilinmeyen tuş: {main}"}
        else:
            seq += _win_key_vk(main)
        for m in reversed(mods):
            pass
        if seq:
            _win_send_inputs(seq)
        # modifier'ları bırak
        ups = []
        for m in mods:
            vk = _VK.get(m)
            if vk:
                inp = _INPUT(type=1)
                inp.u.ki = _KEYBDINPUT(wVk=vk, wScan=0, dwFlags=0x0002, time=0, dwExtraInfo=None)
                ups.append(inp)
        if ups:
            _win_send_inputs(ups)
        return {"ok": True, "combo": combo, "backend": "user32"}
    if IS_MAC and _quartz():
        cg = _QC["cg"]
        flags = 0
        for m in mods:
            flags |= _MAC_FLAGS.get(m, 0)
        vk = _MAC_VK.get(main)
        if vk is None:
            if len(main) == 1:
                return type_text(main)
            return {"ok": False, "error": f"Bilinmeyen tuş: {main}"}
        for down in (True, False):
            ev = cg.CGEventCreateKeyboardEvent(None, vk, down)
            if flags:
                cg.CGEventSetFlags(ev, flags)
            cg.CGEventPost(0, ev)
        return {"ok": True, "combo": combo, "backend": "quartz"}
    if IS_LINUX and _x11():
        codes = []
        for m in mods:
            ks = _XKEYSYM.get(m)
            if ks:
                codes.append(_x_keycode(ks))
        ks_main = _XKEYSYM.get(main)
        if ks_main is None and len(main) == 1:
            ks_main = ord(main)
        kc_main = _x_keycode(ks_main) if ks_main else 0
        if not kc_main:
            return {"ok": False, "error": f"Bilinmeyen tuş: {main}"}
        for kc in codes:
            _x_press_keycode(kc, True)
        _x_press_keycode(kc_main, True)
        _x_press_keycode(kc_main, False)
        for kc in reversed(codes):
            _x_press_keycode(kc, False)
        return {"ok": True, "combo": combo, "backend": "xtest"}
    return {"ok": False, "error": "Tuş basma kullanılamıyor."}


# ============================================================================
#  YETENEKLER
# ============================================================================

def _screen_size():
    if IS_WIN:
        try:
            _win_init()
            u = ctypes.windll.user32
            return {"w": u.GetSystemMetrics(0), "h": u.GetSystemMetrics(1)}
        except Exception:
            return None
    if IS_MAC:
        try:
            r = subprocess.run(["system_profiler", "SPDisplaysDataType"],
                               capture_output=True, timeout=20)
            for line in r.stdout.decode("utf-8", "replace").splitlines():
                if "Resolution" in line:
                    part = line.split(":")[1].strip().split(" ")[0].split("x")
                    if len(part) == 2:
                        return {"w": int(part[0]), "h": int(part[1])}
        except Exception:
            return None
        return None
    if IS_LINUX and _x11():
        try:
            lib = _X["xlib"]
            w, h, w_mm, h_mm = (ctypes.c_int() for _ in range(4))
            lib.XDefaultScreen.argtypes = [ctypes.c_void_p]
            scr = lib.XDefaultScreen(ctypes.c_void_p(_X["dpy"]))
            lib.XDisplayWidth.argtypes = [ctypes.c_void_p, ctypes.c_int]
            lib.XDisplayHeight.argtypes = [ctypes.c_void_p, ctypes.c_int]
            return {"w": int(lib.XDisplayWidth(ctypes.c_void_p(_X["dpy"]), scr)),
                    "h": int(lib.XDisplayHeight(ctypes.c_void_p(_X["dpy"]), scr))}
        except Exception:
            return None
    return None


def capabilities():
    Image, ImageGrab = _pil()
    screen_ok, screen_backend = False, None
    if ImageGrab is not None:
        screen_ok, screen_backend = True, "pillow"
    elif IS_MAC and shutil.which("screencapture"):
        screen_ok, screen_backend = True, "screencapture"
    elif IS_LINUX and shutil.which("import"):
        screen_ok, screen_backend = True, "imagemagick"
    elif IS_WIN:
        screen_ok, screen_backend = True, "powershell-gdi"

    input_ok, input_backend = False, None
    if IS_WIN:
        input_ok, input_backend = True, "user32"
    elif IS_MAC and _quartz():
        input_ok, input_backend = True, "quartz"
    elif IS_LINUX and _x11():
        input_ok, input_backend = True, "xtest"

    size = _screen_size() if (screen_ok or input_ok) else None
    return {
        "screen": screen_ok,
        "input": input_ok,
        "screen_backend": screen_backend,
        "input_backend": input_backend,
        "requires_cursor": bool(IS_WIN or IS_MAC),
        "size": size,
        "note": " · ".join(_NOTE),
    }


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(capabilities(), indent=2, ensure_ascii=False))

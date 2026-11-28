#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — input_bg.py
#  Copyright (c) 2026 BTM Code — MIT License
#
#  ARKA PLAN GİRDİSİ — farenizi ve klavyenizi ELE GEÇİRMEZ
#
#  Sorun: SendInput / XTEST / Quartz girdileri SİSTEM imlecini oynatır.
#  Siz bir şey yazarken ajan da yazarsa çakışır, imleç zıplar.
#
#  Çözüm — platforma göre:
#    Windows : SendInput + "pause guard"  → kullanıcı girdi yaparken bekler,
#              hedef pencereye odaklanır, imleci geri bırakır
#    Linux   : XTEST + pause guard (X11'de gerçek MPX yoksa)
#    macOS   : Quartz
#
#  EŞZAMANLI MOD (v5.1): ajan ARTIK BEKLEMEZ — sizinle aynı anda çalışır.
#    · Gerçek imleciniz HİÇ oynatılmaz (bkz. bg_click / bg_type).
#    · Ekranda görünür bir HAYALET imleç + şerit vardır (goverlay.py).
#    · İsterseniz "wait_for_user" parametresiyle eski bekleme davranışı.
# ============================================================================

import ctypes
import platform
import threading
import time

OS_NAME = platform.system()
IS_WIN = OS_NAME == "Windows"
IS_MAC = OS_NAME == "Darwin"
IS_LINUX = OS_NAME == "Linux"

# Kullanıcı son bu kadar saniye içinde girdi yaptıysa ajan bekler
USER_IDLE_REQUIRED = 0.45
# En fazla bu kadar bekler, sonra devam eder (kilitlenmesin)
MAX_WAIT = 2.0

_lock = threading.Lock()
_stats = {"waited": 0.0, "times": 0, "aborted": 0}


# ============================================================================
#  KULLANICI GİRDİ TESPİTİ
# ============================================================================

if IS_WIN:
    class _LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

    def last_input_age():
        """Kullanıcının son girdisinden bu yana geçen saniye."""
        try:
            li = _LASTINPUTINFO()
            li.cbSize = ctypes.sizeof(_LASTINPUTINFO)
            if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(li)):
                return 999.0
            now = ctypes.windll.kernel32.GetTickCount()
            return max(0.0, ((now - li.dwTime) & 0xFFFFFFFF) / 1000.0)
        except Exception:
            return 999.0

    def cursor_pos():
        try:
            pt = ctypes.wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            return int(pt.x), int(pt.y)
        except Exception:
            return None

elif IS_LINUX:
    _XL = {"ok": None, "dpy": None, "lib": None}

    def _xlib():
        if _XL["ok"] is not None:
            return _XL["ok"]
        try:
            import ctypes.util
            lib = ctypes.CDLL("libX11.so.6")
            lib.XOpenDisplay.restype = ctypes.c_void_p
            lib.XOpenDisplay.argtypes = [ctypes.c_char_p]
            dpy = lib.XOpenDisplay(None)
            if not dpy:
                _XL["ok"] = False
                return False
            _XL.update(ok=True, dpy=dpy, lib=lib)
            return True
        except Exception:
            _XL["ok"] = False
            return False

    class _XQueryKeymap(ctypes.Structure):
        _fields_ = [("key", ctypes.c_char * 32)]

    def last_input_age():
        """X11'de 'son girdi zamanı' API'si yok; tuş durumuna bakarız."""
        if not _xlib():
            return 999.0
        try:
            lib, dpy = _XL["lib"], ctypes.c_void_p(_XL["dpy"])
            # imleç konumu son 300 ms içinde değiştiyse kullanıcı aktif
            lib.XQueryPointer.restype = ctypes.c_int
            root = ctypes.c_ulong()
            child = ctypes.c_ulong()
            rx = ctypes.c_int()
            ry = ctypes.c_int()
            wx = ctypes.c_int()
            wy = ctypes.c_int()
            mask = ctypes.c_uint()
            lib.XQueryPointer(dpy, lib.XDefaultRootWindow(dpy), ctypes.byref(root),
                              ctypes.byref(child), ctypes.byref(rx), ctypes.byref(ry),
                              ctypes.byref(wx), ctypes.byref(wy), ctypes.byref(mask))
            pos = (rx.value, ry.value)
            prev = _XL.get("pos")
            _XL["pos"] = pos
            if prev is not None and prev != pos:
                _XL["moved"] = time.time()
            return max(0.0, time.time() - _XL.get("moved", 0))
        except Exception:
            return 999.0

    def cursor_pos():
        if not _xlib():
            return None
        try:
            lib, dpy = _XL["lib"], ctypes.c_void_p(_XL["dpy"])
            root = ctypes.c_ulong(); child = ctypes.c_ulong()
            rx = ctypes.c_int(); ry = ctypes.c_int(); wx = ctypes.c_int(); wy = ctypes.c_int()
            mask = ctypes.c_uint()
            lib.XQueryPointer(dpy, lib.XDefaultRootWindow(dpy), ctypes.byref(root),
                              ctypes.byref(child), ctypes.byref(rx), ctypes.byref(ry),
                              ctypes.byref(wx), ctypes.byref(wy), ctypes.byref(mask))
            return int(rx.value), int(ry.value)
        except Exception:
            return None

else:  # macOS
    def last_input_age():
        try:
            cg = ctypes.CDLL(
                "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
            cg.CGEventSourceSecondsSinceLastEventType.restype = ctypes.c_double
            # 0xFFFFFFFF = kCGAnyInputEventType
            return float(cg.CGEventSourceSecondsSinceLastEventType(0, 0xFFFFFFFF))
        except Exception:
            return 999.0

    def cursor_pos():
        try:
            cg = ctypes.CDLL(
                "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")

            class P(ctypes.Structure):
                _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]
            p = P()
            cg.CGEventGetLocation.restype = P
            ev = cg.CGEventCreate(None)
            p = cg.CGEventGetLocation(ev)
            return int(p.x), int(p.y)
        except Exception:
            return None


# ============================================================================
#  BEKLEME (pause guard)
# ============================================================================

class Busy(Exception):
    """Kullanıcı bilgisayarı kullanıyor — ajan bekledi ve vazgeçti."""


def wait_until_user_idle(required=USER_IDLE_REQUIRED, maximum=MAX_WAIT, force=False):
    """Kullanıcı girdi yapmayı bırakana kadar bekler.

    force=True → hiç beklemez (kullanıcı açıkça istediğinde).
    Dönüş: beklenen saniye.
    """
    if force:
        return 0.0
    t0 = time.time()
    while True:
        age = last_input_age()
        if age >= required:
            waited = time.time() - t0
            if waited > 0.05:
                with _lock:
                    _stats["waited"] += waited
                    _stats["times"] += 1
            return waited
        if time.time() - t0 >= maximum:
            with _lock:
                _stats["aborted"] += 1
            raise Busy(
                f"Bilgisayarı kullanıyorsunuz (son girdi {age:.1f}s önce). "
                f"{maximum:.0f} saniye bekledim, vazgeçtim. "
                f"Birkaç saniye bekleyip tekrar deneyin veya force=true verin.")
        time.sleep(0.05)


def guard(fn, *a, **kw):
    """Bir girdi işlemini bekleyerek çalıştırır (kısayol)."""
    force = kw.pop("force", False)
    wait_until_user_idle(force=force)
    return fn(*a, **kw)


def stats():
    return dict(_stats)


# ============================================================================
#  İMLECİ KORU — işlem bitince kullanıcının imleci yerine dönsün
# ============================================================================

class CursorRestore:
    """with CursorRestore(): ... → blok bitince imleç eski yerine gelir."""

    def __init__(self, enabled=True):
        # Linux'ta da geri koyma yapılır: ajan hızlıca tıklayıp imleci bırakır
        self.enabled = bool(enabled)
        self.pos = None

    def __enter__(self):
        if self.enabled:
            self.pos = cursor_pos()
        return self

    def __exit__(self, *exc):
        if self.enabled and self.pos:
            try:
                import screen
                screen.move(self.pos[0], self.pos[1])
            except Exception:
                pass
        return False


# ============================================================================
#  PENCERE ODAĞI (Windows) — ajan doğru pencereye yazsın
# ============================================================================

if IS_WIN:
    def window_list():
        """Görünür, başlıklı pencereler."""
        out = []
        try:
            user32 = ctypes.windll.user32
            EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p,
                                          ctypes.c_void_p)

            def cb(hwnd, _lp):
                if not user32.IsWindowVisible(hwnd):
                    return True
                n = user32.GetWindowTextLengthW(hwnd)
                if n <= 0:
                    return True
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                title = buf.value.strip()
                if title and title not in ("Program Manager", "Start"):
                    out.append({"hwnd": int(hwnd), "title": title})
                return True

            user32.EnumWindows(EnumProc(cb), None)
        except Exception:
            pass
        return out

    def window_focus(match):
        """Başlığı 'match' içeren pencereyi öne getirir."""
        import re
        try:
            user32 = ctypes.windll.user32
            target = None
            for w in window_list():
                if re.search(re.escape(match), w["title"], re.I):
                    target = w["hwnd"]
                    break
            if not target:
                return {"ok": False, "error": f"Pencere bulunamadı: {match}"}
            if user32.IsIconic(target):
                user32.ShowWindow(target, 9)   # SW_RESTORE
            user32.SetForegroundWindow(target)
            time.sleep(0.25)
            return {"ok": True, "hwnd": target}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def window_minimize(match):
        import re
        try:
            user32 = ctypes.windll.user32
            for w in window_list():
                if re.search(re.escape(match), w["title"], re.I):
                    user32.ShowWindow(w["hwnd"], 6)  # SW_MINIMIZE
                    return {"ok": True, "hwnd": w["hwnd"]}
            return {"ok": False, "error": f"Pencere bulunamadı: {match}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def active_window():
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            n = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            return {"hwnd": int(hwnd), "title": buf.value}
        except Exception as e:
            return {"error": str(e)}

else:
    def window_list():
        return []

    def window_focus(match):
        return {"ok": False, "error": "Pencere yönetimi şu an yalnız Windows'ta."}

    def window_minimize(match):
        return {"ok": False, "error": "Pencere yönetimi şu an yalnız Windows'ta."}

    def active_window():
        return {"title": "", "error": "Yalnız Windows"}


# ============================================================================
#  PANO (clipboard)
# ============================================================================

def clipboard_get():
    try:
        if IS_WIN:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            CF_UNICODETEXT = 13
            if not user32.OpenClipboard(None):
                return {"ok": False, "error": "Pano açılamadı."}
            try:
                h = user32.GetClipboardData(CF_UNICODETEXT)
                if not h:
                    return {"ok": True, "text": ""}
                ptr = kernel32.GlobalLock(h)
                text = ctypes.wstring_at(ptr)
                kernel32.GlobalUnlock(h)
                return {"ok": True, "text": text}
            finally:
                user32.CloseClipboard()
        if IS_MAC:
            import subprocess
            r = subprocess.run(["pbpaste"], capture_output=True, timeout=10)
            return {"ok": True, "text": r.stdout.decode("utf-8", "replace")}
        import shutil
        import subprocess
        for cmd in (["xclip", "-selection", "clipboard", "-o"],
                    ["xsel", "--clipboard", "--output"],
                    ["wl-paste"]):
            if shutil.which(cmd[0]):
                r = subprocess.run(cmd, capture_output=True, timeout=10)
                return {"ok": True, "text": r.stdout.decode("utf-8", "replace")}
        return {"ok": False, "error": "Pano aracı yok (xclip/xsel/wl-paste)."}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def clipboard_set(text):
    try:
        text = "" if text is None else str(text)
        if IS_WIN:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            kernel32.GlobalAlloc.restype = ctypes.c_void_p
            kernel32.GlobalLock.restype = ctypes.c_void_p
            GMEM_MOVEABLE = 0x0002
            CF_UNICODETEXT = 13
            data = ctypes.create_unicode_buffer(text)
            size = ctypes.sizeof(data)
            h = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
            ptr = kernel32.GlobalLock(ctypes.c_void_p(h))
            ctypes.memmove(ptr, data, size)
            kernel32.GlobalUnlock(ctypes.c_void_p(h))
            if not user32.OpenClipboard(None):
                return {"ok": False, "error": "Pano açılamadı."}
            try:
                user32.EmptyClipboard()
                user32.SetClipboardData(CF_UNICODETEXT, ctypes.c_void_p(h))
            finally:
                user32.CloseClipboard()
            return {"ok": True, "chars": len(text)}
        if IS_MAC:
            import subprocess
            p = subprocess.run(["pbcopy"], input=text.encode("utf-8"), timeout=10)
            return {"ok": p.returncode == 0, "chars": len(text)}
        import shutil
        import subprocess
        for cmd in (["xclip", "-selection", "clipboard"],
                    ["xsel", "--clipboard", "--input"],
                    ["wl-copy"]):
            if shutil.which(cmd[0]):
                p = subprocess.run(cmd, input=text.encode("utf-8"), timeout=10)
                return {"ok": p.returncode == 0, "chars": len(text)}
        return {"ok": False, "error": "Pano aracı yok (xclip/xsel/wl-copy)."}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ============================================================================
#  MONİTÖRLER
# ============================================================================

def monitors():
    out = []
    try:
        if IS_WIN:
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()

            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                            ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

            class MONITORINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_ulong), ("rcMonitor", RECT),
                            ("rcWork", RECT), ("dwFlags", ctypes.c_ulong)]

            Proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p,
                                      ctypes.c_void_p, ctypes.POINTER(RECT), ctypes.c_void_p)
            acc = []

            def cb(hmon, hdc, lprc, data):
                mi = MONITORINFO()
                mi.cbSize = ctypes.sizeof(MONITORINFO)
                if user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
                    r = mi.rcMonitor
                    acc.append({
                        "x": r.left, "y": r.top,
                        "w": r.right - r.left, "h": r.bottom - r.top,
                        "primary": bool(mi.dwFlags & 1),
                    })
                return True

            user32.EnumDisplayMonitors(None, None, Proc(cb), None)
            out = acc
        elif IS_LINUX:
            import shutil
            import subprocess
            if shutil.which("xrandr"):
                r = subprocess.run(["xrandr", "--current"], capture_output=True, timeout=10)
                import re
                for line in r.stdout.decode("utf-8", "replace").splitlines():
                    m = re.match(r"^(\S+) connected (primary )?(\d+)x(\d+)\+(\d+)\+(\d+)", line)
                    if m:
                        out.append({"name": m.group(1), "w": int(m.group(3)),
                                    "h": int(m.group(4)), "x": int(m.group(5)),
                                    "y": int(m.group(6)),
                                    "primary": bool(m.group(2))})
    except Exception:
        pass
    return out


if __name__ == "__main__":
    import json
    print(json.dumps({
        "os": OS_NAME,
        "last_input_age_s": round(last_input_age(), 2),
        "cursor": cursor_pos(),
        "monitors": monitors(),
        "windows": window_list()[:5],
        "clipboard_head": (clipboard_get().get("text") or "")[:80],
        "stats": stats(),
    }, indent=2, ensure_ascii=False))


# ============================================================================
#  EŞZAMANLI GİRDİ — gerçek imleci OYNATMADAN tıkla / yaz
#  Ajan sizinkiyle aynı anda ikinci bir fare-klavye gibi çalışır.
# ============================================================================

_MOUSE = {"left": 0x0002, "right": 0x0008, "middle": 0x0020}
_MOUSE_UP = {"left": 0x0004, "right": 0x0010, "middle": 0x0040}
_WM = {"left": 0x0201, "right": 0x0204, "middle": 0x0207}      # WM_*BUTTONDOWN
_WMU = {"left": 0x0202, "right": 0x0205, "middle": 0x0208}


def _u32():
    import ctypes
    return ctypes.windll.user32


def window_at(x, y):
    """Ekran koordinatındaki en üstteki pencerenin handle'ı."""
    try:
        return int(_u32().WindowFromPoint(_POINT(int(x), int(y))))
    except Exception:
        return 0


def _POINT(x=0, y=0):
    import ctypes

    class P(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    return P(x, y)


def bg_click(x, y, button="left", double=False, visible=True, label=""):
    """PENCEREYE DOĞRUDAN tıklar — gerçek imleç yerinden KIMILDAMAZ.

    Windows: WM_LBUTTONDOWN/UP mesajı doğrudan pencereye postalanır
             (PostMessage) → imleç hiç hareket etmez, sizinki çalışmaya
             devam eder. GUI'nin bir kısmı PostMessage'ı yok sayabilir;
             o durumda sendinput fallback kullanılır (aynı an imleç saklanır).
    Diğer platformlar: XTEST/Quartz + imleç saklama (CursorRestore).
    """
    x, y = int(x), int(y)
    if visible:
        # HIZ: gösterim ayrı iş parçacığında → tıklama animasyonu BEKLEMEZ.
        # (Eskiden 280 ms kayma + 16 adım ana iş parçacığını kilitliyordu.)
        try:
            import goverlay
            threading.Thread(target=_goster,
                             args=(x, y, label or "tıklıyorum", button),
                             daemon=True).start()
        except Exception:
            pass

    if not IS_WIN:
        return _legacy_click(x, y, button, double)

    # HIZ: 3 saniyelik önbellekli window_at (fonksiyon ici)
    hwnd = _hwnd_hizli(x, y)
    if not hwnd:
        return _legacy_click(x, y, button, double)
    # istemci koordinatına çevir
    try:
        pt = _POINT(x, y)
        u.ScreenToClient(hwnd, ctypes.byref(pt))
        cx, cy = pt.x, pt.y
    except Exception:
        return _legacy_click(x, y, button, double)
    lparam = ((cy & 0xFFFF) << 16) | (cx & 0xFFFF)
    down = _WM.get(button, 0x0201)
    up = _WMU.get(button, 0x0202)
    adet = 2 if double else 1
    try:
        for _ in range(adet):
            u.PostMessageW(hwnd, down, 1 if button == "left" else 0, lparam)
            time.sleep(0.03)
            u.PostMessageW(hwnd, up, 0, lparam)
            time.sleep(0.05)
        # SANAL MOD: yazı bundan sonra BU pencereye gider (kullanıcının
        # ön plandaki penceresine değil) → çalışma alanına müdahale biter.
        try:
            import sanaldunya
            if sanaldunya.acik():
                sanaldunya.hedef_ayarla(hwnd)
        except Exception:
            pass
        return {"ok": True, "x": x, "y": y, "mode": "arka plan (imleç oynamadı)",
                "window": hwnd, "concurrent": True}
    except Exception as e:
        r = _legacy_click(x, y, button, double)
        r["fallback"] = str(e)[:80]
        return r


def _goster(x, y, label, button):
    """Hayalet imleç + halka — arka planda, girdiyi geciktirmez."""
    try:
        import goverlay
        goverlay.ghost_glide(x, y, label=label, ms=120, steps=6)
        goverlay.click_ring(x, y, label=f"{label} · {button}")
    except Exception:
        pass


# --- HIZ: ctypes ve pencere önbelleği -------------------------------------
_HWND_ONBELLEK = {}


def _hwnd_hizli(x, y):
    """window_at'i 3 sn önbelleğe al — her tıklamada pencere araması yapmaz."""
    anahtar = (int(x) // 8, int(y) // 8)
    simdi = time.time()
    kayit = _HWND_ONBELLEK.get(anahtar)
    if kayit and simdi - kayit[0] < 3.0:
        return kayit[1]
    hwnd = window_at(x, y)
    if len(_HWND_ONBELLEK) > 512:
        _HWND_ONBELLEK.clear()
    _HWND_ONBELLEK[anahtar] = (simdi, hwnd)
    return hwnd


def _legacy_click(x, y, button, double):
    """Eski yol: imleci taşı, tıkla, ESKİ YERİNE geri koy (hızlı, tek kare)."""
    try:
        import screen
        with CursorRestore():
            return screen.click(x, y, button=button, double=double)
    except Exception as e:
        return {"ok": False, "error": f"tıklanamadı: {e}"}


# ---- klavye: odaklanmış pencereye doğrudan yaz ----------------------------

_KEYMAP = {
    "enter": 0x0D, "return": 0x0D, "tab": 0x09, "esc": 0x1B, "escape": 0x1B,
    "space": 0x20, "backspace": 0x08, "delete": 0x2E, "del": 0x2E,
    "home": 0x24, "end": 0x23, "left": 0x25, "up": 0x26, "right": 0x27,
    "down": 0x28, "pageup": 0x21, "pagedown": 0x22, "insert": 0x2D,
    "ctrl": 0x11, "control": 0x11, "alt": 0x12, "shift": 0x10, "win": 0x5B,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73, "f5": 0x74, "f6": 0x75,
    "f7": 0x76, "f8": 0x77, "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
}


def bg_type(text, visible=True, delay=0.0, hwnd=None):
    """Odaklı pencereye yazar. Gerçek imleç yerinizde kalır.

    Windows: WM_CHAR doğrudan pencereye (PostMessage) → imleç oynamaz.
    Diğer platformlar: ekran modülünün yazma işlevi.
    """
    if visible:
        try:
            import goverlay
            goverlay.hud(f"yazıyorum: {text[:40]}")
        except Exception:
            pass
    if not IS_WIN:
        try:
            import screen
            return screen.type_text(text)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    u = _u32()
    target = 0
    # 1) Açıkça verilen pencere
    try:
        target = int(hwnd or 0)
    except Exception:
        target = 0
    # 2) SANAL MOD: ajanın kendi seçtiği pencere (kullanıcınınki DEĞİL)
    if not target:
        try:
            import sanaldunya
            if sanaldunya.acik():
                target = int(sanaldunya.hedef() or 0)
        except Exception:
            target = 0
    # 3) Son çare: odaklı pencere (gerçek makine davranışı — değişmedi)
    if not target:
        try:
            target = int(u.GetForegroundWindow())
        except Exception:
            target = 0
    if not target:
        try:
            import screen
            return screen.type_text(text)
        except Exception as e:
            return {"ok": False, "error": str(e)}
    try:
        # HIZ: PostMessage kuyruğu kendi sırasını korur → karakter başına
        # bekleme yok. Çok uzun metinde (1000+) nefes payı bırakılır.
        uzun = len(str(text)) > 1000
        for i, ch in enumerate(str(text)):
            u.PostMessageW(target, 0x0102, ord(ch), 1)    # WM_CHAR
            if delay:
                time.sleep(delay)
            elif uzun and i % 200 == 0:
                time.sleep(0.02)
        return {"ok": True, "chars": len(str(text)),
                "mode": "arka plan (imleç oynamadı)", "concurrent": True}
    except Exception as e:
        try:
            import screen
            screen.type_text(text)
            return {"ok": True, "chars": len(str(text)), "fallback": str(e)[:80]}
        except Exception as e2:
            return {"ok": False, "error": f"{e} / {e2}"}


def bg_key(combo, hwnd=None):
    """Kısayol tuşu (örn. 'ctrl+s'). Arka planda pencereye gönderir."""
    keys = [k.strip().lower() for k in str(combo).replace("+", " ").split() if k.strip()]
    if not keys:
        return {"ok": False, "error": "tuş belirtilmedi"}
    if not IS_WIN:
        try:
            import screen
            return screen.key(combo)
        except Exception as e:
            return {"ok": False, "error": str(e)}
    u = _u32()
    target = 0
    try:
        target = int(hwnd or 0)
    except Exception:
        target = 0
    if not target:
        try:
            import sanaldunya
            if sanaldunya.acik():
                target = int(sanaldunya.hedef() or 0)
        except Exception:
            target = 0
    try:
        target = target or int(u.GetForegroundWindow())
        WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
        vks = [_KEYMAP.get(k, ord(k.upper()) if len(k) == 1 else 0) for k in keys]
        for vk in vks:
            if vk:
                u.PostMessageW(target, WM_KEYDOWN, vk, 1)
        for vk in reversed(vks):
            if vk:
                u.PostMessageW(target, WM_KEYUP, vk, 1)
                time.sleep(0.01)
        return {"ok": True, "combo": combo, "mode": "arka plan", "concurrent": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

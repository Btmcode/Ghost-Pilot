#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — goverlay.py  ·  GÖRÜNÜR AJAN KATMANI
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Ajan SİZİNLE AYNI ANDA çalışırken ekranda görünür olsun diye:
#    · Hayalet imleç: hedefe yumuşakça kayar, tıklamada halka bırakır
#    · Şerit (HUD): ekranın altında "şu an ne yapıyorum"
#
#  Tasarım: TAM EKRAN katman DEĞİL — küçük, şeffaf, tıklamayı geçiren
#  pencereler. Böylece hem Windows (transparentcolor) hem Linux/macOS
#  (alpha) üzerinde çalışır ve ekranı karartmaz.
#
#  Sıfır bağımlılık: tkinter + ctypes. Yoksa sessizce devre dışı kalır.
# ============================================================================

import platform
import threading
import time

OS_NAME = platform.system()
IS_WIN = OS_NAME == "Windows"

ACCENT = "#f59e0b"     # amber — ajanın rengi
ACCENT2 = "#22d3ee"    # cyan  — tıklama halkası
DARK = "#0b1120"
KEY = "#ff00fe"        # şeffaflık anahtarı (bu renk görünmez olur)

# Windows'ta gerçek şeffaflık var → büyük pencere (halkalar tam görünür)
# Linux/macOS'ta pencere dikdörtgen → küçük tutuyoruz ki ekranı kaplamasın
EFFECT = 300 if IS_WIN else 150
RING_MAX = 118 if IS_WIN else 68
ARROW_W, ARROW_H = 18, 26

# Hayalet imleç son işlemden bu kadar saniye sonra KENDİLİĞİNDEN gizlenir
OTO_GIZLE = 5.0

_lock = threading.Lock()
_state = {
    "ready": False,
    "reason": "",
    "screen": (0, 0),
    "x": 0, "y": 0,
    "cursor_on": False,
    "hud": "",
    "hud_until": 0.0,
    "quitting": False,
    "son_dokunma": 0.0,
}

_root = None
_tk = None
_eff = None
_hud = None
_evt = threading.Event()


# ============================================================================
#  EFEKT PENCERESİ — hayalet imleç + tıklama halkaları
# ============================================================================

class _Effect:
    """Küçük, şeffaf, tıklamayı geçiren pencere; merkezinde imleç + halkalar."""

    def __init__(self, tk, root):
        self.tk = tk
        self.win = tk.Toplevel(root)
        w = self.win
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        set_key = False
        try:
            w.attributes("-transparentcolor", KEY)
            set_key = True
        except Exception:
            pass
        if not set_key:
            try:
                w.attributes("-alpha", 0.80)
            except Exception:
                pass
        bg = KEY if set_key else DARK
        w.configure(bg=bg)
        self.cv = tk.Canvas(w, width=EFFECT, height=EFFECT, bg=bg,
                            highlightthickness=0, bd=0)
        self.cv.pack()
        self.click_through()
        self.rings = {}          # (id) -> (dogum_zamani, yaricap)
        self.arrow = None
        self.label = None
        self._build_arrow()

    # tıklamaları alt uygulamaya geçir
    def click_through(self):
        if not IS_WIN:
            return
        try:
            import ctypes
            u = ctypes.windll.user32
            self.win.update_idletasks()
            hwnd = u.GetParent(self.win.winfo_id()) or self.win.winfo_id()
            GWL_EXSTYLE = -20
            cur = u.GetWindowLongW(hwnd, GWL_EXSTYLE)
            u.SetWindowLongW(hwnd, GWL_EXSTYLE,
                             cur | 0x80000 | 0x20 | 0x08000000 | 0x80)
        except Exception as e:
            _state["reason"] = f"click-through: {e}"

    def _build_arrow(self):
        """Ajan imleci: amber ok + beyaz kenar (her arka planda görünür)."""
        c = EFFECT // 2
        pts = [c, c,
               c, c + ARROW_H,
               c + 5.2, c + ARROW_H - 7.2,
               c + 9.0, c + ARROW_H - 1.2,
               c + 12.6, c + ARROW_H - 3.0,
               c + 8.8, c + ARROW_H - 9.4,
               c + ARROW_W, c + ARROW_H - 9.4]
        self.arrow = self.cv.create_polygon(
            *pts, fill=ACCENT, outline="#ffffff", width=1.6, state="hidden")
        # çevresinde ince hale → koyu ekranda da görünür
        self.halo = self.cv.create_oval(c - 4, c - 4, c + 4, c + 4,
                                        outline=ACCENT, width=1.2, state="hidden")

    def place(self, x, y):
        """Pencereyi (x,y) imleç noktasına ortalayacak şekilde taşı."""
        h = EFFECT // 2
        self.win.geometry(f"{EFFECT}x{EFFECT}+{int(x) - h}+{int(y) - h}")

    def show(self, x, y, label=""):
        _state["son_dokunma"] = time.time()
        self.place(x, y)
        self.cv.itemconfigure(self.arrow, state="normal")
        self.cv.itemconfigure(self.halo, state="normal")
        if self.label:
            self.cv.delete(self.label)
            self.label = None

    def hide(self):
        self.cv.itemconfigure(self.arrow, state="hidden")
        self.cv.itemconfigure(self.halo, state="hidden")

    def ring(self, x, y):
        _state["son_dokunma"] = time.time()
        cx = cy = EFFECT // 2
        for i in range(3):
            cid = self.cv.create_oval(cx - 3, cy - 3, cx + 3, cy + 3,
                                      outline=ACCENT2 if i % 2 else ACCENT,
                                      width=2.4)
            self.rings[cid] = (time.time() + i * 0.06, 3.0)

    def step(self):
        if not self.rings:
            return
        simdi = time.time()
        for cid, (t0, r) in list(self.rings.items()):
            if simdi < t0:
                continue
            r2 = r + 7.0
            cx = cy = EFFECT // 2
            try:
                self.cv.coords(cid, cx - r2, cy - r2, cx + r2, cy + r2)
                self.cv.itemconfigure(cid, width=max(0.5, 2.6 - r2 / 30))
            except Exception:
                self.rings.pop(cid, None)
                continue
            if r2 > RING_MAX:
                try:
                    self.cv.delete(cid)
                except Exception:
                    pass
                self.rings.pop(cid, None)
            else:
                self.rings[cid] = (t0, r2)


# ============================================================================
#  HUD ŞERİDİ — ekranın altında "ne yapıyorum"
# ============================================================================

class _Hud:
    def __init__(self, tk, root, screen_w, screen_h):
        self.tk = tk
        self.sw, self.sh = screen_w, screen_h
        self.win = tk.Toplevel(root)
        w = self.win
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        set_key = False
        try:
            w.attributes("-transparentcolor", KEY)
            set_key = True
        except Exception:
            pass
        self.bg = KEY if set_key else DARK
        w.configure(bg=self.bg)
        self.cv = tk.Canvas(w, width=520, height=46, bg=self.bg,
                            highlightthickness=0, bd=0)
        self.cv.pack()
        self.click_through()
        self.box = self.cv.create_rectangle(0, 4, 520, 42, fill=DARK,
                                            outline=ACCENT, width=1.6)
        self.dot = self.cv.create_oval(14, 18, 24, 28, fill=ACCENT2, outline="")
        self.tx = self.cv.create_text(36, 23, anchor="w", fill="#e2e8f0",
                                      font=("Segoe UI", 10))
        self.win.withdraw()

    def click_through(self):
        if not IS_WIN:
            return
        try:
            import ctypes
            u = ctypes.windll.user32
            self.win.update_idletasks()
            hwnd = u.GetParent(self.win.winfo_id()) or self.win.winfo_id()
            GWL_EXSTYLE = -20
            cur = u.GetWindowLongW(hwnd, GWL_EXSTYLE)
            u.SetWindowLongW(hwnd, GWL_EXSTYLE,
                             cur | 0x80000 | 0x20 | 0x08000000 | 0x80)
        except Exception:
            pass

    def show(self, text):
        self.cv.itemconfigure(self.tx, text=text[:120])
        self.cv.update_idletasks()
        bx = self.cv.bbox(self.tx) or (36, 18, 336, 28)
        tw = bx[2] - bx[0]
        w = max(220, min(760, tw + 60))
        self.cv.coords(self.box, 0, 4, w, 42)
        self.win.geometry(f"{w}x46+{max(8, (self.sw - w) // 2)}+{self.sh - 96}")
        self.win.deiconify()
        self.win.lift()

    def hide(self):
        self.win.withdraw()


# ============================================================================
#  DÖNGÜ
# ============================================================================

def _boot():
    global _root, _tk, _eff, _hud
    try:
        import tkinter as tk
        _tk = tk
        root = tk.Tk()
        _root = root
        root.withdraw()
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        if IS_WIN:
            try:
                import ctypes
                u = ctypes.windll.user32
                vx, vy = u.GetSystemMetrics(76), u.GetSystemMetrics(77)
                vsx, vsy = u.GetSystemMetrics(78), u.GetSystemMetrics(79)
                if vsx > 0 and vsy > 0:
                    sw, sh = vsx, vsy
            except Exception:
                pass
        _state["screen"] = (sw, sh)
        _eff = _Effect(tk, root)
        _hud = _Hud(tk, root, sw, sh)
        _state["ready"] = True
        _evt.set()

        def tick():
            if _state["quitting"]:
                try:
                    root.quit()
                except Exception:
                    pass
                return
            try:
                if _eff:
                    _eff.step()
                if _state["hud_until"] and time.time() > _state["hud_until"]:
                    _state["hud_until"] = 0
                    if _hud:
                        _hud.hide()
                # 5 saniye işlem yapılmadıysa hayalet imleci gizle
                if (_state["cursor_on"] and _state["son_dokunma"] and
                        time.time() - _state["son_dokunma"] > OTO_GIZLE):
                    _state["cursor_on"] = False
                    if _eff:
                        _eff.hide()
            except Exception:
                pass
            root.after(28, tick)

        root.after(20, tick)
        root.mainloop()
    except Exception as e:
        _state["reason"] = f"tkinter kurulamadı: {e}"
        _evt.set()


def start(timeout=3.0):
    global _root
    if _state["ready"]:
        return True
    if _root is None and not _state["reason"]:
        threading.Thread(target=_boot, daemon=True, name="goverlay").start()
    _evt.wait(timeout)
    return _state["ready"]


def status():
    return {"ready": _state["ready"], "reason": _state["reason"],
            "visible": _state["cursor_on"], "screen": _state["screen"],
            "concurrent": True}


def _ui(fn, *a, **kw):
    if not _state["ready"] or _root is None:
        return False
    try:
        _root.after(0, lambda: fn(*a, **kw))
        return True
    except Exception as e:
        _state["reason"] = f"ui: {e}"
        return False


# ---- kamu API --------------------------------------------------------------

def ghost_show(x=None, y=None, label=""):
    if not start():
        return False
    if x is not None:
        _state["x"], _state["y"] = int(x), int(y)
    _state["cursor_on"] = True
    _state["son_dokunma"] = time.time()
    if label:
        hud(label)
    return _ui(_eff.show, _state["x"], _state["y"], label)


def ghost_hide():
    _state["cursor_on"] = False
    return _ui(_eff.hide)


def ghost_glide(x2, y2, label="", ms=280, steps=16):
    """Hayalet imleci hedefe kaydır — GERÇEK imlece dokunmaz."""
    if not start():
        return False
    x1, y1 = _state["x"], _state["y"]
    x2, y2 = int(x2), int(y2)
    _state["cursor_on"] = True
    _state["son_dokunma"] = time.time()
    for i in range(1, steps + 1):
        p = i / steps
        e = 1 - (1 - p) ** 2.4
        _state["x"] = int(x1 + (x2 - x1) * e)
        _state["y"] = int(y1 + (y2 - y1) * e)
        _ui(_eff.show, _state["x"], _state["y"])
        time.sleep(max(0.004, (ms / 1000) / steps))
    _state["x"], _state["y"] = x2, y2
    _ui(_eff.show, x2, y2)
    if label:
        hud(label)
    return True


def click_ring(x, y, label=""):
    if not start():
        return False
    _state["x"], _state["y"] = int(x), int(y)
    _state["cursor_on"] = True
    _ui(_eff.show, _state["x"], _state["y"])
    _ui(_eff.ring, _state["x"], _state["y"])
    if label:
        hud(label)
    return True


def hud(text, seconds=4.0):
    if not start():
        return False
    _state["hud"] = str(text)[:120]
    _state["hud_until"] = time.time() + max(1.0, float(seconds))
    return _ui(_hud.show, _state["hud"])


def hud_off():
    _state["hud_until"] = 0
    _state["hud"] = ""
    return _ui(_hud.hide)


def shutdown():
    _state["quitting"] = True

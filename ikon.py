#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — ikon.py  ·  Pencere + görev çubuğu ikonu (3 OS)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Windows : AppUserModelID → görev çubuğunda HAYALET ikon (python ikonu değil!)
#            + .ico bitmap ikonu
#  Linux   : iconphoto (PNG) + WM_CLASS
#  macOS   : iconphoto + Dock adı
# ============================================================================

import os
import sys

BURASI = os.path.dirname(os.path.abspath(__file__))
ICO = os.path.join(BURASI, "GhostPilot.ico")
PNG = os.path.join(BURASI, "icon-256.png")
APP_ID = "BTMCode.GhostPilot"


def _win_appid():
    """Görev çubuğunda gruplama + doğru ikon için AppUserModelID."""
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        return True
    except Exception:
        return False


def uygula(pencere, baslik="GhostPilot"):
    """Tk penceresine ikonu uygular. Döner: hangi yöntem kullanıldı."""
    yontem = []
    # ---------- Windows
    if os.name == "nt":
        if _win_appid():
            yontem.append("appid")
        try:
            if os.path.exists(ICO):
                pencere.iconbitmap(default=ICO)     # .ico → görev çubuğu + başlık
                yontem.append("ico")
        except Exception:
            pass
    # ---------- hepsi: PNG
    try:
        if os.path.exists(PNG):
            import tkinter as tk
            # referansı pencere üzerinde tut (yoksa çöp toplanır, ikon kaybolur)
            pencere._gp_ikon = tk.PhotoImage(file=PNG, master=pencere)
            pencere.iconphoto(True, pencere._gp_ikon)
            yontem.append("png")
    except Exception:
        pass
    # ---------- Linux: pencere sınıfı (görev çubuğu eşleştirmesi)
    try:
        if sys.platform.startswith("linux"):
            pencere.wm_class = "GhostPilot"
            yontem.append("wmclass")
    except Exception:
        pass
    try:
        pencere.title(baslik)
    except Exception:
        pass
    return yontem


def konsol_ikonu():
    """Konsol penceresinin başlık ikonu (yalnız Windows)."""
    if os.name != "nt":
        return False
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW("GhostPilot")
        # konsol penceresine ikon: WM_SETICON
        k = ctypes.windll.kernel32.GetConsoleWindow()
        if not k:
            return False
        yukle = ctypes.windll.user32.LoadImageW
        IMAGE_ICON, LR_LOADFROMFILE, LR_DEFAULTSIZE = 1, 0x10, 0x40
        h = yukle(None, ICO, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE)
        if h:
            ctypes.windll.user32.SendMessageW(k, 0x0080, 0, h)   # WM_SETICON, ICON_SMALL
            ctypes.windll.user32.SendMessageW(k, 0x0080, 1, h)   # ICON_BIG
            return True
    except Exception:
        pass
    return False


if __name__ == "__main__":
    print("ico:", os.path.exists(ICO), "| png:", os.path.exists(PNG), "| appid:", _win_appid())

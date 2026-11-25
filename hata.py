#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — hata.py   ·   Hata günlüğü (kullanıcı hiçbir şey kaybetmesin)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Ne yapar?
#    Beklenmedik her hata (çökme) buraya tam olarak yazılır:
#      ~/.ghostpilot/hata.log
#
#    Böylece "pencere açılıp kapandı" durumunda ne olduğu belli olur.
#
#  Kullanım (program içinde):
#      import hata
#      hata.kur("ui")            # bu modülün hatalarını yakala
#
#  Kullanıcı için:
#      python kur.py hata        # son hatayı göster
# ============================================================================

import datetime
import os
import platform
import sys
import traceback

BURASI = os.path.dirname(os.path.abspath(__file__))
LOG_DIZIN = os.path.join(os.path.expanduser("~"), ".ghostpilot")
LOG = os.path.join(LOG_DIZIN, "hata.log")
EN_FAZLA = 400_000          # günlük dosyası çok büyümesin (400 KB)


def _surum():
    try:
        with open(os.path.join(BURASI, "ghostpilot.py"), encoding="utf-8") as f:
            for satir in f:
                if satir.startswith("VERSION"):
                    return satir.split("=")[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return "?"


def yol():
    return LOG


def _kirp():
    """Günlük çok büyürse ikinci yarısını tut."""
    try:
        if os.path.getsize(LOG) > EN_FAZLA:
            with open(LOG, "r", encoding="utf-8", errors="replace") as f:
                veri = f.read()
            with open(LOG, "w", encoding="utf-8") as f:
                f.write("... (eski kayıtlar kırpıldı) ...\n" + veri[-EN_FAZLA // 2:])
    except Exception:
        pass


def yaz(baslik, detay=""):
    """Günlüğe bir kayıt ekle. Hata günlüğü yazarken asla çökmez."""
    try:
        os.makedirs(LOG_DIZIN, exist_ok=True)
        _kirp()
        zaman = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(f"[{zaman}] {baslik}\n")
            f.write(f"sürüm   : {_surum()}\n")
            f.write(f"sistem  : {platform.platform()}\n")
            f.write(f"python  : {sys.version.split()[0]} ({sys.executable})\n")
            f.write(f"klasör  : {BURASI}\n")
            f.write(f"çalışma : {os.getcwd()}\n")
            if detay:
                f.write("-" * 70 + "\n")
                f.write(detay.rstrip() + "\n")
            f.write("\n")
        return LOG
    except Exception:
        return ""


def yaz_hata(exc_type, exc, tb, baslik="BEKLENMEDİK HATA"):
    detay = "".join(traceback.format_exception(exc_type, exc, tb))
    return yaz(baslik, detay)


def kur(modul="ghostpilot", sesli=False):
    """Bu süreçteki yakalanmamış hataları günlüğe yaz.

    sesli=True → hata anında kısa bir pencere/uyarı da gösterilir.
    """

    def _kanca(tip, deger, tb):
        yol_ = yaz_hata(tip, deger, tb, f"BEKLENMEDİK HATA · {modul}")
        try:
            sys.stderr.write("\n  ❌ Beklenmedik hata. Ayrıntılar:\n"
                             f"     {yol_}\n"
                             f"     {tip.__name__}: {deger}\n\n")
        except Exception:
            pass
        if sesli:
            _pencere(tip, deger, yol_)

    sys.excepthook = _kanca

    # arka plan iş parçacıklarındaki hatalar da kaybolmasın
    try:
        import threading

        def _is_kanca(args):
            yaz_hata(args.exc_type, args.exc_value, args.exc_traceback,
                     f"ARKA PLAN HATASI · {modul}")

        threading.excepthook = _is_kanca
    except Exception:
        pass


def _pencere(tip, deger, dosya):
    """Hata olduğunda kullanıcıya görünür bir pencere göster (varsa tkinter)."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        kok = tk.Tk()
        kok.withdraw()
        messagebox.showerror(
            "GhostPilot — beklenmedik hata",
            f"{tip.__name__}: {deger}\n\n"
            f"Ayrıntılar bu dosyada:\n{dosya}\n\n"
            "Bu dosyayı geliştiriciye gönderirseniz sorun hızla bulunur.\n"
            "Çalışmaya devam etmek için Tamam'a basın.")
        kok.destroy()
    except Exception:
        pass


def son(n=60):
    """Son hatayı (son n satır) döndür."""
    try:
        with open(LOG, "r", encoding="utf-8", errors="replace") as f:
            satirlar = f.read().splitlines()
        return "\n".join(satirlar[-n:])
    except Exception:
        return ""


def var_mi():
    try:
        return os.path.getsize(LOG) > 0
    except Exception:
        return False


def temizle():
    try:
        os.remove(LOG)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    print(f"  Günlük dosyası : {LOG}")
    print(f"  Kayıt var mı   : {'evet' if var_mi() else 'hayır'}")
    if var_mi():
        print("-" * 60)
        print(son())

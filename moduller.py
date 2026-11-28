#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — moduller.py  ·  MODÜL SAĞLIĞI ve SÜRÜM BİLGİSİ
#  Copyright (c) 2026 BTM Code — MIT License
#
#  NE ÇÖZER
#    Yedi faz yedi ayrı modüle dağıldı. Bir modül eksik/bozuk olduğunda
#    araç sessizce "yok" davranıyordu. Bu dosya her modülün yüklenip
#    yüklenmediğini, sürümünü ve yeteneğini TEK yerden raporlar.
#
#    `python ghostpilot.py surum` ve NEX paneli buradan beslenir.
# ============================================================================

import os
import platform
import sys

BURASI = os.path.dirname(os.path.abspath(__file__))
if BURASI not in sys.path:
    sys.path.insert(0, BURASI)

# modül → (faz, ne yapar, sürüm)
MODULLER = {
    "oturum":   (1, "Kalıcı terminal & süreç motoru", "1.0"),
    "pty_yardimci": (1, "PTY yardımcısı — yeniden başlatmada yazma", "1.0"),
    "arama":    (2, "Arka plan arama motoru", "1.0"),
    "dosya":    (3, "Atomik dosya & link güvenliği", "1.0"),
    "gui":      (4, "GUI motoru & VM koordinat eşlemesi", "1.0"),
    "izleme":   (5, "Audit, maskeleme, HUD", "1.0"),
    "cihaz":    (6, "Çoklu cihaz (HMAC imzalı)", "1.0"),
    "guvenlik": (7, "3 kademeli izin politikası", "1.0"),
}


def _yukle(ad):
    try:
        __import__(ad)
        return True, ""
    except Exception as e:
        return False, str(e)[:200]


def surum_bilgi():
    """Her modülün durumu + platform yetenekleri."""
    satirlar = {}
    eksik = []
    for ad, (faz, aciklama, surum) in sorted(MODULLER.items(),
                                             key=lambda z: z[1][0]):
        ok, hata = _yukle(ad)
        satirlar[ad] = ("Faz %d · v%s · %s%s"
                        % (faz, surum, aciklama, "" if ok else "  ⚠️ " + hata))
        if not ok:
            eksik.append(ad)
    yetenek = yetenekler()
    return {"ok": not eksik,
            "surum": "v6-dev",
            "platform": platform.system(),
            "python": platform.python_version(),
            "moduller": satirlar,
            "eksik": eksik,
            "yetenekler": yetenek}


def yetenekler():
    """Platformun gerçekten ne yapabildiği (abartısız)."""
    IS_WIN = platform.system() == "Windows"
    y = {}
    # 1) PTY (yeniden başlatmada yazma)
    y["pty_kalici_yazma"] = (not IS_WIN) and os.path.exists(
        os.path.join(BURASI, "pty_yardimci.py"))
    # 2) Nesne ağacı
    agac = "yok"
    if IS_WIN:
        try:
            import uiautomation  # noqa
            agac = "uiautomation"
        except Exception:
            agac = "yok (uiautomation kurulu değil)"
    else:
        try:
            import pyatspi  # noqa
            agac = "atspi"
        except Exception:
            agac = "yok (AT-SPI kurulu değil)"
    y["nesne_agaci"] = agac
    # 3) ekran görüntüsü
    try:
        import PIL  # noqa
        y["ekran_goruntusu"] = True
    except Exception:
        y["ekran_goruntusu"] = False
    # 4) sanal imleç (görsel katman)
    y["sanal_imlec"] = os.path.exists(os.path.join(BURASI, "goverlay.py"))
    # 5) çoklu cihaz
    y["coklu_cihaz"] = True
    # 6) disk alanı
    try:
        st = os.statvfs(BURASI)
        y["disk_bos_mb"] = int(st.f_bavail * st.f_frsize / (1024 * 1024))
    except Exception:
        y["disk_bos_mb"] = None
    return y


def teshis():
    """`doctor` için kısa, okunur teşhis."""
    b = surum_bilgi()
    satir = []
    satir.append("Modüller: %d/%d yüklendi" % (len(b["moduller"]) - len(b["eksik"]),
                                              len(b["moduller"])))
    if b["eksik"]:
        satir.append("EKSİK: " + ", ".join(b["eksik"]))
    y = b["yetenekler"]
    satir.append("PTY kalıcı yazma : %s" % ("açık" if y["pty_kalici_yazma"]
                                            else "kapalı (Windows/eksik)"))
    satir.append("Nesne ağacı     : %s" % y["nesne_agaci"])
    satir.append("Ekran görüntüsü : %s" % ("var" if y["ekran_goruntusu"] else "yok"))
    satir.append("Sanal imleç     : %s" % ("var" if y["sanal_imlec"] else "yok"))
    if y.get("disk_bos_mb") is not None:
        satir.append("Boş disk        : %d MB" % y["disk_bos_mb"])
    return {"ok": b["ok"], "satirlar": satir}


if __name__ == "__main__":
    for s in teshis()["satirlar"]:
        print(" ", s)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  paketle.py — zip üretirken lisans.py özetini ghostpilot.py'ye gömer.
import hashlib, io, os, re, shutil, subprocess, sys, zipfile

BURASI = os.path.dirname(os.path.abspath(__file__))
DOSYALAR = ["ghostpilot.py","screen.py","kur.py","setup.py","exe_yap.py","kurulum_gui.py","kurulum.py","lisans.py","paketler.py","kisayol.py","ui.py","kurulum_ui.py","diller.py","sanalortam.py","kaldir.py","lisans_online.py","ikon.py","tepsi.py","input_bg.py",
            "belge.py","guncelle.py","goverlay.py","simge_uret.py","README.md",
            "GIZLILIK.md","KOSULLAR.md","SECURITY.md","KURULUM_REHBERI.md",
            # Windows girişleri
            "BASLA.bat","KURULUM.bat","PANEL.bat","KALDIR.bat","_bitis.bat",
            # Linux / macOS girişleri
            "basla.sh","kurulum.sh","kurulum_macos.command",
            "LICENSE","COPYRIGHT"]
IKONLAR = [f for f in os.listdir(BURASI)
           if f.startswith(("icon","favicon","chatgpt-icon","GhostPilot.ico"))
           and os.path.isfile(os.path.join(BURASI, f))]

def main(surum):
    with open(os.path.join(BURASI, "lisans.py"), "rb") as f:
        ozet = hashlib.sha256(f.read()).hexdigest()
    gp = os.path.join(BURASI, "ghostpilot.py")
    s = io.open(gp, encoding="utf-8").read()
    s = re.sub(r'LISANS_DOSYA_OZETI = "[0-9a-f]*"', f'LISANS_DOSYA_OZETI = "{ozet}"', s)
    io.open(gp, "w", encoding="utf-8").write(s)
    print("  lisans.py özeti gömüldü:", ozet[:16], "…")

    hedef = f"/home/user/GhostPilot-MCP-v{surum}.zip"
    gecici = "/tmp/paket_gp"
    shutil.rmtree(gecici, ignore_errors=True)
    os.makedirs(os.path.join(gecici, "GhostPilot"))
    for f in DOSYALAR + IKONLAR:
        k = os.path.join(BURASI, f)
        if os.path.exists(k):
            shutil.copy2(k, os.path.join(gecici, "GhostPilot", f))
    if os.path.exists(hedef):
        os.remove(hedef)
    with zipfile.ZipFile(hedef, "w", zipfile.ZIP_DEFLATED) as z:
        for kok, _, dos in os.walk(os.path.join(gecici, "GhostPilot")):
            for d in dos:
                tam = os.path.join(kok, d)
                z.write(tam, os.path.relpath(tam, gecici))
    print(f"  ✓ {hedef} ({os.path.getsize(hedef)/1024:.0f} KB)")
    return hedef

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "5.6.0")

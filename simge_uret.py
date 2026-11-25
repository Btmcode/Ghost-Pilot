#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — ikon üretici
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Çıktı: icon.svg · icon-256.png · icon-128/48/32/16.png · favicon.ico
#  Tasarım: koyu lacivert zemin + amber hayalet + cyan "ajan halkası"
#  Sıfır ek bağımlılık (Pillow yalnız üretim sırasında kullanılır).
# ============================================================================

import math
import os

from PIL import Image, ImageDraw, ImageFilter

S = 1024          # üstünkörü çizim boyutu (sonra küçültülür → yumuşak kenar)
OUT = os.path.dirname(os.path.abspath(__file__))

BG_TOP = (14, 22, 40)        # #0e1628
BG_BOT = (8, 13, 26)         # #080d1a
AMBER = (245, 158, 11)       # #f59e0b
AMBER_HI = (253, 200, 96)    # açık amber
CYAN = (34, 211, 238)        # #22d3ee
WHITE = (255, 255, 255)


def yuvarlak_zemin(img, r):
    """Köşeleri yuvarlatılmış kare maske."""
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, S - 1, S - 1], radius=r, fill=255)
    return m


def dikey_gradyan():
    g = Image.new("RGB", (1, S))
    d = ImageDraw.Draw(g)
    for y in range(S):
        t = y / (S - 1)
        d.point((0, y), tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t) for i in range(3)))
    return g.resize((S, S))


def hayalet_poligon():
    """Klasik hayalet: yarım daire baş + dalgalı etek."""
    cx, cy = S / 2, S * 0.47          # baş merkezi
    r = S * 0.245                     # baş yarıçapı
    sol = cx - r
    sag = cx + r
    govde_alt = S * 0.795             # etek taban çizgisi
    noktalar = []

    # tepe: 180° → 360° (saat yönünde sağdan sola)
    adim = 3
    for a in range(180, 361, adim):
        rad = math.radians(a)
        noktalar.append((cx + r * math.cos(rad), cy + r * math.sin(rad)))
    # sağ yan aşağı
    noktalar.append((sag, govde_alt))
    # etek: 4 yumuşak tarak (gerçek hayalet gibi aşağı sarkan yaylar)
    dis = 4
    gen = sag - sol
    r = gen / (dis * 2)
    for i in range(dis):
        merkez = sol + r * (2 * i + 1)
        for a in range(180, -1, -6):
            rad = math.radians(a)
            noktalar.append((merkez + r * math.cos(rad),
                             govde_alt + r * math.sin(rad) * 0.62))
    noktalar.append((sol, govde_alt))
    noktalar.append((sol, cy))
    return noktalar


def ciz():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    # ---- zemin
    bg = dikey_gradyan().convert("RGBA")
    img.paste(bg, (0, 0), yuvarlak_zemin(bg, int(S * 0.22)))

    # ince iç çerçeve
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S * 0.012, S * 0.012, S * 0.988, S * 0.988],
                        radius=int(S * 0.21), outline=(38, 54, 84, 255),
                        width=int(S * 0.008))

    # ---- cyan "ajan halkası" (arka planda, yumuşak)
    ring = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ring)
    cx = cy = S / 2
    rr = S * 0.335
    dr.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=CYAN + (170,),
               width=int(S * 0.018))
    ring = ring.filter(ImageFilter.GaussianBlur(S * 0.008))
    img = Image.alpha_composite(img, ring)

    # ---- hayalet gövdesi (gölge + dolgu)
    pol = hayalet_poligon()

    golge = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(golge).polygon([(x + S * 0.012, y + S * 0.018) for x, y in pol],
                                  fill=(0, 0, 0, 150))
    golge = golge.filter(ImageFilter.GaussianBlur(S * 0.018))
    img = Image.alpha_composite(img, golge)

    govde = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(govde)
    gd.polygon(pol, fill=AMBER + (255,))
    # hafif üst ışık
    gd.polygon(pol, fill=None, outline=AMBER_HI + (255,), width=int(S * 0.012))
    img = Image.alpha_composite(img, govde)

    # ---- gözler
    d = ImageDraw.Draw(img)
    goz_y = S * 0.44
    goz_r = S * 0.042
    for gx in (S * 0.435, S * 0.565):
        d.ellipse([gx - goz_r, goz_y - goz_r * 1.15, gx + goz_r, goz_y + goz_r * 1.15],
                  fill=(12, 18, 32, 255))

    # ---- etek altında ince cyan yansıma
    d.ellipse([S * 0.315, S * 0.822, S * 0.685, S * 0.855], fill=None,
              outline=CYAN + (140,), width=int(S * 0.009))

    return img


def svg_yaz(yol):
    pol = hayalet_poligon()
    pts = " ".join(f"{x / S * 256:.1f},{y / S * 256:.1f}" for x, y in pol)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0e1628"/><stop offset="1" stop-color="#080d1a"/>
    </linearGradient>
  </defs>
  <rect width="256" height="256" rx="56" fill="url(#g)"/>
  <rect x="3" y="3" width="250" height="250" rx="53" fill="none" stroke="#263654" stroke-width="2"/>
  <circle cx="128" cy="128" r="86" fill="none" stroke="#22d3ee" stroke-opacity=".66" stroke-width="4.6"/>
  <polygon points="{pts}" fill="#f59e0b" stroke="#fdc860" stroke-width="3"/>
  <ellipse cx="111" cy="113" rx="10.7" ry="12.3" fill="#0c1220"/>
  <ellipse cx="145" cy="113" rx="10.7" ry="12.3" fill="#0c1220"/>
  <ellipse cx="128" cy="211" rx="51" ry="5.7" fill="none" stroke="#22d3ee" stroke-opacity=".6" stroke-width="3"/>
</svg>
'''
    with open(yol, "w", encoding="utf-8") as f:
        f.write(svg)


def main():
    img = ciz()
    # yuvarlatılmış zemin dışında kalan köşeleri saydam yap
    mask = yuvarlak_zemin(img, int(S * 0.22))
    img.putalpha(mask)

    boyutlar = [256, 180, 128, 48, 32, 16]
    for b in boyutlar:
        k = img.resize((b, b), Image.LANCZOS)
        k.save(os.path.join(OUT, f"icon-{b}.png"), optimize=True)
    img.resize((256, 256), Image.LANCZOS).save(os.path.join(OUT, "icon.png"),
                                               optimize=True)
    # favicon: çok boyutlu .ico
    img.resize((256, 256), Image.LANCZOS).save(
        os.path.join(OUT, "favicon.ico"), format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    svg_yaz(os.path.join(OUT, "icon.svg"))

    for f in ("icon-256.png", "icon-128.png", "icon-48.png", "favicon.ico", "icon.svg"):
        p = os.path.join(OUT, f)
        print(f"  {f:16s} {os.path.getsize(p) / 1024:6.1f} KB")


if __name__ == "__main__":
    main()

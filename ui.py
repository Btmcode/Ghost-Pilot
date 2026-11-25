#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — ui.py  ·  PROGRAM ARAYÜZÜ
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Tasarım: 3 sekme (Durum · Lisans · Paketler) + alt durum çubuğu.
#  Pencere küçültülse bile hiçbir içerik taşmaz (her sekme kaydırılabilir).
# ============================================================================

import os
import subprocess
import sys
import threading

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)

# ---- tema
ARKA, KART, CIZGI = "#0f172a", "#17233b", "#243450"
UST = "#132038"
METIN, SOLUK, SILIK = "#e8eef7", "#93a4be", "#5f7392"
AMBER, YESIL, KIRMIZI = "#f59e0b", "#22c55e", "#ef4444"
MAVI, VURGU_BG = "#38bdf8", "#14301f"

F = "Segoe UI"

try:
    import tkinter as tk
    from tkinter import ttk
    TK = True
except Exception:
    TK = False

try:
    import diller
    from diller import t
except Exception:
    diller = None

try:
    import hata
    hata.kur("ui", sesli=True)
except Exception:
    hata = None

    def t(k, **kw):
        return k


def _gp():
    import ghostpilot
    return ghostpilot


# ===========================================================================
#  KÜÇÜK YARDIMCILAR
# ===========================================================================
def kart(ata, padx=0, pady=0, **kw):
    f = tk.Frame(ata, bg=KART, highlightbackground=CIZGI, highlightthickness=1, **kw)
    return f


def baslik(ata, yazi, alt=None):
    f = tk.Frame(ata, bg=KART)
    tk.Label(f, text=yazi, bg=KART, fg=METIN, font=(F, 11, "bold"),
             anchor="w").pack(fill="x")
    if alt:
        tk.Label(f, text=alt, bg=KART, fg=SOLUK, font=(F, 9), anchor="w",
                 justify="left", wraplength=560).pack(fill="x", pady=(2, 0))
    return f


def dugme(ata, yazi, komut, tur="normal", genislik=None):
    renkler = {
        "birincil": (AMBER, "#1a1206", "#fbbf24"),
        "normal":   (CIZGI, METIN, KART),
        "tehlike":  ("#3a1518", "#fca5a5", "#4a1c20"),
        "basari":   ("#123222", "#86efac", "#17452e"),
    }
    bg, fg, act = renkler.get(tur, renkler["normal"])
    b = tk.Button(ata, text=yazi, command=komut, bg=bg, fg=fg,
                  activebackground=act, activeforeground=fg,
                  font=(F, 9, "bold"), relief="flat", bd=0, cursor="hand2",
                  padx=14, pady=7, highlightthickness=0)
    if genislik:
        b.config(width=genislik)
    return b


class Kaydirilabilir(tk.Frame):
    """İçeriği taşmayan, gerekirse kaydırılabilen alan."""

    def __init__(self, ata, **kw):
        super().__init__(ata, bg=ARKA, **kw)
        # width=1: içerik genişliği pencereyi ZORLAMASIN (taşma/kırpılma olmasın)
        self.tuval = tk.Canvas(self, bg=ARKA, highlightthickness=0, bd=0,
                               width=1, height=1)
        self.cubuk = ttk.Scrollbar(self, orient="vertical", command=self.tuval.yview)
        self.tuval.configure(yscrollcommand=self.cubuk.set)
        self.cubuk.pack(side="right", fill="y")
        self.tuval.pack(side="left", fill="both", expand=True)
        self.ic = tk.Frame(self.tuval, bg=ARKA)
        self._pencere = self.tuval.create_window((0, 0), window=self.ic, anchor="nw")
        self.ic.bind("<Configure>", self._guncelle)
        self.tuval.bind("<Configure>", self._genislik)
        self.tuval.bind("<Enter>", lambda e: self._teker(True))
        self.tuval.bind("<Leave>", lambda e: self._teker(False))

    def _guncelle(self, _=None):
        self.tuval.configure(scrollregion=self.tuval.bbox("all"))

    def _genislik(self, olay):
        self.tuval.itemconfigure(self._pencere, width=olay.width)

    def _teker(self, bagla):
        if bagla:
            self.tuval.bind_all("<MouseWheel>", self._kaydir)
        else:
            self.tuval.unbind_all("<MouseWheel>")

    def _kaydir(self, olay):
        self.tuval.yview_scroll(int(-1 * (olay.delta / 120)), "units")


# ===========================================================================
#  ANA PENCERE
# ===========================================================================
class Panel:
    def __init__(self, kok, tepsiye_gizle=False):
        self.kok = kok
        self.tepsi = None
        self._cikiyor = False
        self.otomatik = True
        self._sayfa = {}
        self._aktif = None

        kok.title("GhostPilot")
        kok.configure(bg=ARKA)
        kok.geometry("920x720")
        kok.minsize(860, 620)
        try:
            import ikon
            ikon.uygula(kok, "GhostPilot")
        except Exception:
            pass

        self._ust()
        self._sekmeler()
        self._durum_cubugu()

        kok.protocol("WM_DELETE_WINDOW", self.tepsiye_gizle)
        kok.bind("<Unmap>", self._kucult_denetle)

        self._tepsi_kur()
        if self.otomatik:
            kok.after(600, self._otomatik_ac)
        self.yenile()
        self._dongu()
        if tepsiye_gizle:
            kok.after(400, self.tepsiye_gizle)

    # ------------------------------------------------------------------ üst
    def _ust(self):
        u = tk.Frame(self.kok, bg=UST, height=64)
        u.pack(fill="x")
        u.pack_propagate(False)

        sol = tk.Frame(u, bg=UST)
        sol.pack(side="left", padx=18)
        tk.Label(sol, text="GhostPilot", bg=UST, fg=METIN,
                 font=(F, 15, "bold")).pack(side="left", pady=16)
        tk.Label(sol, text="·", bg=UST, fg=SILIK,
                 font=(F, 12)).pack(side="left", padx=6)
        self.rozet = tk.Label(sol, text="…", bg=UST, fg=SILIK, font=(F, 9))
        self.rozet.pack(side="left", pady=(19, 16))

        # konumlandırma şeridi — rakip Desktop Commander'a karşı fark (üst şeritte)
        try:
            import diller as _dl
            self.motto = tk.Label(u, text=_dl.t("slogan"), bg=UST, fg=SILIK,
                                  font=(F, 8))
            self.motto.pack(side="left", padx=(4, 0), pady=(21, 16))
        except Exception:
            self.motto = None

        sag = tk.Frame(u, bg=UST)
        sag.pack(side="right", padx=18)
        # dil
        if diller:
            dk = tk.Frame(sag, bg=UST)
            dk.pack(side="right", padx=(16, 0), pady=20)
            self.dil_var = tk.StringVar(value=diller.dil())
            for kod in diller.DILLER:
                tk.Radiobutton(dk, text=kod.upper(), value=kod, variable=self.dil_var,
                               command=self.dil_degistir, bg=UST, fg=SILIK,
                               selectcolor=UST, activebackground=UST,
                               activeforeground=AMBER, font=(F, 8, "bold"),
                               highlightthickness=0, bd=0,
                               indicatoron=False, width=3,
                               relief="flat").pack(side="left")
        self.rozet_durum = tk.Label(sag, text="…", bg="#1e293b", fg=METIN,
                                    font=(F, 9, "bold"), padx=12, pady=5)
        self.rozet_durum.pack(side="right", pady=18)

    # ------------------------------------------------------------------ sekmeler
    def _sekmeler(self):
        bar = tk.Frame(self.kok, bg=ARKA)
        bar.pack(fill="x", padx=20, pady=(14, 8))
        self._sekme_dug = {}
        for anahtar, etiket in (("durum", t("durum")), ("lisans", t("lisans")),
                                ("paketler", t("paketler_sec"))):
            b = tk.Button(bar, text=etiket, command=lambda a=anahtar: self.sec(a),
                          bg=ARKA, fg=SOLUK, activebackground=ARKA, activeforeground=METIN,
                          font=(F, 10, "bold"), relief="flat", bd=0, cursor="hand2",
                          padx=18, pady=8, highlightthickness=0)
            b.pack(side="left", padx=(0, 4))
            self._sekme_dug[anahtar] = b

        self.govde = tk.Frame(self.kok, bg=ARKA)
        self.govde.pack(fill="both", expand=True, padx=20, pady=(0, 6))

        for anahtar in ("durum", "lisans", "paketler"):
            k = Kaydirilabilir(self.govde)
            self._sayfa[anahtar] = k
        self.durum_sayfasi()
        self.lisans_sayfasi()
        self.paketler_sayfasi()
        self.sec("durum")

    def sec(self, anahtar):
        for a, k in self._sayfa.items():
            k.pack_forget()
        self._sayfa[anahtar].pack(fill="both", expand=True)
        self._aktif = anahtar
        for a, b in self._sekme_dug.items():
            b.config(fg=(METIN if a == anahtar else SOLUK),
                     bg=(KART if a == anahtar else ARKA))

    # ------------------------------------------------------------------ sekme 1
    def durum_sayfasi(self):
        s = self._sayfa["durum"].ic
        s.configure(bg=ARKA)
        # ---- 4 durum kartı
        izg = tk.Frame(s, bg=ARKA)
        izg.pack(fill="x", pady=(0, 10))
        self.kartlar = {}
        for i, (anahtar, etiket) in enumerate([
                ("sunucu", t("sunucu")), ("bekci", t("bekci")),
                ("arac", t("arac")), ("mod", t("mod"))]):
            k = kart(izg)
            k.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 9, 0))
            izg.columnconfigure(i, weight=1, uniform="k")
            tk.Label(k, text=etiket.upper(), bg=KART, fg=SILIK, font=(F, 8, "bold"),
                     anchor="w").pack(fill="x", padx=15, pady=(13, 2))
            d = tk.Label(k, text="—", bg=KART, fg=METIN, font=(F, 13, "bold"), anchor="w")
            d.pack(fill="x", padx=15, pady=(0, 14))
            self.kartlar[anahtar] = d

        # ---- kullanım
        k = kart(s)
        k.pack(fill="x", pady=(0, 10))
        ic = tk.Frame(k, bg=KART)
        ic.pack(fill="x", padx=16, pady=13)
        tk.Label(ic, text=t("kullanim").upper(), bg=KART, fg=SILIK,
                 font=(F, 8, "bold"), anchor="w").pack(fill="x")
        self.kota_metin = tk.Label(ic, text="—", bg=KART, fg=METIN,
                                   font=(F, 16, "bold"), anchor="w")
        self.kota_metin.pack(fill="x", pady=(3, 9))
        self.cubuk = tk.Canvas(ic, height=8, bg="#0b1220", highlightthickness=0)
        self.cubuk.pack(fill="x")
        self.cubuk_parca = self.cubuk.create_rectangle(0, 0, 0, 8, fill=YESIL, width=0)
        self.kota_alt = tk.Label(ic, text="", bg=KART, fg=SOLUK, font=(F, 9),
                                 anchor="w", justify="left", wraplength=780)
        self.kota_alt.pack(fill="x", pady=(8, 0))

        # ---- erişim kontrolü
        k = kart(s)
        k.pack(fill="x", pady=(0, 10))
        ic = tk.Frame(k, bg=KART)
        ic.pack(fill="x", padx=16, pady=13)
        tk.Label(ic, text="UZAKTAN ERİŞİM", bg=KART, fg=SILIK,
                 font=(F, 8, "bold"), anchor="w").pack(fill="x")
        alt = tk.Frame(ic, bg=KART)
        alt.pack(fill="x", pady=(7, 0))
        self.btn_durdur = dugme(alt, "⛔  Erişimi durdur", lambda: self.komut("durdur"),
                                "tehlike")
        self.btn_durdur.pack(side="left")
        self.btn_basla = dugme(alt, "▶  Başlat", lambda: self.komut("basla"), "basari")
        self.btn_basla.pack(side="left", padx=8)
        dugme(alt, t("yenile"), self.yenile).pack(side="left")
        self.erisim_mesaj = tk.Label(ic, text="", bg=KART, fg=SOLUK, font=(F, 9),
                                     anchor="w", justify="left", wraplength=780)
        self.erisim_mesaj.pack(fill="x", pady=(9, 0))

        # ---- mod
        k = kart(s)
        k.pack(fill="x", pady=(0, 10))
        ic = tk.Frame(k, bg=KART)
        ic.pack(fill="x", padx=16, pady=13)
        tk.Label(ic, text=t("mod").upper(), bg=KART, fg=SILIK,
                 font=(F, 8, "bold"), anchor="w").pack(fill="x")
        alt = tk.Frame(ic, bg=KART)
        alt.pack(fill="x", pady=(7, 0))
        dugme(alt, "👁  " + t("salt_okunur"),
              lambda: self.komut("salt-okunur")).pack(side="left")
        dugme(alt, "✍  " + t("yazma"), lambda: self.komut("yazma")).pack(side="left", padx=8)
        dugme(alt, "🔑  " + t("izinleri_iptal"),
              lambda: self.komut("oauth-sil")).pack(side="left")

        # ---- izin verilen klasörler
        k = kart(s)
        k.pack(fill="x", pady=(0, 10))
        ic = tk.Frame(k, bg=KART)
        ic.pack(fill="x", padx=16, pady=13)
        tk.Label(ic, text=t("izin_klasor").upper(), bg=KART, fg=SILIK,
                 font=(F, 8, "bold"), anchor="w").pack(fill="x")
        self.klasorler = tk.Label(ic, text="—", bg=KART, fg=SOLUK, font=("Consolas", 9),
                                  anchor="w", justify="left", wraplength=780)
        self.klasorler.pack(fill="x", pady=(6, 4))
        tk.Label(ic, text='Ekle:  python kur.py izin "D:\\Proje"', bg=KART, fg=SILIK,
                 font=(F, 8), anchor="w").pack(fill="x")

    # ------------------------------------------------------------------ sekme 2
    def lisans_sayfasi(self):
        s = self._sayfa["lisans"].ic
        s.configure(bg=ARKA)
        k = kart(s)
        k.pack(fill="x", pady=(0, 10))
        ic = tk.Frame(k, bg=KART)
        ic.pack(fill="x", padx=16, pady=15)
        baslik(ic, t("lisans_gir"), t("lisans_alt")).pack(fill="x")
        satir = tk.Frame(ic, bg=KART)
        satir.pack(fill="x", pady=(11, 0))
        self.giris = tk.Entry(satir, font=("Consolas", 10), bg="#0b1220", fg=METIN,
                              insertbackground=AMBER, relief="flat", bd=0)
        self.giris.pack(side="left", fill="x", expand=True, ipady=9)
        self.giris.bind("<Return>", lambda e: self.lisans_uygula())
        dugme(satir, t("lisans_ekle"), self.lisans_uygula, "birincil").pack(
            side="left", padx=(8, 0))
        self.lisans_mesaj = tk.Label(ic, text="", bg=KART, fg=SOLUK, font=(F, 9),
                                     anchor="w", justify="left", wraplength=780)
        self.lisans_mesaj.pack(fill="x", pady=(10, 0))

        # mevcut durum
        k2 = kart(s)
        k2.pack(fill="x", pady=(0, 10))
        ic2 = tk.Frame(k2, bg=KART)
        ic2.pack(fill="x", padx=16, pady=15)
        tk.Label(ic2, text=t("durum").upper(), bg=KART, fg=SILIK,
                 font=(F, 8, "bold"), anchor="w").pack(fill="x")
        self.lisans_bilgi = tk.Label(ic2, text="", bg=KART, fg=METIN, font=(F, 10),
                                     anchor="w", justify="left", wraplength=780)
        self.lisans_bilgi.pack(fill="x", pady=(6, 0))

        # cihaz no
        k3 = kart(s)
        k3.pack(fill="x")
        ic3 = tk.Frame(k3, bg=KART)
        ic3.pack(fill="x", padx=16, pady=15)
        tk.Label(ic3, text=t("cihaz").upper(), bg=KART, fg=SILIK,
                 font=(F, 8, "bold"), anchor="w").pack(fill="x")
        try:
            import lisans
            mk = lisans.makine_kimligi()
        except Exception:
            mk = "—"
        tk.Label(ic3, text=mk, bg=KART, fg=MAVI, font=("Consolas", 11, "bold"),
                 anchor="w").pack(fill="x", pady=(4, 3))
        tk.Label(ic3, text=t("cihaz_no_ipucu"), bg=KART, fg=SILIK, font=(F, 8),
                 anchor="w", justify="left", wraplength=760).pack(fill="x")

    # ------------------------------------------------------------------ sekme 3
    def paketler_sayfasi(self):
        s = self._sayfa["paketler"].ic
        s.configure(bg=ARKA)
        try:
            import paketler as PK
        except Exception:
            return

        bas = tk.Frame(s, bg=ARKA)
        bas.pack(fill="x", pady=(0, 10))
        tk.Label(bas, text=PK.m("baslik"), bg=ARKA, fg=METIN,
                 font=(F, 15, "bold"), anchor="w").pack(fill="x")
        tk.Label(bas, text=PK.m("alt"), bg=ARKA, fg=SOLUK, font=(F, 9),
                 anchor="w", justify="left", wraplength=700).pack(fill="x", pady=(3, 0))

        # iki paket kartı yan yana
        izg = tk.Frame(s, bg=ARKA)
        izg.pack(fill="x", pady=(4, 10))
        izg.columnconfigure(0, weight=1, uniform="p")
        izg.columnconfigure(1, weight=1, uniform="p")

        # ÜCRETSİZ
        u = kart(izg)
        u.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        iu = tk.Frame(u, bg=KART)
        iu.pack(fill="both", expand=True, padx=16, pady=10)
        tk.Label(iu, text=PK.m("ucretsiz"), bg=KART, fg=METIN,
                 font=(F, 12, "bold"), anchor="w").pack(fill="x")
        tk.Label(iu, text=f"0 {PK.PARA_BIRIMI}", bg=KART, fg=AMBER,
                 font=(F, 19, "bold"), anchor="w").pack(fill="x", pady=(2, 2))
        tk.Label(iu, text=PK.m("devam"), bg=KART, fg=SILIK, font=(F, 8),
                 anchor="w").pack(fill="x", pady=(0, 6))
        for anahtar, var in PK.OZELLIKLER:
            r = tk.Frame(iu, bg=KART)
            r.pack(fill="x", pady=1)
            tk.Label(r, text=("✓" if var else "·"), bg=KART,
                     fg=(YESIL if var else "#334155"), font=(F, 10, "bold"),
                     width=2, anchor="w").pack(side="left")

            tk.Label(r, text=PK.m(anahtar), bg=KART,
                     fg=(METIN if var else SILIK), font=(F, 9),
                     anchor="w").pack(side="left")

        # PRO
        p = tk.Frame(izg, bg=VURGU_BG, highlightbackground=YESIL, highlightthickness=1)
        p.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ip = tk.Frame(p, bg=VURGU_BG)
        ip.pack(fill="both", expand=True, padx=16, pady=10)
        tk.Label(ip, text=PK.m("en_cok"), bg=VURGU_BG, fg=YESIL,
                 font=(F, 7, "bold"), anchor="w").pack(fill="x")
        tk.Label(ip, text="PRO", bg=VURGU_BG, fg=YESIL,
                 font=(F, 12, "bold"), anchor="w").pack(fill="x")
        tk.Label(ip, text=f"{PK.PARA_BIRIMI}{PK.AYLIK_FIYAT}{PK.m('ay')}",
                 bg=VURGU_BG, fg=AMBER, font=(F, 22, "bold"),
                 anchor="w").pack(fill="x", pady=(2, 2))
        tk.Label(ip, text=PK.m("sinirsiz"), bg=VURGU_BG, fg="#86efac", font=(F, 8),
                 anchor="w").pack(fill="x", pady=(0, 6))
        for anahtar, _ in PK.OZELLIKLER:
            r = tk.Frame(ip, bg=VURGU_BG)
            r.pack(fill="x", pady=1)
            tk.Label(r, text="✓", bg=VURGU_BG, fg=YESIL, font=(F, 10, "bold"),
                     width=2, anchor="w").pack(side="left")
            tk.Label(r, text=PK.m(anahtar), bg=VURGU_BG, fg=METIN,
                     font=(F, 9), anchor="w").pack(side="left")

        # alt bilgi + buton
        alt = tk.Frame(s, bg=ARKA)
        alt.pack(fill="x")
        tk.Label(alt, text=PK.m("fiyat_not"), bg=ARKA, fg=SILIK, font=(F, 8),
                 anchor="w", justify="left", wraplength=560).pack(side="left")

        # ---- rakip karşılaştırması (Desktop Commander ile fark) ----
        try:
            kk = tk.Frame(s, bg=ARKA)
            kk.pack(fill="x", pady=(6, 0))
            tk.Label(kk, text=PK.rakip_metni(), bg=ARKA, fg="#7dd3fc",
                     font=(F, 8), anchor="w", justify="left",
                     wraplength=820).pack(side="left")
        except Exception:
            pass
        dugme(alt, "💛  " + PK.m("katil"), self._bagis_ac, "birincil").pack(side="right")

    # ------------------------------------------------------------------ alt çubuk
    def _durum_cubugu(self):
        c = tk.Frame(self.kok, bg=UST, height=44)
        c.pack(fill="x", side="bottom")
        c.pack_propagate(False)
        self.alt_mesaj = tk.Label(c, text="", bg=UST, fg=SOLUK, font=(F, 9), anchor="w")
        self.alt_mesaj.pack(side="left", padx=20)
        dugme(c, t("kapat"), self.tepsiye_gizle).pack(side="right", padx=16, pady=9)
        dugme(c, "⏻  " + t("cikis_tam"), self.cikis_tam, "tehlike").pack(
            side="right", padx=(0, 6), pady=9)

    # ------------------------------------------------------------------ eylemler
    def _mesaj(self, yazi, tur="normal"):
        renk = {"ok": YESIL, "err": KIRMIZI, "normal": SOLUK}.get(tur, SOLUK)
        try:
            self.erisim_mesaj.config(text=yazi, fg=renk)
            self.alt_mesaj.config(text=yazi, fg=renk)
        except Exception:
            pass

    def komut(self, ad, dugm=None):
        def _():
            if dugm:
                dugm.config(state="disabled")
            self._mesaj("⏳ işleniyor…")
            try:
                r = subprocess.run([sys.executable, os.path.join(BURASI, "kur.py"), ad],
                                   capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=180)
                cikti = (r.stdout or "").strip()
                self._mesaj(cikti.splitlines()[-1][:160] if cikti else "tamam",
                            "ok" if r.returncode == 0 else "err")
            except Exception as e:
                self._mesaj(str(e), "err")
            finally:
                if dugm:
                    dugm.config(state="normal")
            self.yenile()
        threading.Thread(target=_, daemon=True).start()

    def lisans_uygula(self):
        k = self.giris.get().strip()
        if not k:
            self.lisans_mesaj.config(text=t("lisans_yok"), fg=SOLUK)
            return
        try:
            r = _gp().lisans_ayarla(k)
        except Exception as e:
            r = {"ok": False, "error": str(e)}
        if r.get("ok"):
            self.lisans_mesaj.config(text="✓ " + t("ls_gecerli") + " — " +
                                     str(r.get("message", "")), fg=YESIL)
            self.giris.delete(0, "end")
        else:
            self.lisans_mesaj.config(text="✕ " + t("ls_gecersiz") + ": " +
                                     str(r.get("error")), fg=KIRMIZI)
        self.yenile()

    def _bagis_ac(self):
        try:
            import paketler as PK
            import webbrowser
            webbrowser.open(PK.BAGIS_URL)
        except Exception:
            pass

    def web_panel(self):
        threading.Thread(
            target=lambda: subprocess.Popen([sys.executable,
                                             os.path.join(BURASI, "kur.py"), "panel"]),
            daemon=True).start()

    def dil_degistir(self):
        if diller:
            diller.dil_sec(self.dil_var.get())
        # sekmeleri yeniden kur
        for w in self.kok.winfo_children():
            w.destroy()
        self._sayfa, self._sekme_dug = {}, {}
        self._ust()
        self._sekmeler()
        self._durum_cubugu()
        self.yenile()

    # ------------------------------------------------------------------ yenile
    def yenile(self):
        try:
            G = _gp()
        except Exception:
            self.kartlar["sunucu"].config(text=t("modul_yok"), fg=KIRMIZI)
            return
        import kur as K
        try:
            port = K.port_cfg()
            h = K.relay_running(port)
        except Exception:
            h = None

        if h:
            self.kartlar["sunucu"].config(text=t("calisiyor"), fg=YESIL)
            self.kartlar["arac"].config(text=str(h.get("tools", "—")), fg=METIN)
            self.rozet.config(text=f"v{h.get('version', G.VERSION)}")
            self.rozet_durum.config(text="✅  " + t("erisim_acik"),
                                    bg="#123222", fg="#86efac")
        else:
            self.kartlar["sunucu"].config(text=t("durdu"), fg=KIRMIZI)
            self.kartlar["arac"].config(text="—", fg=SILIK)
            self.rozet.config(text=f"v{G.VERSION}")
            self.rozet_durum.config(text="⛔  " + t("erisim_kapali"),
                                    bg="#3a1518", fg="#fca5a5")
        # bekçi
        try:
            pid_f = os.path.join(G.CFG_DIR, "watchdog.pid")
            pid = int(open(pid_f).read().strip() or 0) if os.path.exists(pid_f) else 0
            canli = False
            if pid:
                if os.name == "nt":
                    r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                                       capture_output=True, text=True, timeout=10)
                    canli = str(pid) in (r.stdout or "")
                else:
                    os.kill(pid, 0)
                    canli = True
            self.kartlar["bekci"].config(text=t("aktif") if canli else t("yok"),
                                         fg=YESIL if canli else SILIK)
        except Exception:
            self.kartlar["bekci"].config(text=t("yok"), fg=SILIK)
        # mod
        try:
            self.kartlar["mod"].config(
                text=(t("salt_okunur") if G.CFG.get("read_only") else t("yazma")),
                fg=METIN)
        except Exception:
            pass
        # kullanım
        try:
            kd = G.kota_durum()
            lb = kd.get("lisans_bilgi") or {}
            if kd["pro"]:
                paket = lb.get("plan_adi", "")
                kalan = lb.get("kalan_gun")
                self.kota_metin.config(
                    text="PRO · " + t("sinirsiz") + (f"  ·  {paket}" if paket else ""),
                    fg="#86efac")
                self.cubuk.itemconfig(self.cubuk_parca, fill=YESIL)
                self.cubuk.coords(self.cubuk_parca, 0, 0,
                                  max(4, self.cubuk.winfo_width()), 8)
                self.kota_alt.config(
                    text=(f"{t('kalan_gun', n=kalan)}" if kalan is not None else ""),
                    fg=TURUNCU if lb.get("yenile") else SOLUK)
                self.lisans_bilgi.config(
                    text=(f"{lb.get('plan_adi','—')}  ·  {lb.get('id','—')}  ·  "
                          f"{lb.get('bagli_metin','—')}"), fg=METIN)
            else:
                kull, lim = kd["kullanilan"], kd["limit"]
                self.kota_metin.config(
                    text=f"{kull:,} / {lim:,}".replace(",", "."), fg=METIN)
                yuz = min(100, kd["yuzde"])
                w = max(1, int(self.cubuk.winfo_width() * yuz / 100))
                self.cubuk.coords(self.cubuk_parca, 0, 0, w, 8)
                self.cubuk.itemconfig(
                    self.cubuk_parca,
                    fill=(KIRMIZI if yuz >= 100 else AMBER if yuz >= 80 else YESIL))
                if kd.get("pro_iptal"):
                    self.kota_alt.config(text="⛔ " + str(kd.get("pro_iptal_neden")),
                                         fg=KIRMIZI)
                elif kd["asis"]:
                    self.kota_alt.config(text=t("sinir_doldu"), fg=KIRMIZI)
                else:
                    self.kota_alt.config(
                        text=(f"{t('kalan')}: {kd['kalan']:,}".replace(",", ".")
                              + "   ·   " + t("sifirlanma_alt")),
                        fg=SOLUK)
                    # %80 uyarısı — sürpriz olmasın (rakip standardı)
                    if kd.get("uyari_seviyesi") == "uyari":
                        self.kota_alt.config(text=kd.get("uyari_mesaji") + "  "
                                             + t("sifirlanma_alt"), fg=AMBER)
                    elif kd.get("uyari_seviyesi") == "sinir":
                        self.kota_alt.config(text=kd.get("uyari_mesaji") + "  "
                                             + t("sifirlanma_alt"), fg=KIRMIZI)
                self.lisans_bilgi.config(text=t("lisans_yok"), fg=SOLUK)
        except Exception:
            pass
        # klasörler
        try:
            kokler = (G.CFG.get("read_roots") or []) + (G.CFG.get("write_roots") or [])
            self.klasorler.config(
                text=("\n".join(sorted(set(kokler))[:6]) if kokler else "—"))
        except Exception:
            pass
        self.tepsi_durum_guncelle()

    def _dongu(self):
        try:
            self.yenile()
        except Exception:
            pass
        self.kok.after(3000, self._dongu)

    # ------------------------------------------------------------------ tepsi
    def _tepsi_kur(self):
        try:
            import tepsi
            self.tepsi = tepsi.Tepsi(
                baslik="GhostPilot", ipucu=t("tepsi_ipucu"),
                solda=lambda: self.kok.after(0, self.goster),
                sunucu=lambda: self.kok.after(0, self._tepsi_sunucu),
                cikis=lambda: self.kok.after(0, self.cikis_tam),
                durum=self._tepsi_durum)
            if self.tepsi.baslat():
                self.tepsi_durum_guncelle()
        except Exception:
            self.tepsi = None

    def _tepsi_durum(self):
        try:
            import kur as K
            return {"sunucu": bool(K.relay_running()),
                    "bekci": _gp()._watchdog_alive(),
                    "metin": self.kota_metin.cget("text")}
        except Exception:
            return {}

    def tepsi_durum_guncelle(self):
        if self.tepsi:
            try:
                self.tepsi.guncelle(self._tepsi_durum())
            except Exception:
                pass

    def _tepsi_sunucu(self):
        import kur as K
        self.komut("durdur" if K.relay_running() else "basla")

    def _otomatik_ac(self):
        try:
            import kur as K
            if not K.relay_running():
                K.basla(sessiz=True)
        except Exception:
            pass

    def _kucult_denetle(self, olay=None):
        try:
            if sys.platform.startswith("win") and self.kok.state() == "iconic":
                self.kok.after(250, self.tepsiye_gizle)
        except Exception:
            pass

    def tepsiye_gizle(self):
        self.kok.withdraw()
        if self.tepsi:
            try:
                self.tepsi.bildir("GhostPilot arka planda",
                                  "Saat kenarındaki simgeye tıklayarak geri açabilirsiniz.")
            except Exception:
                pass

    def goster(self):
        self.kok.deiconify()
        self.kok.lift()
        try:
            self.kok.focus_force()
        except Exception:
            pass
        self.yenile()

    def cikis_tam(self):
        if self._cikiyor:
            return
        self._cikiyor = True
        try:
            if self.tepsi:
                self.tepsi.durdur()
        except Exception:
            pass
        try:
            self._mesaj("⏳ " + t("kapatiliyor"), "normal")
        except Exception:
            pass
        try:
            import kur as K
            K.durdur(sessiz=True)
        except Exception:
            pass
        try:
            self.kok.destroy()
        except Exception:
            pass
        os._exit(0)


TURUNCU = AMBER


def main():
    # Hata olsa bile pencere KAPANMASIN: sebep ekranda ve hata.log'da görünür.
    if not TK:
        if hata:
            hata.yaz("ui", "tkinter yok — tarayıcı paneli açılıyor")
        return subprocess.call([sys.executable, os.path.join(BURASI, "kur.py"), "panel"])
    try:
        kok = tk.Tk()
    except Exception as e:
        if hata:
            hata.yaz_hata(type(e), e, e.__traceback__, "PENCERE AÇILAMADI")
        _hata_penceresi("Pencere açılamadı", e)
        return 1
    try:
        kok.tk.call("tk", "scaling", 1.15)
    except Exception:
        pass
    try:
        Panel(kok, tepsiye_gizle=("--tepsi" in sys.argv))
    except Exception as e:
        if hata:
            hata.yaz_hata(type(e), e, e.__traceback__, "PANEL OLUŞTURULAMADI")
        try:
            kok.destroy()
        except Exception:
            pass
        _hata_penceresi("Arayüz oluşturulamadı", e)
        return 1
    try:
        kok.mainloop()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        if hata:
            hata.yaz_hata(type(e), e, e.__traceback__, "ARAYÜZ DÖNGÜSÜ ÇÖKTÜ")
        _hata_penceresi("Arayüz beklenmedik şekilde durdu", e)
        return 1
    return 0


def _hata_penceresi(baslik, exc):
    """Kullanıcıya gösterilecek hata penceresi — pencere anında kapanmasın."""
    yol = hata.yol() if hata else "(günlük yok)"
    try:
        from tkinter import messagebox, scrolledtext
        p = tk.Tk()
        p.title("GhostPilot — hata")
        p.configure(bg="#0e1628")
        p.geometry("720x420")
        tk.Label(p, text=baslik, bg="#0e1628", fg="#f87171",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=18, pady=(16, 4))
        tk.Label(p, text=f"{type(exc).__name__}: {exc}", bg="#0e1628", fg="#e2e8f0",
                 wraplength=680, justify="left", anchor="w",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=(0, 10))
        tk.Label(p, text=f"Ayrıntılar: {yol}", bg="#0e1628", fg="#94a3b8",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=18)
        kutu = scrolledtext.ScrolledText(p, height=12, bg="#080d1a", fg="#cbd5e1",
                                         insertbackground="#cbd5e1",
                                         font=("Consolas", 8), relief="flat")
        kutu.pack(fill="both", expand=True, padx=18, pady=10)
        try:
            kutu.insert("end", hata.son(40) if hata else str(exc))
        except Exception:
            kutu.insert("end", str(exc))
        kutu.configure(state="disabled")
        tk.Button(p, text="Kapat", command=p.destroy, bg="#1e293b", fg="#e2e8f0",
                  relief="flat", padx=22, pady=6).pack(pady=(0, 14))
        p.mainloop()
    except Exception:
        pass


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — kurulum_ui.py  ·  Kurulum Sihirbazı (grafik arayüz)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  4 adım:  Dil → Özet → Lisans anahtarı → Kurulum
#  Tkinter kullanır (Python ile birlikte gelir, ek kurulum yok).
#  Tkinter yoksa (nadir) otomatik olarak konsol kurulumuna düşer.
# ============================================================================

import os
import platform
import subprocess
import sys
import threading

import kurulum

BURASI = os.path.dirname(os.path.abspath(__file__))
SISTEM = platform.system()

KOYU = "#0b1120"
KART = "#111a2e"
CIZGI = "#1e2d4a"
METIN = "#e2e8f0"
SOLUK = "#8b9bb4"
AMBER = "#f59e0b"
CYAN = "#22d3ee"
YESIL = "#22c55e"
KIRMIZI = "#ef4444"

try:
    import tkinter as tk
    from tkinter import ttk
    TK = True
except Exception:
    TK = False

sys.path.insert(0, BURASI)
try:
    import diller
    from diller import t
except Exception:                                     # çok nadir
    def t(k, **kw):
        return k
    diller = None


# ===========================================================================
#  Konsol yedeği (Tkinter yoksa)
# ===========================================================================
def konsol_kurulum():
    print("\n  👻 GhostPilot — kurulum (konsol)\n")
    if diller:
        print("  Diller / Languages: " + " · ".join(
            f"{i+1}) {ad}" for i, ad in enumerate(diller.DILLER.values())))
        try:
            sec = input("  Dil (1-4, Enter=1): ").strip() or "1"
            diller.dil_sec(list(diller.DILLER)[max(0, min(3, int(sec) - 1))])
        except Exception:
            pass
    print("\n  " + t("lisans_alt"))
    try:
        k = input("\n  " + t("lisans_kutu") + ": ").strip()
    except (EOFError, KeyboardInterrupt):
        k = ""
    if k:
        r = subprocess.run([sys.executable, os.path.join(BURASI, "kur.py"),
                            "lisans", k], text=True)
        print()
    return subprocess.call([sys.executable, os.path.join(BURASI, "setup.py")])


# ===========================================================================
#  Grafik sihirbaz
# ===========================================================================
class Sihirbaz:
    def __init__(self, kok):
        self.kok = kok
        self.sayfa = 0
        self.lisans_anahtar = ""
        self.lisans_durum = ""
        self.lisans_ok = False
        self.kurulum_bitti = False
        self.basarili = False

        kok.title("GhostPilot — " + t("kurulum"))
        kok.configure(bg=KOYU)
        kok.geometry("820x600")
        kok.minsize(760, 560)
        try:
            import ikon as _ikon
            _ikon.uygula(kok, "GhostPilot — " + t("kurulum"))
        except Exception:
            pass

        # ---- üst şerit
        self.ust = tk.Frame(kok, bg=KART, height=64)
        self.ust.pack(fill="x")
        self.ust.pack_propagate(False)
        tk.Label(self.ust, text="G h o s t P i l o t", bg=KART, fg=AMBER,
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=22)
        self.asama = tk.Label(self.ust, text="", bg=KART, fg=SOLUK,
                              font=("Segoe UI", 10))
        self.asama.pack(side="right", padx=22)

        # ---- içerik
        self.govde = tk.Frame(kok, bg=KOYU)
        self.govde.pack(fill="both", expand=True, padx=26, pady=18)

        # ---- alt düğmeler
        self.alt = tk.Frame(kok, bg=KOYU)
        self.alt.pack(fill="x", padx=26, pady=(0, 20))
        self.geri = self._dugme(self.alt, t("geri"), self.onceki, ikincil=True)
        self.geri.pack(side="left")
        self.ileri = self._dugme(self.alt, t("devam"), self.sonraki)
        self.ileri.pack(side="right")

        self.sayfalar = [self.sayfa_dil, self.sayfa_ozet,
                         self.sayfa_lisans, self.sayfa_kurulum]
        self.ciz()

    # ------------------------------------------------------------------ yardımcı
    def _dugme(self, ata, yazi, komut, ikincil=False, genis=16):
        b = tk.Button(ata, text=yazi, command=komut, font=("Segoe UI", 10, "bold"),
                      relief="flat", cursor="hand2", padx=18, pady=9,
                      bg=(CIZGI if ikincil else AMBER),
                      fg=(METIN if ikincil else "#1a1206"),
                      activebackground=(KART if ikincil else "#fbbf24"),
                      activeforeground=(METIN if ikincil else "#1a1206"),
                      width=genis, bd=0, highlightthickness=0)
        return b

    def temizle(self):
        for w in self.govde.winfo_children():
            w.destroy()

    def baslik(self, buyuk, alt=""):
        tk.Label(self.govde, text=buyuk, bg=KOYU, fg=METIN,
                 font=("Segoe UI", 18, "bold"), anchor="w").pack(fill="x", pady=(6, 6))
        if alt:
            tk.Label(self.govde, text=alt, bg=KOYU, fg=SOLUK, font=("Segoe UI", 10),
                     anchor="w", justify="left", wraplength=740).pack(fill="x")

    def ciz(self):
        self.temizle()
        self.asama.config(text=t("asama", n=self.sayfa + 1, t=len(self.sayfalar)))
        self.geri.config(state=("normal" if self.sayfa > 0 and not self.kurulum_bitti
                                else "disabled"))
        self.ileri.config(state="normal",
                          text=(t("kapat") if self.sayfa == 3 else t("devam")))
        if self.sayfa == 3:
            self.geri.config(state="disabled")
        self.sayfalar[self.sayfa]()

    # ------------------------------------------------------------------ 1 · DİL
    def sayfa_dil(self):
        self.baslik(t("hos_geldin"), t("hos_alt"))
        tk.Label(self.govde, text=t("dil_sec"), bg=KOYU, fg=METIN,
                 font=("Segoe UI", 11, "bold"), anchor="w").pack(fill="x", pady=(22, 10))
        kutu = tk.Frame(self.govde, bg=KOYU)
        kutu.pack(fill="x")
        self.dil_secim = tk.StringVar(value=diller.dil() if diller else "tr")
        for i, (kod, ad) in enumerate((diller.DILLER if diller else {"tr": "Türkçe"}).items()):
            r = tk.Radiobutton(kutu, text=f"{ad}  ({kod.upper()})", value=kod,
                               variable=self.dil_secim, command=self.dil_degistir,
                               bg=KOYU, fg=METIN, selectcolor=KART, activebackground=KOYU,
                               activeforeground=AMBER, font=("Segoe UI", 11),
                               anchor="w", highlightthickness=0, bd=0)
            r.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 40), pady=8)

    def dil_degistir(self):
        if diller:
            diller.dil_sec(self.dil_secim.get())
        self.kok.title("GhostPilot — " + t("kurulum"))
        self.geri.config(text=t("geri"))
        self.ciz()

    # ------------------------------------------------------------------ 2 · ÖZET
    def sayfa_ozet(self):
        self.baslik(t("kurulum"), t("hos_alt"))
        kart = tk.Frame(self.govde, bg=KART, highlightbackground=CIZGI, highlightthickness=1)
        kart.pack(fill="x", pady=(22, 0))
        satirlar = [
            ("●", "Sistem", f"{SISTEM} · {platform.machine()} · Python {platform.python_version()}"),
            ("●", t("adim_venv"), ".venv — " + ("izole kurulum" if SISTEM != "Windows" else "izole kurulum")),
            ("●", t("adim_paket"), "pip · Pillow"),
            ("●", t("adim_tailscale"), "tailscale.com — " + ("ChatGPT için" )),
            ("●", t("adim_kisayol"), "Masaüstü + menü"),
        ]
        for i, (simge, a, b) in enumerate(satirlar):
            f = tk.Frame(kart, bg=KART)
            f.pack(fill="x", padx=18, pady=9)
            tk.Label(f, text=simge, bg=KART, fg=AMBER, font=("Segoe UI", 12),
                     width=3, anchor="w").pack(side="left")
            tk.Label(f, text=a, bg=KART, fg=METIN, font=("Segoe UI", 10, "bold"),
                     width=22, anchor="w").pack(side="left")
            tk.Label(f, text=b, bg=KART, fg=SOLUK, font=("Segoe UI", 10),
                     anchor="w").pack(side="left")
            if i < len(satirlar) - 1:
                tk.Frame(kart, bg=CIZGI, height=1).pack(fill="x", padx=18)
        try:
            import paketler as PK
            kutu = tk.Frame(self.govde, bg=KART, highlightbackground=CIZGI,
                            highlightthickness=1)
            kutu.pack(fill="x", pady=(0, 10))
            ic = tk.Frame(kutu, bg=KART)
            ic.pack(fill="x", padx=14, pady=10)
            tk.Label(ic, text=f"{PK.m('ucretsiz')}  0 {PK.PARA_BIRIMI}   ·   "
                              f"PRO  {PK.PARA_BIRIMI}{PK.AYLIK_FIYAT}{PK.m('ay')}",
                     bg=KART, fg=AMBER, font=("Segoe UI", 10, "bold"),
                     anchor="w").pack(fill="x")
            tk.Label(ic, text=PK.m("bagis_not"), bg=KART, fg=SOLUK,
                     font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(2, 0))
        except Exception:
            pass
        tk.Label(self.govde, text=t("lisans_alt"), bg=KOYU, fg=SOLUK,
                 font=("Segoe UI", 9), wraplength=740, justify="left",
                 anchor="w").pack(fill="x", pady=16)

    # ------------------------------------------------------------------ 3 · LİSANS
    def sayfa_lisans(self):
        self.baslik(t("lisans_baslik"), t("lisans_alt"))
        kart = tk.Frame(self.govde, bg=KART, highlightbackground=CIZGI, highlightthickness=1)
        kart.pack(fill="x", pady=(24, 0))
        ic = tk.Frame(kart, bg=KART)
        ic.pack(fill="x", padx=18, pady=18)
        tk.Label(ic, text=t("lisans_kutu"), bg=KART, fg=SOLUK,
                 font=("Segoe UI", 9), anchor="w").pack(fill="x")
        self.giris = tk.Entry(ic, font=("Consolas", 10), bg="#0d1626", fg=METIN,
                              insertbackground=AMBER, relief="flat", bd=0)
        self.giris.pack(fill="x", ipady=9, pady=(6, 12))
        self.giris.insert(0, self.lisans_anahtar)
        self.giris.bind("<Return>", lambda e: self.lisans_dogrula())
        dug = tk.Frame(ic, bg=KART)
        dug.pack(fill="x")
        self._dugme(dug, t("lisans_ekle"), self.lisans_dogrula,
                    genis=18).pack(side="left")
        self._dugme(dug, t("lisans_atla"), self.sonraki, ikincil=True,
                    genis=16).pack(side="left", padx=10)
        self.lisans_lbl = tk.Label(self.govde, text=self.lisans_durum, bg=KOYU,
                                   fg=SOLUK, font=("Segoe UI", 10), wraplength=740,
                                   justify="left", anchor="w")
        self.lisans_lbl.pack(fill="x", pady=16)
        tk.Label(self.govde, text=t("cihaz_no") + ":",
                 bg=KOYU, fg=SOLUK, font=("Segoe UI", 9), anchor="w").pack(fill="x")
        try:
            import lisans
            mk = lisans.makine_kimligi()
        except Exception:
            mk = "(kullanılamıyor)"
        tk.Label(self.govde, text=mk, bg=KOYU, fg=CYAN,
                 font=("Consolas", 11, "bold"), anchor="w").pack(fill="x")
        tk.Label(self.govde, text=t("cihaz_no_ipucu"), bg=KOYU, fg=SOLUK,
                 wraplength=760, justify="left",
                 font=("Segoe UI", 8), anchor="w").pack(fill="x")

    def lisans_dogrula(self):
        k = self.giris.get().strip()
        self.lisans_anahtar = k
        if not k:
            self.lisans_durum = t("lisans_yok")
            self.lisans_lbl.config(text=self.lisans_durum, fg=SOLUK)
            return
        try:
            import lisans
            b = lisans.bilgi(k)
        except Exception as e:
            b = {"ok": False, "error": str(e)}
        if b.get("ok"):
            self.lisans_ok = True
            self.lisans_durum = t("lisans_gecerli", plan=b.get("plan_adi"),
                                  bitis=b.get("bitis"))
            self.lisans_lbl.config(text=self.lisans_durum, fg=YESIL)
            self.ileri.config(text=t("devam"))
        else:
            self.lisans_ok = False
            self.lisans_durum = t("lisans_gecersiz", neden=b.get("error", "?"))
            self.lisans_lbl.config(text=self.lisans_durum, fg=KIRMIZI)

    # ------------------------------------------------------------------ 4 · KURULUM
    def sayfa_kurulum(self):
        self.baslik(t("kurulum_baslik"), t("kurulum_alt"))
        self.konsol = tk.Text(self.govde, bg="#070b14", fg=METIN, font=("Consolas", 9),
                              relief="flat", bd=0, height=17, insertbackground=METIN,
                              wrap="word")
        self.konsol.pack(fill="both", expand=True, pady=(16, 10))
        self.konsol.insert("end", f"  GhostPilot v{kurulum._surum()} — kurulum günlüğü\n\n")
        self.konsol.config(state="disabled")
        self.ileri.config(state="disabled", text=t("kapat"))
        threading.Thread(target=self._kur, daemon=True).start()

    def _yaz(self, s):
        def _():
            self.konsol.config(state="normal")
            self.konsol.insert("end", s)
            self.konsol.see("end")
            self.konsol.config(state="disabled")
        try:
            self.kok.after(0, _)
        except Exception:
            pass

    def _kur(self):
        try:
            # 1) sanal ortam
            self._yaz("  [1/5] " + t("adim_venv") + "…\n")
            sys.path.insert(0, BURASI)
            import sanalortam
            self.py = sanalortam.olustur(sessiz=True) or sys.executable
            self._yaz(f"        ✅ {self.py}\n")

            # 2) kur.py oto (gereksinimler + sunucu + kısayol)
            self._yaz("  [2/5] " + t("adim_paket") + " · " + t("adim_tailscale") + "…\n")
            env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1",
                       GP_UI="1")
            p = subprocess.Popen([self.py, os.path.join(BURASI, "setup.py")],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, encoding="utf-8", errors="replace",
                                 env=env, bufsize=1)
            for satir in p.stdout:
                self._yaz("  " + satir)
            p.wait()
            self.basarili = (p.returncode == 0)
            self._yaz(f"\n  → çıkış kodu: {p.returncode}\n")

            # 3) lisansı uygula
            if self.lisans_anahtar:
                self._yaz("  [3/5] " + t("lisans_gir") + "…\n")
                r = subprocess.run([self.py, os.path.join(BURASI, "kur.py"),
                                    "lisans", self.lisans_anahtar],
                                   capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", env=env)
                self._yaz("  " + (r.stdout or ""))
            else:
                self._yaz("  [3/5] " + t("lisans_yok") + "\n")

            # 4) adres
            self._yaz("  [4/5] " + t("adres") + "…\n")
            adres = ""
            try:
                ozet = os.path.join(BURASI, "KURULUM-OZET.txt")
                for satir in open(ozet, encoding="utf-8"):
                    if "Sunucu URL" in satir or "Server URL" in satir:
                        adres = satir.split(":", 1)[1].strip()
            except Exception:
                pass
            self.adres = adres
            self._yaz(f"        {adres or '(tailscale gerekli)'}\n")

            # 5) bitti
            self._yaz("\n  [5/5] " + t("bitti_baslik") + "\n")
            try:
                self.kok.after(0, self._bitti)
            except Exception:
                pass
        except Exception as e:
            self._yaz(f"\n  ❌ {t('hata')}: {e}\n")
            try:
                self.kok.after(0, self._bitti)
            except Exception:
                pass

    def _bitti(self):
        self.kurulum_bitti = True
        self.temizle()
        self.baslik(t("bitti_baslik"), t("bitti_alt"))
        adres = getattr(self, "adres", "") or "(tailscale gerekli)"
        kart = tk.Frame(self.govde, bg=KART, highlightbackground=CIZGI, highlightthickness=1)
        kart.pack(fill="x", pady=(18, 0))
        ic = tk.Frame(kart, bg=KART)
        ic.pack(fill="x", padx=18, pady=16)
        tk.Label(ic, text=t("adres"), bg=KART, fg=SOLUK, font=("Segoe UI", 9),
                 anchor="w").pack(fill="x")
        satir = tk.Frame(ic, bg=KART)
        satir.pack(fill="x", pady=(6, 0))
        e = tk.Entry(satir, font=("Consolas", 10), bg="#0d1626", fg=CYAN,
                     relief="flat", bd=0)
        e.pack(side="left", fill="x", expand=True, ipady=8)
        e.insert(0, adres)
        e.config(state="readonly")

        def kopyala():
            try:
                self.kok.clipboard_clear()
                self.kok.clipboard_append(adres)
                kb.config(text="✓ " + t("kopyalandi"))
            except Exception:
                pass

        kb = self._dugme(satir, t("kopyala"), kopyala, ikincil=True, genis=12)
        kb.pack(side="left", padx=(10, 0))
        tk.Label(self.govde, text=t("chatgpt_adim"), bg=KOYU, fg=SOLUK,
                 font=("Segoe UI", 9), justify="left", anchor="w",
                 wraplength=740).pack(fill="x", pady=16)
        alt = tk.Frame(self.govde, bg=KOYU)
        alt.pack(fill="x")
        self._dugme(alt, t("panel"), self.panel_ac, ikincil=True, genis=16).pack(side="left")
        self._dugme(alt, t("kapat"), self.kok.destroy, genis=14).pack(side="right")
        self.ileri.pack_forget()
        self.geri.pack_forget()

    def panel_ac(self):
        py = getattr(self, "py", sys.executable)
        try:
            subprocess.Popen([py, os.path.join(BURASI, "kur.py"), "panel"])
        except Exception:
            pass

    # ------------------------------------------------------------------ gezinme
    def sonraki(self):
        if self.sayfa == 2:
            self.lisans_anahtar = self.giris.get().strip()
        if self.sayfa >= len(self.sayfalar) - 1:
            self.kok.destroy()
            return
        self.sayfa += 1
        self.ciz()

    def onceki(self):
        if self.sayfa > 0:
            self.sayfa -= 1
            self.ciz()


def main():
    try:
        import ikon as _ikon
        _ikon.konsol_ikonu()
    except Exception:
        pass
    if not TK:
        return konsol_kurulum()
    kok = tk.Tk()
    try:
        kok.tk.call("tk", "scaling", 1.25)
    except Exception:
        pass
    Sihirbaz(kok)
    kok.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())

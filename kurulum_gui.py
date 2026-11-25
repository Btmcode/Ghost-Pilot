#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — kurulum_gui.py  ·  Grafik kurulum sihirbazı
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Ekranlar:  Hoş geldiniz → Klasör seç → İlerleme → Bitti
#  Hiçbir adımda .bat tıklama, cmd penceresi veya el ile komut yok.
# ============================================================================

import os
import queue
import sys
import threading

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)

try:
    import tkinter as tk
    from tkinter import filedialog
    TK = True
except Exception:
    TK = False

KOYU, KART, CIZGI = "#0b1120", "#111a2e", "#1e2d4a"
METIN, SOLUK = "#e2e8f0", "#8b9bb4"
AMBER, YESIL, KIRMIZI = "#f59e0b", "#22c55e", "#ef4444"

try:
    import diller
    from diller import t
except Exception:
    diller = None

    def t(k, **kw):
        return k


class Sihirbaz:
    def __init__(self, kok, hedef=None, sessiz=False):
        self.kok = kok
        self.hedef = hedef or ""
        self.sessiz = sessiz
        self.kuyruk = queue.Queue()
        self.bitti = False
        kok.title("GhostPilot — Kurulum")
        kok.configure(bg=KOYU)
        kok.geometry("760x560")
        kok.resizable(False, False)
        try:
            import ikon
            ikon.uygula(kok, "GhostPilot — Kurulum")
        except Exception:
            pass
        self._cerceve = tk.Frame(kok, bg=KOYU)
        self._cerceve.pack(fill="both", expand=True)
        self.hos_geldin()

    # ------------------------------------------------------------ yardımcı
    def _temizle(self):
        for w in self._cerceve.winfo_children():
            w.destroy()

    def _dugme(self, ata, yazi, komut, birincil=True, genislik=None):
        b = tk.Button(ata, text=yazi, command=komut, relief="flat", cursor="hand2",
                      font=("Segoe UI", 10, "bold"), padx=20, pady=10, bd=0,
                      bg=(AMBER if birincil else CIZGI),
                      fg=("#1a1206" if birincil else METIN),
                      activebackground=("#fbbf24" if birincil else KART),
                      activeforeground=("#1a1206" if birincil else AMBER))
        if genislik:
            b.config(width=genislik)
        return b

    def _baslik(self, ana, alt=""):
        tk.Label(self._cerceve, text=ana, bg=KOYU, fg=AMBER,
                 font=("Segoe UI", 19, "bold"), anchor="w").pack(
                     fill="x", padx=34, pady=(30, 4))
        if alt:
            tk.Label(self._cerceve, text=alt, bg=KOYU, fg=SOLUK, anchor="w",
                     justify="left", wraplength=690,
                     font=("Segoe UI", 10)).pack(fill="x", padx=34)

    # ------------------------------------------------------------ 1) hoş geldin
    def hos_geldin(self):
        self._temizle()
        self._baslik("👻 GhostPilot Kurulumu",
                     "Bu sihirbaz programı bilgisayarınıza kurar. Teknik bilgi "
                     "gerekmez; her adımda size ne yapıldığını gösterir.")
        k = tk.Frame(self._cerceve, bg=KART, highlightbackground=CIZGI,
                     highlightthickness=1)
        k.pack(fill="x", padx=34, pady=22)
        ic = tk.Frame(k, bg=KART)
        ic.pack(fill="x", padx=18, pady=15)
        for i, satir in enumerate([
                "Dosyalar seçtiğiniz klasöre kopyalanır",
                "Gerekli paketler kendi sanal ortamına kurulur",
                "Masaüstüne ve Başlat menüsüne 👻 kısayol eklenir",
                "\"Programlar\" listesine kaydedilir (tek tıkla kaldırılır)",
                "Lisans anahtarınız varsa sorulur",
        ], start=1):
            tk.Label(ic, text=f"{i}.  {satir}", bg=KART, fg=METIN,
                     font=("Segoe UI", 10), anchor="w").pack(fill="x", pady=2)
        tk.Label(ic, text="Yönetici hakkı GEREKMEZ · Program Files'a yazılmaz",
                 bg=KART, fg=YESIL, font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(fill="x", pady=(9, 0))
        alt = tk.Frame(self._cerceve, bg=KOYU)
        alt.pack(fill="x", padx=34, pady=(0, 26))
        self._dugme(alt, "Devam →", self.klasor_sec).pack(side="right")
        self._dugme(alt, "İptal", self.kok.destroy, birincil=False).pack(side="right", padx=8)

    # ------------------------------------------------------------ 2) klasör
    def klasor_sec(self):
        self._temizle()
        import kurulum
        self._baslik("Kurulum klasörü",
                     "Programın kurulacağı yeri seçin. Varsayılan konum yönetici "
                     "hakkı gerektirmez ve önerilir.")
        k = tk.Frame(self._cerceve, bg=KART, highlightbackground=CIZGI,
                     highlightthickness=1)
        k.pack(fill="x", padx=34, pady=(22, 10))
        ic = tk.Frame(k, bg=KART)
        ic.pack(fill="x", padx=18, pady=16)
        tk.Label(ic, text="Kurulacak klasör", bg=KART, fg=SOLUK,
                 font=("Segoe UI", 9), anchor="w").pack(fill="x")
        self.yol_var = tk.StringVar(value=self.hedef or kurulum._varsayilan_dizin())
        giris = tk.Entry(ic, textvariable=self.yol_var, font=("Consolas", 10),
                         bg="#0d1626", fg=METIN, insertbackground=AMBER,
                         relief="flat", bd=0)
        giris.pack(fill="x", ipady=9, pady=(4, 8))
        satir = tk.Frame(ic, bg=KART)
        satir.pack(fill="x")
        self._dugme(satir, "📁 Gözat…", self.gozat, birincil=False).pack(side="left")
        self._dugme(satir, "Önerileni kullan", self.varsayilana_don,
                    birincil=False).pack(side="left", padx=8)
        self.uyari = tk.Label(ic, text="", bg=KART, fg=SOLUK, anchor="w",
                              justify="left", wraplength=650, font=("Segoe UI", 9))
        self.uyari.pack(fill="x", pady=(10, 0))
        tk.Label(self._cerceve, bg=KOYU, fg=SOLUK, anchor="w", justify="left",
                 wraplength=690, font=("Segoe UI", 8),
                 text="Not: C:\\Program Files gibi korumalı klasörler önerilmez — "
                      "kaldırma ve güncelleme sırasında izin sorunu çıkarır.").pack(
                          fill="x", padx=34)
        alt = tk.Frame(self._cerceve, bg=KOYU)
        alt.pack(fill="x", padx=34, pady=22)
        self.ileri = self._dugme(alt, "Kur →", self.kur_baslat)
        self.ileri.pack(side="right")
        self._dugme(alt, "← Geri", self.hos_geldin, birincil=False).pack(side="right", padx=8)
        self.yol_var.trace_add("write", lambda *a: self._yol_kontrol())

    def _yol_kontrol(self):
        yol = (self.yol_var.get() or "").strip().strip('"')
        if not yol:
            self.uyari.config(text="", fg=SOLUK)
            self.ileri.config(state="disabled")
            return
        d = yol.lower().replace("/", "\\")
        if "program files" in d or d.startswith("c:\\windows"):
            self.uyari.config(text="⚠️  Bu klasör korumalı. Önerilen konumu kullanın.",
                              fg=AMBER)
            self.ileri.config(state="disabled")
        else:
            self.uyari.config(text="✅ Bu klasöre kurulacak.", fg=YESIL)
            self.ileri.config(state="normal")

    def gozat(self):
        d = filedialog.askdirectory(title="Kurulum klasörü seçin",
                                    initialdir=os.path.dirname(self.yol_var.get()
                                                               or os.path.expanduser("~")))
        if d:
            self.yol_var.set(os.path.join(d, "GhostPilot"))

    def varsayilana_don(self):
        import kurulum
        self.yol_var.set(kurulum._varsayilan_dizin())

    # ------------------------------------------------------------ 3) ilerleme
    def kur_baslat(self):
        import kurulum
        hedef = os.path.abspath((self.yol_var.get() or "").strip().strip('"'))
        ok, hata = kurulum.hedef_hazirla(hedef)
        if not ok:
            self.uyari.config(text=f"❌ Bu klasöre yazılamıyor: {hata}", fg=KIRMIZI)
            return
        self._temizle()
        self._baslik("Kuruluyor…", "Pencereyi kapatmayın. 1–3 dakika sürer.")
        k = tk.Frame(self._cerceve, bg=KART, highlightbackground=CIZGI,
                     highlightthickness=1)
        k.pack(fill="both", expand=True, padx=34, pady=(20, 10))
        ic = tk.Frame(k, bg=KART)
        ic.pack(fill="both", expand=True, padx=18, pady=16)
        self.adim_lbl = tk.Label(ic, text="Hazırlanıyor…", bg=KART, fg=METIN,
                                 font=("Segoe UI", 11, "bold"), anchor="w")
        self.adim_lbl.pack(fill="x")
        self.cubuk = tk.Canvas(ic, height=12, bg=CIZGI, highlightthickness=0)
        self.cubuk.pack(fill="x", pady=(10, 12))
        self.parca = self.cubuk.create_rectangle(0, 0, 0, 12, fill=AMBER, width=0)
        self.kayit = tk.Text(ic, height=11, bg="#0d1626", fg=SOLUK, relief="flat",
                             font=("Consolas", 9), bd=0, wrap="word")
        self.kayit.pack(fill="both", expand=True)
        self.kayit.config(state="disabled")
        threading.Thread(target=self._is, args=(hedef,), daemon=True).start()
        self.kok.after(120, self._kuyruk_isle)

    def _log(self, s, tur="dim"):
        self.kayit.config(state="normal")
        self.kayit.insert("end", s + "\n")
        self.kayit.see("end")
        self.kayit.config(state="disabled")

    def _ilerleme(self, yuz, metin=None):
        w = max(1, int(self.cubuk.winfo_width() * yuz / 100))
        self.cubuk.coords(self.parca, 0, 0, w, 12)
        if metin:
            self.adim_lbl.config(text=metin)

    def _is(self, hedef):
        """Arka planda kurulum (arayüz donmasın)."""
        import kurulum
        try:
            self.kuyruk.put(("log", "Kurulum yeri: " + hedef))
            self.kuyruk.put(("ilerleme", (5, "Dosyalar kopyalanıyor…")))
            k, a = kurulum.dosyalari_kopyala(
                hedef, lambda i, t_, ad: self.kuyruk.put(
                    ("ilerleme", (5 + int(35 * i / max(1, t_)), f"Kopyalanıyor: {ad}"))))
            self.kuyruk.put(("log", f"{k} dosya kopyalandı"))
            self.kuyruk.put(("ilerleme", (45, "Sanal ortam oluşturuluyor…")))
            ok, mesaj = kurulum.sanalortam_kur(
                hedef, lambda s: self.kuyruk.put(("log", s)))
            self.kuyruk.put(("log", "Sanal ortam hazır" if ok else f"⚠️ {mesaj}"))
            self.kuyruk.put(("ilerleme", (80, "Kısayollar ekleniyor…")))
            kis = kurulum.kisayol_kur(hedef)
            for x in kis:
                self.kuyruk.put(("log", "Kısayol: " + x))
            self.kuyruk.put(("ilerleme", (92, "Programlar listesine kaydediliyor…")))
            kurulum.programlar_kaydi(hedef)
            self.kuyruk.put(("ilerleme", (100, "Tamamlandı")))
            self.kuyruk.put(("bitti", (hedef, k, len(kis))))
        except Exception as e:
            self.kuyruk.put(("hata", str(e)))

    def _kuyruk_isle(self):
        try:
            while True:
                tur, veri = self.kuyruk.get_nowait()
                if tur == "log":
                    self._log(veri)
                elif tur == "ilerleme":
                    self._ilerleme(*veri)
                elif tur == "bitti":
                    self.bitti_sayfasi(*veri)
                    return
                elif tur == "hata":
                    self._log("❌ HATA: " + veri)
                    self.adim_lbl.config(text="Kurulum başarısız", fg=KIRMIZI)
                    return
        except queue.Empty:
            pass
        if not self.bitti:
            self.kok.after(120, self._kuyruk_isle)

    # ------------------------------------------------------------ 4) bitti
    def bitti_sayfasi(self, hedef, kopya, kis_sayi):
        self.bitti = True
        self._temizle()
        self._baslik("✅ Kurulum tamamlandı",
                     "Program hazır. Masaüstündeki 👻 kısayolundan açabilirsiniz.")
        k = tk.Frame(self._cerceve, bg=KART, highlightbackground=CIZGI,
                     highlightthickness=1)
        k.pack(fill="x", padx=34, pady=20)
        ic = tk.Frame(k, bg=KART)
        ic.pack(fill="x", padx=18, pady=16)
        for etiket, deger in [("Kurulum klasörü", hedef),
                              ("Kopyalanan dosya", str(kopya)),
                              ("Kısayol", f"{kis_sayi} adet"),
                              ("Kaldırma", "Ayarlar → Uygulamalar → GhostPilot")]:
            r = tk.Frame(ic, bg=KART)
            r.pack(fill="x", pady=3)
            tk.Label(r, text=etiket + ":", bg=KART, fg=SOLUK, width=18,
                     anchor="w", font=("Segoe UI", 9)).pack(side="left")
            tk.Label(r, text=deger, bg=KART, fg=METIN, anchor="w",
                     font=("Consolas", 9)).pack(side="left")
        alt = tk.Frame(self._cerceve, bg=KOYU)
        alt.pack(fill="x", padx=34, pady=20)
        self._dugme(alt, "▶  Programı şimdi aç", lambda: self.ac(hedef)).pack(side="left")
        self._dugme(alt, "Kapat", self.kok.destroy, birincil=False).pack(side="right")

    def ac(self, hedef):
        import subprocess
        try:
            giris = os.path.join(hedef, "ui.py")
            pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            py = pyw if os.path.exists(pyw) else sys.executable
            subprocess.Popen([py, giris], cwd=hedef)
        except Exception:
            pass
        self.kok.destroy()


def main(hedef=None):
    if not TK:
        import kurulum
        return kurulum.konsol_kurum(hedef)
    kok = tk.Tk()
    try:
        kok.tk.call("tk", "scaling", 1.2)
    except Exception:
        pass
    Sihirbaz(kok, hedef)
    kok.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())

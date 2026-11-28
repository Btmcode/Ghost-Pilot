#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — ui.py  ·  PROGRAM ARAYÜZÜ
#  Copyright (c) 2026 BTM Code — MIT License
#
#  TASARIM KURALI: tek ekran, tek büyük düğme.
#  Kullanıcı programı açınca NE YAPACAĞINI düşünmek zorunda kalmamalı.
#  Her şey (lisans, klasörler, hata kaydı, dil) "Gelişmiş" penceresinde.
# ============================================================================

import os
import subprocess
import sys
import threading

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)

# Windows'ta alt süreçler konsol penceresi açmasın (pythonw.exe yanıp sönmesin)
SESSIZ = {}
if sys.platform.startswith("win"):
    SESSIZ["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

# ---- tema
ARKA = "#0b1120"
KART = "#141f33"
CIZGI = "#22314e"
METIN, SOLUK, SILIK = "#e8eef7", "#93a4be", "#5f7392"
YESIL, KIRMIZI, AMBER = "#22c55e", "#ef4444", "#f59e0b"
F = "Segoe UI"

try:
    import tkinter as tk
    from tkinter import ttk
    TK = True
except Exception:
    TK = False

try:
    import hata
    hata.kur("ui", sesli=True)
except Exception:
    hata = None

try:
    import diller as _D
except Exception:
    _D = None


# ---------------------------------------------------------------------------
#  METİNLER — dört dil. Seçili dil yoksa Türkçe.
# ---------------------------------------------------------------------------
_M = {
    "tr": {
        "hazir": "Bilgisayarınız hazır",
        "hazir_alt": "Aşağıdaki düğmeye basın, ChatGPT bilgisayarınıza bağlanır.",
        "kapali": "Bağlantı kapalı",
        "kapali_alt": "Bağlanmak için aşağıdaki düğmeye basın.",
        "bagla": "🔗  ChatGPT'ye Bağlan",
        "kapat": "⛔  Bağlantıyı Kapat",
        "bekle": "Adres hazırlanıyor… (10–40 saniye)",
        "hazir_adres": "Adresiniz hazır. Kopyalayın, ChatGPT'ye yapıştırın.",
        "kopyala": "📋  Adresi Kopyala",
        "kopyalandi": "✅ Kopyalandı",
        "adim_baslik": "CHATGPT'DE NE YAPACAKSINIZ",
        "adim1": "1.  ChatGPT'yi açın → Ayarlar → Bağlayıcılar",
        "adim2": "2.  Gelişmiş → Geliştirici modunu açın",
        "adim3": "3.  Oluştur → adresi yapıştırın → Kimlik doğrulama: Yok",
        "adim4": "4.  Oluştur'a basın. Yeni sohbette + menüsünden GhostPilot'u seçin.",
        "destek": "Destek",
        "gelismis": "Gelişmiş",
        "lisans": "Lisans",
        "cikis": "Çıkış",
        "kapali_hata": "Sunucu açılamadı. Aşağıdaki ayrıntıya bakın.",
        "aciliyor": "Sunucu açılıyor…",
        "alt_not": "Bağlantı program kapanınca kesilir.",
    },
    "en": {
        "hazir": "Your computer is ready",
        "hazir_alt": "Press the button below and ChatGPT can use your computer.",
        "kapali": "Connection is off",
        "kapali_alt": "Press the button below to connect.",
        "bagla": "🔗  Connect ChatGPT",
        "kapat": "⛔  Disconnect",
        "bekle": "Preparing the address… (10–40 seconds)",
        "hazir_adres": "Your address is ready. Copy it and paste it into ChatGPT.",
        "kopyala": "📋  Copy address",
        "kopyalandi": "✅ Copied",
        "adim_baslik": "WHAT TO DO IN CHATGPT",
        "adim1": "1.  Open ChatGPT → Settings → Connectors",
        "adim2": "2.  Advanced → turn on Developer mode",
        "adim3": "3.  Create → paste the address → Authentication: None",
        "adim4": "4.  Press Create. In a new chat pick GhostPilot from the + menu.",
        "destek": "Support",
        "gelismis": "Advanced",
        "lisans": "Licence",
        "cikis": "Quit",
        "kapali_hata": "The server could not start. See the details below.",
        "aciliyor": "Starting the server…",
        "alt_not": "The connection ends when you close this program.",
    },
    "de": {
        "hazir": "Ihr Computer ist bereit",
        "hazir_alt": "Drücken Sie die Taste unten, dann kann ChatGPT Ihren Computer nutzen.",
        "kapali": "Verbindung getrennt",
        "kapali_alt": "Drücken Sie die Taste unten, um zu verbinden.",
        "bagla": "🔗  ChatGPT verbinden",
        "kapat": "⛔  Verbindung trennen",
        "bekle": "Adresse wird vorbereitet… (10–40 Sekunden)",
        "hazir_adres": "Ihre Adresse ist bereit. Kopieren und in ChatGPT einfügen.",
        "kopyala": "📋  Adresse kopieren",
        "kopyalandi": "✅ Kopiert",
        "adim_baslik": "WAS SIE IN CHATGPT TUN",
        "adim1": "1.  ChatGPT öffnen → Einstellungen → Connectors",
        "adim2": "2.  Erweitert → Entwicklermodus einschalten",
        "adim3": "3.  Erstellen → Adresse einfügen → Authentifizierung: Keine",
        "adim4": "4.  Erstellen drücken. Im neuen Chat GhostPilot im + Menü wählen.",
        "destek": "Unterstützen",
        "gelismis": "Erweitert",
        "lisans": "Lizenz",
        "cikis": "Beenden",
        "kapali_hata": "Der Server konnte nicht starten. Details siehe unten.",
        "aciliyor": "Server startet…",
        "alt_not": "Die Verbindung endet, wenn Sie das Programm schließen.",
    },
    "es": {
        "hazir": "Su equipo está listo",
        "hazir_alt": "Pulse el botón de abajo y ChatGPT podrá usar su equipo.",
        "kapali": "Conexión cerrada",
        "kapali_alt": "Pulse el botón de abajo para conectar.",
        "bagla": "🔗  Conectar ChatGPT",
        "kapat": "⛔  Desconectar",
        "bekle": "Preparando la dirección… (10–40 segundos)",
        "hazir_adres": "Su dirección está lista. Cópiela y péguela en ChatGPT.",
        "kopyala": "📋  Copiar dirección",
        "kopyalandi": "✅ Copiado",
        "adim_baslik": "QUÉ HACER EN CHATGPT",
        "adim1": "1.  Abra ChatGPT → Ajustes → Conectores",
        "adim2": "2.  Avanzado → active el modo desarrollador",
        "adim3": "3.  Crear → pegue la dirección → Autenticación: Ninguna",
        "adim4": "4.  Pulse Crear. En un chat nuevo elija GhostPilot en el menú +.",
        "destek": "Apoyar",
        "gelismis": "Avanzado",
        "lisans": "Licencia",
        "cikis": "Salir",
        "kapali_hata": "El servidor no pudo iniciarse. Vea los detalles abajo.",
        "aciliyor": "Iniciando el servidor…",
        "alt_not": "La conexión termina al cerrar el programa.",
    },
}


def _dilkod():
    try:
        return _D.dil() if _D else "tr"
    except Exception:
        return "tr"


def m(anahtar):
    """Seçili dilde metin. Yoksa Türkçe."""
    kod = _dilkod()
    return _M.get(kod, _M["tr"]).get(anahtar) or _M["tr"].get(anahtar, anahtar)


# ---------------------------------------------------------------------------
#  YARDIMCILAR
# ---------------------------------------------------------------------------
def _port():
    try:
        import kur as K
        return K.port_cfg()
    except Exception:
        return 17381


def _calisiyor():
    try:
        import kur as K
        return K.relay_running(_port())
    except Exception:
        return None


def _istek(yol, sure=180):
    """Yerel panel API'sine istek at (arka planda çalışır)."""
    import json as _j
    import urllib.request as _u
    r = _u.Request("http://127.0.0.1:%d%s" % (_port(), yol), method="POST")
    with _u.urlopen(r, timeout=sure) as f:
        return _j.loads(f.read().decode("utf-8", "replace"))


def _sunucu_baslat():
    try:
        import kur as K
        K.basla(sessiz=True)
    except Exception:
        pass
    import time
    for _ in range(40):
        if _calisiyor():
            return True
        time.sleep(0.5)
    return False


# ===========================================================================
#  ANA PENCERE
# ===========================================================================
class Panel:
    def __init__(self, kok, tepsiye_gizle=False):
        self.kok = kok
        self.tepsi = None
        self._cikiyor = False
        self._tunel = ""
        self._mesgul = False

        kok.title("GhostPilot")
        kok.configure(bg=ARKA)
        kok.geometry("700x360")
        kok.minsize(660, 340)
        try:
            import ikon
            ikon.uygula(kok, "GhostPilot")
        except Exception:
            pass

        self._kur_arayuz()
        kok.protocol("WM_DELETE_WINDOW", self.cikis_tam)

        self._tepsi_kur()
        kok.after(400, self._ilk_kontrol)
        kok.after(2500, self._dongu)

    # ---------------------------------------------------------------- arayüz
    def _kur_arayuz(self):
        kok = self.kok

        ust = tk.Frame(kok, bg=ARKA)
        ust.pack(fill="x", padx=26, pady=(22, 0))
        tk.Label(ust, text="GhostPilot", bg=ARKA, fg=METIN,
                 font=(F, 16, "bold")).pack(side="left")
        self.surum = tk.Label(ust, text="", bg=ARKA, fg=SILIK, font=(F, 9))
        self.surum.pack(side="left", padx=(10, 0))

        # ---- durum satırı
        dur = tk.Frame(kok, bg=ARKA)
        dur.pack(fill="x", padx=26, pady=(26, 0))
        self.nokta = tk.Label(dur, text="●", bg=ARKA, fg=SILIK, font=(F, 15))
        self.nokta.pack(side="left")
        yan = tk.Frame(dur, bg=ARKA)
        yan.pack(side="left", padx=(9, 0), fill="x", expand=True)
        self.baslik = tk.Label(yan, text=m("kapali"), bg=ARKA, fg=METIN,
                               font=(F, 14, "bold"), anchor="w")
        self.baslik.pack(fill="x")
        self.alt = tk.Label(yan, text=m("kapali_alt"), bg=ARKA, fg=SOLUK,
                            font=(F, 10), anchor="w", justify="left", wraplength=600)
        self.alt.pack(fill="x", pady=(3, 0))

        # ---- BÜYÜK DÜĞME
        self.dugme = tk.Button(
            kok, text=m("bagla"), command=self.tikla,
            bg=YESIL, fg="#04170c", activebackground="#16a34a",
            activeforeground="#04170c", font=(F, 14, "bold"), relief="flat",
            bd=0, cursor="hand2", pady=18, highlightthickness=0)
        self.dugme.pack(fill="x", padx=26, pady=(26, 0))

        self.not_ = tk.Label(kok, text=m("alt_not"), bg=ARKA, fg=SILIK,
                             font=(F, 9), anchor="center")
        self.not_.pack(fill="x", padx=26, pady=(8, 0))

        # ---- adres alanı (bağlanınca görünür)
        self.adres_kutu = tk.Frame(kok, bg=KART, highlightbackground=CIZGI,
                                   highlightthickness=1)
        ic = tk.Frame(self.adres_kutu, bg=KART)
        ic.pack(fill="x", padx=16, pady=14)
        tk.Label(ic, text=m("hazir_adres"), bg=KART, fg=SOLUK,
                 font=(F, 10), anchor="w").pack(fill="x")
        ad = tk.Frame(ic, bg=KART)
        ad.pack(fill="x", pady=(8, 0))
        self.adres = tk.Entry(ad, bg="#0a1322", fg="#a5d6ff",
                              readonlybackground="#0a1322", relief="flat",
                              font=("Consolas", 9))
        self.adres.pack(side="left", fill="x", expand=True, ipady=7)
        self.adres.config(state="readonly")
        self.kopyala_btn = tk.Button(ad, text=m("kopyala"), command=self.kopyala,
                                     bg=CIZGI, fg=METIN, relief="flat", bd=0,
                                     activebackground="#2c3f61", activeforeground=METIN,
                                     font=(F, 9, "bold"), cursor="hand2",
                                     padx=14, pady=7)
        self.kopyala_btn.pack(side="left", padx=(8, 0))
        self.kopya_mesaj = tk.Label(ic, text="", bg=KART, fg=YESIL, font=(F, 9),
                                    anchor="w")
        self.kopya_mesaj.pack(fill="x", pady=(6, 0))

        # ---- adımlar
        self.adimlar = tk.Frame(self.adres_kutu, bg="#0f2a1c")
        ai = tk.Frame(self.adimlar, bg="#0f2a1c")
        ai.pack(fill="x", padx=16, pady=12)
        tk.Label(ai, text=m("adim_baslik"), bg="#0f2a1c", fg="#86efac",
                 font=(F, 8, "bold"), anchor="w").pack(fill="x")
        for k in ("adim1", "adim2", "adim3", "adim4"):
            tk.Label(ai, text=m(k), bg="#0f2a1c", fg="#c9e8d4", font=(F, 9),
                     anchor="w", justify="left").pack(fill="x", pady=(4, 0))

        # ---- alt çubuk
        alt = tk.Frame(kok, bg=ARKA)
        alt.pack(side="bottom", fill="x", padx=26, pady=16)
        for yazi, fn in ((m("lisans"), self.lisans_penceresi),
                         (m("destek"), self.destek_penceresi),
                         (m("gelismis"), self.gelismis_penceresi),
                         (m("cikis"), self.cikis_tam)):
            tk.Button(alt, text=yazi, command=fn, bg=ARKA, fg=SOLUK,
                      activebackground="#1b2942", activeforeground=METIN,
                      relief="flat", bd=0, highlightthickness=0,
                      font=(F, 9), cursor="hand2",
                      padx=10, pady=5).pack(side="left", padx=(0, 6))

    # ----------------------------------------------------------------- durum
    def _boya(self, acik, yazi=None, alt=None):
        if acik:
            self.nokta.config(fg=YESIL)
            self.baslik.config(text=yazi or m("hazir"))
            self.alt.config(text=alt or m("hazir_alt"))
            self.dugme.config(text=m("kapat"), bg="#3a1518", fg="#fca5a5",
                              activebackground="#4a1c20", activeforeground="#fca5a5")
            self.adres_kutu.pack(fill="x", padx=26, pady=(16, 0),
                                 before=self.not_)
            self.adimlar.pack(fill="x")
            try:
                self.kok.geometry("700x700")
            except Exception:
                pass
        else:
            self.nokta.config(fg=SILIK)
            self.baslik.config(text=yazi or m("kapali"))
            self.alt.config(text=alt or m("kapali_alt"))
            self.dugme.config(text=m("bagla"), bg=YESIL, fg="#04170c",
                              activebackground="#16a34a", activeforeground="#04170c")
            self.adres_kutu.pack_forget()
            try:
                self.kok.geometry("700x360")
            except Exception:
                pass

    def _ilk_kontrol(self):
        try:
            import ghostpilot as G
            self.surum.config(text="v" + G.VERSION)
        except Exception:
            pass
        self.durum_guncelle()

    # -------- tünel durumu: sunucunun kendi kaydından oku (asıl kaynak)
    @staticmethod
    def _tunel_bilgi():
        try:
            import json
            p = os.path.join(os.path.expanduser("~"), ".ghostpilot", "tunel.json")
            with open(p, encoding="utf-8") as f:
                return json.load(f) or {}
        except Exception:
            return {}

    def _tunel_canli(self):
        d = self._tunel_bilgi()
        url = (d.get("url") or "").strip()
        pid = d.get("pid")
        if not url:
            return ""
        if not pid:
            return url  # tailscale: pid yok, adres varsa açık
        try:
            if os.name == "nt":
                r = subprocess.run(["tasklist", "/FI", "PID eq %s" % pid],
                                   capture_output=True, text=True, timeout=10, **SESSIZ)
                return url if str(pid) in (r.stdout or "") else ""
            os.kill(int(pid), 0)
            return url
        except Exception:
            return ""

    def durum_guncelle(self):
        if not self._mesgul:
            url = self._tunel_canli()
            if url and not self._tunel:
                self._tunel = url
            elif not url and self._tunel:
                self._tunel = ""
        h = _calisiyor()
        if self._tunel:
            if self.adres.get().strip() != self._tunel:
                self.adres.config(state="normal")
                self.adres.delete(0, "end")
                self.adres.insert(0, self._tunel)
                self.adres.config(state="readonly")
            self._boya(True)
        elif h:
            self._boya(False, yazi=m("kapali"),
                       alt="Bağlanmak için aşağıdaki düğmeye basın.")
        else:
            self._boya(False)

    def _dongu(self):
        try:
            self.durum_guncelle()
        except Exception:
            pass
        self.kok.after(3000, self._dongu)

    # ---------------------------------------------------------------- eylem
    def tikla(self):
        if self._mesgul:
            return
        if self._tunel:
            self._kapat()
        else:
            self._baglan()

    def _mesgul_yap(self, acik, yazi=None):
        self._mesgul = acik
        self.dugme.config(state="disabled" if acik else "normal",
                          text=yazi or (m("kapat") if self._tunel else m("bagla")))

    def _baglan(self):
        self._mesgul_yap(True, m("bekle"))
        self.alt.config(text=m("aciliyor"))
        self.nokta.config(fg=AMBER)

        def _():
            sonuc = {"tip": "hata", "metin": m("kapali_hata")}
            if not _calisiyor() and not _sunucu_baslat():
                sonuc["metin"] = m("kapali_hata")
            else:
                try:
                    d = _istek("/panel/eylem?k=bagla", sure=180)
                    msg = str(d.get("message") or "")
                    if msg.startswith("BAGLANDI|"):
                        self._tunel = msg.split("|")[2]
                        sonuc = {"tip": "ok"}
                    elif msg.startswith("TUNEL_YOK|"):
                        sonuc = {"tip": "hata", "metin": msg.split("|", 1)[1]}
                    else:
                        sonuc = {"tip": "hata", "metin": msg or m("kapali_hata")}
                except Exception as e:
                    sonuc = {"tip": "hata", "metin": "%s\n%s" % (m("kapali_hata"), e)}
            self.kok.after(0, lambda: self._baglan_bitti(sonuc))
        threading.Thread(target=_, daemon=True).start()

    def _baglan_bitti(self, sonuc):
        self._mesgul_yap(False)
        if sonuc.get("tip") == "ok":
            self.adres.config(state="normal")
            self.adres.delete(0, "end")
            self.adres.insert(0, self._tunel)
            self.adres.config(state="readonly")
            self.kopya_mesaj.config(text="")
            self._boya(True)
        else:
            self._boya(False, yazi="Bağlanamadı", alt=sonuc.get("metin", "")[:400])
            self.nokta.config(fg=KIRMIZI)

    def _kapat(self):
        self._tunel = ""
        self._boya(False)
        self.kopya_mesaj.config(text="")

        def _():
            try:
                _istek("/panel/eylem?k=bagla", sure=60)
            except Exception:
                pass
        threading.Thread(target=_, daemon=True).start()

    def kopyala(self):
        a = self.adres.get().strip()
        if not a:
            return
        try:
            self.kok.clipboard_clear()
            self.kok.clipboard_append(a)
            self.kopya_mesaj.config(text=m("kopyalandi"))
        except Exception as e:
            self.kopya_mesaj.config(text=str(e)[:80], fg=KIRMIZI)

    # --------------------------------------------------------------- lisans
    def lisans_penceresi(self):
        p = tk.Toplevel(self.kok)
        p.title("GhostPilot — " + m("lisans"))
        p.configure(bg=ARKA)
        p.geometry("560x480")
        try:
            import paketler as PK
            import lisans as LS
        except Exception:
            PK = LS = None

        tk.Label(p, text=m("lisans"), bg=ARKA, fg=METIN,
                 font=(F, 13, "bold")).pack(anchor="w", padx=22, pady=(20, 4))
        try:
            import ghostpilot as G
            k = (G.CFG.get("license_key") or "").strip()
            durum = "PRO" if k else "Ücretsiz"
            kota = G._kota_yukle() if hasattr(G, "_kota_yukle") else {}
            kullanilan = int(kota.get("used") or 0)
        except Exception:
            k, durum, kullanilan = "", "Ücretsiz", 0

        tk.Label(p, text="Durum: %s" % durum, bg=ARKA, fg=YESIL if k else AMBER,
                 font=(F, 11, "bold")).pack(anchor="w", padx=22)
        tk.Label(p, text="Bu ay: %d / 20.000 çağrı" % kullanilan, bg=ARKA,
                 fg=SOLUK, font=(F, 10)).pack(anchor="w", padx=22, pady=(6, 0))

        giris = tk.Frame(p, bg=ARKA)
        giris.pack(fill="x", padx=22, pady=(16, 0))
        e = tk.Entry(giris, bg=KART, fg=METIN, insertbackground=METIN,
                     relief="flat", font=("Consolas", 10))
        e.pack(side="left", fill="x", expand=True, ipady=8)
        e.insert(0, k)

        def uygula():
            v = e.get().strip()
            try:
                import ghostpilot as G
                G.CFG["license_key"] = v
                G.save_cfg(G.CFG)
                sonuc.config(text="Kaydedildi.", fg=YESIL)
            except Exception as ex:
                sonuc.config(text="Hata: %s" % ex, fg=KIRMIZI)

        tk.Button(giris, text="Uygula", command=uygula, bg=CIZGI, fg=METIN,
                  relief="flat", bd=0, font=(F, 9, "bold"), cursor="hand2",
                  padx=14, pady=7).pack(side="left", padx=(8, 0))
        sonuc = tk.Label(p, text="", bg=ARKA, fg=SOLUK, font=(F, 9), anchor="w")
        sonuc.pack(fill="x", padx=22, pady=(6, 0))

        if PK:
            try:
                tk.Label(p, text=PK.m("baslik"), bg=ARKA, fg=METIN,
                         font=(F, 11, "bold")).pack(anchor="w", padx=22, pady=(22, 2))
                tk.Label(p, text=PK.m("ucretsiz") + " — 0",
                         bg=ARKA, fg=SOLUK, font=(F, 10)).pack(anchor="w", padx=22)
                tk.Label(p, text="PRO — %d %s / ay" % (PK.AYLIK_FIYAT, PK.PARA_BIRIMI),
                         bg=ARKA, fg=AMBER, font=(F, 10, "bold")).pack(anchor="w", padx=22,
                                                                      pady=(4, 0))
                tk.Label(p, text="Ödeme yok — yalnız bağış. Anahtar bağış yapanlara verilir.",
                         bg=ARKA, fg=SILIK, font=(F, 9), wraplength=480,
                         justify="left").pack(anchor="w", padx=22, pady=(6, 0))
                if getattr(PK, "BAGIS_URL", ""):
                    tk.Button(p, text="☕  Bağış yap", cursor="hand2",
                              command=lambda: self._ac_url(PK.BAGIS_URL),
                              bg="#123222", fg="#86efac", relief="flat", bd=0,
                              font=(F, 10, "bold"), padx=18, pady=9).pack(anchor="w",
                                                                          padx=22, pady=(14, 0))
            except Exception:
                pass
        tk.Button(p, text="Kapat", command=p.destroy, bg=CIZGI, fg=METIN,
                  relief="flat", bd=0, font=(F, 9), padx=18, pady=6).pack(side="bottom",
                                                                         pady=16)

    @staticmethod
    def _ac_url(url):
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass

    # --------------------------------------------------------------- destek
    def destek_penceresi(self):
        p = tk.Toplevel(self.kok)
        p.title("GhostPilot — " + m("destek"))
        p.configure(bg=ARKA)
        p.geometry("600x560")
        tk.Label(p, text=m("destek"), bg=ARKA, fg=METIN,
                 font=(F, 14, "bold")).pack(anchor="w", padx=24, pady=(22, 6))
        tk.Label(p, text="GhostPilot ücretsiz ve açık kaynak (MIT). Satış yok — "
                         "sürdürmenin tek yolu bağış.",
                 bg=ARKA, fg=SOLUK, font=(F, 10), wraplength=540,
                 justify="left", anchor="w").pack(anchor="w", padx=24)

        tk.Button(p, text="☕  Bağış yap — Buy me a coffee", cursor="hand2",
                  command=lambda: self._ac_url("https://buymeacoffee.com/btmcode"),
                  bg="#ffdd00", fg="#0b1120", relief="flat", bd=0,
                  font=(F, 11, "bold"), padx=20, pady=12).pack(anchor="w", padx=24,
                                                               pady=(18, 0))
        sat = tk.Frame(p, bg=ARKA)
        sat.pack(fill="x", padx=24, pady=(10, 0))
        for yazi, url in (("⭐ GitHub deposu", "https://github.com/Btmcode/Ghost-Pilot"),
                          ("🌐 Web sitesi", "https://btmcode.vercel.app")):
            tk.Button(sat, text=yazi, cursor="hand2",
                      command=lambda u=url: self._ac_url(u),
                      bg=CIZGI, fg=METIN, relief="flat", bd=0,
                      font=(F, 9, "bold"), padx=14, pady=8).pack(side="left",
                                                                 padx=(0, 8))

        tk.Label(p, text="BAĞLANTILAR", bg=ARKA, fg=SILIK,
                 font=(F, 8, "bold"), anchor="w").pack(fill="x", padx=24, pady=(22, 6))
        linkler = [
            ("Geliştirici", "BtmCode · Ömer Zirve", ""),
            ("Web sitesi", "btmcode.vercel.app", "https://btmcode.vercel.app"),
            ("Kaynak kodu", "github.com/Btmcode/Ghost-Pilot",
             "https://github.com/Btmcode/Ghost-Pilot"),
            ("GitHub profili", "github.com/Btmcode", "https://github.com/Btmcode"),
            ("Bağış", "buymeacoffee.com/btmcode", "https://buymeacoffee.com/btmcode"),
            ("Gizlilik", "Gizlilik politikası",
             "https://github.com/Btmcode/Ghost-Pilot/blob/main/GIZLILIK.md"),
            ("Koşullar", "Kullanım koşulları",
             "https://github.com/Btmcode/Ghost-Pilot/blob/main/KOSULLAR.md"),
            ("Blog", "mnemark.blogspot.com", "https://mnemark.blogspot.com"),
            ("E-posta", "devcloudpy@gmail.com", "mailto:devcloudpy@gmail.com"),
        ]
        for etiket, deger, url in linkler:
            r = tk.Frame(p, bg=ARKA)
            r.pack(fill="x", padx=24, pady=1)
            tk.Label(r, text=etiket, bg=ARKA, fg=SILIK, font=(F, 9),
                     width=16, anchor="w").pack(side="left")
            lb = tk.Label(r, text=deger, bg=ARKA,
                          fg="#38bdf8" if url else METIN, font=(F, 9), anchor="w")
            lb.pack(side="left")
            if url:
                lb.configure(cursor="hand2")
                lb.bind("<Button-1>", lambda e, u=url: self._ac_url(u))

        tk.Button(p, text="Kapat", command=p.destroy, bg=CIZGI, fg=METIN,
                  relief="flat", bd=0, font=(F, 9), padx=18, pady=6).pack(side="bottom",
                                                                         pady=16)

    # ------------------------------------------------------------- gelişmiş
    def gelismis_penceresi(self):
        p = tk.Toplevel(self.kok)
        p.title("GhostPilot — " + m("gelismis"))
        p.configure(bg=ARKA)
        p.geometry("640x540")

        kay = tk.Frame(p, bg=ARKA)
        kay.pack(fill="both", expand=True, padx=18, pady=14)

        # dil
        sat = tk.Frame(kay, bg=ARKA)
        sat.pack(fill="x", pady=(0, 12))
        tk.Label(sat, text="Dil / Language", bg=ARKA, fg=SOLUK,
                 font=(F, 9, "bold")).pack(side="left")
        for kod, etiket in (("tr", "TR"), ("en", "EN"), ("de", "DE"), ("es", "ES")):
            tk.Button(sat, text=etiket, cursor="hand2",
                      command=lambda k=kod: self._dil(k, p),
                      bg=CIZGI, fg=METIN, relief="flat", bd=0,
                      font=(F, 9, "bold"), padx=10, pady=4).pack(side="left", padx=(6, 0))

        # klasörler
        tk.Label(kay, text="İZİN VERİLEN KLASÖRLER", bg=ARKA, fg=SOLUK,
                 font=(F, 8, "bold"), anchor="w").pack(fill="x")
        self._klasor_liste(kay)

        # mod
        sat2 = tk.Frame(kay, bg=ARKA)
        sat2.pack(fill="x", pady=(14, 0))
        tk.Button(sat2, text="👁  Salt okunur", cursor="hand2",
                  command=lambda: self._komut("salt-okunur", p),
                  bg=CIZGI, fg=METIN, relief="flat", bd=0,
                  font=(F, 9), padx=12, pady=6).pack(side="left")
        tk.Button(sat2, text="✍  Okuma + yazma", cursor="hand2",
                  command=lambda: self._komut("yazma", p),
                  bg=CIZGI, fg=METIN, relief="flat", bd=0,
                  font=(F, 9), padx=12, pady=6).pack(side="left", padx=8)

        # hata kaydı
        sat3 = tk.Frame(kay, bg=ARKA)
        sat3.pack(fill="x", pady=(16, 4))
        tk.Label(sat3, text="HATA KAYDI", bg=ARKA, fg=SOLUK,
                 font=(F, 8, "bold")).pack(side="left")
        tk.Button(sat3, text="Yenile", cursor="hand2",
                  command=lambda: self._log_yenile(kutu),
                  bg=CIZGI, fg=METIN, relief="flat", bd=0,
                  font=(F, 8), padx=10, pady=3).pack(side="right")

        kutu = tk.Text(kay, height=12, bg="#070c17", fg="#cbd5e1", relief="flat",
                       font=("Consolas", 8), wrap="word")
        kutu.pack(fill="both", expand=True, pady=(4, 0))
        self._log_yenile(kutu)

        tk.Button(p, text="Kapat", command=p.destroy, bg=CIZGI, fg=METIN,
                  relief="flat", bd=0, font=(F, 9), padx=18, pady=6).pack(pady=(0, 14))

    def _klasor_liste(self, ata):
        try:
            import ghostpilot as G
            kokler = (G.CFG.get("read_roots") or []) + (G.CFG.get("write_roots") or [])
            yaz = set(G.CFG.get("write_roots") or [])
        except Exception:
            kokler, yaz = [], set()
        gorulen = []
        for k in kokler:
            if k in gorulen:
                continue
            gorulen.append(k)
            tk.Label(ata, text=("yazma  " if k in yaz else "okuma  ") + k,
                     bg=ARKA, fg=SOLUK if k not in yaz else METIN,
                     font=("Consolas", 8), anchor="w").pack(fill="x")
        if not gorulen:
            tk.Label(ata, text="—", bg=ARKA, fg=SILIK, font=(F, 9)).pack(anchor="w")

    def _log_yenile(self, kutu):
        try:
            icerik = ""
            if hata and hasattr(hata, "son"):
                icerik = hata.son(60)
            if not icerik:
                icerik = "(kayıt boş — hata yok)"
        except Exception as e:
            icerik = str(e)
        kutu.config(state="normal")
        kutu.delete("1.0", "end")
        kutu.insert("end", icerik)
        kutu.config(state="disabled")

    def _dil(self, kod, pencere=None):
        try:
            _D.dil_sec(kod)
        except Exception:
            pass
        if pencere:
            pencere.destroy()
        self.kok.title("GhostPilot")
        self.baslik.config(text=m(self._durum_anahtari()))
        self.alt.config(text=m("hazir_alt") if self._tunel else m("kapali_alt"))
        self.dugme.config(text=m("kapat") if self._tunel else m("bagla"))
        self.not_.config(text=m("alt_not"))
        self.kopyala_btn.config(text=m("kopyala"))

    def _durum_anahtari(self):
        return "hazir" if self._tunel else "kapali"

    def _komut(self, ad, pencere=None):
        def _():
            try:
                subprocess.run([sys.executable, os.path.join(BURASI, "kur.py"), ad],
                               capture_output=True, timeout=60, **SESSIZ)
            except Exception:
                pass
            if pencere:
                try:
                    self.kok.after(0, pencere.destroy)
                except Exception:
                    pass
        threading.Thread(target=_, daemon=True).start()

    # ---------------------------------------------------------------- tepsi
    def _tepsi_kur(self):
        try:
            import tepsi
            self.tepsi = tepsi.Tepsi(
                baslik="GhostPilot", ipucu="GhostPilot",
                solda=lambda: self.kok.after(0, self.goster),
                sunucu=lambda: self.kok.after(0, self.cikis_tam),
                cikis=lambda: self.kok.after(0, self.cikis_tam),
                durum=self._tepsi_durum)
            if self.tepsi.baslat():
                self.tepsi.guncelle(self._tepsi_durum())
        except Exception:
            self.tepsi = None

    def _tepsi_durum(self):
        return {"sunucu": bool(_calisiyor()), "bekci": False, "metin": ""}

    def goster(self):
        try:
            self.kok.deiconify()
            self.kok.lift()
            self.kok.focus_force()
        except Exception:
            pass

    def cikis_tam(self):
        if self._cikiyor:
            return
        self._cikiyor = True
        # tüneli ve sunucuyu kapat — arkada pythonw süreçleri kalmasın
        try:
            import kur as K
            K.durdur(sessiz=True)
        except Exception:
            pass
        try:
            if self.tepsi:
                self.tepsi.durdur()
        except Exception:
            pass
        try:
            self.kok.destroy()
        except Exception:
            pass


# ===========================================================================
#  GİRİŞ
# ===========================================================================
def main():
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
        Panel(kok)
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
    yol = hata.yol() if hata else "(günlük yok)"
    try:
        from tkinter import scrolledtext
        p = tk.Tk()
        p.title("GhostPilot — hata")
        p.configure(bg="#0e1628")
        p.geometry("700x400")
        tk.Label(p, text=baslik, bg="#0e1628", fg="#f87171",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=18, pady=(16, 4))
        tk.Label(p, text="%s: %s" % (type(exc).__name__, exc), bg="#0e1628",
                 fg="#e2e8f0", wraplength=660, justify="left", anchor="w",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=(0, 10))
        tk.Label(p, text="Ayrıntılar: " + yol, bg="#0e1628", fg="#94a3b8",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=18)
        kutu = scrolledtext.ScrolledText(p, height=12, bg="#080d1a", fg="#cbd5e1",
                                         font=("Consolas", 8), relief="flat")
        kutu.pack(fill="both", expand=True, padx=18, pady=10)
        try:
            kutu.insert("end", hata.son(40) if hata else str(exc))
        except Exception:
            kutu.insert("end", str(exc))
        tk.Button(p, text="Kapat", command=p.destroy, bg="#1e293b", fg="#e2e8f0",
                  relief="flat", padx=22, pady=6).pack(pady=(0, 14))
        p.mainloop()
    except Exception:
        pass


if __name__ == "__main__":
    sys.exit(main())

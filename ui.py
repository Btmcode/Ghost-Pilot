#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — ui.py  ·  PROGRAM ARAYÜZÜ
#  Copyright (c) 2026 BTM Code — MIT License
#
#  TASARIM İLKELERİ (Apple yaklaşımı):
#    1. TEK karar: bağlan / kapat. Gerisi programın işi.
#    2. Sessiz arayüz — kullanıcıyı sayılarla, loglarla, sekmelerle boğma.
#    3. Her adım TEK satır, KOPYALA düğmeli. Kullanıcı düşünmesin.
#    4. Geri alma her zaman görünür: "Bağlantıyı Kapat" hep aynı yerde.
#    5. Yumuşak, düşük kontrastlı renkler; tek vurgu rengi.
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

# ---- tema: düşük kontrast, tek vurgu
ARKA = "#0d1117"
KART = "#161b22"
KART2 = "#1c2333"
CIZGI = "#21262d"
METIN = "#e6edf3"
SOLUK = "#8d96a0"
SILIK = "#5a6470"
YESIL = "#2ea043"
YESIL_K = "#0d2a17"
KIRMIZI = "#d9453f"
KIRMIZI_K = "#2b1315"
MAVI = "#388bfd"
F = "Segoe UI"

try:
    import tkinter as tk
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

EKLENTI_URL = "https://chatgpt.com/plugins"


# ---------------------------------------------------------------------------
#  METİNLER
# ---------------------------------------------------------------------------
_M = {
    "tr": {
        "baslik_off": "Bağlantı kapalı",
        "alt_off": "ChatGPT'nin bilgisayarınızı kullanmasını istiyorsanız bağlanın.",
        "baslik_on": "Bağlı",
        "alt_on": "ChatGPT artık bilgisayarınızı kullanabilir.",
        "bagla": "ChatGPT'ye bağlan",
        "kapat": "Bağlantıyı kapat",
        "bekle": "Bağlanıyor…",
        "kopyala": "Kopyala",
        "kopyalandi": "Kopyalandı",
        "adres_bas": "1 · BAĞLANTI ADRESİN",
        "adres_alt": "Bu adres yalnız bu oturum için geçerli.",
        "adim_bas": "2 · CHATGPT'DE",
        "adim_ipucu": "Kopyaladığınız adresi ChatGPT'de bu alana yapıştırın.",
        "a1": "Eklentiler sayfasını aç",
        "a1_btn": "chatgpt.com/plugins",
        "a6": "Simge: chatgpt-icon-256.png dosyasını seç",
        "a2": "Sağ üstten Ekle → Özel MCP sunucusu",
        "a3": "Ad: GhostPilot · Açıklama: bilgisayarım",
        "a4": "Kimlik doğrulama: Yok — OAuth'a dokunmayın",
        "a5": "Kutuyu işaretle → Oluştur",
        "test": "3 · DENEYİN",
        "test_alt": "Yeni sohbet → + → GhostPilot → yazın:",
        "test_kod": "ghostpilot_status",
        "hata_bas": "Bağlanamadı",
        "sunucu_yok": "Sunucu açılamadı.",
        "lisans": "Lisans",
        "destek": "Destek",
        "gelismis": "Gelişmiş",
        "cikis": "Çıkış",
        "kapat_btn": "Kapat",
        "kapatildi": "Bağlantı kapatıldı.",
    },
    "en": {
        "baslik_off": "Not connected",
        "alt_off": "Connect to let ChatGPT use your computer.",
        "baslik_on": "Connected",
        "alt_on": "ChatGPT can now use your computer.",
        "bagla": "Connect ChatGPT",
        "kapat": "Disconnect",
        "bekle": "Connecting…",
        "kopyala": "Copy",
        "kopyalandi": "Copied",
        "adres_bas": "1 · YOUR ADDRESS",
        "adres_alt": "This address is valid for this session only.",
        "adim_bas": "2 · IN CHATGPT",
        "adim_ipucu": "Paste the address you copied into that field in ChatGPT.",
        "a1": "Open the Plugins page",
        "a1_btn": "chatgpt.com/plugins",
        "a6": "Icon: pick the chatgpt-icon-256.png file",
        "a2": "Top right Add → Custom MCP server",
        "a3": "Name: GhostPilot · Description: my computer",
        "a4": "Authentication: None — do not pick OAuth",
        "a5": "Tick the box → Create",
        "test": "3 · TRY IT",
        "test_alt": "New chat → + → GhostPilot → type:",
        "test_kod": "ghostpilot_status",
        "hata_bas": "Could not connect",
        "sunucu_yok": "The server could not start.",
        "lisans": "Licence",
        "destek": "Support",
        "gelismis": "Advanced",
        "cikis": "Quit",
        "kapat_btn": "Close",
        "kapatildi": "Disconnected.",
    },
    "de": {
        "baslik_off": "Nicht verbunden",
        "alt_off": "Verbinden, damit ChatGPT Ihren Computer nutzen kann.",
        "baslik_on": "Verbunden",
        "alt_on": "ChatGPT kann Ihren Computer jetzt nutzen.",
        "bagla": "ChatGPT verbinden",
        "kapat": "Verbindung trennen",
        "bekle": "Verbinde…",
        "kopyala": "Kopieren",
        "kopyalandi": "Kopiert",
        "adres_bas": "1 · IHRE ADRESSE",
        "adres_alt": "Diese Adresse gilt nur für diese Sitzung.",
        "adim_bas": "2 · IN CHATGPT",
        "adim_ipucu": "Fügen Sie die kopierte Adresse dort in ChatGPT ein.",
        "a1": "Plugins-Seite öffnen",
        "a1_btn": "chatgpt.com/plugins",
        "a6": "Symbol: Datei chatgpt-icon-256.png wählen",
        "a2": "Oben rechts Hinzufügen → Eigener MCP-Server",
        "a3": "Name: GhostPilot · Beschreibung: mein Computer",
        "a4": "Authentifizierung: Keine — nicht OAuth wählen",
        "a5": "Kästchen ankreuzen → Erstellen",
        "test": "3 · AUSPROBIEREN",
        "test_alt": "Neuer Chat → + → GhostPilot → eingeben:",
        "test_kod": "ghostpilot_status",
        "hata_bas": "Verbindung fehlgeschlagen",
        "sunucu_yok": "Der Server konnte nicht starten.",
        "lisans": "Lizenz",
        "destek": "Unterstützen",
        "gelismis": "Erweitert",
        "cikis": "Beenden",
        "kapat_btn": "Schließen",
        "kapatildi": "Verbindung getrennt.",
    },
    "es": {
        "baslik_off": "Sin conexión",
        "alt_off": "Conecte para que ChatGPT use su equipo.",
        "baslik_on": "Conectado",
        "alt_on": "ChatGPT ya puede usar su equipo.",
        "bagla": "Conectar ChatGPT",
        "kapat": "Desconectar",
        "bekle": "Conectando…",
        "kopyala": "Copiar",
        "kopyalandi": "Copiado",
        "adres_bas": "1 · SU DIRECCIÓN",
        "adres_alt": "Esta dirección solo vale para esta sesión.",
        "adim_bas": "2 · EN CHATGPT",
        "adim_ipucu": "Pegue la dirección copiada en ese campo de ChatGPT.",
        "a1": "Abra la página de Complementos",
        "a1_btn": "chatgpt.com/plugins",
        "a6": "Icono: elija el archivo chatgpt-icon-256.png",
        "a2": "Arriba a la derecha Añadir → Servidor MCP propio",
        "a3": "Nombre: GhostPilot · Descripción: mi equipo",
        "a4": "Autenticación: Ninguna — no elija OAuth",
        "a5": "Marque la casilla → Crear",
        "test": "3 · PRUÉBELO",
        "test_alt": "Chat nuevo → + → GhostPilot → escriba:",
        "test_kod": "ghostpilot_status",
        "hata_bas": "No se pudo conectar",
        "sunucu_yok": "El servidor no pudo iniciarse.",
        "lisans": "Licencia",
        "destek": "Apoyar",
        "gelismis": "Avanzado",
        "cikis": "Salir",
        "kapat_btn": "Cerrar",
        "kapatildi": "Desconectado.",
    },
}


def _dilkod():
    try:
        return _D.dil() if _D else "tr"
    except Exception:
        return "tr"


def m(k):
    return _M.get(_dilkod(), _M["tr"]).get(k) or _M["tr"].get(k, k)


# ---------------------------------------------------------------------------
#  KÜÇÜK YARDIMCILAR
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


def _cfg_yolu(ad):
    return os.path.join(os.path.expanduser("~"), ".ghostpilot", ad)


def _ac_url(url):
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception:
        pass


def btn(ata, yazi, komut, tur="normal", **kw):
    """Apple tarzı yumuşak düğme."""
    renk = {
        "birincil": (YESIL, "#ffffff", "#3fb950"),
        "tehlike": (KIRMIZI_K, "#ff9b96", "#3a1a1c"),
        "sade": (CIZGI, METIN, KART2),
        "mini": (KART2, "#a9b6c6", CIZGI),
    }.get(tur, (CIZGI, METIN, KART2))
    bg, fg, act = renk
    b = tk.Button(ata, text=yazi, command=komut, bg=bg, fg=fg,
                  activebackground=act, activeforeground=fg,
                  relief="flat", bd=0, highlightthickness=0,
                  font=(F, 9, "bold"), cursor="hand2",
                  padx=kw.pop("padx", 16), pady=kw.pop("pady", 9), **kw)
    return b


def satir(ata, no, baslik, alt=None):
    """Numaralı adım satırı — hepsi aynı hizada."""
    r = tk.Frame(ata, bg=KART)
    tk.Label(r, text=str(no), bg=KART2, fg=SOLUK, font=(F, 8, "bold"),
             width=2).pack(side="left", anchor="n", ipady=2)
    g = tk.Frame(r, bg=KART)
    g.pack(side="left", fill="x", expand=True, padx=(10, 0))
    tk.Label(g, text=baslik, bg=KART, fg=METIN, font=(F, 9), anchor="w",
             justify="left", wraplength=430).pack(fill="x")
    if alt:
        tk.Label(g, text=alt, bg=KART, fg=SILIK, font=(F, 8), anchor="w",
                 justify="left").pack(fill="x")
    return r


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
        kok.geometry("560x330")
        kok.minsize(520, 300)
        try:
            import ikon
            ikon.uygula(kok, "GhostPilot")
        except Exception:
            pass

        self._kur()
        kok.protocol("WM_DELETE_WINDOW", self.cikis_tam)
        self._tepsi_kur()
        kok.after(300, self._ilk)
        kok.after(2500, self._dongu)

    # ------------------------------------------------------------------ yapı
    def _kur(self):
        kok = self.kok

        # üst: ad + sürüm
        ust = tk.Frame(kok, bg=ARKA)
        ust.pack(fill="x", padx=28, pady=(26, 0))
        tk.Label(ust, text="GhostPilot", bg=ARKA, fg=METIN,
                 font=(F, 15, "bold")).pack(side="left")
        self.surum = tk.Label(ust, text="", bg=ARKA, fg=SILIK, font=(F, 8))
        self.surum.pack(side="left", padx=(9, 0))

        # orta: durum
        orta = tk.Frame(kok, bg=ARKA)
        orta.pack(fill="x", padx=28, pady=(34, 0))
        self.nokta = tk.Label(orta, text="○", bg=ARKA, fg=SILIK, font=(F, 16))
        self.nokta.pack(side="left", anchor="n", pady=(2, 0))
        yan = tk.Frame(orta, bg=ARKA)
        yan.pack(side="left", padx=(12, 0), fill="x", expand=True)
        self.baslik = tk.Label(yan, text=m("baslik_off"), bg=ARKA, fg=METIN,
                               font=(F, 17, "bold"), anchor="w")
        self.baslik.pack(fill="x")
        self.alt = tk.Label(yan, text=m("alt_off"), bg=ARKA, fg=SOLUK,
                            font=(F, 10), anchor="w", justify="left", wraplength=440)
        self.alt.pack(fill="x", pady=(5, 0))

        # büyük düğme
        self.dugme = tk.Button(
            kok, text=m("bagla"), command=self.tikla,
            bg=YESIL, fg="#ffffff", activebackground="#3fb950",
            activeforeground="#ffffff", font=(F, 12, "bold"), relief="flat",
            bd=0, cursor="hand2", pady=15, highlightthickness=0)
        self.dugme.pack(fill="x", padx=28, pady=(30, 0))

        # ayrıntı kartı (bağlanınca görünür)
        self.kart = tk.Frame(kok, bg=KART, highlightbackground=CIZGI,
                             highlightthickness=1)
        ic = tk.Frame(self.kart, bg=KART)
        ic.pack(fill="x", padx=18, pady=16)

        # 1 · adres
        tk.Label(ic, text=m("adres_bas"), bg=KART, fg=SILIK,
                 font=(F, 8, "bold"), anchor="w").pack(fill="x")
        adr = tk.Frame(ic, bg=KART)
        adr.pack(fill="x", pady=(7, 0))
        self.adres = tk.Entry(adr, bg="#0b0f16", fg="#79c0ff",
                              readonlybackground="#0b0f16", relief="flat",
                              font=("Consolas", 8))
        self.adres.pack(side="left", fill="x", expand=True, ipady=8)
        self.adres.config(state="readonly")
        self.kopya = btn(adr, m("kopyala"), self.kopyala, "sade", pady=8)
        self.kopya.pack(side="left", padx=(8, 0))
        # tek tık da kopyalar (küçük dokunmatik/erişilebilirlik kolaylığı)
        self.adres.bind("<Button-1>", lambda e: (self.kopyala(), "break")[1])
        self.adres.config(cursor="hand2")

        # 2 · adımlar
        tk.Label(ic, text=m("adim_bas"), bg=KART, fg=SILIK,
                 font=(F, 8, "bold"), anchor="w").pack(fill="x", pady=(16, 6))
        tk.Label(ic, text=m("adim_ipucu"), bg=KART, fg=SILIK,
                 font=(F, 8), anchor="w", justify="left").pack(fill="x")

        a1 = tk.Frame(ic, bg=KART)
        a1.pack(fill="x", pady=2)
        tk.Label(a1, text="1", bg=KART2, fg=SOLUK, font=(F, 8, "bold"),
                 width=2).pack(side="left", ipady=2)
        tk.Label(a1, text=m("a1") + "  ", bg=KART, fg=METIN,
                 font=(F, 9)).pack(side="left", padx=(10, 0))
        lb = tk.Label(a1, text=m("a1_btn") + "  ↗", bg=KART, fg=MAVI,
                      font=(F, 9, "underline"), cursor="hand2")
        lb.pack(side="left")
        lb.bind("<Button-1>", lambda e: _ac_url(EKLENTI_URL))

        for no, anahtar in ((2, "a2"), (3, "a3"), (4, "a4"), (5, "a5"), (6, "a6")):
            r = satir(ic, no, m(anahtar).replace("**", ""))
            r.pack(fill="x", pady=2)

        # 3 · dene
        tk.Label(ic, text=m("test"), bg=KART, fg=SILIK,
                 font=(F, 8, "bold"), anchor="w").pack(fill="x", pady=(16, 4))
        d = tk.Frame(ic, bg=KART)
        d.pack(fill="x")
        tk.Label(d, text=m("test_alt"), bg=KART, fg=SOLUK,
                 font=(F, 8)).pack(side="left")
        kod = tk.Label(d, text=m("test_kod"), bg=KART2, fg="#79c0ff",
                       font=("Consolas", 8), cursor="hand2", padx=7, pady=2)
        kod.pack(side="left", padx=(7, 0))
        kod.bind("<Button-1>", lambda e: self._kopya_metin(m("test_kod")))

        # alt çubuk
        tk.Frame(kok, bg=CIZGI, height=1).pack(side="bottom", fill="x",
                                                padx=20, pady=(0, 0))
        alt = tk.Frame(kok, bg=ARKA)
        alt.pack(side="bottom", fill="x", padx=22, pady=12)
        for anahtar, fn in (("lisans", self.lisans_penceresi),
                            ("destek", self.destek_penceresi),
                            ("gelismis", self.gelismis_penceresi),
                            ("cikis", self.cikis_tam)):
            tk.Button(alt, text=m(anahtar), command=fn, bg=ARKA, fg=SILIK,
                      activebackground=ARKA, activeforeground=METIN,
                      relief="flat", bd=0, highlightthickness=0,
                      font=(F, 8), cursor="hand2", padx=6, pady=3).pack(
                side="left", padx=(0, 4))

    # ----------------------------------------------------------------- durum
    def _boya(self, acik):
        if acik:
            self.nokta.config(text="●", fg=YESIL)
            self.baslik.config(text=m("baslik_on"))
            self.alt.config(text=m("alt_on"))
            self.dugme.config(text=m("kapat"), bg=KIRMIZI_K, fg="#ff9b96",
                              activebackground="#3a1a1c", activeforeground="#ff9b96")
            self.kart.pack(fill="x", padx=28, pady=(18, 0))
            self._boyut(700)
        else:
            self.nokta.config(text="○", fg=SILIK)
            self.baslik.config(text=m("baslik_off"))
            self.alt.config(text=m("alt_off"))
            self.dugme.config(text=m("bagla"), bg=YESIL, fg="#ffffff",
                              activebackground="#3fb950", activeforeground="#ffffff")
            self.kart.pack_forget()
            self._boyut(330)
        self._acik = acik

    def _boyut(self, yukseklik):
        """Pencereyi büyüt/küçült — SOL ÜST köşe sabit kalır (içerik kaymaz)."""
        try:
            self.kok.update_idletasks()
            x, y = self.kok.winfo_x(), self.kok.winfo_y()
            if x <= 0 and y <= 0:
                x = y = None
            if x is None:
                self.kok.geometry("560x%d" % yukseklik)
            else:
                self.kok.geometry("560x%d+%d+%d" % (yukseklik, x, y))
        except Exception:
            pass

    def _ilk(self):
        try:
            import ghostpilot as G
            self.surum.config(text="v" + G.VERSION)
        except Exception:
            pass
        self.durum_guncelle()

    @staticmethod
    def _tunel_bilgi():
        try:
            import json
            with open(_cfg_yolu("tunel.json"), encoding="utf-8") as f:
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
            return url
        try:
            if os.name == "nt":
                r = subprocess.run(["tasklist", "/FI", "PID eq %s" % pid],
                                   capture_output=True, text=True, timeout=10,
                                   **SESSIZ)
                return url if str(pid) in (r.stdout or "") else ""
            os.kill(int(pid), 0)
            return url
        except Exception:
            return ""

    def durum_guncelle(self):
        if not self._mesgul:
            url = self._tunel_canli()
            self._tunel = url
        if self._tunel:
            if self.adres.get().strip() != self._tunel:
                self.adres.config(state="normal")
                self.adres.delete(0, "end")
                self.adres.insert(0, self._tunel)
                self.adres.config(state="readonly")
            if not getattr(self, "_acik", False):
                self._boya(True)
        elif getattr(self, "_acik", False):
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
        self._kapat() if self._tunel else self._baglan()

    def _mesgul_yap(self, acik, yazi=None):
        self._mesgul = acik
        self.dugme.config(state="disabled" if acik else "normal",
                          text=yazi or (m("kapat") if self._tunel else m("bagla")))

    def _baglan(self):
        self._mesgul_yap(True, m("bekle"))
        self.alt.config(text=m("bekle"))
        self.nokta.config(text="◌", fg=SOLUK)

        def _():
            sonuc = {"tip": "hata", "metin": m("sunucu_yok")}
            if _calisiyor() or _sunucu_baslat():
                try:
                    d = _istek("/panel/eylem?k=bagla", sure=180)
                    msg = str(d.get("message") or "")
                    if msg.startswith("BAGLANDI|"):
                        self._tunel = msg.split("|")[2]
                        sonuc = {"tip": "ok"}
                    elif msg.startswith("TUNEL_YOK|"):
                        sonuc = {"tip": "hata", "metin": msg.split("|", 1)[1]}
                    else:
                        sonuc = {"tip": "hata", "metin": msg or m("sunucu_yok")}
                except Exception as e:
                    sonuc = {"tip": "hata", "metin": "%s\n%s" % (m("sunucu_yok"), e)}
            self.kok.after(0, lambda: self._bitti(sonuc))
        threading.Thread(target=_, daemon=True).start()

    def _bitti(self, sonuc):
        self._mesgul_yap(False)
        if sonuc.get("tip") == "ok":
            self.durum_guncelle()
            self._boya(True)
        else:
            self.nokta.config(text="○", fg=KIRMIZI)
            self.baslik.config(text=m("hata_bas"))
            self.alt.config(text=sonuc.get("metin", "")[:300])
            self.dugme.config(state="normal", text=m("bagla"))

    def _kapat(self):
        self._tunel = ""
        self._boya(False)

        def _():
            try:
                _istek("/panel/eylem?k=bagla", sure=60)
            except Exception:
                pass
        threading.Thread(target=_, daemon=True).start()

    def _kopya_metin(self, metin):
        try:
            self.kok.clipboard_clear()
            self.kok.clipboard_append(metin)
        except Exception:
            pass

    def kopyala(self):
        a = self.adres.get().strip()
        if not a:
            return
        self._kopya_metin(a)
        self.kopya.config(text="✓ " + m("kopyalandi"), bg=YESIL_K, fg="#7ee787")
        self.adres.config(highlightthickness=1, highlightbackground=YESIL)
        self.kok.after(1800, self._kopya_bitti)

    def _kopya_bitti(self):
        self.kopya.config(text=m("kopyala"), bg=CIZGI, fg=METIN)
        self.adres.config(highlightthickness=0)

    # --------------------------------------------------------------- lisans
    def lisans_penceresi(self):
        p = self._pencere(m("lisans"), "520x430")
        try:
            import paketler as PK
        except Exception:
            PK = None
        try:
            import ghostpilot as G
            k = (G.CFG.get("license_key") or "").strip()
            kota = G._kota_yukle() if hasattr(G, "_kota_yukle") else {}
            kul = int(kota.get("used") or 0)
        except Exception:
            k, kul = "", 0

        tk.Label(p, text="PRO" if k else "Ücretsiz", bg=ARKA,
                 fg=YESIL if k else SOLUK, font=(F, 15, "bold")).pack(
            anchor="w", padx=26, pady=(6, 2))
        tk.Label(p, text="Bu ay %d / 20.000 çağrı" % kul, bg=ARKA, fg=SOLUK,
                 font=(F, 10)).pack(anchor="w", padx=26)

        g = tk.Frame(p, bg=ARKA)
        g.pack(fill="x", padx=26, pady=(18, 0))
        e = tk.Entry(g, bg=KART, fg=METIN, insertbackground=METIN, relief="flat",
                     font=("Consolas", 9))
        e.pack(side="left", fill="x", expand=True, ipady=8)
        e.insert(0, k)
        sonuc = tk.Label(p, text="", bg=ARKA, fg=SOLUK, font=(F, 8), anchor="w")
        sonuc.pack(fill="x", padx=26, pady=(6, 0))

        def uygula():
            try:
                import ghostpilot as G
                G.CFG["license_key"] = e.get().strip()
                G.save_cfg(G.CFG)
                sonuc.config(text="Kaydedildi.", fg=YESIL)
            except Exception as ex:
                sonuc.config(text="Hata: %s" % ex, fg=KIRMIZI)

        btn(g, "Uygula", uygula, "sade", pady=8).pack(side="left", padx=(8, 0))

        if PK:
            try:
                kutu = tk.Frame(p, bg=KART)
                kutu.pack(fill="x", padx=26, pady=(22, 0))
                ic = tk.Frame(kutu, bg=KART)
                ic.pack(fill="x", padx=16, pady=14)
                tk.Label(ic, text="Ücretsiz  ·  20.000 çağrı/ay", bg=KART,
                         fg=METIN, font=(F, 10)).pack(anchor="w")
                tk.Label(ic, text="PRO  ·  %d %s/ay  ·  sınırsız" % (
                    PK.AYLIK_FIYAT, PK.PARA_BIRIMI), bg=KART, fg=SOLUK,
                    font=(F, 10)).pack(anchor="w", pady=(4, 0))
                tk.Label(ic, text="Satış yok — yalnız bağış.", bg=KART, fg=SILIK,
                         font=(F, 8)).pack(anchor="w", pady=(6, 0))
            except Exception:
                pass

    # --------------------------------------------------------------- destek
    def destek_penceresi(self):
        p = self._pencere(m("destek"), "540x520")
        tk.Label(p, text="Açık kaynak, ücretsiz. Satış yok — sürdürmenin tek yolu bağış.",
                 bg=ARKA, fg=SOLUK, font=(F, 10), wraplength=480,
                 justify="left", anchor="w").pack(anchor="w", padx=26, pady=(6, 0))
        tk.Button(p, text="☕  Bağış yap — buymeacoffee.com/btmcode", cursor="hand2",
                  command=lambda: _ac_url("https://buymeacoffee.com/btmcode"),
                  bg="#ffdd00", fg="#111", relief="flat", bd=0, highlightthickness=0,
                  font=(F, 10, "bold"), padx=18, pady=12,
                  anchor="w").pack(fill="x", padx=26, pady=(18, 0))

        tk.Label(p, text="BAĞLANTILAR", bg=ARKA, fg=SILIK, font=(F, 8, "bold"),
                 anchor="w").pack(fill="x", padx=26, pady=(22, 6))
        for etiket, deger, url in [
            ("Geliştirici", "BtmCode", ""),
            ("E-posta", "devcloudpy@gmail.com", "mailto:devcloudpy@gmail.com"),
            ("Web sitesi", "btmcode.vercel.app", "https://btmcode.vercel.app"),
            ("Kaynak kodu", "github.com/Btmcode/Ghost-Pilot",
             "https://github.com/Btmcode/Ghost-Pilot"),
            ("GitHub", "github.com/Btmcode", "https://github.com/Btmcode"),
            ("Bağış", "buymeacoffee.com/btmcode", "https://buymeacoffee.com/btmcode"),
            ("Gizlilik", "Gizlilik politikası",
             "https://github.com/Btmcode/Ghost-Pilot/blob/main/GIZLILIK.md"),
            ("Koşullar", "Kullanım koşulları",
             "https://github.com/Btmcode/Ghost-Pilot/blob/main/KOSULLAR.md"),
        ]:
            r = tk.Frame(p, bg=ARKA)
            r.pack(fill="x", padx=26, pady=1)
            tk.Label(r, text=etiket, bg=ARKA, fg=SILIK, font=(F, 9),
                     width=13, anchor="w").pack(side="left")
            lb = tk.Label(r, text=deger, bg=ARKA, fg=MAVI if url else METIN,
                          font=(F, 9), anchor="w")
            lb.pack(side="left")
            if url:
                lb.configure(cursor="hand2")
                lb.bind("<Button-1>", lambda e, u=url: _ac_url(u))

    # -------------------------------------------------------------- gelişmiş
    def gelismis_penceresi(self):
        p = self._pencere(m("gelismis"), "600x540")

        sat = tk.Frame(p, bg=ARKA)
        sat.pack(fill="x", padx=26, pady=(6, 14))
        tk.Label(sat, text="Dil", bg=ARKA, fg=SILIK, font=(F, 9)).pack(side="left")
        for kod, et in (("tr", "TR"), ("en", "EN"), ("de", "DE"), ("es", "ES")):
            btn(sat, et, lambda k=kod: self._dil(k, p), "mini", pady=4,
                padx=9).pack(side="left", padx=(6, 0))

        tk.Label(p, text="İZİN VERİLEN KLASÖRLER", bg=ARKA, fg=SILIK,
                 font=(F, 8, "bold"), anchor="w").pack(fill="x", padx=26)
        try:
            import ghostpilot as G
            yaz = set(G.CFG.get("write_roots") or [])
            for k in list(dict.fromkeys((G.CFG.get("read_roots") or []) +
                                        (G.CFG.get("write_roots") or []))):
                tk.Label(p, text=("yazma  " if k in yaz else "okuma  ") + k,
                         bg=ARKA, fg=METIN if k in yaz else SOLUK,
                         font=("Consolas", 8), anchor="w").pack(fill="x", padx=26)
        except Exception:
            pass

        sat2 = tk.Frame(p, bg=ARKA)
        sat2.pack(fill="x", padx=26, pady=(16, 0))
        btn(sat2, "👁  Salt okunur", lambda: self._komut("salt-okunur", p),
            "mini", pady=6).pack(side="left")
        btn(sat2, "✍  Okuma + yazma", lambda: self._komut("yazma", p),
            "mini", pady=6).pack(side="left", padx=8)

        sat3 = tk.Frame(p, bg=ARKA)
        sat3.pack(fill="x", padx=26, pady=(20, 4))
        tk.Label(sat3, text="HATA KAYDI", bg=ARKA, fg=SILIK,
                 font=(F, 8, "bold")).pack(side="left")
        btn(sat3, "Yenile", lambda: self._log(kutu), "mini",
            pady=3).pack(side="right")

        kutu = tk.Text(p, height=11, bg="#0b0f16", fg="#a9b6c6", relief="flat",
                       font=("Consolas", 8), wrap="word")
        kutu.pack(fill="both", expand=True, padx=26, pady=(4, 0))
        self._log(kutu)

    def _log(self, kutu):
        try:
            ic = (hata.son(60) if hata and hasattr(hata, "son") else "") or \
                 "(kayıt boş — hata yok)"
        except Exception as e:
            ic = str(e)
        kutu.config(state="normal")
        kutu.delete("1.0", "end")
        kutu.insert("end", ic)
        kutu.config(state="disabled")

    def _dil(self, kod, pencere=None):
        try:
            _D.dil_sec(kod)
        except Exception:
            pass
        if pencere:
            pencere.destroy()
        self.baslik.config(text=m("baslik_on") if self._tunel else m("baslik_off"))
        self.alt.config(text=m("alt_on") if self._tunel else m("alt_off"))
        self.dugme.config(text=m("kapat") if self._tunel else m("bagla"))
        self.kopya.config(text=m("kopyala"))

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

    # ------------------------------------------------------------- pencere
    def _pencere(self, baslik, boyut):
        p = tk.Toplevel(self.kok)
        p.title("GhostPilot — " + baslik)
        p.configure(bg=ARKA)
        p.geometry(boyut)
        p.transient(self.kok)
        u = tk.Frame(p, bg=ARKA)
        u.pack(fill="x", padx=26, pady=(22, 12))
        tk.Label(u, text=baslik, bg=ARKA, fg=METIN,
                 font=(F, 14, "bold")).pack(side="left")
        tk.Button(u, text="✕", command=p.destroy, bg=ARKA, fg=SILIK,
                  relief="flat", bd=0, highlightthickness=0, font=(F, 12),
                  cursor="hand2", padx=4).pack(side="right")
        return p

    # ---------------------------------------------------------------- tepsi
    def _tepsi_kur(self):
        try:
            import tepsi
            self.tepsi = tepsi.Tepsi(
                baslik="GhostPilot", ipucu="GhostPilot",
                solda=lambda: self.kok.after(0, self.goster),
                sunucu=lambda: self.kok.after(0, self.cikis_tam),
                cikis=lambda: self.kok.after(0, self.cikis_tam),
                durum=lambda: {"sunucu": bool(_calisiyor()), "bekci": False,
                               "metin": ""})
            if self.tepsi.baslat():
                self.tepsi.guncelle({"sunucu": bool(_calisiyor()), "bekci": False,
                                     "metin": ""})
        except Exception:
            self.tepsi = None

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
        kok.tk.call("tk", "scaling", 1.25)
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
        p.configure(bg=ARKA)
        p.geometry("700x400")
        tk.Label(p, text=baslik, bg=ARKA, fg="#ff7b72",
                 font=(F, 13, "bold")).pack(anchor="w", padx=20, pady=(18, 6))
        tk.Label(p, text="%s: %s" % (type(exc).__name__, exc), bg=ARKA, fg=METIN,
                 wraplength=660, justify="left", anchor="w",
                 font=(F, 9)).pack(anchor="w", padx=20)
        tk.Label(p, text="Ayrıntılar: " + yol, bg=ARKA, fg=SILIK,
                 font=(F, 8)).pack(anchor="w", padx=20, pady=(4, 0))
        kutu = scrolledtext.ScrolledText(p, height=12, bg="#0b0f16", fg="#a9b6c6",
                                         font=("Consolas", 8), relief="flat")
        kutu.pack(fill="both", expand=True, padx=20, pady=10)
        try:
            kutu.insert("end", hata.son(40) if hata else str(exc))
        except Exception:
            kutu.insert("end", str(exc))
        tk.Button(p, text="Kapat", command=p.destroy, bg=CIZGI, fg=METIN,
                  relief="flat", bd=0, padx=22, pady=6).pack(pady=(0, 14))
        p.mainloop()
    except Exception:
        pass


if __name__ == "__main__":
    sys.exit(main())

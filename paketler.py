#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — paketler.py  ·  TEK DOĞRULUK KAYNAĞI (fiyat + özellikler)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Fiyatı veya özelliği DEĞİŞTİRMEK İÇİN YALNIZ BU DOSYAYI düzenleyin.
#  Arayüz (ui.py), web paneli (ghostpilot.py), kurulum (kurulum_ui.py) ve
#  admin paneli buradan okur. Başka yerde fiyat yazmayın.
# ============================================================================

import sys

# ---------------------------------------------------------------------------
#  FİYAT — tek yer
# ---------------------------------------------------------------------------
PARA_BIRIMI = "$"
AYLIK_FIYAT = 10
YILLIK_FIYAT = 96            # 10 x 12 = 120 → 2 ay bedava
BAGIS_URL = "https://buymeacoffee.com/btmcode"
SITE_URL = "https://btmcode.vercel.app"

# ---------------------------------------------------------------------------
#  ÖZELLİK LİSTESİ
#  (anahtar, ücretsizde_var_mi)  →  metinler aşağıdaki OZELLIK_METIN'de
# ---------------------------------------------------------------------------
OZELLIKLER = [
    ("arac",        True),
    ("kota",        True),
    ("ekran",       True),
    ("dosya",       True),
    ("terminal",    True),
    ("zamanla",     True),
    ("cevaplama",   True),
    ("onay",        True),
    ("hesap",         False),
    ("sinirsiz",    False),
    ("cihaz",       False),
    ("destek",      False),
    ("erken",       False),
    ("ozel",        False),
]

OZELLIK_METIN = {
    "tr": {
        "arac":      "44 aracın tamamı",
        "kota":      "Ayda 20.000 çağrı",
        "ekran":     "Ekran görüntüsü ve fare/klavye",
        "dosya":     "Dosya okuma, yazma, taşıma",
        "terminal":  "Terminal komutu çalıştırma",
        "zamanla":   "Zamanlanmış görevler",
        "cevaplama": "Bekleme yok, hemen cevap",
        "onay":      "Onay ekranı (riskli işlemler)",
                "sinirsiz":  "Sınırsız çağrı",
        "cihaz":     "Sınırsız bilgisayar",
        "destek":    "Öncelikli destek (24 saat)",
        "erken":     "Yeni özelliklere erken erişim",
        "ozel":      "Özel araç isteği",
        "ucretsiz":  "Ücretsiz",
        "aylik":     "Aylık",
        "yillik":    "Yıllık",
        "ay":        "/ay",
        "yil":       "/yıl",
        "en_cok":    "EN ÇOK TERCİH EDİLEN",
        "sonsuz":    "Sınırsız",
        "dahil":     "dahil",
        "yok":       "—",
        "baslik":    "Paketler",
        "alt":       ("GhostPilot'un tamamı ücretsizdir. Destek anahtarı alırsanız "
                      "sınırsız kullanır, geliştirmeye katkı sağlarsınız."),
        "katil":     "Destek ol",
        "devam":     "Ücretsiz devam et",
        "sizde":     "Şu anki paketiniz",
        "fiyat_not": ("İstediğiniz zaman iptal edebilirsiniz. Ödeme alınmazsa "
                      "paket kendiliğinden ücretsize döner."),
        "bagis_not": "Bağış yoluyla desteklenir — zorunlu değildir.",
        "erisim": "Uzaktan erişim",
        "hesap": "Hesabınızı cihazlar arası taşıma",
    },
    "en": {
        "arac":      "All 44 tools",
        "kota":      "20,000 calls per month",
        "ekran":     "Screenshots and mouse/keyboard",
        "dosya":     "Read, write, move files",
        "terminal":  "Run terminal commands",
        "zamanla":   "Scheduled tasks",
        "cevaplama": "No waiting, instant replies",
        "onay":      "Approval screen (risky actions)",
                "sinirsiz":  "Unlimited calls",
        "cihaz":     "Unlimited computers",
        "destek":    "Priority support (24h)",
        "erken":     "Early access to new features",
        "ozel":      "Custom tool requests",
        "ucretsiz":  "Free",
        "aylik":     "Monthly",
        "yillik":    "Yearly",
        "ay":        "/mo",
        "yil":       "/yr",
        "en_cok":    "MOST POPULAR",
        "sonsuz":    "Unlimited",
        "dahil":     "included",
        "yok":       "—",
        "baslik":    "Plans",
        "alt":       ("GhostPilot is entirely free. A support key gives you unlimited "
                      "use and funds development."),
        "katil":     "Support us",
        "devam":     "Continue free",
        "sizde":     "Your current plan",
        "fiyat_not": ("Cancel anytime. If payment stops, the plan falls back to free "
                      "automatically."),
        "bagis_not": "Funded by donations — never mandatory.",
        "erisim": "Remote access",
        "hesap": "Move your account between devices",
    },
    "de": {
        "arac":      "Alle 44 Werkzeuge",
        "kota":      "20.000 Aufrufe pro Monat",
        "ekran":     "Screenshots und Maus/Tastatur",
        "dosya":     "Dateien lesen, schreiben, verschieben",
        "terminal":  "Terminalbefehle ausführen",
        "zamanla":   "Geplante Aufgaben",
        "cevaplama": "Kein Warten, sofortige Antwort",
        "onay":      "Bestätigungsfenster (riskante Aktionen)",
                "sinirsiz":  "Unbegrenzte Aufrufe",
        "cihaz":     "Unbegrenzte Computer",
        "destek":    "Bevorzugter Support (24 Std.)",
        "erken":     "Früher Zugang zu Neuheiten",
        "ozel":      "Individuelle Werkzeugwünsche",
        "ucretsiz":  "Kostenlos",
        "aylik":     "Monatlich",
        "yillik":    "Jährlich",
        "ay":        "/Mon.",
        "yil":       "/Jahr",
        "en_cok":    "AM BELIEBTESTEN",
        "sonsuz":    "Unbegrenzt",
        "dahil":     "enthalten",
        "yok":       "—",
        "baslik":    "Pakete",
        "alt":       ("GhostPilot ist vollständig kostenlos. Ein Supportschlüssel "
                      "ermöglicht unbegrenzte Nutzung und finanziert die Entwicklung."),
        "katil":     "Unterstützen",
        "devam":     "Kostenlos fortfahren",
        "sizde":     "Ihr aktuelles Paket",
        "fiyat_not": ("Jederzeit kündbar. Ohne Zahlung fällt das Paket automatisch "
                      "auf kostenlos zurück."),
        "bagis_not": "Durch Spenden finanziert — niemals Pflicht.",
        "erisim": "Fernzugriff",
        "hesap": "Konto zwischen Geräten übertragen",
    },
    "es": {
        "arac":      "Las 44 herramientas",
        "kota":      "20.000 llamadas al mes",
        "ekran":     "Capturas y ratón/teclado",
        "dosya":     "Leer, escribir y mover archivos",
        "terminal":  "Ejecutar comandos de terminal",
        "zamanla":   "Tareas programadas",
        "cevaplama": "Sin esperas, respuesta inmediata",
        "onay":      "Pantalla de aprobación (acciones de riesgo)",
                "sinirsiz":  "Llamadas ilimitadas",
        "cihaz":     "Ordenadores ilimitados",
        "destek":    "Soporte prioritario (24 h)",
        "erken":     "Acceso anticipado a novedades",
        "ozel":      "Solicitudes de herramientas propias",
        "ucretsiz":  "Gratis",
        "aylik":     "Mensual",
        "yillik":    "Anual",
        "ay":        "/mes",
        "yil":       "/año",
        "en_cok":    "MÁS POPULAR",
        "sonsuz":    "Ilimitado",
        "dahil":     "incluido",
        "yok":       "—",
        "baslik":    "Planes",
        "alt":       ("GhostPilot es totalmente gratis. Una clave de soporte da uso "
                      "ilimitado y financia el desarrollo."),
        "katil":     "Apóyanos",
        "devam":     "Continuar gratis",
        "sizde":     "Su plan actual",
        "fiyat_not": ("Cancele cuando quiera. Si el pago se detiene, el plan vuelve "
                      "a gratuito automáticamente."),
        "bagis_not": "Financiado con donaciones — nunca obligatorio.",
        "erisim": "Acceso remoto",
        "hesap": "Mover su cuenta entre dispositivos",
    },
}


def m(anahtar, dil=None):
    """Seçili dilde özellik metni."""
    if dil is None:
        try:
            import diller
            dil = diller.dil()
        except Exception:
            dil = "tr"
    return (OZELLIK_METIN.get(dil) or OZELLIK_METIN["tr"]).get(anahtar, anahtar)


def fiyat_yaz(plan="AY"):
    """'$10/ay' gibi kısa fiyat metni."""
    if (plan or "").upper() == "YI":
        return f"{PARA_BIRIMI}{YILLIK_FIYAT}{m('yil')}"
    if (plan or "").upper() == "DE":
        return m("ucretsiz")
    return f"{PARA_BIRIMI}{AYLIK_FIYAT}{m('ay')}"


def paket_listesi():
    """[{'kod','ad','fiyat','gun','ozellikler':[(metin,var)]}] — 2 paket."""
    return [
        {"kod": "FREE", "ad": m("ucretsiz"), "fiyat": m("ucretsiz"),
         "gun": 0, "vurgu": False,
         "ozellikler": [(m(a), v) for a, v in OZELLIKLER]},
        {"kod": "AY", "ad": "PRO", "fiyat": f"{PARA_BIRIMI}{AYLIK_FIYAT}{m('ay')}",
         "gun": 30, "vurgu": True,
         "ozellikler": [(m(a), True) for a, _ in OZELLIKLER]},
    ]


def satir_metinleri(kod="AY"):
    """Konsol/CLI için düz metin karşılaştırma."""
    satirlar = []
    baslik = f"{m('baslik'):<34}{m('ucretsiz'):<14}{'PRO':<14}"
    satirlar.append(baslik)
    satirlar.append("─" * 62)
    satirlar.append(f"{'':<34}{'0 ' + PARA_BIRIMI:<14}{PARA_BIRIMI}{AYLIK_FIYAT}{m('ay')}")
    satirlar.append("─" * 62)
    for ad, ucretsizde in OZELLIKLER:
        u = "✓" if ucretsizde else "·"
        p = "✓"
        satirlar.append(f"{m(ad):<34}{u:<14}{p}")
    satirlar.append("─" * 62)
    satirlar.append(m("bagis_not"))
    return "\n".join(satirlar)


if __name__ == "__main__":
    print(satir_metinleri())

# ---- Rakip karşılaştırması (Desktop Commander: 10.000 çağrı / $20+KDV) ----
RAKIP = {"ad": "Desktop Commander", "kota": 10000, "fiyat": 20}
KARSILASTIRMA = {
    "tr": "Karşılaştırma: {rakip} ayda 10.000 çağrı verir, sınırsız için $20/ay. "
          "GhostPilot 20.000 çağrı verir, sınırsız için $10/ay.",
    "en": "Compare: {rakip} gives 10,000 calls a month, $20/mo for unlimited. "
          "GhostPilot gives 20,000 calls, $10/mo for unlimited.",
    "de": "Vergleich: {rakip} bietet 10.000 Aufrufe pro Monat, 20 $/Monat für unbegrenzt. "
          "GhostPilot bietet 20.000 Aufrufe, 10 $/Monat für unbegrenzt.",
    "es": "Comparación: {rakip} ofrece 10.000 llamadas al mes, 20 $/mes por ilimitado. "
          "GhostPilot ofrece 20.000 llamadas, 10 $/mes por ilimitado.",
}


def rakip_metni():
    import diller
    kal = KARSILASTIRMA.get(diller.dil(), KARSILASTIRMA["tr"])
    return kal.format(rakip=RAKIP["ad"])

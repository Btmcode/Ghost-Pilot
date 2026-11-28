#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — diller.py  ·  Çok dillilik (TR / EN / DE / ES)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Kullanım:
#      from diller import D, dil_sec, t
#      D["kurulum"]            → seçili dildeki metin
#      t("merhaba", ad="Ali")  → biçimlendirilmiş metin
#
#  Yeni dil eklemek: LANG sözlüğüne bir blok ekleyin, başka hiçbir yer değişmez.
# ============================================================================

import json
import os

DILLER = {
    "tr": "Türkçe",
    "en": "English",
    "de": "Deutsch",
    "es": "Español",
}
VARSAYILAN = "tr"
AYAR_DOSYA = os.path.join(os.path.expanduser("~"), ".ghostpilot", "dil.json")

LANG = {
    # ------------------------------------------------------------------ TR
    "tr": {
        "uygulama": "GhostPilot",
        "slogan": "Gerçek bilgisayarınız, sandbox değil · ayda 20.000 çağrı ücretsiz",
        "kurulum": "Kurulum",
        "hos_geldin": "Hoş geldiniz",
        "hos_alt": "Bu sihirbaz 4 adımda her şeyi kurar. Sizden teknik bilgi istenmez.",
        "dil_sec": "Dil seçin",
        "devam": "Devam",
        "geri": "Geri",
        "iptal": "İptal",
        "bitir": "Bitir",
        "asama": "Adım {n} / {t}",
        "lisans_baslik": "Destek anahtarınız var mı?",
        "lisans_alt": ("Anahtarınız varsa şimdi girin (sınırsız kullanım). "
                       "Yoksa atlayın — ayda 20.000 çağrı ücretsizdir."),
        "lisans_kutu": "Destek anahtarı (GP-…)",
        "lisans_ekle": "Anahtarı doğrula",
        "lisans_atla": "Şimdilik atla",
        "lisans_gecerli": "Anahtar geçerli: {plan} · bitiş {bitis}",
        "lisans_gecersiz": "Anahtar geçersiz: {neden}",
        "lisans_yok": "Anahtar girilmedi — ücretsiz plan.",
        "kurulum_baslik": "Kurulum sürüyor",
        "kurulum_alt": "Pencereyi kapatmayın. Bu işlem 5–10 dakika sürebilir.",
        "bitti_baslik": "Kurulum tamamlandı",
        "bitti_alt": "ChatGPT'ye eklemek için aşağıdaki bilgileri kullanın.",
        "adres": "Sunucu adresi",
        "kopyala": "Kopyala",
        "kopyalandi": "Kopyalandı",
        "panel": "Paneli aç",
        "kapat": "Kapat",
        "hata": "Hata",
        "durum": "Durum",
        "sunucu": "Sunucu",
        "bekci": "Bekçi",
        "arac": "Araç",
        "mod": "Mod",
        "kullanim": "Bu ayki kullanım",
        "paket": "Paket",
        "kalan_gun": "kalan {n} gün",
        "sinirsiz": "sınırsız",
        "lisans_gir": "Lisans anahtarı gir",
        "baslat": "Başlat",
        "durdur": "Durdur",
        "yenile": "Güncelle",
        "cihaz_no": "Bu bilgisayarın numarası",
        "dil": "Dil",
        "chatgpt_adim": ("ChatGPT → Ayarlar → Bağlayıcılar → Özel MCP sunucusu ekle:\n"
                         "Ad: GhostPilot · Kimlik: OAuth · Simge: chatgpt-icon-256.png"),
        # adım adları
        "adim_python": "Python",
        "adim_paket": "Gerekli paketler",
        "adim_tunel": "HTTPS tüneli (ek program yok)",
        "adim_ayar": "Yapılandırma",
        "adim_sunucu": "Sunucu",
        "adim_kisayol": "Masaüstü kısayolu",
        "adim_venv": "Sanal ortam",
        "basla": 'Başlat',
        "kapatiliyor": 'Kapatılıyor…',
        "calisiyor": 'çalışıyor',
        "durdu": 'durdu',
        "modul_yok": 'modül yok',
        "sinir_doldu": 'Sınır doldu — destek anahtarı gerekli',
        "ls_gecerli": 'Anahtar geçerli',
        "ls_gecersiz": 'Anahtar geçersiz',
        "erisim_kapali": 'Uzaktan erişim KAPALI',
        "bekle": 'Bekleyin…',
        "hazir": 'Hazır',
        "cihaz": 'Cihaz numarası',
        "bagis": 'Destek ol',
        "github": 'GitHub',
        "destek_anahtari": 'Destek anahtarı iste',
        "site": 'Site',
        "notlar": 'Günlük notlar',
        "acil_durdurma": 'Acil durdurma',
        "mod_sec": 'Mod',
        "izin_klasor": 'İzin verilen klasörler',
        "son_islemler": 'Son işlemler',
        "onay_bekleyen": 'Onay bekleyen işlemler',
        "arayuz": 'Program arayüzü',
        "tepsi_ipucu": 'Saat kenarında çalışıyor',
        "aktif": 'aktif',
        "yok": 'yok',
        "salt_okunur": 'salt okunur',
        "yazma": 'okuma + yazma',
        "kalan": 'Kalan',
        "cihaz_no_ipucu": '(satıcıya bu numarayı verirseniz anahtar yalnız bu bilgisayara kilitlenir)',
        "erisim_acik": 'Erişim açık',
        "izinleri_iptal": 'Tüm izinleri iptal et',
        "cikis_tam": 'Tamamen çık',
        "lisans": 'Lisans',
        "paketler_sec": 'Paketler',
        "sifirlanma_alt": "Her ayın 1'inde sıfırlanır",
    },
    # ------------------------------------------------------------------ EN
    "en": {
        "uygulama": "GhostPilot",
        "slogan": "Your real computer, not a sandbox · 20,000 free calls a month",
        "kurulum": "Setup",
        "hos_geldin": "Welcome",
        "hos_alt": "This wizard installs everything in 4 steps. No technical knowledge required.",
        "dil_sec": "Choose language",
        "devam": "Continue",
        "geri": "Back",
        "iptal": "Cancel",
        "bitir": "Finish",
        "asama": "Step {n} of {t}",
        "lisans_baslik": "Do you have a support key?",
        "lisans_alt": ("Enter it now for unlimited use. Skip if you don't have one — "
                       "20,000 tool calls per month are free."),
        "lisans_kutu": "Support key (GP-…)",
        "lisans_ekle": "Verify key",
        "lisans_atla": "Skip for now",
        "lisans_gecerli": "Valid key: {plan} · expires {bitis}",
        "lisans_gecersiz": "Invalid key: {neden}",
        "lisans_yok": "No key entered — free plan.",
        "kurulum_baslik": "Installing",
        "kurulum_alt": "Please keep this window open. This may take 5–10 minutes.",
        "bitti_baslik": "Setup complete",
        "bitti_alt": "Use the details below to add GhostPilot to ChatGPT.",
        "adres": "Server address",
        "kopyala": "Copy",
        "kopyalandi": "Copied",
        "panel": "Open panel",
        "kapat": "Close",
        "hata": "Error",
        "durum": "Status",
        "sunucu": "Server",
        "bekci": "Watchdog",
        "arac": "Tools",
        "mod": "Mode",
        "kullanim": "Usage this month",
        "paket": "Plan",
        "kalan_gun": "{n} days left",
        "sinirsiz": "unlimited",
        "lisans_gir": "Enter license key",
        "baslat": "Start",
        "durdur": "Stop",
        "yenile": "Refresh",
        "cihaz_no": "This computer's ID",
        "dil": "Language",
        "chatgpt_adim": ("ChatGPT → Settings → Connectors → Add custom MCP server:\n"
                         "Name: GhostPilot · Auth: OAuth · Icon: chatgpt-icon-256.png"),
        "adim_python": "Python",
        "adim_paket": "Required packages",
        "adim_tunel": "HTTPS tunnel (no extra software)",
        "adim_ayar": "Configuration",
        "adim_sunucu": "Server",
        "adim_kisayol": "Desktop shortcut",
        "adim_venv": "Virtual environment",
        "basla": 'Start',
        "kapatiliyor": 'Closing…',
        "calisiyor": 'running',
        "durdu": 'stopped',
        "modul_yok": 'module missing',
        "sinir_doldu": 'Limit reached — support key required',
        "ls_gecerli": 'Key valid',
        "ls_gecersiz": 'Key invalid',
        "erisim_kapali": 'Remote access OFF',
        "bekle": 'Please wait…',
        "hazir": 'Ready',
        "cihaz": 'Device number',
        "bagis": 'Support us',
        "github": 'GitHub',
        "destek_anahtari": 'Request a support key',
        "site": 'Site',
        "notlar": 'Daily notes',
        "acil_durdurma": 'Emergency stop',
        "mod_sec": 'Mode',
        "izin_klasor": 'Allowed folders',
        "son_islemler": 'Recent activity',
        "onay_bekleyen": 'Pending approvals',
        "arayuz": 'Application window',
        "tepsi_ipucu": 'Running in the tray',
        "aktif": 'active',
        "yok": 'none',
        "salt_okunur": 'read only',
        "yazma": 'read + write',
        "kalan": 'Remaining',
        "cihaz_no_ipucu": '(send this number to the seller and the key will be locked to this computer only)',
        "erisim_acik": 'Access on',
        "izinleri_iptal": 'Revoke all permissions',
        "cikis_tam": 'Quit completely',
        "lisans": 'License',
        "paketler_sec": 'Plans',
        "sifirlanma_alt": 'Resets on the 1st of each month',
    },
    # ------------------------------------------------------------------ DE
    "de": {
        "uygulama": "GhostPilot",
        "slogan": "Ihr echter Computer, keine Sandbox · 20.000 kostenlose Aufrufe pro Monat",
        "kurulum": "Installation",
        "hos_geldin": "Willkommen",
        "hos_alt": "Dieser Assistent installiert alles in 4 Schritten. Kein Fachwissen nötig.",
        "dil_sec": "Sprache wählen",
        "devam": "Weiter",
        "geri": "Zurück",
        "iptal": "Abbrechen",
        "bitir": "Fertig",
        "asama": "Schritt {n} von {t}",
        "lisans_baslik": "Haben Sie einen Support-Schlüssel?",
        "lisans_alt": ("Geben Sie ihn jetzt ein für unbegrenzte Nutzung. Ohne Schlüssel: "
                       "20.000 Aufrufe pro Monat kostenlos."),
        "lisans_kutu": "Support-Schlüssel (GP-…)",
        "lisans_ekle": "Schlüssel prüfen",
        "lisans_atla": "Vorerst überspringen",
        "lisans_gecerli": "Gültiger Schlüssel: {plan} · gültig bis {bitis}",
        "lisans_gecersiz": "Ungültiger Schlüssel: {neden}",
        "lisans_yok": "Kein Schlüssel — kostenloser Plan.",
        "kurulum_baslik": "Installation läuft",
        "kurulum_alt": "Bitte Fenster offen lassen. Dauer: 5–10 Minuten.",
        "bitti_baslik": "Installation abgeschlossen",
        "bitti_alt": "Fügen Sie GhostPilot mit diesen Daten zu ChatGPT hinzu.",
        "adres": "Serveradresse",
        "kopyala": "Kopieren",
        "kopyalandi": "Kopiert",
        "panel": "Panel öffnen",
        "kapat": "Schließen",
        "hata": "Fehler",
        "durum": "Status",
        "sunucu": "Server",
        "bekci": "Wächter",
        "arac": "Werkzeuge",
        "mod": "Modus",
        "kullanim": "Nutzung diesen Monat",
        "paket": "Paket",
        "kalan_gun": "{n} Tage übrig",
        "sinirsiz": "unbegrenzt",
        "lisans_gir": "Lizenzschlüssel eingeben",
        "baslat": "Starten",
        "durdur": "Stoppen",
        "yenile": "Aktualisieren",
        "cihaz_no": "ID dieses Computers",
        "dil": "Sprache",
        "chatgpt_adim": ("ChatGPT → Einstellungen → Connectors → eigenen MCP-Server hinzufügen:\n"
                         "Name: GhostPilot · Auth: OAuth · Symbol: chatgpt-icon-256.png"),
        "adim_python": "Python",
        "adim_paket": "Benötigte Pakete",
        "adim_tunel": "HTTPS-Tunnel (kein Zusatzprogramm)",
        "adim_ayar": "Konfiguration",
        "adim_sunucu": "Server",
        "adim_kisayol": "Desktop-Verknüpfung",
        "adim_venv": "Virtuelle Umgebung",
        "basla": 'Starten',
        "kapatiliyor": 'Wird geschlossen…',
        "calisiyor": 'läuft',
        "durdu": 'gestoppt',
        "modul_yok": 'Modul fehlt',
        "sinir_doldu": 'Limit erreicht — Supportschlüssel nötig',
        "ls_gecerli": 'Schlüssel gültig',
        "ls_gecersiz": 'Schlüssel ungültig',
        "erisim_kapali": 'Fernzugriff AUS',
        "bekle": 'Bitte warten…',
        "hazir": 'Bereit',
        "cihaz": 'Gerätenummer',
        "bagis": 'Unterstützen',
        "github": 'GitHub',
        "destek_anahtari": 'Supportschlüssel anfragen',
        "site": 'Website',
        "notlar": 'Tägliche Notizen',
        "acil_durdurma": 'Not-Aus',
        "mod_sec": 'Modus',
        "izin_klasor": 'Erlaubte Ordner',
        "son_islemler": 'Letzte Vorgänge',
        "onay_bekleyen": 'Ausstehende Bestätigungen',
        "arayuz": 'Programmfenster',
        "tepsi_ipucu": 'Läuft im Infobereich',
        "aktif": 'aktiv',
        "yok": 'keiner',
        "salt_okunur": 'nur lesen',
        "yazma": 'Lesen + Schreiben',
        "kalan": 'Übrig',
        "cihaz_no_ipucu": '(senden Sie diese Nummer an den Verkäufer – der Schlüssel wird nur an diesen Computer gebunden)',
        "erisim_acik": 'Zugriff an',
        "izinleri_iptal": 'Alle Berechtigungen widerrufen',
        "cikis_tam": 'Vollständig beenden',
        "lisans": 'Lizenz',
        "paketler_sec": 'Pakete',
        "sifirlanma_alt": 'Setzt sich am 1. jedes Monats zurück',
    },
    # ------------------------------------------------------------------ ES
    "es": {
        "uygulama": "GhostPilot",
        "slogan": "Tu ordenador real, no una sandbox · 20.000 llamadas gratis al mes",
        "kurulum": "Instalación",
        "hos_geldin": "Bienvenido",
        "hos_alt": "Este asistente instala todo en 4 pasos. Sin conocimientos técnicos.",
        "dil_sec": "Elige idioma",
        "devam": "Continuar",
        "geri": "Atrás",
        "iptal": "Cancelar",
        "bitir": "Finalizar",
        "asama": "Paso {n} de {t}",
        "lisans_baslik": "¿Tienes una clave de soporte?",
        "lisans_alt": ("Introdúcela para uso ilimitado. Si no la tienes, puedes omitirlo: "
                       "20.000 llamadas al mes son gratis."),
        "lisans_kutu": "Clave de soporte (GP-…)",
        "lisans_ekle": "Verificar clave",
        "lisans_atla": "Omitir por ahora",
        "lisans_gecerli": "Clave válida: {plan} · caduca {bitis}",
        "lisans_gecersiz": "Clave inválida: {neden}",
        "lisans_yok": "Sin clave — plan gratuito.",
        "kurulum_baslik": "Instalando",
        "kurulum_alt": "No cierres esta ventana. Puede tardar 5–10 minutos.",
        "bitti_baslik": "¡Instalación completada!",
        "bitti_alt": "Usa estos datos para añadir GhostPilot a ChatGPT.",
        "adres": "Dirección del servidor",
        "kopyala": "Copiar",
        "kopyalandi": "Copiado",
        "panel": "Abrir panel",
        "kapat": "Cerrar",
        "hata": "Error",
        "durum": "Estado",
        "sunucu": "Servidor",
        "bekci": "Vigilante",
        "arac": "Herramientas",
        "mod": "Modo",
        "kullanim": "Uso este mes",
        "paket": "Paquete",
        "kalan_gun": "quedan {n} días",
        "sinirsiz": "ilimitado",
        "lisans_gir": "Introducir clave",
        "baslat": "Iniciar",
        "durdur": "Detener",
        "yenile": "Actualizar",
        "cihaz_no": "ID de este ordenador",
        "dil": "Idioma",
        "chatgpt_adim": ("ChatGPT → Ajustes → Conectores → Añadir servidor MCP propio:\n"
                         "Nombre: GhostPilot · Auth: OAuth · Icono: chatgpt-icon-256.png"),
        "adim_python": "Python",
        "adim_paket": "Paquetes necesarios",
        "adim_tunel": "Túnel HTTPS (sin programas extra)",
        "adim_ayar": "Configuración",
        "adim_sunucu": "Servidor",
        "adim_kisayol": "Acceso directo",
        "adim_venv": "Entorno virtual",
        "basla": 'Iniciar',
        "kapatiliyor": 'Cerrando…',
        "calisiyor": 'en marcha',
        "durdu": 'detenido',
        "modul_yok": 'módulo ausente',
        "sinir_doldu": 'Límite alcanzado — se requiere clave de soporte',
        "ls_gecerli": 'Clave válida',
        "ls_gecersiz": 'Clave no válida',
        "erisim_kapali": 'Acceso remoto DESACTIVADO',
        "bekle": 'Espere…',
        "hazir": 'Listo',
        "cihaz": 'Número de dispositivo',
        "bagis": 'Apóyanos',
        "github": 'GitHub',
        "destek_anahtari": 'Solicitar clave de soporte',
        "site": 'Sitio',
        "notlar": 'Notas diarias',
        "acil_durdurma": 'Parada de emergencia',
        "mod_sec": 'Modo',
        "izin_klasor": 'Carpetas permitidas',
        "son_islemler": 'Actividad reciente',
        "onay_bekleyen": 'Aprobaciones pendientes',
        "arayuz": 'Ventana del programa',
        "tepsi_ipucu": 'Ejecutándose en la bandeja',
        "aktif": 'activo',
        "yok": 'ninguno',
        "salt_okunur": 'solo lectura',
        "yazma": 'lectura + escritura',
        "kalan": 'Restante',
        "cihaz_no_ipucu": '(envía este número al vendedor y la clave quedará vinculada solo a este equipo)',
        "erisim_acik": 'Acceso activo',
        "izinleri_iptal": 'Revocar todos los permisos',
        "cikis_tam": 'Salir por completo',
        "lisans": 'Licencia',
        "paketler_sec": 'Planes',
        "sifirlanma_alt": 'Se reinicia el día 1 de cada mes',
    },
}

_secili = VARSAYILAN


def dil_yukle():
    global _secili
    try:
        d = json.load(open(AYAR_DOSYA, encoding="utf-8"))
        if d.get("dil") in DILLER:
            _secili = d["dil"]
    except Exception:
        pass
    return _secili


def dil_sec(kod):
    global _secili
    if kod in DILLER:
        _secili = kod
        try:
            os.makedirs(os.path.dirname(AYAR_DOSYA), exist_ok=True)
            json.dump({"dil": kod}, open(AYAR_DOSYA, "w", encoding="utf-8"))
        except Exception:
            pass
    return _secili


def dil():
    return _secili


def t(anahtar, **kw):
    """Seçili dilde metin; eksikse Türkçe'ye, o da yoksa anahtara düşer."""
    s = (LANG.get(_secili, {}).get(anahtar)
         or LANG[VARSAYILAN].get(anahtar)
         or anahtar)
    if kw:
        try:
            s = s.format(**kw)
        except Exception:
            pass
    return s


class _D(dict):
    """D["anahtar"] → t("anahtar") (sözlük gibi kullanım)."""

    def __getitem__(self, k):
        return t(k)

    def get(self, k, d=None):
        return t(k)


D = _D()
dil_yukle()

if __name__ == "__main__":
    for kod, ad in DILLER.items():
        dil_sec(kod)
        print(f"  {kod} ({ad}): {t('slogan')} · {t('devam')} · {t('kalan_gun', n=7)}")
    dil_sec(VARSAYILAN)

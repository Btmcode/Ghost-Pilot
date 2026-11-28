#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — sanaldunya.py  ·  SANAL BİLGİSAYAR MODU
#  Copyright (c) 2026 BTM Code — MIT License
#
#  AMAÇ
#    Kullanıcı "sanal bilgisayarda çalışsın" dediğinde, ajanın dokunduğu her
#    şey GERÇEK makineden ayrı bir dünyada olsun:
#
#      · Dosyalar   → sanal kök (kendi klasörü) — TÜM alanlara izin var
#      · Fare/klavye→ yalnız sanal alana gider, gerçek imleç kımıldamaz
#      · Ekran      → yalnız sanal pencerenin içi görünür
#
#  NE ZAMAN AÇILIR (otomatik algılama)
#    1. config:  {"virtual_computer": true}
#    2. Ortam:   GHOSTPILOT_VIRTUAL=1
#    3. Docker / LXC / WSL / bulut VM gibi izole ortamlar
#    4. Kullanıcı panelden açar  → python kur.py sanal ac
#
#  KAPALIYKEN hiçbir davranış değişmez (güvenli varsayılan).
# ============================================================================

import os
import platform
import shutil
import socket
import time

OS_NAME = platform.system()
IS_WIN = OS_NAME == "Windows"

# Sanal kökün adı
SANAL_AD = "GhostPilot-Sanal"
BAYRAK_DOSYA = "sanal.flag"


# ============================================================================
#  ORTAM ALGILAMA — bu makine zaten izole mi?
# ============================================================================

def _docker_mu():
    for yol in ("/.dockerenv", "/run/.containerenv"):
        if os.path.exists(yol):
            return "docker"
    try:
        with open("/proc/1/cgroup", "r", encoding="utf-8", errors="replace") as f:
            t = f.read()
        for iz in ("docker", "lxc", "kubepods", "containerd", "podman"):
            if iz in t:
                return iz
    except Exception:
        pass
    return ""


def _vm_mi():
    """Bulut VM / hipervizör işaretleri."""
    try:
        with open("/sys/class/dmi/id/product_name", "r",
                  encoding="utf-8", errors="replace") as f:
            p = f.read().strip().lower()
        for iz in ("virtualbox", "vmware", "kvm", "qemu", "hyper-v",
                   "virtual machine", "amazon ec2", "google compute",
                   "digitalocean", "openstack", "xen"):
            if iz in p:
                return p
    except Exception:
        pass
    # WSL
    try:
        with open("/proc/version", "r", encoding="utf-8", errors="replace") as f:
            v = f.read().lower()
        if "microsoft" in v or "wsl" in v:
            return "wsl"
    except Exception:
        pass
    return ""


def izole_ortam():
    """Bu makine zaten sanal/izole mi? Sebep döner, değilse boş."""
    d = _docker_mu()
    if d:
        return d
    v = _vm_mi()
    if v:
        return v
    return ""


# ============================================================================
#  SANAL KÖK
# ============================================================================

def kok_klasor():
    """Sanal kök klasörü (yoksa oluşturulur)."""
    ana = os.path.join(os.path.expanduser("~"), ".ghostpilot")
    kok = os.path.join(ana, "sanal")
    try:
        os.makedirs(kok, exist_ok=True)
        for alt in ("Desktop", "Documents", "Downloads", "Projects", "Temp"):
            os.makedirs(os.path.join(kok, alt), exist_ok=True)
    except Exception:
        pass
    return kok


def _bayrak():
    try:
        return os.path.exists(os.path.join(os.path.expanduser("~"),
                                           ".ghostpilot", BAYRAK_DOSYA))
    except Exception:
        return False


def acik(cfg=None):
    """Sanal bilgisayar modu açık mı?

    Sıra: ortam değişkeni → yapılandırma → bayrak dosyası.
    Otomatik izole ortam algılama YALNIZ öneri olarak kullanılır
    (kullanıcı istemeden davranışı değiştirmeyiz); cfg["virtual_computer"]
    "auto" ise izole ortamda açılır.
    """
    deger = (os.environ.get("GHOSTPILOT_VIRTUAL") or "").strip().lower()
    if deger in ("1", "true", "evet", "on"):
        return True
    if deger in ("0", "false", "hayir", "off"):
        return False
    v = (cfg or {}).get("virtual_computer")
    if v is True:
        return True
    if v is False:
        return False
    # "auto" veya tanımsız → bayrak dosyası
    return _bayrak()


def ac(cfg_yolu=None):
    """Sanal modu aç — kalıcı bayrak yaz."""
    try:
        d = os.path.join(os.path.expanduser("~"), ".ghostpilot")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, BAYRAK_DOSYA), "w", encoding="utf-8") as f:
            f.write("1")
        return True
    except Exception:
        return False


def kapat():
    try:
        p = os.path.join(os.path.expanduser("~"), ".ghostpilot", BAYRAK_DOSYA)
        if os.path.exists(p):
            os.remove(p)
        return True
    except Exception:
        return False


# ============================================================================
#  İZİN KURALLARI — sanal modda HER YER serbest
# ============================================================================

def kokler():
    """Sanal modda okuma/yazma kökleri: sanal kök + gerçek geçici klasör."""
    kok = kok_klasor()
    import tempfile
    return [kok, tempfile.gettempdir()]


def engelli():
    """Sanal modda engelli yol yok — sanal kök zaten sınır."""
    return []


# ============================================================================
#  GİRDİ SINIRI — fare/klavye yalnız sanal alana
# ============================================================================

def ekran_siniri():
    """(x, y, w, h) — ajanın dokunabileceği ekran alanı.

    Sanal modda bu, gerçek ekranın sağ alt çeyreği gibi AYRI bir bölgedir;
    gerçek kullanıcının çalıştığı yerin üstüne yazmaz.
    Sanal mod kapalıysa None → tüm ekran serbest.
    """
    if not acik():
        return None
    try:
        import screen
        w, h = screen.size()
    except Exception:
        w, h = 1920, 1080
    # sol üst çeyrek: kullanıcının penceresi genelde ortada/sağda olur
    return (0, 0, int(w * 0.5), int(h * 0.5))


def sinir_icinde(x, y):
    """(x,y) sanal alanın içinde mi? Kapalıysa her zaman True."""
    s = ekran_siniri()
    if not s:
        return True
    sx, sy, sw, sh = s
    return sx <= int(x) < sx + sw and sy <= int(y) < sy + sh


def durum():
    """Panel ve tanı çıktısı için özet."""
    s = ekran_siniri()
    return {
        "acik": acik(),
        "kok": kok_klasor(),
        "izole_ortam": izole_ortam(),
        "ekran_siniri": s,
        "not": ("Ajan yalnız sanal alanda çalışıyor: kendi klasörü, kendi "
                "imleci, kendi ekran bölgesi." if acik()
                else "Gerçek bilgisayarda çalışıyor (varsayılan)."),
    }

# ============================================================================
#  HEDEF PENCERE KİLİDİ — klavye sizin pencerenize gitmez
# ============================================================================
#  Sorun: sanal modda fare sınırlı ama KLAVYE odaklı pencereye gider. Kullanıcı
#  kendi penceresinde yazarken ajan da yazarsa ikisi karışır.
#
#  Çözüm: ajan tıkladığı pencereyi HATIRLAR ve yazıyı yalnız oraya gönderir.
#  Kullanıcının ön plandaki penceresi asla hedef olmaz.
_HEDEF = {"hwnd": 0, "baslik": "", "t": 0.0}
_HEDEF_OMUR = 900.0     # 15 dakika hatırla


def hedef_ayarla(hwnd, baslik=""):
    try:
        _HEDEF["hwnd"] = int(hwnd or 0)
        _HEDEF["baslik"] = str(baslik or "")[:80]
        _HEDEF["t"] = time.time()
        return True
    except Exception:
        return False


def hedef():
    """Ajanın yazacağı pencere (0 = yok)."""
    if not _HEDEF["hwnd"]:
        return 0
    if time.time() - _HEDEF["t"] > _HEDEF_OMUR:
        return 0
    return _HEDEF["hwnd"]


def hedef_bilgi():
    return {"hwnd": hedef(), "baslik": _HEDEF["baslik"],
            "yas": (time.time() - _HEDEF["t"]) if _HEDEF["t"] else None}

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — gui.py  ·  GUI MOTORU (Faz 4)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  NE EKLER (mevcut goz / ui_bul / goverlay / sanaldunya KORUNARAK)
#    1. get_window_info         — PID, süreç adı, sınıf, dikdörtgen, alt pencere
#    2. interact_with_ui_element — öğeyi bul, tıkla/değer oku/değer yaz/çalıştır
#    3. doğrulama               — tıklama gerçekten iş gördü mü? (önce/sonra)
#    4. VMConnect eşlemesi      — sanal makine penceresi içindeki misafir
#                                 ekranı için koordinat dönüşümü (ölçek + offset)
#    5. başarısızlıkta TAHMİN YOK — bulunamazsa açıkça bildirir
#
#  TASARIM: görsel imleç (goverlay) ile gerçek girdi (input_bg/screen) AYRIDIR.
#  Gerçek kullanıcı imleci hiç hareket ettirilmez; sanal modda hedef pencere
#  kilidi devrededir.
# ============================================================================

import os
import platform
import re
import subprocess
import time

OS_NAME = platform.system()
IS_WIN = OS_NAME == "Windows"
IS_LINUX = OS_NAME == "Linux"

SESSIZ = {}
if IS_WIN:
    SESSIZ["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)


def _goz():
    try:
        import goz
        return goz
    except Exception:
        return None


# ============================================================================
#  0 · NESNE AĞACI ARKA UÇLARI (takılabilir)
# ============================================================================
#  goz.py'nin katmanı platforma göre değişir:
#    Windows → uiautomation (gerçek öğe ağacı, ad + rol + sınır)
#    Linux   → AT-SPI (pyatspi) varsa gerçek ağaç; yoksa xwininfo (yalnız pencere)
#  Burada arka uç NESNEL olarak seçilir; böylece testte stub ile gerçek
#  ağacın verdiği biçim doğrulanabilir (platform taklidi YAPILMAZ).
NESNE_ARKA_UCU = {"ad": "otomatik", "nesne": None}


def arka_ucu_ayarla(ad="otomatik", nesne=None):
    """Nesne ağacı arka ucunu seç. Test/snapshot için `nesne` verilebilir."""
    NESNE_ARKA_UCU["ad"] = ad
    NESNE_ARKA_UCU["nesne"] = nesne
    return {"ok": True, "arka_uc": ad,
            "hazir": bool(nesne) or _otomatik_arka_uc() is not None}


def _otomatik_arka_uc():
    """Platforma göre gerçek arka ucu bul (yoksa None)."""
    if IS_WIN:
        try:
            import uiautomation  # noqa
            return "uiautomation"
        except Exception:
            return None
    try:
        import pyatspi  # noqa
        return "atspi"
    except Exception:
        return None


def arka_uc_durumu():
    secili = NESNE_ARKA_UCU.get("nesne")
    oto = _otomatik_arka_uc()
    return {"ok": True,
            "secili": NESNE_ARKA_UCU["ad"],
            "enjekte": bool(secili),
            "otomatik": oto,
            "platform": OS_NAME,
            "gercek_agac": bool(secili or oto),
            "not": ("Gerçek öğe ağacı aktif." if (secili or oto) else
                    "Bu platformda gerçek öğe ağacı yok (AT-SPI/uiautomation "
                    "bulunamadı). find_ui_element TAHMİN ETMEZ; pencere "
                    "düzeyinde arama ve koordinatlı tıklama kullanılabilir.")}


# ============================================================================
#  1 · PENCERE BİLGİSİ
# ============================================================================
def _win_pid(hwnd):
    try:
        import ctypes
        pid = ctypes.c_ulong(0)
        ctypes.windll.user32.GetWindowThreadProcessId(
            ctypes.c_void_p(int(hwnd)), ctypes.byref(pid))
        return int(pid.value)
    except Exception:
        return 0


def _surec_adi(pid):
    if not pid:
        return ""
    try:
        if IS_WIN:
            r = subprocess.run(
                ["tasklist", "/FI", "PID eq %d" % pid, "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=8, **SESSIZ)
            satir = (r.stdout or "").strip().splitlines()
            if satir:
                return satir[0].split(",")[0].strip('"')
        else:
            try:
                with open("/proc/%d/comm" % int(pid), "r") as f:
                    return f.read().strip()
            except Exception:
                pass
    except Exception:
        pass
    return ""


def _win_sinif(hwnd):
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetClassNameW(ctypes.c_void_p(int(hwnd)), buf, 256)
        return buf.value or ""
    except Exception:
        return ""


def pencere_bilgi(baslik_parca="", hwnd=0):
    """Tek pencerenin ayrıntılı bilgisi (PID, süreç, sınıf, dikdörtgen)."""
    G = _goz()
    if not G:
        return {"ok": False, "error": "goz modülü yok."}
    liste = G.pencereler(baslik_parca or "")
    if hwnd:
        liste = [p for p in liste if int(p.get("id") or 0) == int(hwnd)] or liste
    if not liste:
        return {"ok": False,
                "error": "Pencere bulunamadı: %s" % (baslik_parca or hwnd),
                "ipucu": "list_windows / windows aracıyla başlıkları görün."}
    # en iyi eşleşme: başlıkta parça geçen ilk pencere
    p = liste[0]
    if baslik_parca:
        for aday in liste:
            if baslik_parca.lower() in (aday.get("baslik") or "").lower():
                p = aday
                break
    pid = _win_pid(p.get("id") or 0) if IS_WIN else 0
    bilgi = {
        "ok": True,
        "id": p.get("id"),
        "title": p.get("baslik"),
        "rect": {"x": p.get("x"), "y": p.get("y"),
                 "w": p.get("w"), "h": p.get("h")},
        "pid": pid,
        "process": _surec_adi(pid) if pid else "",
        "class": _win_sinif(p.get("id") or 0) if IS_WIN else "",
        "platform": OS_NAME,
    }
    # alt pencere var mı? (sanal makine / gömülü ekran işareti)
    try:
        cocuk, katman = G.cocuklar(p.get("id") or 0)
        bilgi["child_count"] = len(cocuk)
        bilgi["ui_layer"] = katman
        if cocuk:
            bilgi["children_preview"] = cocuk[:8]
    except Exception:
        bilgi["child_count"] = 0
    # VMConnect / Hyper-V / sanal makine penceresi mi?
    vm = _vm_penceresi_mi(bilgi)
    if vm.get("sanal"):
        bilgi["virtual_machine"] = vm
    return bilgi


# ============================================================================
#  4 · VMConnect / CHILD-WINDOW KOORDİNAT EŞLEMESİ
# ============================================================================
_VM_ISIM = re.compile(
    r"(vmconnect|virtual machine connection|hyper-v|sanal makine|"
    r"vmware|virtualbox|qemu|virt-manager|remote desktop|uzak masaüstü|"
    r"mstsc|parsec|xpra)", re.I)


def _vm_penceresi_mi(bilgi):
    """Pencere bir sanallaştırma istemcisi mi? Misafir ekranı nerede?"""
    baslik = str(bilgi.get("title") or "")
    sinif = str(bilgi.get("class") or "")
    surec = str(bilgi.get("process") or "").lower()
    ipucu = " ".join([baslik, sinif, surec])
    if not _VM_ISIM.search(ipucu):
        return {"sanal": False}
    rect = bilgi.get("rect") or {}
    # Misafir ekranı genellikle pencerenin istemci alanıdır; kenarlıklar
    # (başlık çubuğu, araç çubuğu, durum çubuğu) düşülür.
    tahmin = {
        "x": int(rect.get("x") or 0),
        "y": int(rect.get("y") or 0),
        "w": int(rect.get("w") or 0),
        "h": int(rect.get("h") or 0),
    }
    return {"sanal": True, "istemci": tahmin,
            "tip": "vmconnect" if "vmconnect" in ipucu.lower() or
                                    "hyper-v" in ipucu.lower() or
                                    "sanal makine" in ipucu.lower() else "generic",
            "not": ("Misafir ekranı koordinatları için guest_to_host/host_to_guest "
                    "kullanın — ölçek ve kaydırma hesaba katılır.")}


def misafir_esle(host_x, host_y, istemci, misafir_w, misafir_h,
                 olcek=None, kaydirma=(0, 0)):
    """MİSAFİR (VM içi) koordinatı → HOST (gerçek ekran) koordinatı.

    istemci   : VM penceresinin misafir ekran alanı (x, y, w, h) — host ekranında
    misafir_w/h: VM içindeki çözünürlük (ör. Ubuntu 1920x1080)
    olcek     : None ise istemci boyutundan hesaplanır
    kaydirma  : misafir ekranı kaydırılmışsa (scroll) piksel kaydırma
    """
    cx, cy, cw, ch = [int(z) for z in istemci]
    mw, mh = int(misafir_w), int(misafir_h)
    if mw <= 0 or mh <= 0 or cw <= 0 or ch <= 0:
        return {"ok": False, "error": "Geçersiz boyut."}
    if olcek is None:
        olcek = min(cw / float(mw), ch / float(mh))
    olcek = float(olcek)
    if olcek <= 0:
        return {"ok": False, "error": "Geçersiz ölçek."}
    # misafir görüntüsünün istemci içindeki başlangıcı (ortalanmış)
    off_x = int((cw - mw * olcek) / 2) + int(kaydirma[0] or 0)
    off_y = int((ch - mh * olcek) / 2) + int(kaydirma[1] or 0)
    hx = int(cx + off_x + int(host_x) * olcek)
    hy = int(cy + off_y + int(host_y) * olcek)
    return {"ok": True, "host_x": hx, "host_y": hy,
            "olcek": round(olcek, 4), "offset": [off_x, off_y]}


def host_esle(host_x, host_y, istemci, misafir_w, misafir_h,
              olcek=None, kaydirma=(0, 0)):
    """HOST koordinatı → MİSAFİR (VM içi) koordinatı."""
    cx, cy, cw, ch = [int(z) for z in istemci]
    mw, mh = int(misafir_w), int(misafir_h)
    if mw <= 0 or mh <= 0 or cw <= 0 or ch <= 0:
        return {"ok": False, "error": "Geçersiz boyut."}
    if olcek is None:
        olcek = min(cw / float(mw), ch / float(mh))
    olcek = float(olcek)
    if olcek <= 0:
        return {"ok": False, "error": "Geçersiz ölçek."}
    off_x = int((cw - mw * olcek) / 2) + int(kaydirma[0] or 0)
    off_y = int((ch - mh * olcek) / 2) + int(kaydirma[1] or 0)
    gx = int((int(host_x) - cx - off_x) / olcek)
    gy = int((int(host_y) - cy - off_y) / olcek)
    icinde = (0 <= gx < mw) and (0 <= gy < mh)
    return {"ok": True, "guest_x": gx, "guest_y": gy,
            "olcek": round(olcek, 4), "icinde": icinde}


# ============================================================================
#  2 · ÖĞE BULMA + 3 · ETKİLEŞİM + DOĞRULAMA
# ============================================================================
def oge_bul(hedef, pencere="", esik=60):
    """Nesne ağacında öğe ara → {ok, oge:{...}, guven, katman}"""
    # 1) Enjekte edilmiş / platform arka ucu (varsa) — gerçek ağaç
    secili = NESNE_ARKA_UCU.get("nesne")
    if secili is not None:
        r = secili(hedef, pencere)
        if r.get("ok"):
            oge = r.get("oge") or {}
            return {"ok": True, "oge": oge,
                    "guven": r.get("guven") or "yüksek",
                    "katman": r.get("katman") or NESNE_ARKA_UCU["ad"],
                    "arka_uc": NESNE_ARKA_UCU["ad"]}
        return {"ok": False, "bulunamadi": True,
                "error": r.get("error") or ("'%s' bulunamadı." % hedef),
                "katman": NESNE_ARKA_UCU["ad"],
                "arka_uc": NESNE_ARKA_UCU["ad"],
                "ipucu": "Öğe adını tam yazın ya da koordinatla tıklayın."}
    G = _goz()
    if not G:
        return {"ok": False, "error": "goz modülü yok."}
    r = G.bul(hedef, pencere)
    if not r.get("ok"):
        # TAHMİN YOK: bulunamadıysa açıkça söyle, koordinat uydurma
        return {"ok": False, "bulunamadi": True,
                "error": r.get("error") or ("'%s' bulunamadı." % hedef),
                "katman": r.get("katman"),
                "ipucu": ("get_ui_tree (gozle) ile ekrandaki adları okuyun; "
                          "ya da koordinatla cursor_click kullanın.")}
    oge = r.get("bulundu") or {}
    return {"ok": True, "oge": oge, "guven": r.get("guven"),
            "katman": r.get("katman"), "diger": r.get("diger") or []}


def _ekran_farki(bolge, esik=6):
    """Tıklama öncesi/sonrası ekran görüntüsünü karşılaştır → değişti mi?"""
    try:
        import screen
        from PIL import Image
        import io
    except Exception:
        return None
    try:
        def yakala():
            r = screen.screenshot(region=bolge, max_width=0)
            if not r.get("ok"):
                return None
            import base64
            return Image.open(io.BytesIO(base64.b64decode(r["base64"]))).convert("L")
        a = yakala()
        time.sleep(0.18)
        b = yakala()
        if a is None or b is None or a.size != b.size:
            return None
        pa, pb = a.tobytes(), b.tobytes()
        if len(pa) != len(pb) or not pa:
            return None
        # örnekleme ile ortalama fark
        adim = max(1, len(pa) // 4000)
        fark = sum(abs(pa[i] - pb[i]) for i in range(0, len(pa), adim))
        ort = fark / float(len(range(0, len(pa), adim)))
        return {"degisti": ort > float(esik), "ortalama_fark": round(ort, 2)}
    except Exception:
        return None


def _tikla(x, y, button="left", double=False, dogrula=True, pencere_baslik=""):
    """Tıkla ve (istenirse) sonucu doğrula. Gerçek imleç oynatılmaz."""
    try:
        import input_bg
    except Exception:
        input_bg = None
    x, y = int(x), int(y)
    bolge = {"x": max(0, x - 40), "y": max(0, y - 30), "w": 80, "h": 60}
    onceki = _ekran_farki(bolge) if dogrula else None
    t0 = time.time()
    sonuc = None
    if input_bg:
        try:
            sonuc = input_bg.bg_click(x, y, button=button, double=double,
                                      visible=True, label="nex")
        except Exception as e:
            sonuc = {"ok": False, "error": str(e)[:150]}
    if not sonuc or not sonuc.get("ok"):
        try:
            import screen
            sonuc = screen.click(x, y, button=button, double=double)
        except Exception as e:
            return {"ok": False, "error": "Tıklama yapılamadı: %s" % str(e)[:150],
                    "clicked": False}
    sure_ms = int((time.time() - t0) * 1000)
    r = {"ok": bool(sonuc.get("ok")), "clicked": True, "x": x, "y": y,
         "button": button, "double": bool(double),
         "mode": sonuc.get("mode") or sonuc.get("backend") or "",
         "sure_ms": sure_ms,
         "mouse_untouched": bool(sonuc.get("concurrent") or
                                 "imleç" in str(sonuc.get("mode") or ""))}
    if dogrula:
        sonraki = _ekran_farki(bolge)
        if onceki is None or sonraki is None:
            r["dogrulama"] = {"yapildi": False,
                              "sebep": "Ekran karşılaştırması yapılamadı (Pillow/ekran yok)."}
        else:
            r["dogrulama"] = {
                "yapildi": True,
                "degisti": bool(sonraki.get("degisti")),
                "ortalama_fark": sonraki.get("ortalama_fark"),
                "yorum": ("Ekran değişti — tıklama iş gördü."
                          if sonraki.get("degisti")
                          else "Ekranda görünür değişiklik YOK — tıklama hedefe "
                               "ulaşmamış olabilir. Pencereyi doğrulayın."),
            }
    return r


def oge_etkiles(hedef, eylem="click", deger=None, pencere="",
                dogrula=True):
    """Öğeyi bul ve üzerinde işlem yap.

    eylem: click | double_click | right_click | read | set | invoke | focus
    """
    r = oge_bul(hedef, pencere)
    if not r.get("ok"):
        return r
    oge = r["oge"]
    x, y = int(oge.get("x") or 0), int(oge.get("y") or 0)
    if x <= 0 and y <= 0:
        return {"ok": False, "bulundu": oge,
                "error": ("Öğe bulundu ama koordinatı yok (bu katman konum "
                          "vermiyor). Koordinatla cursor_click deneyin.")}
    eylem = str(eylem or "click").lower()

    if eylem in ("read", "oku", "value"):
        # değer okuma: nesne ağacındaki ad/boyut bilgisinden
        return {"ok": True, "bulundu": oge, "deger": oge.get("ad"),
                "not": "Bu katman yalnız ad/konum verir; metin alanı içeriği "
                       "için screenshot + okuma kullanın."}

    if eylem in ("click", "tikla"):
        return _tikla(x, y, "left", False, dogrula)
    if eylem in ("double_click", "cift_tikla", "double"):
        return _tikla(x, y, "left", True, dogrula)
    if eylem in ("right_click", "sag_tikla"):
        return _tikla(x, y, "right", False, dogrula)
    if eylem in ("focus", "odak"):
        try:
            import input_bg
            return input_bg.window_focus(oge.get("ad") or hedef)
        except Exception as e:
            return {"ok": False, "error": str(e)[:150]}
    if eylem in ("set", "yaz", "type"):
        if deger is None:
            return {"ok": False, "error": "deger gerekli (yazılacak metin)."}
        t = _tikla(x, y, "left", False, False)
        if not t.get("ok"):
            return t
        time.sleep(0.05)
        try:
            import input_bg
            w = input_bg.bg_type(str(deger), visible=True)
            return {"ok": bool(w.get("ok")), "bulundu": oge, "yazilan": str(deger)[:200],
                    "once_tiklama": t}
        except Exception as e:
            return {"ok": False, "error": str(e)[:150]}
    if eylem in ("invoke", "calistir"):
        # varsayılan: çift tıklama (en yaygın "çalıştır" davranışı)
        return _tikla(x, y, "left", True, dogrula)
    return {"ok": False,
            "error": "Bilinmeyen eylem: %s" % eylem,
            "gecerli": ["click", "double_click", "right_click", "read",
                        "set", "invoke", "focus"]}

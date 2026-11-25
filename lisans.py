#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — lisans.py  ·  LİSANS DOĞRULAMA (yalnız AÇIK anahtar)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  NEDEN GÜVENLİ?
#  Lisanslar **Ed25519** özel anahtarıyla imzalanır. Özel anahtar yalnızca
#  satıcıdadır ve asla dağıtılmaz. Bu dosyada bulunan tek şey **açık**
#  anahtardır; onunla YENİ ANAHTAR ÜRETİLEMEZ — yalnız imza doğrulanabilir.
#
#  → Kodu okuyan biri bu dosyayı görse bile kendi geçerli lisansını üretemez.
#    (Önceki HMAC sürümünde sır kodun içindeydi; o gerçek bir hataydı.)
#
#  Sıfır bağımlılık: saf Python Ed25519 doğrulaması (RFC 8032).
# ============================================================================

import base64
import hashlib
import re

# ---------------------------------------------------------------------------
#  AÇIK ANAHTAR — dağıtılabilir, gizli değil
# ---------------------------------------------------------------------------
ACIK_ANAHTAR_PEM = """-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEANloDSvHW1v/EO+/r563Yt3u0AHaNirvcaZiP30WMZhY=
-----END PUBLIC KEY-----"""

ONEK = "GP-"

# ===========================================================================
#  Ed25519 — RFC 8032 doğrulama (saf Python, ~40 satır)
# ===========================================================================
_P = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493   # grup mertebesi
_D = -121665 * pow(121666, _P - 2, _P) % _P
_I = pow(2, (_P - 1) // 4, _P)


def _xrecover(y):
    xx = (y * y - 1) * pow(_D * y * y + 1, _P - 2, _P)
    x = pow(xx, (_P + 3) // 8, _P)
    if (x * x - xx) % _P != 0:
        x = (x * _I) % _P
    if x % 2 != 0:
        x = _P - x
    return x


_By = 4 * pow(5, _P - 2, _P) % _P
_Bx = _xrecover(_By)
_B = [_Bx % _P, _By % _P, 1, _Bx * _By % _P]


def _topla(P, Q):
    """Twisted Edwards nokta toplama (genişletilmiş koordinatlar)."""
    X1, Y1, Z1, T1 = P
    X2, Y2, Z2, T2 = Q
    A = (Y1 - X1) * (Y2 - X2) % _P
    B = (Y1 + X1) * (Y2 + X2) % _P
    C = T1 * 2 * _D * T2 % _P
    D = Z1 * 2 * Z2 % _P
    E = B - A
    F = D - C
    G = D + C
    H = B + A
    return [E * F % _P, G * H % _P, F * G % _P, E * H % _P]


def _carp(P, e):
    if e == 0:
        return [0, 1, 1, 0]
    Q = _carp(P, e // 2)
    Q = _topla(Q, Q)
    if e & 1:
        Q = _topla(Q, P)
    return Q


def _kodla(P):
    zinv = pow(P[2], _P - 2, _P)
    x = P[0] * zinv % _P
    y = P[1] * zinv % _P
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _nokta_coz(s):
    y = int.from_bytes(s, "little")
    y &= (1 << 255) - 1
    if y >= _P:
        return None
    x = _xrecover(y)
    if (x & 1) != (s[31] >> 7):
        x = _P - x
    return [x, y, 1, x * y % _P]


def _esit(P, Q):
    return ((P[0] * Q[2] - Q[0] * P[2]) % _P == 0 and
            (P[1] * Q[2] - Q[1] * P[2]) % _P == 0)


def _h(m):
    """Ed25519'da hash SHA-512'dir ve L modunda indirgenir (RFC 8032)."""
    return int.from_bytes(hashlib.sha512(m).digest(), "little") % _L


def ed25519_dogrula(acik_anahtar, mesaj, imza):
    """True → imza geçerli."""
    if len(acik_anahtar) != 32 or len(imza) != 64:
        return False
    try:
        A = _nokta_coz(acik_anahtar)
        if A is None:
            return False
        R = _nokta_coz(imza[:32])
        if R is None:
            return False
        S = int.from_bytes(imza[32:], "little")
        if S >= _L:
            return False
        h = _h(imza[:32] + acik_anahtar + mesaj)
        return _esit(_carp(_B, S), _topla(R, _carp(A, h)))
    except Exception:
        return False


def _pem_coz(pem):
    """PEM → 32 baytlık ham açık anahtar."""
    govde = "".join(s for s in pem.strip().splitlines() if not s.startswith("-----"))
    der = base64.b64decode(govde)
    # SubjectPublicKeyInfo: ... BIT STRING (32 bayt)
    return der[-32:]


try:
    _AÇIK = _pem_coz(ACIK_ANAHTAR_PEM)
except Exception:
    _AÇIK = b""


# ===========================================================================
#  MAKİNE KİMLİĞİ — anahtarı tek bilgisayara kilitlemek için
#  Windows: MachineGuid · macOS: IOPlatformUUID · Linux: /etc/machine-id
# ===========================================================================
def _ham_makine():
    import os
    import platform
    import subprocess
    import sys
    ham = ""
    try:
        if os.name == "nt":
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\Microsoft\Cryptography", 0,
                                winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0)) as k:
                ham = str(winreg.QueryValueEx(k, "MachineGuid")[0])
        elif sys.platform == "darwin":
            ham = subprocess.run(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                                 capture_output=True, text=True, timeout=10).stdout
        else:
            for p in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
                if os.path.exists(p):
                    ham = open(p, encoding="utf-8").read().strip()
                    break
    except Exception:
        ham = ""
    if not ham:                       # yedek: kalıcı yerel dosya
        yol = os.path.join(os.path.expanduser("~"), ".ghostpilot", "makine")
        try:
            ham = open(yol, encoding="utf-8").read().strip()
        except Exception:
            ham = ""
        if not ham:
            import secrets
            ham = secrets.token_hex(16)
            try:
                os.makedirs(os.path.dirname(yol), exist_ok=True)
                with open(yol, "w", encoding="utf-8") as f:
                    f.write(ham)
            except Exception:
                pass
    return ham


def makine_kimligi():
    """16 karakterlik kısa makine kimliği (satıcıya bildirilecek numara)."""
    return hashlib.sha256(("GP-MAKINE|" + _ham_makine().strip().lower()).encode()).hexdigest()[:16]


# ===========================================================================
#  PAKET / PLANLAR  —  "ömür boyu sınırsız" YOK, aylık döngü var
#  Süre bitince Pro kendiliğinden KAPANIR (ücretsiz 20.000'e döner).
# ===========================================================================
try:
    import paketler as _PK          # fiyat tek yerden gelir (paketler.py)
except Exception:
    _PK = None

PLANLAR = {
    "DE": {"ad": "Deneme", "gun": 7,
           "fiyat": "0", "aciklama": "7 gün ücretsiz"},
    "AY": {"ad": "PRO", "gun": 30,
           "fiyat": (f"${_PK.AYLIK_FIYAT}" if _PK else "$10"),
           "periyot": ("/ay" if _PK is None else _PK.m("ay")),
           "aciklama": "Sınırsız kullanım"},
    "YI": {"ad": "PRO yıllık", "gun": 365,
           "fiyat": (f"${_PK.YILLIK_FIYAT}" if _PK else "$96"),
           "periyot": ("/yıl" if _PK is None else _PK.m("yil")),
           "aciklama": "2 ay bedava"},
}
PLAN_VARSAYILAN = "AY"
YENILEME_UYARI_GUN = 7          # bu kadar gün kalınca "yenileyin" uyarısı


def plan_adi(kod):
    return (PLANLAR.get((kod or "").upper()) or {}).get("ad", "Genel")


# ===========================================================================
#  ANAHTAR BİÇİMİ
#  v1 (eski):  GP-<gövde12>-<bitiş8>-<imza128>
#  v2 (makine):GP-<gövde12>-<bitiş8>-<makine12>-<imza128>
#  v3 (paket): GP-<plan2>-<gövde12>-<bitiş8>-<makine12>-<imza128>   ← GÜNCEL
#  imza = Ed25519( "GP-<gövde>|<bitiş>" ), ("…|<makine>"), ("GP-<plan>-<gövde>|<bitiş>|<makine>")
#  Eski (genel):  GP-<gövde12>-<bitiş8>-<imza128hex>
#  Yeni (makine): GP-<gövde12>-<bitiş8>-<makine12|000000000000>-<imza128hex>
#  imza Ed25519( "GP-<gövde>|<bitiş>" )  veya  "GP-<gövde>|<bitiş>|<makine>"
#  makine "000000000000" → her bilgisayarda geçerli (genel anahtar)
#  GP-<gövde12>-<bitiş8>-<imza128hex>
#  imza = Ed25519( "GP-<gövde12>|<bitiş8>" )
# ===========================================================================
_BICIM = re.compile(r"^GP-([A-Z0-9]{12})-(\d{8})-([0-9A-Fa-f]{128})$")
# v3: GP-<PLAN2>-<gövde12>-<bitiş8>-<makine12>-<imza128>
_BICIM_P = re.compile(r"^GP-([A-Z]{2})-([A-Z0-9]{12})-(\d{8})-([0-9A-Fa-f]{12})-([0-9A-Fa-f]{128})$")
_BICIM_M = re.compile(r"^GP-([A-Z0-9]{12})-(\d{8})-([0-9A-Fa-f]{12})-(\d*[0-9A-Fa-f]{128}|[0-9A-Fa-f]{128})$")
GENEL_MAKINE = "0" * 12


def _anahtar_coz(k):
    k = (k or "").strip().replace(" ", "")
    m = _BICIM_P.match(k) or _BICIM_P.match(k.upper())
    if m:
        return {"plan": m.group(1), "govde": m.group(2), "bitis": m.group(3),
                "makine": m.group(4).lower(), "imza": m.group(5).lower(),
                "tam": k, "surum": 3}
    m = _BICIM_M.match(k) or _BICIM_M.match(k.upper())
    if m:
        return {"govde": m.group(1), "bitis": m.group(2), "makine": m.group(3).lower(),
                "imza": m.group(4).lower(), "tam": k, "surum": 2}
    m = _BICIM.match(k) or _BICIM.match(k.upper())
    if not m:
        return None
    return {"govde": m.group(1), "bitis": m.group(2), "makine": GENEL_MAKINE,
            "imza": m.group(3).lower(), "tam": k, "surum": 1}


def _imza_mesaji(p):
    if p.get("surum") == 3:
        return (f"{ONEK}{p['plan']}-{p['govde']}|{p['bitis']}|{p['makine']}"
                ).encode("utf-8")
    if p.get("surum") == 2:
        return f"{ONEK}{p['govde']}|{p['bitis']}|{p['makine']}".encode("utf-8")
    return f"{ONEK}{p['govde']}|{p['bitis']}".encode("utf-8")


def dogrula(anahtar, bugun=None, makine=None):
    """(geçerli_mi, neden). makine verilmezse bu bilgisayarınki kullanılır."""
    p = _anahtar_coz(anahtar)
    if not p:
        return False, ("biçim hatalı — beklenen: GP-XXXXXXXXXXXX-YYYYMMDD-<imza>")
    if p["bitis"] != "00000000":
        try:
            import datetime
            bitis = datetime.date(int(p["bitis"][:4]), int(p["bitis"][4:6]),
                                  int(p["bitis"][6:8]))
        except Exception:
            return False, "bitiş tarihi hatalı"
        if (bugun or datetime.date.today()) > bitis:
            return False, f"lisans süresi doldu ({p['bitis']})"
    if not _AÇIK:
        return False, "açık anahtar yüklenemedi"
    if not ed25519_dogrula(_AÇIK, _imza_mesaji(p), bytes.fromhex(p["imza"])):
        return False, "imza geçersiz — bu anahtar BTM Code tarafından verilmemiş"
    # makine bağı: anahtar tek bir bilgisayara kilitlenmişse başkasında çalışmaz
    if p.get("makine") and p["makine"] != GENEL_MAKINE:
        benim = (makine or makine_kimligi()).lower()[:12]
        if p["makine"] != benim:
            return False, ("bu anahtar başka bir bilgisayara kilitlenmiş "
                           f"(anahtar: {p['makine']} · bu bilgisayar: {benim})")
    return True, "geçerli"


def bilgi(anahtar, bugun=None):
    ok, neden = dogrula(anahtar)
    if not ok:
        return {"ok": False, "error": neden}
    p = _anahtar_coz(anahtar)
    bagli = bool(p.get("makine")) and p["makine"] != GENEL_MAKINE
    plan = p.get("plan") or ""
    kalan = None
    if p["bitis"] != "00000000":
        try:
            import datetime
            b = datetime.date(int(p["bitis"][:4]), int(p["bitis"][4:6]), int(p["bitis"][6:8]))
            kalan = (b - (bugun or datetime.date.today())).days
        except Exception:
            kalan = None
    return {"ok": True, "id": p["govde"],
            "plan": plan, "plan_adi": plan_adi(plan) if plan else "Genel (eski)",
            "kalan_gun": kalan,
            "yenile": (kalan is not None and 0 <= kalan <= YENILEME_UYARI_GUN),
            "bitis": "süresiz" if p["bitis"] == "00000000" else p["bitis"],
            "makine": p.get("makine", GENEL_MAKINE),
            "bagli": bagli,
            "bagli_metin": (f"bu bilgisayara kilitli ({p['makine']})" if bagli
                            else "tüm bilgisayarlarda geçerli"),
            "mesaj": neden}


def ozet(anahtar):
    """Kısa, paylaşılabilir özet (kullanıcı satıcıya gönderebilir)."""
    b = bilgi(anahtar)
    if not b.get("ok"):
        return b
    return {"id": b["id"], "bitis": b["bitis"], "makine": b["makine"],
            "bagli": b["bagli"]}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(bilgi(sys.argv[1]))
    else:
        print("Kullanım: python lisans.py GP-XXXXXXXXXXXX-YYYYMMDD-<imza>")
        print("Açık anahtar:", "yüklü" if _AÇIK else "HATALI")

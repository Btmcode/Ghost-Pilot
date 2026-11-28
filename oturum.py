#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — oturum.py  ·  KALICI TERMİNAL OTURUM MOTORU
#  Copyright (c) 2026 BTM Code — MIT License
#
#  NE ÇÖZER
#    Eski hâlde `job_start` bir komutu çalıştırıp SONUCUNU bekliyordu:
#      · stdin yok        → REPL, SSH, onay soran kurulum çalışmıyordu
#      · canlı çıktı yok  → 5 dakikalık derlemede model kör kalıyordu
#      · bellek içi       → sunucu yeniden başlarsa tüm işler kayboluyordu
#
#  BU DOSYA
#    Her süreç bir "oturum"dur ve şu bilgileri taşır:
#      session_id, pid, command, cwd, durum, exit_code,
#      başlangıç/bitiş zamanı, stdout+stderr halkası, satır sayacı
#
#    · stdin GERÇEK: yazılan satır sürece gider (REPL'e `print(2+2)` yazılır)
#    · CANLI çıktı: okuyucu iş parçacıkları satır satır halkaya ekler;
#      model "son 200 satır" veya "50. satırdan sonrası" diyebilir
#    · KALICI: durum her değişimde ~/.ghostpilot/oturumlar/<id>.json yazılır
#      → yeniden başlatmada `kurtar()` ile geri yüklenir (süreç yaşıyorsa
#      çıktı dosyadan okunmaya devam eder)
#    · SÜREÇ AĞACI: kill sırasında çocuklar da ölür (Windows: taskkill /T,
#      POSIX: process group)
#    · DURUM AYRIMI: running / exited / timeout / waiting_input / failed
#
#  BAĞIMLILIK: yalnız standart kütüphane.
# ============================================================================

import json
import os
import platform
import re
import secrets
import shutil
import signal
import subprocess
import sys
import threading
import time

OS_NAME = platform.system()
IS_WIN = OS_NAME == "Windows"

CFG_DIR = os.path.join(os.path.expanduser("~"), ".ghostpilot")
OTURUM_DIR = os.path.join(CFG_DIR, "oturumlar")
LOG_DIR = os.path.join(CFG_DIR, "oturum-log")
YARDIMCI_DIR = os.path.join(CFG_DIR, "oturum-soket")
YARDIMCI_DOSYA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "pty_yardimci.py")
# PTY yardımcısı sayesinde oturumlar sunucudan BAĞIMSIZ yaşar ve yeniden
# başlatmadan sonra da YAZILABİLİR kalır. Windows'ta ConPTY gerekir → kapalı.
PTY_DESTEK = (not IS_WIN) and os.path.exists(YARDIMCI_DOSYA)


def _soket_yolu(sid):
    return os.path.join(YARDIMCI_DIR, sid + ".sock")


def _yardimci_cagri(sid, istek, timeout=5.0):
    """PTY yardımcısına soket üzerinden istek gönder."""
    import socket as _sock
    yol = _soket_yolu(sid)
    if not os.path.exists(yol):
        return {"ok": False, "yardimci_yok": True,
                "error": "PTY yardımcısı bulunamadı (bu oturum boru modunda)."}
    try:
        s = _sock.socket(_sock.AF_UNIX, _sock.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(yol)
        s.sendall((json.dumps(istek, ensure_ascii=False) + "\n").encode())
        ham = b""
        while not ham.endswith(b"\n"):
            parca = s.recv(65536)
            if not parca:
                break
            ham += parca
        s.close()
        return json.loads(ham.decode("utf-8", "replace") or "{}")
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def yardimci_saglik(sid):
    return _yardimci_cagri(sid, {"op": "durum"}, timeout=3.0)

MAX_SATIR = 20000          # halkada tutulacak en fazla satır
MAX_BEKLEYEN = 40          # en fazla eşzamanlı oturum
VARSAYILAN_TIMEOUT = 3600  # saniye (24 saat üst sınır)
EN_UZUN_TIMEOUT = 86400

# "Kullanıcı girdisi bekliyor" işaretleri — modelin beklemesini durdurmak için
_GIRDI_ISARET = re.compile(
    r"(?:^|\n)\s*(?:>>>\s*$|password[^\n]*:\s*$|parola[^\n]*:\s*$|"
    r"\[y/n\]\s*$|\(y/n\)\s*$|\(yes/no\)\s*$|Press any key[^\n]*$|"
    r"Enter [^\n]*:\s*$|Devam[^\n]*:\s*$|Continue\?[^\n]*$|"
    r"\$\s*$|#\s*$|>\s*$)",
    re.I | re.M)

_KILIT = threading.RLock()
_OTURUMLAR = {}
_YUKLENDI = False


# ============================================================================
#  YARDIMCILAR
# ============================================================================
def _mkdir():
    for d in (CFG_DIR, OTURUM_DIR, LOG_DIR):
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass


def _simdi():
    return time.time()


def _iso(t):
    if not t:
        return ""
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t))


def _pid_yasiyor(pid):
    """PID gerçekten yaşıyor mu? (zombie/başka süreç karışmasın diye dikkatli)"""
    if not pid:
        return False
    try:
        if IS_WIN:
            r = subprocess.run(
                ["tasklist", "/FI", "PID eq %d" % int(pid), "/NH"],
                capture_output=True, text=True, timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            return str(int(pid)) in (r.stdout or "")
        os.kill(int(pid), 0)
        # zombie kontrolü (Linux)
        try:
            with open("/proc/%d/stat" % int(pid), "r") as f:
                alanlar = f.read().split()
            if len(alanlar) > 2 and alanlar[2] == "Z":
                return False
        except Exception:
            pass
        return True
    except Exception:
        return False


def _log_yolu(sid, akis):
    return os.path.join(LOG_DIR, "%s.%s.log" % (sid, akis))


def _kaydet(o):
    """Oturum durumunu diske yaz (kalıcılık)."""
    if not o.get("sid"):
        return
    yol = os.path.join(OTURUM_DIR, o["sid"] + ".json")
    try:
        _mkdir()
        d = {k: v for k, v in o.items() if k not in ("_p", "_okuyucular")}
        d["stdout_log"] = _log_yolu(o["sid"], "out")
        d["stderr_log"] = _log_yolu(o["sid"], "err")
        gecici = yol + ".tmp"
        with open(gecici, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
        os.replace(gecici, yol)      # atomik
    except Exception:
        pass


def _sil_kayit(sid):
    try:
        p = os.path.join(OTURUM_DIR, sid + ".json")
        if os.path.exists(p):
            os.remove(p)
    except Exception:
        pass


# ============================================================================
#  OTURUM NESNESİ
# ============================================================================
class Oturum(object):
    """Tek bir süreç oturumu."""

    def __init__(self, sid, komut, cwd, timeout=None, etiket=""):
        self.d = {
            "sid": sid,
            "command": komut,
            "cwd": cwd,
            "etiket": etiket or "",
            "pid": 0,
            "durum": "baslatiliyor",     # baslatiliyor/running/exited/timeout/killed/failed
            "exit_code": None,
            "basladi": _simdi(),
            "bitti": None,
            "timeout": timeout,
            "satir_sayisi": {"out": 0, "err": 0},
            # SIRA NUMARASI: her yayınlanan satıra artan tekil numara.
            # Sayaç tabanlı "yeni çıktı" tespiti yarışa açıktı; sıra numarası
            # yarışı ortadan kaldırır (kesin "bundan sonrası" semantiği).
            "seq_out": 0,
            "seq_err": 0,
            "girdi_sayisi": 0,
            "son_cikti_ts": 0.0,
            "bash": False,
            # "pty"  → yardımcı süreç + PTY (yeniden başlatmadan sonra YAZILIR)
            # "boru" → klasik boru modu (yalnız okuma kurtarılır)
            "mod": "boru",
            "yardimci_pid": 0,
        }
        self._p = None
        self._kilit = threading.RLock()

    # -- erişim -------------------------------------------------------------
    def __getitem__(self, k):
        return self.d[k]

    def __setitem__(self, k, v):
        self.d[k] = v

    def get(self, k, v=None):
        return self.d.get(k, v)

    def ozet(self):
        d = dict(self.d)
        d["calisma_s"] = round((d.get("bitti") or _simdi()) - d["basladi"], 2)
        d["basladi_iso"] = _iso(d["basladi"])
        d["bitti_iso"] = _iso(d.get("bitti"))
        d["pid_yasiyor"] = _pid_yasiyor(d.get("pid"))
        return d

    # -- çalıştırma ---------------------------------------------------------
    def baslat(self):
        _mkdir()
        if PTY_DESTEK:
            r = self._pty_baslat()
            if r:
                return True
            # PTY başlatılamazsa boru moduna düş (sessizce değil, kayıtlı)
            self.d["pty_hata"] = self.d.get("pty_hata") or "PTY yardımcısı başlamadı"
        kw = dict(
            cwd=self.d["cwd"] or None,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,          # tamponsuz → kısmi satır (prompt) hemen gelir
        )
        if IS_WIN:
            kw["creationflags"] = (getattr(subprocess, "CREATE_NO_WINDOW", 0)
                                   | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        else:
            kw["start_new_session"] = True      # süreç ağacı yönetimi
        try:
            self._p = subprocess.Popen(self.d["command"], shell=True, **kw)
        except Exception as e:
            self.d["durum"] = "failed"
            self.d["exit_code"] = -1
            self.d["bitti"] = _simdi()
            self.d["hata"] = str(e)[:300]
            _kaydet(self.d)
            return False
        self.d["pid"] = self._p.pid
        self.d["durum"] = "running"
        _kaydet(self.d)
        threading.Thread(target=self._oku, args=("out", self._p.stdout), daemon=True).start()
        threading.Thread(target=self._oku, args=("err", self._p.stderr), daemon=True).start()
        threading.Thread(target=self._bekle, daemon=True).start()
        if self.d.get("timeout"):
            threading.Thread(target=self._zamanlayici, daemon=True).start()
        return True

    def _pty_baslat(self):
        """Oturumu UZUN ÖMÜRLÜ yardımcı süreç + PTY ile başlat.

        Yardımcı, MCP sunucusundan bağımsızdır: sunucu yeniden başlasa bile
        süreç yaşar ve UNIX soketi üzerinden YAZILABİLİR kalır.
        """
        try:
            os.makedirs(YARDIMCI_DIR, exist_ok=True)
            yol = _soket_yolu(self.d["sid"])
            try:
                if os.path.exists(yol):
                    os.remove(yol)
            except Exception:
                pass
            kw = {}
            if IS_WIN:
                kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            else:
                kw["start_new_session"] = True
            y = subprocess.Popen(
                [sys.executable, YARDIMCI_DOSYA, self.d["sid"],
                 str(self.d["command"]), self.d["cwd"] or os.path.expanduser("~"),
                 yol, _log_yolu(self.d["sid"], "out"), _log_yolu(self.d["sid"], "err")],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL, **kw)
            # soketin oluşmasını bekle (en fazla 6 sn)
            for _ in range(60):
                if os.path.exists(yol):
                    break
                time.sleep(0.1)
            if not os.path.exists(yol):
                try:
                    y.kill()
                except Exception:
                    pass
                return False
            d = _yardimci_cagri(self.d["sid"], {"op": "durum"}, timeout=4.0)
            if not d.get("ok"):
                return False
            self.d["yardimci_pid"] = y.pid
            self.d["pid"] = d.get("pid") or 0
            self.d["mod"] = "pty"
            self.d["durum"] = "running"
            _kaydet(self.d)
            threading.Thread(target=self._pty_izle, daemon=True).start()
            if self.d.get("timeout"):
                threading.Thread(target=self._zamanlayici, daemon=True).start()
            return True
        except Exception as e:
            self.d["pty_hata"] = str(e)[:200]
            return False

    def _pty_izle(self):
        """Yardımcının yazdığı logu oku → satırları aynı sıra numarası
        motoruna aktar; süreç bitince çıkış kodunu diske yazılan dosyadan al.
        """
        yol = _log_yolu(self.d["sid"], "out")
        konum = 0
        tampon = ""
        while True:
            try:
                if os.path.exists(yol):
                    with open(yol, "r", encoding="utf-8", errors="replace") as f:
                        f.seek(konum)
                        parca = f.read()
                        konum = f.tell()
                    if parca:
                        tampon += parca
                        while "\n" in tampon:
                            satir, tampon = tampon.split("\n", 1)
                            self._yayinla("out", satir.rstrip("\r"),
                                          tam=True, dosya=None)
                        if tampon:
                            self._yayinla("out", tampon.rstrip("\r"), tam=False)
            except Exception:
                pass
            d = _yardimci_cagri(self.d["sid"], {"op": "durum"}, timeout=3.0)
            if d.get("ok") and d.get("canli"):
                time.sleep(0.15)
                continue
            if tampon:
                self._yayinla("out", tampon.rstrip("\r"), tam=True, dosya=None)
            kod = d.get("exit_code")
            try:
                with open(yol + ".exit", "r", encoding="utf-8") as f:
                    kod = json.load(f).get("exit_code", kod)
            except Exception:
                pass
            with self._kilit:
                if self.d["durum"] in ("running", "baslatiliyor"):
                    self.d["exit_code"] = kod
                    if kod in (None, 0):
                        self.d["durum"] = "exited"
                    elif kod is not None and int(kod) < 0:
                        self.d["durum"] = "failed"
                    else:
                        self.d["durum"] = "exited"
                    self.d["bitti"] = _simdi()
            _kaydet(self.d)
            return

    def _oku(self, akis, boru):
        """Satır satır oku → halkaya + log dosyasına (canlı, kısmi satır dahil).

        ÖNEMLİ: REPL ve `read` gibi programlar istemi (">>> ", "isim: ")
        satır sonu OLMADAN yazar. Satır tamponuyla beklenirse model istemi
        hiç göremez. Bu yüzden 0,12 sn veri gelmezse eldeki parça "kısmi
        satır" olarak yayınlanır.
        """
        if boru is None:
            return
        import select
        try:
            f = open(_log_yolu(self.d["sid"], akis), "a", encoding="utf-8", errors="replace")
        except Exception:
            f = None
        tampon = ""
        son_veri = _simdi()
        try:
            while True:
                try:
                    hazir, _, _ = select.select([boru], [], [], 0.06)
                except Exception:
                    hazir = [boru]
                if hazir:
                    parca = boru.read(4096)
                    if not parca:
                        break
                    tampon += parca.decode("utf-8", "replace")
                    son_veri = _simdi()
                    while "\n" in tampon:
                        satir, tampon = tampon.split("\n", 1)
                        self._yayinla(akis, satir, tam=True, dosya=f)
                else:
                    if tampon and (_simdi() - son_veri) > 0.12:
                        self._yayinla(akis, tampon, tam=False, dosya=f)
                        tampon = ""
        except Exception:
            pass
        finally:
            if tampon:
                self._yayinla(akis, tampon, tam=False, dosya=f)
            try:
                if f:
                    f.close()
            except Exception:
                pass

    def _yayinla(self, akis, metin, tam=True, dosya=None):
        """Bir satırı (veya kısmi satırı) halkaya + loga yaz."""
        anahtar = "kuyruk_" + akis
        sseq = "seq_" + akis
        with self._kilit:
            kuyruk = self.d.get(anahtar) or []
            kismi = self.d.get("kismi_" + akis) or False
            if not tam and kismi and kuyruk:
                kuyruk[-1][1] = metin[:4000]        # aynı kısmi satırı güncelle
            else:
                self.d[sseq] = self.d.get(sseq, 0) + 1
                kuyruk.append([self.d[sseq], metin[:4000]])
                self.d["satir_sayisi"][akis] = self.d["satir_sayisi"].get(akis, 0) + 1
            self.d["kismi_" + akis] = not tam
            if len(kuyruk) > MAX_SATIR:
                atilan = len(kuyruk) - MAX_SATIR
                del kuyruk[:atilan]
                self.d["atilan_" + akis] = self.d.get("atilan_" + akis, 0) + atilan
            self.d[anahtar] = kuyruk
            self.d["son_cikti_ts"] = _simdi()
        if dosya and tam:
            try:
                dosya.write(metin + "\n")
                dosya.flush()
            except Exception:
                pass

    def _bekle(self):
        try:
            kod = self._p.wait()
        except Exception:
            kod = -1
        with self._kilit:
            if self.d["durum"] == "running":
                self.d["durum"] = "exited" if kod == 0 else "failed"
            self.d["exit_code"] = kod
            self.d["bitti"] = _simdi()
        _kaydet(self.d)

    def _zamanlayici(self):
        bitis = _simdi() + float(self.d["timeout"])
        while _simdi() < bitis:
            if self.d["durum"] != "running":
                return
            time.sleep(min(1.0, max(0.05, bitis - _simdi())))
        if self.d["durum"] == "running":
            with self._kilit:
                self.d["durum"] = "timeout"
            self.kill(sebep="timeout")

    # -- girdi --------------------------------------------------------------
    def yaz(self, metin, satir_sonu=True):
        """Sürece GERÇEK stdin yaz. REPL/SSH/onay soruları için."""
        # --- PTY modu: sunucu yeniden başlasa bile yazma ÇALIŞIR
        if self.d.get("mod") == "pty":
            if self.d["durum"] not in ("running", "baslatiliyor"):
                return {"ok": False, "error": "Süreç çalışmıyor (durum: %s)."
                        % self.d["durum"]}
            veri = str(metin)
            if satir_sonu and not veri.endswith("\n"):
                veri += "\n"
            r = _yardimci_cagri(self.d["sid"], {"op": "yaz", "veri": veri})
            if r.get("ok"):
                self.d["girdi_sayisi"] += 1
                _kaydet(self.d)
                return {"ok": True, "yazilan": veri[:200], "mod": "pty",
                        "girdi_sayisi": self.d["girdi_sayisi"]}
            return r
        if not self._p or not self._p.stdin:
            if self.get("elle_baglanildi") and _pid_yasiyor(self.get("pid")):
                return {"ok": False, "elle_baglanildi": True,
                        "error": ("Bu oturum sunucu yeniden başladıktan sonra "
                                  "pid ile kurtarıldı; süreç YAŞIYOR ama stdin "
                                  "borusu kayboldu. Okuma ve takip çalışır, "
                                  "yazma çalışmaz. Komut göndermek için yeni "
                                  "oturum açın.")}
            return {"ok": False, "error": "Bu oturumda stdin yok (süreç bitti veya kapalı)."}
        if self.d["durum"] not in ("running", "baslatiliyor"):
            return {"ok": False, "error": "Süreç çalışmıyor (durum: %s)." % self.d["durum"]}
        try:
            veri = str(metin)
            if satir_sonu and not veri.endswith("\n"):
                veri += "\n"
            self._p.stdin.write(veri.encode("utf-8"))
            self._p.stdin.flush()
            self.d["girdi_sayisi"] += 1
            _kaydet(self.d)
            return {"ok": True, "yazilan": veri[:200],
                    "girdi_sayisi": self.d["girdi_sayisi"]}
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}

    def kapat_stdin(self):
        try:
            if self._p and self._p.stdin:
                self._p.stdin.close()
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)[:150]}

    # -- çıktı --------------------------------------------------------------
    def oku(self, akis="out", baslangic=0, adet=200):
        """Sıra numarasına göre satır ver.

        baslangic = "bu sıra numarasından İTİBAREN" (dahil).
        Dönen `sonraki_baslangic` bir sonraki çağrıya verilir → kayıpsız sayfalama.
        Halkadan düşmüş satır varsa `kirpildi` = True ve sayısı bildirilir.
        """
        with self._kilit:
            kuyruk = list(self.d.get("kuyruk_" + akis) or [])
            son_seq = self.d.get("seq_" + akis, 0)
            atilan = self.d.get("atilan_" + akis, 0)
            kismi = bool(self.d.get("kismi_" + akis))
        secili = [(q[0], q[1]) for q in kuyruk if q[0] >= int(baslangic)]
        dilim = secili[:int(adet)]
        kayip = False
        if not dilim and int(baslangic) < son_seq:
            # halkada yok (çok eski) → log dosyasından oku
            dosya = _logdan_seq(self.d["sid"], akis, int(baslangic), int(adet))
            dilim = dosya
            kayip = atilan > 0 and int(baslangic) <= atilan
        sonraki = (dilim[-1][0] + 1) if dilim else int(baslangic)
        return {
            "ok": True,
            "akis": akis,
            "satirlar": [t for _s, t in dilim],
            "baslangic": int(baslangic),
            "sonraki_baslangic": sonraki,
            "donen": len(dilim),
            "toplam_satir": self.d["satir_sayisi"].get(akis, 0),
            "kismi_satir": kismi,
            "devami_var": sonraki <= son_seq and len(secili) > len(dilim),
            "kirpildi": kayip,
            "kirpilan_satir": atilan if kayip else 0,
            "durum": self.d["durum"],
        }

    def bekle(self, saniye=5.0, kadar_satir=None):
        """Çıktı gelene veya süre dolana kadar bekle (modelin kör kalmasını önler).

        kadar_satir: bu kadar YENİ satır (out+err) gelirse erken dön.
        """
        bitis = _simdi() + float(saniye)
        hedef = None
        if kadar_satir is not None:
            hedef = (self.d["satir_sayisi"]["out"] + self.d["satir_sayisi"]["err"]
                     + int(kadar_satir))
        while _simdi() < bitis:
            if self.d["durum"] not in ("running", "baslatiliyor"):
                return True
            if hedef is not None:
                if self.d["satir_sayisi"]["out"] + self.d["satir_sayisi"]["err"] >= hedef:
                    return True
            time.sleep(0.05)
        return False

    # -- durum --------------------------------------------------------------
    def girdi_bekliyor(self):
        """Çıktı 'girdi bekliyor' ile bitiyor mu? (ayrı raporlanır)"""
        with self._kilit:
            son = (self.d.get("kuyruk_out") or [])[-3:]
        # kuyruk öğeleri [sira_no, metin] biçiminde
        metin = "\n".join([z[1] if isinstance(z, (list, tuple)) else str(z) for z in son])
        return bool(_GIRDI_ISARET.search(metin)) and self.d["durum"] == "running"

    def durum_etiketi(self):
        d = self.d["durum"]
        if d == "running":
            if self.girdi_bekliyor():
                return "waiting_input"
            return "running"
        return d

    # -- öldürme ------------------------------------------------------------
    def kill(self, sebep="kullanici", agac=True):
        """Süreci VE çocuklarını öldür (süreç ağacı)."""
        # --- PTY modu: yardımcı süreç ağacını TERM→KILL ile kapatır
        if self.d.get("mod") == "pty":
            pid = self.d.get("pid")
            r1 = _yardimci_cagri(self.d["sid"], {"op": "sinyal", "sinyal": "TERM"},
                                 timeout=6.0)
            time.sleep(0.3)
            d = _yardimci_cagri(self.d["sid"], {"op": "durum"}, timeout=3.0)
            yontem = "pty killpg TERM"
            if d.get("ok") and d.get("canli"):
                _yardimci_cagri(self.d["sid"], {"op": "sinyal", "sinyal": "KILL"},
                                timeout=6.0)
                yontem = "pty killpg TERM→KILL"
            with self._kilit:
                self.d["durum"] = "killed"
                self.d["bitti"] = self.d.get("bitti") or _simdi()
                self.d["bitti_sebep"] = sebep
            _kaydet(self.d)
            _yardimci_cagri(self.d["sid"], {"op": "kapat_ve_cik"}, timeout=4.0)
            return {"ok": True, "pid": pid, "yontem": yontem, "mod": "pty"}
        pid = self.d.get("pid")
        if not pid:
            return {"ok": False, "error": "PID yok — süreç hiç başlamamış."}
        if not _pid_yasiyor(pid):
            with self._kilit:
                if self.d["durum"] == "running":
                    self.d["durum"] = "killed"
                self.d["bitti"] = self.d.get("bitti") or _simdi()
            _kaydet(self.d)
            return {"ok": True, "zaten_olu": True, "pid": pid}
        yontem = ""
        try:
            if IS_WIN:
                if agac:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                                   capture_output=True, timeout=20,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                    yontem = "taskkill /T"
                else:
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                                   capture_output=True, timeout=20,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                    yontem = "taskkill"
            else:
                if agac:
                    try:
                        os.killpg(os.getpgid(int(pid)), signal.SIGTERM)
                    except Exception:
                        os.kill(int(pid), signal.SIGTERM)
                    time.sleep(0.4)
                    if _pid_yasiyor(pid):
                        try:
                            os.killpg(os.getpgid(int(pid)), signal.SIGKILL)
                        except Exception:
                            os.kill(int(pid), signal.SIGKILL)
                    yontem = "killpg TERM→KILL"
                else:
                    os.kill(int(pid), signal.SIGTERM)
                    yontem = "kill TERM"
        except Exception as e:
            return {"ok": False, "error": str(e)[:200], "pid": pid}
        with self._kilit:
            if self.d["durum"] == "running":
                self.d["durum"] = "killed" if sebep == "kullanici" else self.d["durum"]
            self.d["bitti"] = self.d.get("bitti") or _simdi()
            self.d["kill_sebep"] = sebep
        _kaydet(self.d)
        return {"ok": True, "pid": pid, "yontem": yontem,
                "surec_agaci": bool(agac), "sebep": sebep}


def _logdan_seq(sid, akis, baslangic, adet):
    """Log dosyasından sıra numarasına göre satır oku (1 tabanlı)."""
    yol = _log_yolu(sid, akis)
    out = []
    try:
        with open(yol, "r", encoding="utf-8", errors="replace") as f:
            for i, satir in enumerate(f, start=1):
                if i < baslangic:
                    continue
                if len(out) >= adet:
                    break
                out.append((i, satir.rstrip("\n")[:4000]))
    except Exception:
        pass
    return out


def _logdan(sid, akis, baslangic, adet):
    yol = _log_yolu(sid, akis)
    out = []
    try:
        with open(yol, "r", encoding="utf-8", errors="replace") as f:
            for i, satir in enumerate(f):
                if i < baslangic:
                    continue
                if len(out) >= adet:
                    break
                out.append(satir.rstrip("\n")[:4000])
    except Exception:
        pass
    return out


# ============================================================================
#  GENEL API
# ============================================================================
def _yukle():
    """Diskteki oturum kayıtlarını yükle (sunucu yeniden başlarsa)."""
    global _YUKLENDI
    with _KILIT:
        if _YUKLENDI:
            return
        _YUKLENDI = True
        _mkdir()
        try:
            adlar = [a for a in os.listdir(OTURUM_DIR) if a.endswith(".json")]
        except Exception:
            return
        for ad in adlar:
            yol = os.path.join(OTURUM_DIR, ad)
            try:
                with open(yol, "r", encoding="utf-8") as f:
                    d = json.load(f)
            except Exception:
                continue
            sid = d.get("sid")
            if not sid:
                continue
            o = Oturum(sid, d.get("command", ""), d.get("cwd") or os.path.expanduser("~"),
                       timeout=d.get("timeout"), etiket=d.get("etiket") or "")
            for k, v in d.items():
                if k in ("_p", "_okuyucular"):
                    continue
                o.d[k] = v
            # halka RAM'de yok → log dosyasından doldur (son 500 satır)
            for akis in ("out", "err"):
                if not o.d.get("kuyruk_" + akis):
                    tam = _logdan_seq(sid, akis, 1, 10 ** 9)
                    o.d["kuyruk_" + akis] = tam[-MAX_SATIR:]
                    o.d["satir_sayisi"][akis] = max(o.d["satir_sayisi"].get(akis, 0), len(tam))
                    o.d["seq_" + akis] = max(o.d.get("seq_" + akis, 0), len(tam))
            # süreç hâlâ yaşıyorsa durumu düzelt
            if o.d.get("pid") and _pid_yasiyor(o.d["pid"]):
                if o.d.get("durum") in ("running", "baslatiliyor"):
                    o.d["durum"] = "running"
            elif o.d.get("durum") in ("running", "baslatiliyor"):
                o.d["durum"] = "kayip"     # sunucu kapandı, süreç de gitmiş
                o.d["bitti"] = o.d.get("bitti") or _simdi()
            _OTURUMLAR[sid] = o


def basla(komut, cwd=None, timeout=None, etiket=""):
    """Yeni oturum başlat. Kalıcı ID döner."""
    _yukle()
    komut = str(komut or "").strip()
    if not komut:
        return {"ok": False, "error": "command gerekli."}
    # UTF-8 exit kodu 2 = Python 'bad interpreter' uyarısı (çalışmayı etkilemez)
    if re.search(r"(?:^|&&|;|\|\||\s)b(?:ad|aşla)\s*$", komut):
        return {"ok": False, "error": "Geçersiz komut."}
    cwd = os.path.abspath(os.path.expanduser(str(cwd or os.getcwd())))
    if not os.path.isdir(cwd):
        return {"ok": False, "error": "Çalışma dizini yok: %s" % cwd}
    try:
        timeout = int(timeout) if timeout else VARSAYILAN_TIMEOUT
        timeout = max(1, min(timeout, EN_UZUN_TIMEOUT))
    except Exception:
        timeout = VARSAYILAN_TIMEOUT
    with _KILIT:
        # eşzamanlı oturum sınırı: en eski bitmişleri temizle
        if len(_OTURUMLAR) >= MAX_BEKLEYEN:
            bitmis = [s for s, o in _OTURUMLAR.items()
                      if o["durum"] not in ("running", "baslatiliyor")]
            bitmis.sort(key=lambda s: _OTURUMLAR[s].get("bitti") or 0)
            for s in bitmis[:max(1, len(bitmis) // 2)]:
                _OTURUMLAR.pop(s, None)
                _sil_kayit(s)
        if len(_OTURUMLAR) >= MAX_BEKLEYEN:
            return {"ok": False,
                    "error": "Açık oturum sınırı (%d). Önce terminate_session ile kapatın."
                             % MAX_BEKLEYEN}
        sid = "sess-" + secrets.token_hex(5)
        o = Oturum(sid, komut, cwd, timeout, etiket)
        _OTURUMLAR[sid] = o
    if not o.baslat():
        return {"ok": False, "session_id": sid,
                "error": o.d.get("hata") or "Süreç başlatılamadı."}
    return {"ok": True, "session_id": sid, "pid": o["pid"], "cwd": cwd,
            "command": komut, "timeout_s": timeout, "durum": "running",
            "not": "read_process_output ile canlı çıktı alın; interact_with_process ile girdi gönderin."}


def al(sid):
    _yukle()
    with _KILIT:
        return _OTURUMLAR.get(sid)


def oku(sid, akis="out", baslangic=0, adet=200, bekle_s=0.0):
    """read_process_output — canlı çıktı, sıra numarasıyla sayfalama.

    akis: "out" (stdout) | "err" (stderr) | "hepsi" (ikisi, sıralı)
    baslangic: bu sıra numarasından itibaren (bir önceki çağrının
               `sonraki_baslangic` değeri verilir → kayıpsız takip)
    """
    o = al(sid)
    if not o:
        return {"ok": False, "error": "Oturum bulunamadı: %s" % sid,
                "acik_oturumlar": list(_OTURUMLAR.keys())[-10:]}
    if bekle_s and o["durum"] in ("running", "baslatiliyor"):
        o.bekle(bekle_s)
    if str(akis).lower() in ("hepsi", "all", "both"):
        a = o.oku("out", baslangic, adet)
        b = o.oku("err", baslangic, max(1, adet // 3))
        satirlar = [("[out] " + z) for z in a["satirlar"]] + \
                   [("[err] " + z) for z in b["satirlar"]]
        r = {"ok": True, "akis": "hepsi", "satirlar": satirlar,
             "baslangic": int(baslangic),
             "sonraki_baslangic": max(a.get("sonraki_baslangic", baslangic),
                                      b.get("sonraki_baslangic", baslangic)),
             "donen": len(satirlar),
             "toplam_satir": o["satir_sayisi"]["out"] + o["satir_sayisi"]["err"],
             "devami_var": a.get("devami_var") or b.get("devami_var"),
             "kirpildi": a.get("kirpildi") or b.get("kirpildi"),
             "kismi_satir": a.get("kismi_satir") or b.get("kismi_satir")}
    else:
        r = o.oku(akis=akis, baslangic=baslangic, adet=adet)
    r["session_id"] = sid
    r["durum"] = o.durum_etiketi()
    r["exit_code"] = o["exit_code"]
    r["pid"] = o["pid"]
    r["girdi_bekliyor"] = o.girdi_bekliyor() if o["durum"] == "running" else False
    r["calisma_s"] = round((o["bitti"] or _simdi()) - o["basladi"], 2)
    return r


def yaz(sid, metin, satir_sonu=True, bekle_s=0.8):
    """Sürece GERÇEK stdin yaz ve cevabı aynı çağrıda döndür.

    Modelin "yazdım, şimdi oku" diye ikinci tur harcamaması için, gönderimden
    SONRA gelen çıktı `cevap` alanında döner.
    """
    o = al(sid)
    if not o:
        return {"ok": False, "error": "Oturum bulunamadı: %s" % sid}
    with o._kilit:
        once_seq = o.get("seq_out", 0) + 1     # bu noktadan sonrası "cevap"
    r = o.yaz(metin, satir_sonu=satir_sonu)
    if r.get("ok") and bekle_s:
        bitis = time.time() + float(bekle_s)
        while time.time() < bitis and (o.get("seq_out", 0) < once_seq):
            time.sleep(0.02)
        time.sleep(0.10)          # sonuç + istem birlikte gelsin
        cev = o.oku("out", once_seq, 500)
        satirlar = list(cev.get("satirlar") or [])
        # REPL/terminalin yankıladığı girdi satırını at.
        # PTY modunda yankı, istem önekiyle gelir: "user@x:~$ echo abc" veya
        # ">>> print(1)" → satırın SONU gönderilen metinle eşleşiyorsa yankıdır.
        hedef = str(metin).strip()
        def _yanki(z):
            z = z.strip()
            if not hedef:
                return True
            if z == hedef:
                return True
            return z.endswith(hedef) and len(z) <= len(hedef) + 200
        yankisiz = [z for z in satirlar if not _yanki(z)]
        cev["satirlar"] = yankisiz if yankisiz else satirlar
        r["cevap"] = cev
        r["yeni_satir"] = len(cev["satirlar"])
    return r


def liste(sadece_canli=False):
    _yukle()
    with _KILIT:
        maddeler = []
        for sid, o in _OTURUMLAR.items():
            if sadece_canli and o["durum"] not in ("running", "baslatiliyor"):
                continue
            maddeler.append({
                "session_id": sid,
                "etiket": o.get("etiket"),
                "command": (o.get("command") or "")[:200],
                "cwd": o.get("cwd"),
                "pid": o.get("pid"),
                "durum": o.durum_etiketi(),
                "exit_code": o.get("exit_code"),
                "basladi": _iso(o.get("basladi")),
                "calisma_s": round((o.get("bitti") or _simdi()) - o["basladi"], 1),
                "satir": dict(o["satir_sayisi"]),
                "girdi_bekliyor": (o.girdi_bekliyor()
                                   if (o["durum"] == "running" and o._p) else False),
                "pid_yasiyor": _pid_yasiyor(o.get("pid")) if o.get("pid") else False,
                "elle_baglanildi": bool(o.get("elle_baglanildi")),
                "mod": o.get("mod") or "boru",
                "yazilabilir": (bool(o.get("mod") == "pty" and
                                     o["durum"] in ("running", "baslatiliyor"))
                                or bool(o._p and o._p.stdin)),
            })
    maddeler.sort(key=lambda z: z["basladi"])
    return {"ok": True, "sayi": len(maddeler), "oturumlar": maddeler}


def durum(sid):
    o = al(sid)
    if not o:
        return {"ok": False, "error": "Oturum bulunamadı: %s" % sid}
    d = o.ozet()
    d["ok"] = True
    d["durum"] = o.durum_etiketi()
    d["girdi_bekliyor"] = o.girdi_bekliyor() if o["durum"] == "running" else False
    return d


def kill(sid, agac=True, sebep="kullanici"):
    o = al(sid)
    if not o:
        return {"ok": False, "error": "Oturum bulunamadı: %s" % sid}
    return o.kill(sebep=sebep, agac=agac)


def bitir(sid, sil_kayit=True):
    """Oturumu kapat: çalışıyorsa öldür, kaydı sil."""
    o = al(sid)
    if not o:
        return {"ok": False, "error": "Oturum bulunamadı: %s" % sid}
    sonuc = {"ok": True, "session_id": sid}
    if o["durum"] in ("running", "baslatiliyor"):
        sonuc["kill"] = o.kill(sebep="terminate", agac=True)
    with _KILIT:
        _OTURUMLAR.pop(sid, None)
    if sil_kayit:
        _sil_kayit(sid)
    sonuc["kapatildi"] = True
    return sonuc


def pid_ile_oldur(pid, agac=True):
    """PID ile (oturum dışı süreç) öldür — kill_process aracı için."""
    try:
        pid = int(pid)
    except Exception:
        return {"ok": False, "error": "Geçersiz PID."}
    if pid <= 0:
        return {"ok": False, "error": "Geçersiz PID."}
    if not _pid_yasiyor(pid):
        return {"ok": True, "zaten_olu": True, "pid": pid}
    try:
        if IS_WIN:
            komut = ["taskkill", "/F", "/PID", str(pid)]
            if agac:
                komut.insert(2, "/T")
            subprocess.run(komut, capture_output=True, timeout=20,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            return {"ok": True, "pid": pid, "yontem": "taskkill" + (" /T" if agac else "")}
        if agac:
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            except Exception:
                os.kill(pid, signal.SIGTERM)
            time.sleep(0.3)
            if _pid_yasiyor(pid):
                os.kill(pid, signal.SIGKILL)
            return {"ok": True, "pid": pid, "yontem": "killpg"}
        os.kill(pid, signal.SIGTERM)
        return {"ok": True, "pid": pid, "yontem": "kill"}
    except Exception as e:
        return {"ok": False, "pid": pid, "error": str(e)[:200]}


def kurtar(elle_baglan=True):
    """Sunucu yeniden başladığında çağrılır — diskteki oturumları geri yükler.

    `elle_baglan=True` ise, süreci HÂLÂ YAŞAYAN oturumlara yeniden bağlanılır:
    kayıtlı pid bir sonraki çağrıda bulunur ve stdin/stdout boruları yerine
    pid + log dosyaları üzerinden devam edilir (yazma desteklenmez, okuma
    ve süreç takibi desteklenir). Bu, "MCP sunucusu yeniden başladığında
    kalıcı görev durumu kurtarılmalı" kriterinin karşılığıdır.
    """
    _yukle()
    baglanan = 0
    if elle_baglan:
        with _KILIT:
            for o in list(_OTURUMLAR.values()):
                if o.get("durum") in ("running", "baslatiliyor") and not o._p:
                    # PTY yardımcısı yaşıyorsa TAM yetenek geri gelir
                    yol = _soket_yolu(o["sid"])
                    if o.get("mod") == "pty" and os.path.exists(yol):
                        d = _yardimci_cagri(o["sid"], {"op": "durum"}, timeout=4.0)
                        if d.get("ok") and d.get("canli"):
                            o.d["elle_baglanildi"] = False
                            o.d["pid"] = d.get("pid") or o.get("pid")
                            import threading as _th
                            _th.Thread(target=o._pty_izle, daemon=True).start()
                            baglanan += 1
                            continue
                    pid = o.get("pid")
                    if pid and _pid_yasiyor(pid):
                        o.d["elle_baglanildi"] = True
                        baglanan += 1
                    elif pid:
                        o.d["durum"] = "kayip"
                        o.d["elle_baglanildi"] = False
                        _kaydet(o.d)
    r = liste()
    r["elle_baglanan"] = baglanan
    r["uyari"] = ("Yeniden bağlanılan oturumlarda YAZMA yapılamaz "
                  "(stdin borusu kayboldu); okuma ve süreç takibi sürer."
                  if baglanan else "")
    return r


def temizle(bitmis_saat=24):
    """Eski bitmiş oturum kayıtlarini temizle (disk sismesin)."""
    _yukle()
    simdi = _simdi()
    silinen = 0
    with _KILIT:
        adaylar = [sid for sid, o in _OTURUMLAR.items()
                   if o["durum"] not in ("running", "baslatiliyor")
                   and o.get("bitti") and (simdi - o["bitti"]) > bitmis_saat * 3600]
        for sid in adaylar:
            _OTURUMLAR.pop(sid, None)
            _sil_kayit(sid)
            silinen += 1
    return {"ok": True, "silinen": silinen}


def istatistik():
    _yukle()
    with _KILIT:
        from collections import Counter
        c = Counter(o.durum_etiketi() for o in _OTURUMLAR.values())
    return {"ok": True, "toplam": len(_OTURUMLAR), "durumlar": dict(c),
            "en_fazla": MAX_BEKLEYEN}

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  GhostPilot — pty_yardimci.py  ·  KALICI OTURUM YARDIMCISI
#  Copyright (c) 2026 BTM Code — MIT License
#
#  NE ÇÖZER
#    Normalde bir sürecin stdin/stdout boruları, onu açan süreç (MCP sunucusu)
#    ölünce kaybolur. Bu yüzden "sunucu yeniden başladığında yazma çalışmıyor"
#    sınırı vardı.
#
#  ÇÖZÜM
#    Her oturum için ayrı ve UZUN ÖMÜRLÜ bir yardımcı süreç (bu dosya) açılır.
#    Yavru süreç bir PTY'ye bağlanır; PTY'nin ana ucu YARDIMCIDA kalır.
#    Sunucu yeniden başlayınca yardımcıya bir UNIX soketi üzerinden bağlanılır:
#        {"op":"yaz","veri":"ls\n"}      → stdin'e yaz
#        {"op":"kapat"}                  → stdin'i kapat (EOF)
#        {"op":"sinyal","sinyal":"TERM"} → sürece sinyal
#        {"op":"durum"}                  → canlı mı, pid, çalışma süresi
#
#    Böylece MCP sunucusu istediği kadar yeniden başlasın, oturum yaşar ve
#    YAZILABİLİR kalır.
#
#  KULLANIM (oturum.py tarafından çağrılır)
#      python3 pty_yardimci.py <sid> <komut> <cwd> <soket_yolu> <log_out> <log_err>
#
#  Windows: PTY yok (ConPTY gerekir) → bu yardımcı Linux/macOS'ta devreye girer,
#  Windows'ta eski (boru + pid kurtarma) yola düşülür. Sınır açıkça bildirilir.
# ============================================================================

import json
import os
import platform
import pty
import select
import signal
import socket
import subprocess
import sys
import time

IS_WIN = platform.system() == "Windows"


def _simdi():
    return time.time()


class Yardimci(object):
    def __init__(self, sid, komut, cwd, soket, log_out, log_err):
        self.sid = sid
        self.komut = komut
        self.cwd = cwd
        self.soket_yolu = soket
        self.log_out = log_out
        self.log_err = log_err
        self.ana_fd, self.yavru_fd = pty.openpty()
        # Gerçek terminal kontrolü: yavru, PTY'yi KENDİ kontrol terminali yapar.
        # preexec_fn yalnız ana süreçte (fork sonrası) çalışır; pty.fork()'un
        # yaptığı işi elle yaparız → "no job control" uyarısı kaybolur.
        def _hazirla():
            os.setsid()
            try:
                import fcntl
                import struct
                import termios
                fcntl.ioctl(0, termios.TIOCSCTTY, 0)
                # pencere boyutu (satır, sütun) — bazı programlar ister
                fcntl.ioctl(0, termios.TIOCSWINSZ,
                            struct.pack("HHHH", 40, 120, 0, 0))
            except Exception:
                pass
        self.p = subprocess.Popen(
            komut, shell=True, cwd=cwd or None,
            stdin=self.yavru_fd, stdout=self.yavru_fd, stderr=self.yavru_fd,
            preexec_fn=_hazirla, close_fds=True)
        os.close(self.yavru_fd)
        self.basladi = _simdi()
        self._dosya = open(self.log_out, "a", encoding="utf-8", errors="replace")
        self._dur = False

    # ------------------------------------------------------------------ okuma
    def oku_dongusu(self):
        """PTY'den geleni log dosyasına yaz (sunucu okur)."""
        tampon = b""
        while not self._dur:
            try:
                hazir, _, _ = select.select([self.ana_fd], [], [], 0.1)
            except Exception:
                break
            if not hazir:
                continue
            try:
                parca = os.read(self.ana_fd, 4096)
            except OSError:
                break
            if not parca:
                break
            tampon += parca
            # satır satır yaz; kısmi satırı da yaz (istem kaybolmasın)
            while b"\n" in tampon:
                satir, tampon = tampon.split(b"\n", 1)
                self._yaz(satir.decode("utf-8", "replace") + "\n")
            if tampon and len(tampon) > 0:
                # küçük gecikmeyle kısmi satırı da yayınla
                self._yaz(tampon.decode("utf-8", "replace"))
                tampon = b""
        if tampon:
            self._yaz(tampon.decode("utf-8", "replace"))
        try:
            self._dosya.flush()
        except Exception:
            pass

    def _yaz(self, metin):
        try:
            self._dosya.write(metin)
            self._dosya.flush()
        except Exception:
            pass

    # ---------------------------------------------------------------- istekler
    def isle(self, istek):
        op = (istek or {}).get("op")
        if op == "yaz":
            veri = str(istek.get("veri") or "")
            try:
                os.write(self.ana_fd, veri.encode("utf-8"))
                return {"ok": True, "yazilan": len(veri)}
            except Exception as e:
                return {"ok": False, "error": str(e)[:200]}
        if op == "kapat":
            try:
                os.write(self.ana_fd, b"\x04")     # EOF (Ctrl-D)
                return {"ok": True}
            except Exception as e:
                return {"ok": False, "error": str(e)[:150]}
        if op == "sinyal":
            ad = str(istek.get("sinyal") or "TERM").upper()
            try:
                os.killpg(os.getpgid(self.p.pid), getattr(signal, "SIG" + ad))
                return {"ok": True, "sinyal": ad}
            except Exception as e:
                return {"ok": False, "error": str(e)[:150]}
        if op == "durum":
            return {"ok": True, "pid": self.p.pid, "canli": self.p.poll() is None,
                    "exit_code": self.p.poll(),
                    "calisma_s": round(_simdi() - self.basladi, 2),
                    "sid": self.sid}
        if op == "kapat_ve_cik":
            try:
                self._dur = True
                if self.p.poll() is None:
                    os.killpg(os.getpgid(self.p.pid), signal.SIGTERM)
            except Exception:
                pass
            return {"ok": True}
        return {"ok": False, "error": "bilinmeyen op: %s" % op}

    # ------------------------------------------------------------------ soket
    def cikis_kodu_yaz(self):
        """Süreç bitince çıkış kodunu diske yaz (sunucu buradan okur)."""
        try:
            kod = self.p.wait()
        except Exception:
            kod = -1
        try:
            self._dosya.flush()
        except Exception:
            pass
        try:
            with open(self.log_out + ".exit", "w", encoding="utf-8") as f:
                json.dump({"sid": self.sid, "exit_code": kod,
                           "bitti": time.time()}, f)
        except Exception:
            pass
        return kod

    def calistir(self):
        try:
            if os.path.exists(self.soket_yolu):
                os.remove(self.soket_yolu)
        except Exception:
            pass
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(self.soket_yolu)
        os.chmod(self.soket_yolu, 0o600)     # yalnız sahibi
        s.listen(8)
        s.settimeout(0.2)
        while not self._dur:
            try:
                bag, _ = s.accept()
            except socket.timeout:
                if self.p.poll() is not None:
                    break
                continue
            except Exception:
                break
            try:
                bag.settimeout(10)
                ham = b""
                while not ham.endswith(b"\n") and len(ham) < 1_000_000:
                    parca = bag.recv(65536)
                    if not parca:
                        break
                    ham += parca
                istek = json.loads(ham.decode("utf-8", "replace") or "{}")
                cevap = self.isle(istek)
                bag.sendall((json.dumps(cevap, ensure_ascii=False) + "\n").encode())
            except Exception as e:
                try:
                    bag.sendall((json.dumps({"ok": False, "error": str(e)[:200]}) + "\n").encode())
                except Exception:
                    pass
            finally:
                try:
                    bag.close()
                except Exception:
                    pass
        try:
            s.close()
            os.remove(self.soket_yolu)
        except Exception:
            pass


def main():
    if IS_WIN:
        print("Bu yardımcı Windows'ta kullanılmaz (ConPTY gerekir).", file=sys.stderr)
        return 2
    if len(sys.argv) < 7:
        print("kullanım: pty_yardimci.py <sid> <komut> <cwd> <soket> <log_out> <log_err>",
              file=sys.stderr)
        return 2
    sid, komut, cwd, soket, lo, le = sys.argv[1:7]
    y = Yardimci(sid, komut, cwd, soket, lo, le)
    import threading
    threading.Thread(target=y.oku_dongusu, daemon=True).start()
    try:
        y.calistir()
    finally:
        y.cikis_kodu_yaz()
        try:
            y._dosya.close()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

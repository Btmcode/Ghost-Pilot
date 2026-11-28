# GhostPilot NEX — FULL SÜRÜM

**Belge tarihi:** 2026‑11‑16
**Geliştirme dizini:** `/home/user/Ghost-Pilot-dev`
**Sürüm numarası:** verilmedi (belirleme size ait — `VERSION` alanı olduğu gibi bırakıldı)
**Mevcut kurulum:** ⚠️ dokunulmadı

---

## 1 · Bu sürümde ne var

| Faz | Konu | Araç | Durum |
|---|---|---|---|
| 1 | Terminal & Process (+ **PTY kalıcı yazma**) | 6 | ✅ |
| 2 | Search | 4 | ✅ |
| 3 | Filesystem | 3 | ✅ |
| 4 | GUI | 4 | ✅ (nesne ağacı arka ucu takılabilir) |
| 5 | Audit / Observability | 5 | ✅ |
| 6 | Multi‑Device | 5 | ✅ |
| 7 | Güvenlik | 4 | ✅ |

- **81 araç**, **33 alias** (eski Türkçe adlar korunuyor)
- **Test: 59/59 geçti, 0 başarısız** (`python3 testler.py`)
- **Politika atlatma testi: 28/28**
- **Gizli bilgi sızıntısı: 0**

### Bu turda KAPANAN eksikler

| Önce | Şimdi |
|---|---|
| Sunucu yeniden başlayınca oturuma **yazma çalışmıyordu** | ✅ **PTY yardımcısı** (`pty_yardimci.py`) — süreç sunucudan bağımsız yaşar, yeniden başlatma sonrası **yazma da çalışır** |
| Exit code PTY'de kaybolabiliyordu | ✅ yardımcı `.exit` dosyasına yazar → `exit 42` doğru raporlanır |
| PTY'de "no job control" uyarısı | ✅ `setsid` + `TIOCSCTTY` → gerçek terminal |
| Nesne ağacı yalnız `goz.py`'ye bağlıydı | ✅ **takılabilir arka uç** (`gui.arka_ucu_ayarla`) — Windows'ta `uiautomation`, Linux'ta AT‑SPI |
| Panelde NEX görünmüyordu | ✅ panoda **NEX · canlı durum** şeridi (cihaz, işlem, sonuç, pencere, oturum/arama/cihaz/çağrı sayaçları, yetenek satırı) |
| Modül sağlığı görünmüyordu | ✅ `moduller.py` + `python ghostpilot.py surum` |
| Sınırsız mod yoktu | ✅ `python ghostpilot.py sinirsiz` — kota/lisans kapalı, **güvenlik kapıları aynen geçerli** |
| Kurulumda yeni modüller eksik kalıyordu | ✅ `exe_yap.py` + `kurulum.py` listeleri tamamlandı, **kurulan dizinde doğrulandı** |

---

## 2 · Sınırsız mod (kota + lisans açık)

```bash
python ghostpilot.py sinirsiz          # SINIRSIZ MOD aç
python ghostpilot.py sinirsiz kapat    # ücretsiz plana dön
python ghostpilot.py kota-durum        # durum
python kurulum.py --tam                # kurulum + sınırsız mod birlikte
```

| Mod | Aylık sınır | Lisans/destek anahtarı | Güvenlik kapıları |
|---|---|---|---|
| Ücretsiz (varsayılan) | 20.000 çağrı/ay | sınırsız için destek anahtarı | ✅ aynen |
| **Sınırsız** | **yok** | **istenmez** | ✅ **aynen** |

**Ölçülen:** sınır 2'ye çekilmişken sınırsız modda **6/6 kabul**, mod kapatılınca **2/6 kabul**.

> Satış modeli değişmedi: ücretsiz plan + bağış ile sürdürülebilirlik. Sınırsız mod bir **kullanım tercihi**, yeni bir ücret kapısı değil.

---

## 3 · PTY kalıcı yazma (en önemli iyileştirme)

Normalde stdin/stdout boruları, onları açan süreç ölünce kaybolur. Bu yüzden "sunucu yeniden başladığında yazma çalışmıyor" sınırı vardı.

**Çözüm:** Her oturum için uzun ömürlü `pty_yardimci.py` süreci; yavru bir PTY'ye bağlanır, PTY'nin ana ucu yardımcıda kalır. Sunucu yeniden başlayınca UNIX soketi (izin `0600`) üzerinden bağlanılır:

```
{"op":"yaz","veri":"ls\n"} · {"op":"kapat"} · {"op":"sinyal","sinyal":"TERM"} · {"op":"durum"}
```

### Doğrulanmış davranış (gerçek çıktı)

```
PTY modu etkin                          ✓ pty
PTY canlı yazma                         ✓
kurtarma: oturum geri geldi             ✓ elle=1
kurtarılan oturum YAZILABİLİR           ✓
KURTARMA SONRASI YAZMA çalışıyor        ✓
PTY exit kodu (7)  exit=7               ✓
```

Bellek sıfırlanıp `kurtar()` çağrıldıktan sonra aynı oturuma yazıldı ve cevap alındı:

```
ok: True → ['user@e2b:~$ echo kurtarma-yazma-OK', 'kurtarma-yazma-OK', 'user@e2b:~$ ']
```

**Windows sınırı (dürüst):** Windows'ta PTY yoktur (ConPTY gerekir); orada eski boru+pid kurtarma yolu kullanılır → okuma ve takip çalışır, yazma çalışmaz ve araç bunu **açıkça** bildirir.

---

## 4 · Kurulum EXE'si

```bat
:: Windows'ta, GhostPilot klasörünün içinde:
yap_exe.bat
```

Betik: PyInstaller'ı denetler/kurar → kaynakları derler → `dist\GhostPilot-Kurulum.exe` üretir.

### Bu ortamda yapılan gerçek derleme

| Adım | Sonuç |
|---|---|
| PyInstaller ile onefile derleme | ✅ `54,6 MB` tek dosya |
| Tüm modüller + kaynaklar gömüldü | ✅ |
| **EXE'yi çalıştırıp gerçek kurulum** | ✅ 58 dosya kopyalandı, venv kuruldu, kısayol yazıldı |
| **Kurulan dizinde modül bütünlüğü** | ✅ 9/9 motor dosyası yerinde |

> ⚠️ **Önemli sınır:** Bu sandbox Linux'tur; burada üretilen ikili **Linux ELF** dosyasıdır (`file`: ELF 64-bit LSB executable). PyInstaller **çapraz derleme yapmaz** — Windows `.exe` yalnız Windows'ta üretilebilir. Bu yüzden Windows için `yap_exe.bat` hazır; aynı komut zinciri Windows'ta `.exe` üretir. **Windows `.exe` testi yapılmadı ve PASS gösterilmiyor.**

---

## 5 · NEX paneli

`http://127.0.0.1:<port>/panel` → **🛰️ NEX · canlı durum** bölümü:

- Cihaz · İşlem · Sonuç · Pencere · Güncelleme saati (canlı HUD)
- Terminal oturumu (canlı / toplam, kaç tanesi yazılabilir)
- Arama (çalışıyor / toplam, kırpılan)
- Cihaz (online / toplam)
- Bugünkü çağrı + hata + ortalama süre
- Yetenek satırı: kademe sınırı, bekleyen onay, PTY, nesne ağacı, sanal imleç, plan, eksik modül

Panel her alt sistemi **ayrı ayrı** korur: tek bozuk modül tüm paneli düşürmez.

---

## 6 · Testler

```bash
python3 testler.py             # 59 test (Linux/Xvfb)
python3 testler_windows.py     # Windows'a özel (Windows'ta çalıştırılır)
python3 -m py_compile *.py     # sözdizimi
python ghostpilot.py doctor    # kurulum + modül teşhisi
python ghostpilot.py surum     # modül sürümleri
```

| Bölüm | Kapsam | Sonuç |
|---|---|---|
| A | Araç/alias bütünlüğü (81/33) | ✅ |
| B | Terminal (başlat/yaz/oku/listele/kapat) | ✅ |
| C | Arama (sayfalama, durdurma) | ✅ |
| D | Dosya (atomik blok, link reddi) | ✅ |
| E | GUI (pencere, VM eşleme, tahmin yok) | ✅ |
| F | Audit (maskeleme, HUD, sızıntı) | ✅ |
| G | Çoklu cihaz (HMAC, 401, izin) | ✅ |
| H | Güvenlik 28/28 | ✅ |
| I | **PTY kalıcı yazma** | ✅ |
| J | **Sınırsız mod** | ✅ |
| K | **Modüller + panel** | ✅ |

---

## 7 · Windows vs Linux ayrımı

**🟢 Linux/Xvfb — çalıştırıldı ve geçti:** yukarıdaki 59 test.

**🔴 Windows — çalıştırılmadı, ayrı raporlanacak:**
PowerShell/`cmd.exe` oturumları, `taskkill /T`, `GetClassNameW`, junction tespiti, gerçek `uiautomation` ağacı, Hyper‑V/VMConnect ile gerçek Ubuntu ekranı, fiziksel imlecin hiç hareket etmemesi, `yap_exe.bat` ile `.exe` üretimi.

`python testler_windows.py` bu 8 başlığı otomatik dener (Linux'ta çalışmayı reddeder, çıkış kodu 2).

---

## 8 · Geri alma

| Ne yapıldı | Geri alma |
|---|---|
| `python ghostpilot.py sinirsiz` | `python ghostpilot.py sinirsiz kapat` |
| `python kurulum.py --tam` | `python ghostpilot.py sinirsiz kapat` |
| PTY kullanımı | `~/.ghostpilot/oturum-soket/` silinir; oturumlar boru moduna döner |
| Kurulum | `KALDIR.bat` / `kaldir.py` |

Tüm geliştirme `Ghost-Pilot-dev` içinde; yayın deposu (`bda7bc1`) ve mevcut kurulumlar değiştirilmedi.

# GhostPilot NEX — Faz 1‑7 Geliştirme ve Test Raporu

**Tarih:** 2026‑11‑16
**Geliştirme dizini:** `/home/user/Ghost-Pilot-dev`
**Mevcut kurulum:** ⚠️ **DOKUNULMADI** (`D:\AiProjelerim\GhostPilot-MCP` ve `/home/user/GhostPilot` üzerinde hiçbir işlem yapılmadı)
**Sürüm numarası:** verilmedi (belirleme kullanıcıya ait)
**Dil:** Python (mimari korundu, yeniden yazım yok)

---

## 0 · Özet

| Faz | Konu | Araç | Durum |
|---|---|---|---|
| 1 | Terminal & Process | 6 | ✅ Tamam (canlı doğrulandı) |
| 2 | Search | 4 | ✅ Tamam |
| 3 | Filesystem | 3 | ✅ Tamam |
| 4 | GUI | 4 | ✅ Tamam (Linux) · ⚠️ Windows alt kümesi ayrı raporda |
| 5 | Audit / Observability | 5 | ✅ Tamam |
| 6 | Multi‑Device | 5 | ✅ Tamam (HMAC imzalı, Tailscale'siz) |
| 7 | Güvenlik | 4 | ✅ Tamam (28/28 atlatma testi) |

- **Toplam araç: 81** (önceki 56 → +25)
- **Alias: 33** (eski Türkçe adlar korunuyor, geriye dönük uyumlu)
- **Bütünleşik test: 38/38 geçti, 0 başarısız**
- **Politika atlatma testi: 28/28 geçti**
- **Gizli bilgi sızıntısı: 0** (hem maskeleme testinde hem gerçek çağrıda)

---

## 1 · Faz 1 — Terminal & Process

**Yeni dosya:** `oturum.py` (kalıcı terminal motoru)

| Araç | İşlev |
|---|---|
| `start_process` | Süreç başlat, kalıcı `session_id` döndür |
| `read_process_output` | Sıra numaralı, kayıpsız sayfalı canlı okuma |
| `interact_with_process` | Gerçek stdin yaz, cevabı aynı turda döndür |
| `list_sessions` | Oturumlar, durum, pid canlılığı, yazılabilirlik |
| `terminate_session` | Düzgün kapatma |
| `kill_process` | Süreç ağacıyla zorla sonlandırma |

### Çözülen iki kritik hata

1. **Satır tamponu istemleri yutuyordu.** `python -i` → `>>> ` ve `read -p "Ad: "` satır sonu olmadan yazar; tamponlu okuma modeli kör kalıyordu.
   → **Çözüm:** ikili boru + `select`, "0,12 sn sessizlik → kısmi satır yayınla". *(Geri dönülmez karar.)*
2. **Sayaç tabanlı "yeni çıktı" tespiti yarışa açıktı.** stderr satırı sayaca eklenince `sonra > once` hiç sağlanmıyor, cevap `None` dönüyordu.
   → **Çözüm:** monoton **sıra numarası** (`seq_out` / `seq_err`), sayfalama `sonraki_baslangic` ile kayıpsız.

### Doğrulanmış davranış

| Test | Beklenen | Sonuç |
|---|---|---|
| REPL `2+2` | `['4']` | ✅ |
| `print('merhaba')` | `['merhaba']` | ✅ |
| `read -p "Adiniz: "` → stdin | `['Merhaba BtmCode']` | ✅ |
| `seq 1 500` sayfalama | 1‑5 / 6‑10 / 496‑500 | ✅ |
| stderr ayrı akış | `HATA`, exit 3, durum `failed` | ✅ |
| **Sunucu yeniden başlatma** | oturumlar diskten kurtarılır | ✅ pid yaşıyor, geçmiş logdan okunuyor |

### Kalıcılık (kabul kriteri 6)

Sunucu yeniden başlatıldığında bellek sıfırlanıyor, `kurtar()` diskteki kayıtları ve log dosyalarını geri yüklüyor. Test sonucu:

```
kurtarılan: 1 | elle bağlanan: 1
durum: running | pid yaşıyor: True | elle: True | yazılabilir: False
geçmiş okundu: ['satir-1', 'satir-2', 'satir-3']
yazma denemesi: False | "…süreç YAŞIYOR ama stdin borusu kayboldu. Okuma ve takip
                        çalışır, yazma çalışmaz. Komut göndermek için yeni oturum açın."
```

> **Dürüstlük notu:** Yeniden bağlanılan oturumda **yazma çalışmaz** (stdin borusu süreçle birlikte kaybolur, boruyu yeniden açmak mümkün değildir). Bu **başarısız test değil**, mimari sınırdır ve araç bunu tahminle gizlemek yerine açıkça bildirir. Okuma, süreç takibi ve sonlandırma çalışır.

---

## 2 · Faz 2 — Search

**Yeni dosya:** `arama.py` (arka plan arama motoru)

| Araç | İşlev |
|---|---|
| `start_search` | Arka planda başlat, anında `search_id` döndür (**bloklamaz**) |
| `get_more_search_results` | Sayfa sayfa oku (`start` = önceki `sonraki_baslangic`) |
| `stop_search` | Durdur (`search_id` yoksa hepsini) |
| `list_searches` | Durum + sonuç sayısı + `kirpildi` bayrağı |

**Ölçülen:** 600 dosyalık ağaçta `start_search` dönüş süresi **0,5 ms** (arka planda tarama sürüyor).

| Test | Sonuç |
|---|---|
| İsim araması (`*.py`) | 300 sonuç, sayfalama doğru ✅ |
| İçerik araması (regex `TODO: (\w+)`) | 600 sonuç, satır numaraları doğru ✅ |
| **Kırpma bildirimi** (sınır 20) | `kirpildi: True` + "SONUÇLAR EKSİK OLABİLİR" uyarısı ✅ |
| İzin dışı kök | `{'ok': False, 'error': 'Bu klasör okuma izninin dışında…'}` ✅ |

> Eski `t_glob` (300) ve `t_grep` (150) sabit kırpmaları **korunuyor**; yeni motor isteğe bağlı olarak kullanılıyor. Eski araçlar silinmedi (geriye dönük uyumluluk).

---

## 3 · Faz 3 — Filesystem

**Yeni dosya:** `dosya.py`

| Araç | İşlev |
|---|---|
| `read_multiple_files` | Tek çağrıda ≤50 dosya; her biri için ayrı sonuç/sebep |
| `edit_block` | **Çoklu blok, atomik** düzenleme |
| `link_check` | symlink / junction / hardlink + hedef izin denetimi |

**Atomiklik kanıtı:** İki bloktan biri eşleşmezse **hiçbir şey yazılmaz**.

```
önce: def a():| return 100|def b():| return 200
bloklar: ["return 100"→"return 111" ✅, "BOYLE BIR METIN YOK" ❌]
sonuç: ok=False · "2. blok eşleşmedi — HİÇBİR DEĞİŞİKLİK YAPILMADI."
dosya DEĞİŞMEDİ mi: True   ← atomiklik kanıtı
```

**Link güvenliği** — iki katmanlı denetim (hem linkin kendi konumu hem çözülmüş hedefi):

| Durum | Sonuç |
|---|---|
| `kutu/disari_link → /etc/passwd` | ❌ reddedildi (`izinli: False`) |
| `kutu/ic2 → kutu/icerde.txt` (kutu içinde) | ✅ izinli |
| hardlink (nlink > 1) | 🏷️ tespit edilir |
| Windows junction (reparse point) | 🏷️ tespit edilir |

**Dosya kilidi:** 3 eşzamanlı yazıcı → sıralı giriş/çıkış (`giris0,cikis0,giris1,cikis1,giris2,cikis2`) ✅

---

## 4 · Faz 4 — GUI

**Yeni dosya:** `gui.py` — mevcut `gozle`, `goverlay` (sanal imleç), `ui_bul`, `sanaldunya` **korundu**.

| Araç | İşlev |
|---|---|
| `get_window_info` | Başlık, dikdörtgen, PID, süreç adı, sınıf, alt pencere sayısı, VM tespiti |
| `find_ui_element` | Addan öğe bul (koordinat gerekmez) |
| `interact_with_ui_element` | click / double_click / right_click / read / set / invoke / focus **+ doğrulama** |
| `vm_coordinates` | VMConnect/Hyper‑V/VMware için misafir↔host koordinat dönüşümü |

### Tıklama doğrulaması (kabul kriteri: "gerçek tıklama doğrulama")

Tıklama öncesi ve sonrası hedef bölgenin ekran görüntüsü karşılaştırılır:

```
tıklama: True | ekran değişti: True
yorum: "Ekran değişti — tıklama iş gördü."
```

Değişiklik yoksa araç **"Ekranda görünür değişiklik YOK — tıklama hedefe ulaşmamış olabilir"** der. Sessizce "başarılı" demez.

### VMConnect koordinat eşlemesi

Host'ta (100,100) konumlu 800×600 VMConnect penceresi, misafir çözünürlük 1920×1080:

| Test | Sonuç |
|---|---|
| misafir (960,540) → host | (500, 400), ölçek 0,4167 ✅ |
| host → misafir geri dönüş | (960, 540) — **tutarlı** ✅ |
| misafir (0,0) → host | (100, 175), offset `[0, 75]` (dikey ortalama) ✅ |
| ekran dışı nokta | `icinde: False` ✅ |

### İki dürüst sınır

1. **Nesne adı bulma, Linux/Tk katmanında sınırlı.** Sandbox'ta `pyatspi`/`xdotool`/`wmctrl` yok; `find_ui_element` bir öğe adını çözemezse **tahmin etmez**, `bulunamadi: True` + `ipucu` döndürür. Gerçek öğe ağacı testi **Windows'ta** yapılmalıdır.
2. **Pencere sınıfı/PID** Linux'ta `xwininfo` katmanından gelmediği için boş; Windows'ta `GetClassNameW` + `GetWindowThreadProcessId` ile doldurulur.

---

## 5 · Faz 5 — Audit / Observability

**Yeni dosya:** `izleme.py`

Eski kayıt 4 alanlıydı: `{"t","action","ok","detail"}` → hangi cihaz, hangi oturum, ne kadar sürdü bilinmiyordu; `detail` serbest metin olduğu için **token sızabiliyordu**.

Yeni kayıt (`~/.ghostpilot/audit.jsonl`):

```json
{"t":"2026-11-28T04:46:46","ts":1795841206.203,"tool":"read_multiple_files",
 "device_id":"local","session_id":"","ok":true,"sure_ms":11,
 "params":{"paths":["a.txt"]},"result":{"okunan":3},"error":""}
```

| Araç | İşlev |
|---|---|
| `get_recent_tool_calls` | Son çağrılar (tool/cihaz/oturum/süre/sonuç) |
| `get_usage_stats` | Çağrı, hata oranı, ortalama süre, en çok kullanılan |
| `get_audit_log` | Ham kayıt + **sızıntı öz denetimi** |
| `nex_hud` | Canlı HUD: cihaz, pencere, işlem, sonuç |
| `mask_test` | Maskelemenin kendi kendini testi |

### Gizli bilgi maskeleme (kabul kriteri 7) — iki katman

1. **Anahtar adı** deseni: `token|secret|password|parola|şifre|api_key|authorization|bearer|cookie|private_key|credential…` → değer tamamen `[GİZLİ]`
2. **Değer** deseni: `?token=…`, `Bearer …`, 32+ karakterlik anahtar, SSH private key bloğu → `[GİZLİ]`

**Gerçek çağrı üzerinde kanıt:**

```
g.call_tool("status", {"api_key":"sk-CANLI-TEST-1234567890", "token":"Bearer abcdefghijklmnop"})
→ audit.jsonl içinde 'sk-CANLI-TEST-1234567890' var mı: False
→ audit.jsonl içinde 'abcdefghijklmnop'        var mı: False
```

Sızıntı dedektörü **kendi çıktısına karşı da doğrulandı** (yanlış pozitif yok):

| Girdi | Tespit |
|---|---|
| `?token=ELLE_YAZILMIS_GIZLI` (maskelenmemiş) | `True` — sızıntı yakalanır ✅ |
| `dosya.txt okundu` | `False` ✅ |
| `?token=[GİZLİ]` (maskelenmiş) | `False` — yanlış alarm yok ✅ |

---

## 6 · Faz 6 — Multi‑Device

**Yeni dosya:** `cihaz.py` — **Tailscale yok**, bağımlılık tamamen kaldırıldı.

| Araç | İşlev |
|---|---|
| `list_devices` | Cihazlar + durum (online/offline) |
| `add_device` | Kayıt + 256 bit anahtar üretimi |
| `remove_device` | Silme |
| `device_health` | Gecikme ölçümlü sağlık kontrolü |
| `device_call` | Başka cihazda imzalı araç çağrısı |

### Güvenlik modeli

- İstek imzası: `HMAC-SHA256(anahtar, cihaz_id|zaman|nonce|gövde)`
- Saat sapması ±120 sn dışında → **red**
- nonce tek kullanımlık (son 2000 nonce bellekte)
- **İmza doğrulandıktan sonra** nonce tüketilir → saldırgan meşru nonce yakamaz
- `cihazlar.json` izinleri **0600**
- Uzaktan çağrılabilir araçlar **açık liste** (`allow_tools`); kalanı reddedilir

| Test | Sonuç |
|---|---|
| Geçerli imza | `(True, '')` ✅ |
| Yanlış imza | `(False, 'İmza geçersiz.')` ✅ |
| 500 sn sapma | `(False, 'Saat sapması çok büyük (>120 sn)')` ✅ |
| Replay (aynı nonce) | `(False, 'Nonce tekrar kullanılmış (replay)')` ✅ |
| İmzasız HTTP isteği | **HTTP 401** ✅ |
| İzinsiz araç (`start_process`) | `reddedildi: True` ✅ |
| Sağlık: erişilebilir cihaz | `online`, 12 ms ✅ |
| Üstel geri çekilme | 2 → 4 → 8 sn ✅ |
| Arka plan izleyici | `olu-cihaz offline`, `ubuntu-ai online` ✅ |

---

## 7 · Faz 7 — Güvenlik (3 kademeli izin politikası)

**Yeni dosya:** `guvenlik.py`

| Kademe | Kapsam | Davranış |
|---|---|---|
| **1 · Okuma** | `ls`, `cat`, `grep`, `git status`, salt‑okunur araçlar | Onaysız serbest |
| **2 · Yazma** | dosya değiştirme, paket kurma, süreç başlatma | Çalışma alanı içinde serbest; **sandbox dışına çıkamaz** |
| **3 · Tehlikeli** | disk, kapatma, yetki yükseltme, uzaktan kod | **Açık onay zorunlu** |

### Onay mekanizması — atlatılamaz

- Belirteç **tek kullanımlık**, **120 sn** geçerli, **araç + parametreye bağlı** (SHA‑256 özeti)
- Ajan kendi onayını üretemez: `onay_ver(kaynak="ajan")` → **reddedilir**
- Araç parametresine `"onay": true` yazmak **işe yaramaz**

### 28/28 atlatma testi (hepsi geçti)

| # | Test | Sonuç |
|---|---|---|
| 1‑7 | `rm -rf /`, `rm -rf ~`, `mkfs`, `shutdown`, `curl … \| bash`, `sudo`, `dd if=…of=/dev/sda` → kademe 3 | ✅ |
| 8‑10 | `ls -la`, `cat`, `git status` → kademe 1 | ✅ |
| 11‑13 | `rm eski.txt`, `echo x > f.txt`, `pip install` → kademe 2 | ✅ |
| 14 | Parametreye `"onay": true` yazma → **reddedildi** | ✅ |
| 15 | Sahte belirteç → reddedildi | ✅ |
| 16 | Geçerli onay → izinli | ✅ |
| 17 | Aynı onay 2. kez → reddedildi | ✅ |
| 18 | Onay başka komuta aktarılamaz | ✅ |
| 19 | Ajan kendi onayını üretemez | ✅ |
| 20‑21 | Sandbox dışı yazma red / içi izinli | ✅ |
| 22 | Salt‑okunur mod yazmayı engeller | ✅ |
| 23 | Süresi dolmuş onay reddedilir | ✅ |
| 24‑27 | **Onay + mutlak yasak** (`rm -rf /`, `mkfs`, `shutdown`, `dd`) → **onayla bile çalışmaz** | ✅ |
| 28 | Kademe 3 + geçerli onay (`rm -rf ~/arsiv`) → izinli | ✅ |

> **Mutlak yasak listesi**, eski `SHELL_BLOCKLIST` ile birebir uyumlu ve ondan daha geniştir. Onay verilse dahi çalışmaz (savunma derinliği).

**Önemli düzeltme:** Salt‑okuma araçları (`start_search`, `read_multiple_files`) yazma kökleriyle denetlendiği için yanlışlıkla engelleniyordu. Araç türüne göre ayrı kök listesi eklendi:
- **okuyan araç** → okuma + yazma köklerinin birleşimi
- **yazan araç** → yalnız yazma kökleri
- `link_check` sandbox kapısından muaf (yoksa kaçış girişimini bildiremez; yalnız durum raporlar, içerik okumaz)

---

## 8 · Bütünleşik test sonucu (38/38)

```
=== A · ARAÇ SAYISI / ALIAS ===        ✓ 81 araç · 33 alias · tüm aliaslar geçerli
=== B · FAZ 1 TERMİNAL ===             ✓ başlat / yaz / oku / listele / kapat
=== C · FAZ 2 ARAMA ===                ✓ başlat · sayfa1 · sayfa2 farklı · listele · durdur
=== D · FAZ 3 DOSYA ===                ✓ çoklu okuma · atomik blok · atomiklik kanıtı · link reddi
=== E · FAZ 4 GUI ===                  ✓ pencere bilgisi · VM ölçek · gidiş-dönüş · tahmin yok
=== F · FAZ 5 AUDIT ===                ✓ maskeleme · son çağrılar · istatistik · sızıntısız · HUD
=== G · FAZ 6 CİHAZ ===                ✓ ekle · sağlık · izinli çağrı · izinsiz red · listele
=== H · FAZ 7 GÜVENLİK ===             ✓ 28/28 · tehlikeli engel · onay · sandbox · salt okunur

SONUÇ: 38 geçti, 0 başarısız — TÜM TESTLER GEÇTİ ✓
```

**HTTP `/mcp` uçtan uca (Bearer kimlik doğrulamalı):**

```
tools/list : 81 araç
nex_hud    : 7 ms
tehlikeli komut (HTTP) : {'ok': false, 'blocked': true, 'policy': {'kademe': 9, 'mutlak_yasak': true…}}
```

---

## 9 · Windows vs Linux test ayrımı (kabul kriteri 8)

### 🟢 Linux / Xvfb — bu raporda ÇALIŞTIRILDI ve GEÇTİ

| Konu | Durum |
|---|---|
| Terminal (bash, python REPL, `read -p` stdin) | ✅ |
| Arama motoru (600 dosya) | ✅ |
| Dosya (atomik, kilit, symlink/hardlink) | ✅ |
| GUI pencere bilgisi, VM koordinat matematiği | ✅ |
| Tıklama doğrulaması (ekran farkı) | ✅ |
| Audit + maskeleme | ✅ |
| Çoklu cihaz (HMAC, replay, 401) | ✅ |
| İzin politikası 28/28 | ✅ |

### 🔴 Windows — ÇALIŞTIRILMADI, ayrı raporlanacak

Bu testler Linux sandbox'ta **fiziksel olarak yapılamaz**; PASS olarak işaretlenmemiştir:

| Test | Neden gerekli |
|---|---|
| PowerShell / `cmd.exe` oturumları | `-q -i` davranışı farklı, istem `stderr`'e gider |
| `taskkill /T` ile süreç ağacı | `killpg` yok |
| `GetClassNameW`, `GetWindowThreadProcessId`, junction tespiti | Windows API |
| Gerçek nesne ağacı (`uiautomation`) | Sandbox'ta `pyatspi`/`xdotool` yok |
| **Hyper‑V + VMConnect + gerçek Ubuntu ekranı** | Kabul kriteri 4 — yalnız Windows host'ta mümkün |
| Gerçek Excel/Not Defteri tıklama doğrulaması | Gerçek pencere gerektirir |
| Fiziksel imlecin hiç hareket etmemesi | `SendInput` / mesaj tabanlı girdi |

**Windows test prosedürü (sırayla):**
1. `python ghostpilot.py doctor`
2. `python testler.py` (temel 38 test)
3. `python -c "import ghostpilot as g; print(g.call_tool('policy_test',{}))"` → 28/28
4. Hyper‑V'de Ubuntu VM aç → `vm_coordinates` ile ölçek doğrula → gerçek ekranda tıklama doğrula
5. Fiziksel fare imleci başka yerdeyken sanal imlecin çalıştığını gözle doğrula

---

## 10 · Kabul kriterleri durumu

| # | Kriter | Durum |
|---|---|---|
| 1 | Fiziksel fare hiç hareket etmemeli | 🟡 Tasarım hazır (`input_bg` mesaj tabanlı + `goverlay` sanal imleç), **Windows'ta doğrulanmalı** |
| 2 | NEX kendi görünür imlecini kullanmalı | 🟡 `goverlay` korundu, 5 sn otomatik gizleme mevcut, **Windows'ta doğrulanmalı** |
| 3 | Windows ve Ubuntu bağımsız kontrol | ✅ `cihaz.py` — ayrı ajan, imzalı yönlendirme, canlı doğrulandı |
| 4 | VMConnect girişleri gerçek Ubuntu ekranında doğrulanmalı | 🔴 Koordinat eşlemesi ✅, **gerçek VM testi Windows'ta bekliyor** |
| 5 | Terminal oturumları süreç bitene kadar izlenebilmeli | ✅ canlı stdout/stderr + sayfalama |
| 6 | Sunucu yeniden başladığında kalıcı görev durumu kurtarılmalı | ✅ pid + log kurtarma; yazma sınırı açıkça bildirilir |
| 7 | Token/gizli bilgi audit'e yazılmamalı | ✅ iki katmanlı maskeleme + gerçek çağrı kanıtı |
| 8 | Windows testleri Xvfb'den ayrı raporlanmalı | ✅ Bölüm 9 |

---

## 11 · Değişen / eklenen dosyalar

| Dosya | Durum | Satır (yaklaşık) |
|---|---|---|
| `oturum.py` | 🆕 Faz 1 motoru (elle bağlanma eklendi) | ~850 |
| `arama.py` | 🆕 Faz 2 motoru | ~300 |
| `dosya.py` | 🆕 Faz 3 motoru | ~380 |
| `gui.py` | 🆕 Faz 4 motoru | ~430 |
| `izleme.py` | 🆕 Faz 5 motoru | ~400 |
| `cihaz.py` | 🆕 Faz 6 motoru | ~460 |
| `guvenlik.py` | 🆕 Faz 7 motoru | ~450 |
| `ghostpilot.py` | ✏️ 25 yeni araç + 20 alias + politika kapısı + otomatik izleme | 81 araç, 33 alias |
| `paketle.py` | ✏️ `DOSYALAR` 7 modül eklendi | 53 dosya |
| `kurulum.py` | ✏️ `KOPYALANACAK` 7 modül eklendi | 58 dosya |
| `testler.py` | 🆕 bütünleşik test koşucusu | ~150 |

Her iki paket listesi **birlikte** güncellendi; eksik dosya denetimi temiz (`paketle eksik: []`).

---

## 12 · Notlar ve geri dönüş planı

**Geri dönüş:** Tüm geliştirme `Ghost-Pilot-dev` içinde, git deposu yok. Geri dönmek için dizini silmek yeterlidir; yayın deposu (`/home/user/Ghost-Pilot`, HEAD `bda7bc1`) ve mevcut kurulumlar **hiç değiştirilmedi**.

**Bilinen sınırlar (gizlenmedi):**
- Yeniden bağlanılan oturumda yazma çalışmaz (mimari sınır, açık hata mesajı)
- Linux'ta nesne ağacı katmanı zayıf (`pyatspi` yok) → öğe adı bulma Windows'ta test edilmeli
- `guvenlik.py` komut sınıflandırması desen tabanlıdır; yeni komutlar için kural eklenmeli (bilinmeyen komut **kademe 2** varsayılır — güvenli taraf)
- `cihaz.py` HTTP üzerinden çalışır; **üretimde TLS sonlandırıcı** (reverse proxy) arkasına konmalıdır

**Sıradaki doğal adım:** Windows host'ta Bölüm 9'daki prosedürün çalıştırılması ve Hyper‑V/VMConnect testinin tamamlanması.


---

# EK · FULL SÜRÜM TURU (aynı gün, ikinci tur)

Yukarıdaki 1‑12 bölümü ilk turun raporudur. Bu ek, **full sürüm** turunda kapatılan
maddeleri ve güncel sayıları içerir. **Ayrıntılı kullanım belgesi: `FULL_SURUM.md`.**

## Güncel sayılar

| Ölçüt | İlk tur | Full sürüm |
|---|---|---|
| Araç | 81 | **81** |
| Alias | 33 | **33** |
| Bütünleşik test | 38/38 | **59/59 geçti, 0 başarısız** |
| Politika atlatma testi | 28/28 | **28/28** |
| Maskeleme sızıntısı | 0 | **0** |
| Modül | 7 | **9** (+`moduller.py`, +`pty_yardimci.py`) |

## Kapanan açık maddeler

| İlk raporda açık kalan | Full sürümde |
|---|---|
| Yeniden başlatma sonrası **yazma çalışmıyor** | ✅ **ÇALIŞIYOR** (PTY yardımcısı; 6 test ile kanıtlandı) |
| Exit code PTY'de kayboluyordu | ✅ `exit 42` doğru raporlanır |
| PTY'de "no job control" | ✅ gerçek terminal (`setsid`+`TIOCSCTTY`) |
| Nesne ağacı tek katmana bağlı | ✅ takılabilir arka uç; bu platformda **yok** ve araç bunu **açıkça** söylüyor |
| Panelde NEX yok | ✅ NEX · canlı durum şeridi |
| Modül sağlığı görünmüyor | ✅ `moduller.py` + `surum`/`doctor` |
| Sınırsız mod yok | ✅ `sinirsiz` / `--tam` |
| Kurulumda yeni modüller eksik | ✅ 9/9 kuruluyor (gerçek EXE ile doğrulandı) |

## Yeni bulunan ve düzeltilen gerçek hatalar

1. **Kota mühür çelişkisi:** `kota_sifirla()` imzalı mührü silmiyordu; mühür "EN AZ bu kadar" alt sınırı tuttuğu için sıfırlama işe yaramıyor, sayfa 6'da kalıyordu. → Mühür de silinir.
2. **Sınırsız modda izler geride kalıyordu:** makine defteri/damga güncellenmediği için mod kapatılınca dürüst kullanıcı "kurcalandı" alarmı alıyordu. → `_kota_izlerini_guncelle()` her iki modda da çalışır.
3. **Kurulum listeleri eksikti:** `moduller.py` ve `pty_yardimci.py` `kurulum.py`/`exe_yap.py` listelerinde yoktu → kurulan dizinde araçlar "modül yok" diyordu. Gerçek EXE kurulumuyla yakalandı ve düzeltildi.
4. **Hayalet dosya referansı:** `GhostPilot.command` üç listede vardı ama depoda hiç yoktu → temizlendi.

## EXE durumu (dürüst)

| Adım | Sonuç |
|---|---|
| PyInstaller onefile derleme (Linux) | ✅ 54,6 MB tek dosya |
| EXE ile **gerçek kurulum** | ✅ 58 dosya, venv, kısayol |
| **Kurulan dizinde 59/59 test** | ✅ |
| Kurulan dizinde HTTP `/mcp` (81 araç, 7 ms, PTY yazma, tehlikeli engel) | ✅ |
| **Windows `.exe`** | 🔴 **üretilmedi** — PyInstaller çapraz derleme yapmaz. `yap_exe.bat` Windows'ta hazır. |

## Kabul kriterleri (güncel)

| # | Kriter | Durum |
|---|---|---|
| 1 | Fiziksel fare hareket etmemeli | 🟡 Windows'ta doğrulanmalı |
| 2 | NEX kendi görünür imlecini kullanmalı | 🟡 Windows'ta doğrulanmalı |
| 3 | Windows + Ubuntu bağımsız kontrol | ✅ |
| 4 | VMConnect girişleri gerçek Ubuntu ekranında | 🔴 koordinat ✅, gerçek VM testi Windows'ta |
| 5 | Oturum süreç bitene kadar izlenebilmeli | ✅ |
| 6 | Yeniden başlatmada kalıcı görev durumu | ✅ **artık yazma dahil** |
| 7 | Token/gizli bilgi audit'e yazılmamalı | ✅ |
| 8 | Windows testleri ayrı raporlanmalı | ✅ |

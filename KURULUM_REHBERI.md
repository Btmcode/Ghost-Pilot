# 👻 GhostPilot — Kurulum Rehberi

> **Ne kadar sürer:** 8–10 dakika
> **Ne gerekir:** Windows 10/11 bilgisayar + internet
> **Python kurmanız gerekmez** — program yoksa kendisi indirip kurar.
> **Ne yapmanız gerekir:** Sadece tıklamak. Kod yazmayacaksınız.

---

## 📦 Adım 1 — Dosyayı indirin ve açın (2 dk)

1. Size gelen **`GhostPilot-MCP-v5.19.0.zip`** dosyasını **İndirilenler** klasörüne indirin
2. Dosyaya **sağ tıklayın** → **Tümünü ayıkla** → **Ayıkla**
3. Açılan **`GhostPilot`** klasörünü **Masaüstüne** sürükleyin

**✅ Oldu mu?** Masaüstünde `GhostPilot` klasörü var, içinde `KURULUM.bat` görüyorsunuz.

> ⚠️ **Önemli:** Zip'in **içinden** çalıştırmayın. Önce mutlaka ayıklayın.
> `C:\Program Files` klasörüne de koymayın — Masaüstü veya `D:\` idealdir.

---

## ⚙️ Adım 2 — Kurulumu başlatın (3 dk)

1. Masaüstündeki **`GhostPilot`** klasörünü açın
2. **`KURULUM.bat`** dosyasına **çift tıklayın**

**Ne olacak:**

- Siyah bir pencere açılır
- **Python kurulu değilse:** program kendisi indirir ve kurar. 5–10 dakika sürebilir, **pencereyi kapatmayın**. Ekranda bir Python kurulum penceresi çıkarsa **Install Now** deyin.
- **Python kuruluysa:** bu adım saniyeler sürer, doğrudan devam eder.
- Ardından **"Nereye kurulsun?"** diye sorar → **Enter**'a basın (kendisi doğru yeri seçer)
- Kurulum başlar, kendi özel ortamını oluşturur (30 saniye kadar)

**✅ Oldu mu?** En altta şunu görürsünüz:

```
✅ KURULUM TAMAM
   Klasör : C:\Users\<adınız>\GhostPilot
   Başlat : masaüstündeki 👻 GhostPilot kısayolu
```

ve masaüstünüzde 👻 ikonlu **GhostPilot** kısayolu belirir.

> ❓ **"Windows korumalı bilgisayarınızı" uyarısı çıkarsa:** **Ek bilgi** → **Yine de çalıştır** deyin.
> ❓ **Mavi pencere aniden kapanırsa:** internet bağlantınızı kontrol edip tekrar çift tıklayın.

---

## 🚀 Adım 3 — GhostPilot'u açın (30 sn)

Masaüstündeki **👻 GhostPilot** kısayoluna çift tıklayın.

**Ne göreceksiniz:** Koyu renkli bir panel açılır. En üstte:

```
GhostPilot · v5.19.0    Gerçek bilgisayarınız, sandbox değil · ayda 20.000 çağrı ücretsiz
```

Ve **3 sekme**: Durum · Lisans · Paketler

**✅ Oldu mu?** İlk kartta **SUNUCU → çalışıyor** (yeşil) yazıyor.

> 📌 **Bu paneli kapatmayın.** Sohbet yaparken açık kalmalı. Küçültebilirsiniz.

---

## 🤖 Adım 4 — ChatGPT'ye bağlayın (3 dk)

### 4a. Panelden adresi kopyalayın

1. GhostPilot panelinde **Durum** sekmesine bakın
2. **UZAKTAN ERİŞİM** bölümünü bulun
3. Oradaki adresi görün — şuna benzer: `http://127.0.0.1:17381/mcp`
4. Yanındaki **erişim anahtarını** da kopyalayın (uzun harf-rakam dizisi)

### 4b. ChatGPT'de bağlayıcı oluşturun

1. **ChatGPT masaüstü uygulamasını** açın (tarayıcı değil — uygulama olsun)
2. Sol altta profil resminize tıklayın → **Settings** (Ayarlar)
3. **Connectors** (Bağlayıcılar) sekmesine tıklayın
4. **Advanced** (Gelişmiş) bölümünü açın → **Developer mode** (Geliştirici modu) nu **açın**
5. Geri dönün, **Create** veya **Add custom connector** (Özel bağlayıcı ekle) düğmesine tıklayın
6. Şu bilgileri girin:

| Alan | Ne yazacaksınız |
|---|---|
| **Name** (Ad) | `GhostPilot` |
| **URL** (Adres) | `http://127.0.0.1:17381/mcp` |
| **Authentication** | `No authentication` (Kimlik doğrulama yok) |

> Panelde farklı bir port yazıyorsa (örn. 17382), o numarayı kullanın.

7. **Save** (Kaydet) düğmesine tıklayın

### 4c. Deneyin

Yeni bir sohbet açın ve şunu yazın:

> **"ghostpilot_status aracını kullan ve bu bilgisayarda neler yapabildiğini söyle."**

**✅ Oldu mu?** Asistan araç listesini ve bilgisayarınızın adını söylüyor.
İlk kullanımda ChatGPT izin isteyebilir → **Allow / İzin ver** deyin.

---

## 🖥️ Claude Desktop kullanıyorsanız (alternatif)

1. **Claude Desktop** → **Settings** → **Developer** → **Edit Config**
2. Açılan dosyaya şunu yapıştırın (yolu kendi kullanıcı adınıza göre değiştirin):

```json
{
  "mcpServers": {
    "ghostpilot": {
      "command": "python",
      "args": ["C:\\Users\\KULLANICI_ADINIZ\\GhostPilot\\ghostpilot.py", "bridge"]
    }
  }
}
```

3. Kaydedin → Claude Desktop'ı **kapatıp yeniden açın**
4. Sohbette çekiç 🔨 simgesine tıklayın → araçlar görünmeli

---

## 🎯 Adım 5 — Gerçekten çalışıyor mu? (3 test)

Sohbete sırayla yazın:

### Test 1 — Ekran görüntüsü
> **"Ekranımın görüntüsünü al ve ne gördüğünü söyle."**

Beklenen: Ekranda ne olduğunu anlatır. 👻 hayalet imleç görünür, **sizin fareniz oynamaz**.

### Test 2 — Dosya okuma
> **"Masaüstümde hangi dosyalar var listele."**

Beklenen: Masaüstünüzdeki dosya adlarını sayar.

### Test 3 — Onay ekranı
> **"Masaüstünde test.txt dosyası oluştur ve içine merhaba yaz."**

Beklenen: GhostPilot panelinde **onay isteği** çıkar → **Onayla**'ya tıklayın → dosya oluşur.

**✅ Üçü de olduysa kurulum tamam.** 🎉

---

## 📊 Ne kadar hakkım var?

Sohbete sorun:

> **"Ne kadar kullanım hakkım kaldı?"**

Asistan şunu söyler:

```
Bu ay kullanılan: 0 / 20.000
Kalan: 20.000 çağrı
Sıfırlanma: Her ayın 1'inde 00:00 UTC
Sayım kuralı: yalnız gerçek araç çalışmaları sayılır.
Zaman aşımı ve bağlantı kopması sayılmaz.
```

**Ayda 20.000 çağrı ücretsiz.** %80'e gelince panelde uyarı çıkar. Bitmesin diye bir şey yapmanız gerekmez — ayın 1'inde kendiliğinden sıfırlanır.

---

## 🛑 İş bitince ne yapmalı?

**Güvenlik için:** Panelde **Tümünü iptal et** düğmesine basın, sonra **Kapat**.

Ya da tek komutla kapatın:

```
python kur.py dur
```

Bu komuttan sonra **hiçbir sohbet programı bilgisayarınıza erişemez**.

---

## 🗑️ Programı tamamen kaldırmak

1. Masaüstündeki **`GhostPilot`** klasörünü açın
2. **`KALDIR.bat`** dosyasına çift tıklayın
3. **E** (evet) yazıp Enter'a basın

Her şey silinir: program dosyaları, ayarlar, sayaç, masaüstü kısayolu, Programlar listesi kaydı.

---

## ❓ Bir şey ters giderse

| Sorun | Çözüm |
|---|---|
| `KURULUM.bat` açılıp hemen kapanıyor | Klasörü zip'in içinden çalıştırıyorsunuz. Önce **ayıklayın** |
| Python indirilirken hata verdi | İnternet bağlantısı veya antivirüs engeli. Bağlantıyı kontrol edip tekrar çift tıklayın |
| Python kuruldu ama "bulunamadı" diyor | Bilgisayarı **yeniden başlatın**, sonra `KURULUM.bat`'a tekrar çift tıklayın |
| Panel açılıyor ama "SUNUCU → durdu" | Port dolu. `PANEL.bat` içinden başlatın veya bilgisayarı yeniden başlatın |
| ChatGPT'de "Connector failed" | Adreste `http` var mı? `/mcp` ile bitiyor mu? Panel açık mı? |
| ChatGPT aracı bulamıyor | **Geliştirici modu** açık mı? Bağlayıcıyı **Save** ettiniz mi? Sohbeti yenileyin |
| "Bu bilgisayarda erişim yok" diyor | Panelde **UZAKTAN ERİŞİM → Başlat**'a basın |
| Ekran görüntüsü siyah çıkıyor | Uzak masaüstü oturumunda sınırlıdır; normal oturumda çalışır |
| Hiçbiri olmadı | Komut İsteminde: `python kur.py doktor` → çıktısını bana gönderin |

**Yardım isterken:** `python kur.py doktor` çıktısını yapıştırın — ama **erişim anahtarını silin**.

---

## 🍎 macOS / Linux kullanıyorsanız

Windows'taki otomatik Python kurulumu bu platformlarda **yok**. Önce Python'u kurun:

| Platform | Komut |
|---|---|
| macOS | `brew install python3` (Homebrew yoksa [python.org/downloads/macos](https://www.python.org/downloads/macos/)) |
| Ubuntu / Debian | `sudo apt update && sudo apt install -y python3 python3-venv python3-pip` |
| Fedora | `sudo dnf install -y python3 python3-pip` |

Sonra klasörde `./kurulum.sh` komutunu çalıştırın.

---

---

## 🆘 Bir şey ters giderse — hata kaydı nasıl alınır

Program açılıp hemen kapanıyorsa bile **sebebi kaydedilir**. Hiçbir şey kaybolmaz.

### 1. Kısayola çift tıklayın

- **Hata varsa** pencere kapanmaz; hata sebebi hem **ekranda** hem şu dosyada olur:
  `C:\Users\<adınız>\.ghostpilot\hata.log`
- Ekrandaki yazıyı okuyabilirsiniz: hangi dosya, hangi satır, ne hata.

### 2. `BASLA.bat` ile açın

Masaüstündeki klasörde **`BASLA.bat`** dosyasına çift tıklayın. Siyah pencerede hata sebebi **açıkça yazar** ve pencere kapanmaz.

### 3. Tek komutla hatayı görün

**Başlat** → `cmd` → kurulum klasörüne gidin, sonra:

```
python kur.py hata
```

Örnek çıktı:

```
[2026-11-25 18:49:22] PANEL OLUŞTURULAMADI
sürüm   : 5.19.0
sistem  : Windows-11-...
python  : 3.13.7 (C:\Users\ali\GhostPilot\.venv\Scripts\python.exe)
klasör  : C:\Users\ali\GhostPilot
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\ali\GhostPilot\ui.py", line 769, in main
NameError: name 't' is not defined
```

> **Bu metnin tamamını** geliştiriciye gönderin — sorun dakikalar içinde bulunur.
> Erişim anahtarınızı metinden silmeyi unutmayın.

### 4. Kaydı temizleyin

```
python kur.py hata-temizle
```

### Kısayol yanlış yeri gösteriyorsa

Kurulum artık kısayolu **kontrol eder** ve yanlışsa kendisi düzeltir:

```
[3/5] Kısayollar…
      ✅ kısayollar doğru klasörü gösteriyor
```

Böyle bir satır görmezseniz kısayolu elle onarın:

```
python kur.py kisayol ekle
```

Kısayol her zaman **kurulum yaptığınız klasörü** (örn. `C:\Users\ali\GhostPilot`) çalıştırır — zip'i açtığınız yeri **değil**.

---

## ⚠️ Bilmeniz gereken 3 şey

1. **Bu program bilgisayarınıza gerçekten erişir.** Sohbet asistanı dosyalarınızı okuyabilir, komut çalıştırabilir. Yalnız güvendiğiniz asistanlara bağlayın.
2. **Verileriniz kendi bilgisayarınızda kalır.** Buluta yüklenmez. Ama sohbet asistanı gördüğü içeriği kendi hizmetine gönderir — normal sohbet gibi.
3. **İş bitince kapatın.** `python kur.py dur` — en temiz alışkanlık.

---

## 📚 Daha fazlası

- **Kota sorunu:** sohbette "Ne kadar hakkım kaldı?"
- **Sınırsız kullanım:** [buymeacoffee.com/btmcode](https://buymeacoffee.com/btmcode) üzerinden destek anahtarı
- **Tüm komutlar:** program klasöründeki `README.md`
- **Sorun bildirme:** [github.com/Btmcode/Ghost-Pilot/issues](https://github.com/Btmcode/Ghost-Pilot/issues)

---

<p align="center">
<b>GhostPilot</b> — gerçek bilgisayarınız, sandbox değil.<br>
BTM Code
</p>

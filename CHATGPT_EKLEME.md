# ChatGPT'ye GhostPilot ekleme

> **Kolay yol `BAGLA.md` dosyasında.** Programı aç, tek düğmeye bas, adresi
> ChatGPT'ye yapıştır. Bu belgeye yalnız tek düğme çalışmazsa bakın.



## Önce şunu bilin

ChatGPT **sizin bilgisayarınızdaki** bir programa doğrudan ulaşamaz. Arada bir
**köprü** gerekir. GhostPilot bu köprüyü kurar:

```
ChatGPT  ──internet──►  köprü (sizin adresiniz)  ──►  sizin bilgisayarınız
```

Köprüyü kurmak için **Tailscale** adlı ücretsiz bir program kullanılır.
Tek seferlik iş. Sonra ChatGPT her sohbette bilgisayarınıza erişebilir.


---

## Gerekenler

| Ne | Şart mı | Not |
|
---|
---|
---|
| GhostPilot kurulu olmalı | ✅ Evet | `KURULUM.bat` |
| ChatGPT **Plus / Pro / Business** | ✅ Evet | Ücretsiz planda bu bölüm yok |
| Tailscale hesabı | ✅ Evet | Ücretsiz, 1 dakikalık kayıt |
| İnternet | ✅ Evet | |


---

## Adım 1 — GhostPilot'u kurun

1. Zip dosyasını bir klasöre çıkarın.
2. **`KURULUM.bat`** dosyasına **çift tıklayın**.
3. Kurulum biterken bir klasör yolu sorar → istediğiniz yeri seçin.
4. Bittiğinde masaüstünde **Ghost ikonu** olur.

> Kurulum kendisi her şeyi hazırlar. Python kurulu mu diye bakmanıza gerek yok.


---

## Adım 2 — Tailscale'i kurun

1. Tarayıcıda **tailscale.com/download** adresini açın.
2. **Windows** seçeneğini indirin.
3. İndirdiğiniz dosyaya **çift tıklayın** → **Install**.
4. Kurulunca **Log in** → Google/Microsoft hesabıyla giriş yapın.
5. Ekranın sağ alt köşesinde Tailscale simgesi görünür → hazır.


---

## Adım 3 — Köprüyü açın

1. GhostPilot klasörünü açın.
2. **`python kur.py chatgpt`** komutunu çalıştırın (ya da panelde
   **ChatGPT** bölümünden başlatın).
3. Ekranda şuna benzer iki satır çıkar:

```
Adres  : https://bilgisayarim.tail1a2b3c.ts.net/mcp?token=abc123...
Anahtar: abc123...
```

> ⚠️ **Bu pencereyi kapatmayın.** Kapatırsanız ChatGPT bağlantısı kesilir.
> Bilgisayar kapanınca da kesilir — tekrar açmanız yeterli.


---

## Adım 4 — ChatGPT'ye ekleyin

Aşağıdaki sırayı **birebir** takip edin. Her satır bir tıklama.

| # | Nerede | Ne yapacaksınız |
|
---|
---|
---|
| 1 | ChatGPT'yi açın | Sol alttaki **profil resminize** tıklayın |
| 2 | Açılan menü | **Ayarlar** (Settings) |
| 3 | Sol menü | **Bağlayıcılar** (Connectors) |
| 4 | Sağ üst | **Gelişmiş** (Advanced) |
| 5 | Burada | **Geliştirici modu**nu (Developer mode) **açın** |
| 6 | Geri dönün | **Bağlayıcılar** sayfası |
| 7 | Sağ üst | **Oluştur** (Create) düğmesi |
| 8 | Ad alanı | `GhostPilot` yazın |
| 9 | Açıklama | `Bilgisayarımdaki dosyalar ve komutlar` yazın |
| 10 | Sunucu adresi | Adım 3'teki **Adres** satırının tamamını yapıştırın |
| 11 | Kimlik doğrulama | **Yok** (None) seçin |
| 12 | Onay kutusu | **"Anladım ve devam etmek istiyorum"** işaretleyin |
| 13 | Kaydet | **Oluştur / Create** |

> Adresin içinde anahtar zaten var. O yüzden "Kimlik doğrulama" alanında
> **Yok** seçiyorsunuz. Ayrı anahtar girmeniz gerekmiyor.


---

## Adım 5 — Deneyin

1. ChatGPT'de **yeni bir sohbet** açın (eski sohbet olmaz).
2. Sohbette **`+`** işaretine tıklayın → **GhostPilot**'u seçin.
3. Şunu yazın:

> ghostpilot_status aracını çalıştır ve ne yapabildiğini özetle

Cevap geliyorsa **bağlantı tamam** 🎉

Sonra gerçek işler:

> Masaüstümdeki dosyaları listele

> Bu klasördeki hata loglarını oku ve özetle

> Şu projeyi test et ve sonucu söyle


---

## Bir şey ters giderse

| Ne görüyorsunuz | Sebep | Çözüm |
|
---|
---|
---|
| **Oluştur** düğmesi yok | Geliştirici modu kapalı ya da ücretsiz plan | Adım 4'ün 5. satırını tekrar yapın; planı kontrol edin |
| "Bağlanılamadı" | Adres yanlış ya da köprü kapalı | Adım 3'teki pencere açık mı? Adresi baştan kopyalayın |
| 401 / yetkisiz | Anahtar değişmiş | `python kur.py token` → yeni adresi kopyalayıp ChatGPT'de adresi güncelleyin |
| Bağlandı ama hiç kullanmıyor | Sohbette seçilmemiş | Sohbette `+` → GhostPilot'u seçin, ya da soruda adını yazın |
| Hepsi tamam, cevap yok | Bilgisayar uyuyor | Bilgisayarı açık tutun, ekran kilidini açın |
| Kurulumda hata | — | `python kur.py hata` → çıkan yazıyı bize gönderin |


---

## Güvenlik — 3 kural

1. **Adresi kimseyle paylaşmayın.** Adresin içinde erişim anahtarı var.
   Ekran görüntüsü alırken o satırı kapatın.
2. **İşiniz bitince köprüyü kapatın.** Pencereyi kapatmak yeterli.
3. **Anahtarı yenilerseniz adres de değişir.** ChatGPT'de adresi güncellemeniz gerekir.

Anahtar sadece sizin bilgisayarınızda ve sizin ChatGPT hesabınızda durur.
GhostPilot hiçbir veriyi kendi sunucusuna göndermez.


---

## Tünel istemiyorsanız — daha kolay yollar

ChatGPT'ye eklemek **zorunlu değil**. Tailscale kurmak istemiyorsanız:

| Program | Komut | Tünel gerekir mi |
|
---|
---|
---|
| **Claude Desktop** | `python kur.py claude` | ❌ Hayır |
| **Cursor / VS Code** | `python kur.py cursor` | ❌ Hayır |
| **Aynı Wi-Fi'daki telefon** | `192.168.x.x:17381/mcp` | ❌ Hayır |
| **ChatGPT (web)** | `python kur.py chatgpt` | ✅ Evet |

Claude ve Cursor aynı bilgisayarda çalıştığı için köprüye gerek yok —
GhostPilot'u doğrudan başlatıp kullanabilirsiniz.


---

## Not

Bu tarif **Windows içindir**. Windows'a özel adımlar (Tailscale kurulumu,
kısayol, tepsi simgesi) bizim test ortamımızda birebir denenemedi —
kod kontrol edildi, ama ilk kurulumda bir aksilik olursa `python kur.py hata`
çıktısını bize iletin, aynı gün düzeltiriz.

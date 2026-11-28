# ChatGPT'ye bağlanmak — 3 adım, tek düğme

Eskiden 13 tıklama vardı. Artık **3 adım** var.

---

## Adım 1 — Programı açın

Masaüstündeki **👻 GhostPilot** simgesine **çift tıklayın**.

Pencere açılır. Bir şey yazmanız gerekmiyor.

> Pencere açılmazsa: klasördeki **`BASLA.bat`** dosyasına çift tıklayın.

---

## Adım 2 — Tek düğmeye basın

Pencerede **UZAKTAN ERİŞİM** bölümünü bulun. Orada şu düğme var:

> ## 🔗 Bağlantı adresi hazırla

Ona **bir kez** basın. 10–40 saniye bekleyin.

Ekranda şuna benzer bir adres çıkar:

```
https://xxxxx-xx-xx-xx-xx.free.pinggy.net/mcp?token=abc123...
```

Hemen altındaki **📋 Kopyala** düğmesine basın.

> ⚠️ Pencere açık kalmalı. Kapatırsanız bağlantı kesilir.
> Kapatmak isterseniz aynı düğme **⛔ Bağlantı kapat** olur, ona basın.

---

## Adım 3 — ChatGPT'ye yapıştırın

Aşağıdaki sırayı takip edin. Her satır **bir tıklama**.

| # | Nerede | Ne yapacaksınız |
|---|---|---|
| 1 | ChatGPT'yi açın | Sol alttan **profil resminiz** |
| 2 | Menü | **Ayarlar** |
| 3 | Sol menü | **Bağlayıcılar** |
| 4 | Sağ üst | **Gelişmiş** |
| 5 | Burada | **Geliştirici modu**nu **açın** |
| 6 | **Bağlayıcılar**'a dönün | **Oluştur** |
| 7 | Ad | `GhostPilot` |
| 8 | Açıklama | `Bilgisayarımdaki dosyalar` |
| 9 | Sunucu adresi | **Yapıştır** (Ctrl+V) |
| 10 | Kimlik doğrulama | **Yok** |
| 11 | Kutuyu işaretleyin | "Anladım ve devam etmek istiyorum" |
| 12 | **Oluştur** | Bitti |

---

## Deneyin

ChatGPT'de **yeni sohbet** açın. Sohbette **`+`** işaretine basın → **GhostPilot**'u seçin.

Sonra yazın:

> ghostpilot_status aracını çalıştır

Cevap geldiyse **bağlantı tamam** ✅

Artık şunları yazabilirsiniz:

> Masaüstümdeki dosyaları listele

> Bu projeyi test et ve sonucu söyle

> Ekran görüntüsü al ve ne gördüğünü anlat

---

## Ne oldu da bu kadar kolaylaştı?

Eskiden **Tailscale** kurmanız, hesap açmanız, tünel adresini elle bulmanız
gerekiyordu. Şimdi program bunu kendisi yapıyor:

- Bilgisayarınızı internete **geçici bir adresle** açar
- Adresi **anahtarıyla birlikte** hazırlar
- Siz sadece **kopyalayıp yapıştırıyorsunuz**

Tailscale kurmanız **gerekmiyor**. Hesap açmanız **gerekmiyor**.
Program kendi tünelini kendisi başlatıyor.

---

## Bir şey ters giderse

| Ne görüyorsunuz | Sebep | Çözüm |
|---|---|---|
| Düğme hiç cevap vermiyor | Sunucu kapalı | **▶ Başlat** düğmesine basın, sonra tekrar deneyin |
| "Adres açılamadı" | İnternet yok ya da güvenlik duvarı engelliyor | İnterneti kontrol edin; internet varsa 1 dakika sonra tekrar basın |
| Adres çıktı ama ChatGPT bağlanmıyor | Adres eksik kopyalanmış | **📋 Kopyala** düğmesini kullanın, elle seçmeyin |
| ChatGPT "Oluştur" düğmesi yok | Geliştirici modu kapalı | Adım 3'ün 5. satırını tekrar yapın |
| 401 hatası | Anahtar değişmiş | Düğmeye tekrar basıp yeni adresi yapıştırın |
| Bağlandı ama kullanmıyor | Sohbette seçilmemiş | Sohbette `+` → GhostPilot |
| Cevaplar çok yavaş | Tünel yavaş | Normaldir; ilk cevap 5–10 saniye sürebilir |

Hâlâ olmuyorsa, GhostPilot klasöründe şunu çalıştırın:

```
python kur.py hata
```

Çıkan yazıyı bize gönderin — sorunun ne olduğunu görürüz.

---

## Bu güvenli mi?

**Evet.** Şunlara dikkat edin:

1. **Adresi kimseyle paylaşmayın** — içinde erişim anahtarı var
2. **İşiniz bitince kapatın** — düğme zaten kapatma düğmesine dönüşüyor
3. **Adres geçicidir** — her açtığınızda değişir, eskisi çalışmaz

Program verilerinizi hiçbir yere göndermez. Adres yalnız sizin bilgisayarınızla
ChatGPT arasında çalışır.

---

## Alternatif: tünel hiç istemiyorsanız

ChatGPT'ye eklemek **zorunlu değil**. Aynı bilgisayarda çalışan programlar
tünel istemez:

| Program | Nasıl |
|---|---|
| **Claude Desktop** | `python kur.py claude` — 2 dakika, tünel yok |
| **Cursor / VS Code** | `python kur.py cursor` — tünel yok |

Bunlar aynı bilgisayarda çalıştığı için köprüye hiç gerek yok. En hızlı yol bunlar.

---

## Not

Bu tarif **Windows** içindir. Tünel ve panel bizim test ortamımızda çalıştırıldı
ve doğrulandı; Windows'ta masaüstü kısayolu ve tepsi simgesi ilk kurulumda
bir aksilik çıkarırsa `python kur.py hata` çıktısını bize iletin.

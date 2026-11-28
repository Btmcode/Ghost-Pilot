# ChatGPT'ye bağlanma — form alanları dahil, birebir

Bu belge ChatGPT'nin **"Özel MCP sunucusu ekle"** formunu doldurmayı anlatır.
Her alanın karşısında ne yazacağınız yazılı. Kopyalayıp yapıştırabilirsiniz.

---

## Adım 1 — Programı aç, adresi üret

1. Masaüstündeki **👻 GhostPilot** simgesine çift tıklayın.
2. **ChatGPT'ye bağlan** düğmesine basın.
3. 10–40 saniye bekleyin. Ekranda bir adres çıkar:
   ```
   https://xxxxx-xx-xx-xx.free.pinggy.net/mcp?token=abc123...
   ```
4. **Kopyala** düğmesine basın.

> Bu adresin içinde erişim anahtarı var. Kimseyle paylaşmayın.

---

## Adım 2 — ChatGPT'de Eklentiler sayfasını aç

Doğrudan link:

### 👉 https://chatgpt.com/plugins

Sol menüden **Eklentiler**'e basarak da aynı yere gelirsiniz.

---

## Adım 3 — "Ekle" → "Özel MCP sunucusu"

Sayfanın **sağ üstünde** mavi **Ekle** düğmesi var. Ona basın.

Açılan listede **Özel MCP sunucusu** seçeneğini seçin.

Karşınıza şu form çıkar:

```
┌─ Özel MCP sunucusu ekle ────────────────────┐
│  Simge (isteğe bağlı)      [ + ]              │
│  Ad                       [            ]     │
│  Açıklama (isteğe bağlı)  [            ]     │
│  Bağlantı         (Sunucu URL'si) (Tünel)    │
│  [ https://example.com/mcp            ]      │
│  Kimlik doğrulama        [ OAuth ▾ ]         │
│  □ Anladım ve devam etmek istiyorum          │
│                       [İptal]  [Ekle]        │
└──────────────────────────────────────────────┘
```

---

## Adım 4 — Alanları böyle doldurun

Her satır bir alan. **Aynen** yazın.

| Formdaki alan | Ne yazacaksınız | Nasıl |
|---|---|---|
| **Simge** | Klasördeki `chatgpt-icon-256.png` dosyası | **+** işaretine bas → dosyayı seç. 256×256 PNG, 9.9 KB — sınırın altında ✅ |
| **Ad** | `GhostPilot` | Aşağıdaki kutudan kopyala |
| **Açıklama** | `Bilgisayarımdaki dosyalar ve komutlar` | Aşağıdaki kutudan kopyala |
| **Bağlantı** | **Sunucu URL'si** seçili kalsın | Dokunmayın |
| **Sunucu URL'si** | Adım 1'de kopyaladığınız adres | Yapıştır (Ctrl+V) |
| **Kimlik doğrulama** | **Yok** | 🔴 **OAuth'u SEÇMEYİN** |
| **Onay kutusu** | ☑ işaretleyin | "Anladım ve devam etmek istiyorum" |

### Kopyalanacak metinler

**Ad:**
```
GhostPilot
```

**Açıklama:**
```
Bilgisayarımdaki dosyalar ve komutlar
```

---

## 🔴 En sık yapılan hata: Kimlik doğrulama

Form açıldığında **Kimlik doğrulama** alanı **OAuth** yazıyor. **Bunu değiştirin.**

| Seçim | Sonuç |
|---|---|
| **OAuth** ❌ | Bağlanmaz. Sürekli hata verir. |
| **Yok** ✅ | Çalışır. |

**Neden?** GhostPilot'un erişim anahtarı **adresin içinde** geliyor
(`?token=...`). Ayrıca OAuth akışına gerek yok. OAuth seçilirse ChatGPT
anahtarı aramaya çalışır, bulamaz, bağlanamaz.

---

## Adım 5 — Ekle'ye bas ve dene

1. Sağ alttaki **Ekle** düğmesine basın.
2. ChatGPT "GhostPilot bağlandı" gibi bir şey gösterir.
3. **Yeni bir sohbet** açın.
4. Sohbette **`+`** işaretine basın → **GhostPilot**'u seçin.
5. Şunu yazın:

```
ghostpilot_status aracını çalıştır
```

Cevap geldiyse **tamam** ✅

Artık gerçek işleri yapabilirsiniz:

```
Masaüstümdeki dosyaları listele
```
```
Bu projeyi test et ve sonucu söyle
```
```
Ekran görüntüsü al ve ne gördüğünü anlat
```

---

## Bir şey ters giderse

| Ne görüyorsunuz | Sebep | Çözüm |
|---|---|---|
| **Ekle** düğmesini bulamıyorum | Sayfa eski | Sayfayı yenileyin: `chatgpt.com/plugins` |
| "Özel MCP sunucusu" yok | Geliştirici modu kapalı | Ayarlar → Bağlayıcılar → Gelişmiş → **Geliştirici modu**nu açın |
| Simge yüklenmiyor | Dosya 10 KB'dan büyük | Klasördeki `chatgpt-icon-256.png` kullanın (9.9 KB) |
| Bağlanamadı / kırmızı hata | Kimlik doğrulama OAuth seçili | Formu düzenleyin → **Yok** yapın |
| Bağlanamadı (başka sebep) | Adres yanlış ya da program kapalı | GhostPilot açık mı? **Kopyala** düğmesini kullanın |
| 401 hatası | Anahtar değişmiş | Programda düğmeye tekrar basın, yeni adresi yapıştırın |
| Bağlandı ama hiç kullanmıyor | Sohbette seçilmemiş | Sohbette `+` → GhostPilot |
| Cevaplar çok yavaş | Tünel gecikmesi | Normaldir; ilk cevap 5–10 saniye |

Hâlâ olmuyorsa: GhostPilot'ta **Gelişmiş** → **Hata kaydı** → kopyalayıp gönderin.

---

## Kapatmak

Programda **Bağlantıyı kapat** düğmesine basın.
Programı kapatmak da bağlantıyı keser. Arkada hiçbir şey kalmaz.

---

## Ücretsiz kullanmak istiyorsanız — dürüst cevap

ChatGPT'de **özel MCP sunucusu eklemek ücretli plan gerektirir.**
Bu OpenAI'nin kısıtı, GhostPilot'un değil. Biz bunu değiştiremeyiz.

**Tamamen ücretsiz alternatifler:**

| Program | Ücret | Tünel | Komut |
|---|---|---|---|
| **Claude Desktop** | ✅ Ücretsiz | ❌ Gerekmez | `python kur.py claude` |
| **Cursor** | ✅ Ücretsiz | ❌ Gerekmez | `python kur.py cursor` |
| **VS Code** | ✅ Ücretsiz | ❌ Gerekmez | `python kur.py cursor` |

Aynı bilgisayarda çalıştıkları için tünel, hesap, adres — hiçbiri gerekmez.
**En kolay ve en ucuz yol Claude Desktop.** Tek komut, 2 dakika.

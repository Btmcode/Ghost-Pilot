# Bağlanmak — tek ekran, tek düğme

## 1. Aç

Masaüstündeki **👻 GhostPilot** simgesine çift tıkla.

Karşına **tek ekran** çıkar. Üzerinde **tek büyük yeşil düğme** var:

> ## 🔗 ChatGPT'ye Bağlan

## 2. Düğmeye bas

Bir kez bas. 10–40 saniye bekle.

Ekranda adresin çıkar:

```
https://xxxxx-xx-xx-xx.free.pinggy.net/mcp?token=abc123...
```

Yanındaki **📋 Adresi Kopyala** düğmesine bas. "✅ Kopyalandı" yazacak.

## 3. ChatGPT'ye yapıştır

Ekranda adımlar zaten yazılı. Sıra şu:

| # | Nerede | Ne yapacaksın |
|---|---|---|
| 1 | ChatGPT | **Ayarlar → Bağlayıcılar** |
| 2 | Sağ üst | **Gelişmiş → Geliştirici modu**nu aç |
| 3 | **Oluştur** | Adres alanına **yapıştır** |
| 4 | Kimlik doğrulama | **Yok** |
| 5 | **Oluştur** | Bitti |

Sonra **yeni sohbet** aç, sohbette **`+`** → **GhostPilot** → yaz:

> ghostpilot_status

## Kapatmak

Aynı düğme artık **⛔ Bağlantıyı Kapat** yazıyor. Ona bas. Programı kapatsan da
bağlantı kesilir — arkada hiçbir şey kalmaz.

---

## Sık sorulan

**Adres değişir mi?** Her bağlandığında değişir. Eski adres çalışmaz.

**Anahtar nerede?** Adresin içinde (`?token=...`). O yüzden ChatGPT'de
"Kimlik doğrulama: Yok" seçiyorsun.

**Adres kimseye gitmiyor mu?** Yalnız senin bilgisayarınla ChatGPT arasında.
Ekran görüntüsü alırken adresi kapat.

**Yavaş?** İlk cevap 5–10 saniye sürebilir. Normal.

---

## Hiç ücret ödemeden kullanmak istiyorsan

Şunu bilmen gerekiyor: **ChatGPT'ye bağlanmak ücretli plan istiyor.** Bu bir
OpenAI kısıtı — özel bağlayıcılar (Connectors) ücretsiz planda açık değil.

GhostPilot bunu değiştiremez. Ama **tamamen ücretsiz** yollar var:

| Program | Ücret | Tünel | Kurulum |
|---|---|---|---|
| **Claude Desktop** | ✅ Ücretsiz | ❌ Gerekmez | `python kur.py claude` |
| **Cursor** | ✅ Ücretsiz | ❌ Gerekmez | `python kur.py cursor` |
| **VS Code + Copilot** | ✅ Ücretsiz | ❌ Gerekmez | `python kur.py cursor` |
| ChatGPT (web) | 💳 Plus gerekir | ✅ Gerekir | yukarıdaki 3 adım |

**En kolay ve en ucuz yol: Claude Desktop.**

Aynı bilgisayarda çalıştığı için tünel, hesap, adres — hiçbiri gerekmez.
GhostPilot'u bir kez bağlarsın, Claude bilgisayarını kullanır. Ücret yok.

Kurulumu:

```
python kur.py claude
```

Tek komut. Sonra Claude Desktop'ı aç, bilgisayarını kullanabildiğini görürsün.

---

## Bir şey ters giderse

| Ne görüyorsun | Ne yapmalı |
|---|---|
| Düğme "Adres hazırlanıyor…" de kalıyor | İnterneti kontrol et, 1 dakika sonra tekrar bas |
| "Bağlanamadı" | Altındaki yazıya bak; genelde internet yok ya da güvenlik duvarı |
| Adres çıktı ama ChatGPT bağlanmıyor | 📋 Kopyala'yı kullan, elle seçme (uzun adres kolay eksilir) |
| ChatGPT'de "Oluştur" yok | Geliştirici modu kapalı — 2. satırı tekrar yap |
| 401 hatası | Düğmeye tekrar bas, yeni adresi yapıştır |

Hâlâ olmuyorsa: **Gelişmiş** düğmesine bas. Hata kaydı orada yazılı.
Kopyalayıp bana gönder, bakarım.

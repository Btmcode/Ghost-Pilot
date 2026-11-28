# GhostPilot — Gizlilik Politikası

**Son güncelleme:** 16 Kasım 2026
**Geliştirici:** BTM Code · [btmcode.vercel.app](https://btmcode.vercel.app)

## Kısa özet

GhostPilot **sizin bilgisayarınızda** çalışır. Bizim sunucumuz, veritabanımız veya
kullanıcı hesabı sistemimiz **yoktur**. Verileriniz bilgisayarınız ile kullandığınız
sohbet programı (ör. ChatGPT) arasında doğrudan akar. BTM Code bu verileri
**görmez, toplamaz, saklamaz, satmaz**.

## 1. Hangi veriler işlenir?

GhostPilot bir MCP sunucusudur; sohbet programı sizin adınıza araç çağırdığında:

| Araç | İşlenen veri | Nerede kalır |
|---|---|---|
| `read`, `ls`, `glob`, `grep` | Dosya içeriği ve yolları | Bilgisayarınızda okunur, yalnızca yanıt olarak sohbet programına iletilir |
| `write`, `edit`, `delete` | Yazılan/silinen dosya | Bilgisayarınızda |
| `doc_read` | Belge içeriği (Word/Excel/PDF) | Bilgisayarınızda |
| `screenshot` | Ekran görüntüsü | Bilgisayarınızda alınır, yanıt olarak iletilir |
| `shell` | Komut ve çıktısı | Bilgisayarınızda |
| `clipboard_*` | Pano metni | Bilgisayarınızda |
| `mouse` / `keyboard` araçları | Koordinat, tuş bilgisi | Bilgisayarınızda |

**Hiçbir veri BTM Code'a gönderilmez.** Üçüncü taraf analitik, reklam veya izleme yoktur.

## 2. Yerel olarak saklanan bilgiler

GhostPilot kendi bilgisayarınızda `~/.ghostpilot/` klasöründe şunları saklar:

| Dosya | İçerik | Amaç |
|---|---|---|
| `config.json` | Port, izin verilen klasörler, modlar | Ayarlar |
| `token` | Yerel erişim anahtarı | Kimlik doğrulama |
| `oauth.json` | OAuth istemci ve erişim kayıtları | İzin verdiğiniz sohbet programları |
| `audit.log` | Yapılan işlemlerin kaydı | Denetim ve sizin incelemeniz |
| `tasks.json` | Zamanlanmış görevler | Otomatik işler |

Bu dosyalar **yalnızca sizin bilgisayarınızdadır**, hiçbir yere yüklenmez.
Dilediğiniz an silebilirsiniz.

## 3. Ağ bağlantıları

| Bağlantı | Neden |
|---|---|
| Bilgisayarınız ↔ sohbet programı | Araç çağrıları (ücretsiz HTTPS tüneli veya yerel ağ) |
| `api.github.com` | Yalnızca güncelleme kontrolü (istek sizce başlatılırsa) |
| `api.telegram.org` | Yalnızca siz açtıysanız ve yalnızca **giden** bildirim |

Tünel açıkken trafik uçtan uca şifrelenir. Sunucu adresinizi
tahmin eden biri bile **OAuth onay ekranını geçemediği için** bağlanamaz.

## 4. Verilerin paylaşılması

BTM Code hiçbir veriyi **satmaz, kiralamaz, paylaşmaz**. Yalnızca sizin
yönlendirdiğiniz sohbet programı, sizin verdiğiniz yetkiyle yanıtları görür —
o hizmetin kendi gizlilik politikası geçerlidir.

## 5. Haklarınız ve denetim

* `~/.ghostpilot/` klasörünü silerek **tüm** yerel veriyi kaldırabilirsiniz.
* sohbet programı erişimini anında kesmek için: panelden **DURDUR** veya
  `python kur.py durdur` / `python kur.py kapat`.
* Verilen tüm izinleri iptal etmek için: `python kur.py oauth-sil`.
* Ne yapıldığını görmek için: paneldeki denetim kaydı ya da `~/.ghostpilot/audit.log`.

## 6. Çocukların verileri

GhostPilot genel kullanım içindir; 13 yaş altı çocuklardan bilerek veri toplamaz
(zaten hiç veri toplamaz).

## 7. Değişiklikler

Bu politika güncellenirse değişiklik tarihi yukarıda güncellenir ve depoda
(`github.com/Btmcode/Ghost-Pilot`) yayımlanır.

## 8. İletişim

**E-posta:** [devcloudpy@gmail.com](mailto:devcloudpy@gmail.com)

Sorularınız için GitHub üzerinden de konu açabilirsiniz:
[github.com/Btmcode/Ghost-Pilot/issues](https://github.com/Btmcode/Ghost-Pilot/issues)

---

*GhostPilot MIT lisanslı açık kaynak yazılımdır. Copyright (c) 2026 BTM Code.*

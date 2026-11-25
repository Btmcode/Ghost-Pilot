# 👻 GhostPilot

> **Your real computer, not a sandbox.** · **Gerçek bilgisayarınız, sandbox değil.**

GhostPilot connects ChatGPT, Claude, Cursor and any MCP-compatible assistant to **your own machine** — so the assistant can read your files, run your commands and see the result. No cloud, no upload, no sandbox.

<!-- LANGUAGE SWITCHER -->
**[English](#-english)** · **[Türkçe](#-türkçe)** · **[Deutsch](#-deutsch)** · **[Español](#-español)** · **[中文](#-中文)** · **[日本語](#-日本語)**

---

## Badges

![Version](https://img.shields.io/badge/version-5.16.0-22d3ee)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Tools](https://img.shields.io/badge/tools-44-f59e0b)
![Platforms](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Free](https://img.shields.io/badge/free-20.000%20calls%2Fmonth-success)
![Dependencies](https://img.shields.io/badge/dependencies-zero-black)

---

# 🇬🇧 English

## What is GhostPilot?

GhostPilot is a local **MCP (Model Context Protocol) server**. It runs on your computer and gives your chat assistant 44 real tools: files, terminal, screen, mouse and keyboard — plus an on-screen ghost cursor so you can see exactly what is happening.

**Nothing leaves your machine.** The assistant connects directly to `localhost` (or through an optional Tailscale tunnel for phone access). No third-party cloud, no telemetry, no account.

## Why not a cloud agent?

| | Cloud agent | **GhostPilot** |
|---|---|---|
| Where it runs | Vendor's sandbox | **Your own computer** |
| Sees your files | Uploaded copies | **The real files** |
| Sees your programs | No | **Yes — every installed app** |
| Your data | Leaves your device | **Stays on your device** |
| Works offline | No | **Yes** |

## Features

- **44 tools** — read/write/edit files, glob, grep, shell, processes, screenshots, click, drag, type, hotkeys, clipboard, windows, documents (docx/xlsx/pptx/pdf), scheduled tasks
- **Visible agent** — a ghost cursor shows where the work happens; your own mouse never moves
- **Approval screen** — risky actions (delete, shell) wait for your click
- **Read-only mode** — one switch, nothing can be changed
- **Works alongside you** — the assistant types while you keep working
- **Scheduled tasks** — "every day at 09:30, clean the downloads folder"
- **4 languages** — Turkish, English, German, Spanish
- **Zero dependencies** — pure Python standard library; no pip install required
- **One-click uninstall** — removes itself from the Apps list

## Quick start (5 minutes)

### 1. Python — installed for you (Windows)

**On Windows you do not need to install Python.** `KURULUM.bat` checks for Python 3.9+ and, if it is missing, downloads the official installer from python.org and installs it automatically (per-user, no admin rights). This can take 5–10 minutes on the first run.

**macOS / Linux:** install Python 3.9+ first — `brew install python3` or `sudo apt install -y python3 python3-venv python3-pip`.

### 2. Run the installer

| Platform | Do this |
|---|---|
| **Windows** | Unzip → double-click **`KURULUM.bat`** |
| **macOS** | Unzip → double-click **`kurulum_macos.command`** |
| **Linux** | Unzip → `./kurulum.sh` |

The installer asks **where** to install, creates a private environment, adds a desktop shortcut and registers GhostPilot in your Apps list. It takes about 30 seconds.

> **Tip:** Do not unzip into `C:\Program Files` — pick something like `D:\GhostPilot` or your Desktop.

### 3. Start GhostPilot

Double-click the ghost shortcut on your desktop — or run:

```bash
python kur.py basla
```

A panel opens. Keep it running while you work.

### 4. Connect your assistant

#### ChatGPT (custom connector)

1. Open **ChatGPT** → **Settings** → **Connectors** → **Advanced** → enable **Developer mode**
2. Click **Create** / **Add custom connector**
3. Fill in:
   - **Name:** `GhostPilot`
   - **URL:** the address GhostPilot shows in its panel, e.g. `http://127.0.0.1:17381/mcp`
   - **Authentication:** `No authentication` (local) or `API key` → paste the access key from the panel
4. Save, then start a chat and ask: *"What can you do on my computer?"*

> **Using ChatGPT on the web (not desktop)?** `127.0.0.1` on a website points to OpenAI's server, not your PC. Use the Tailscale tunnel GhostPilot offers (`python kur.py tunel`) and paste the public HTTPS address instead.

#### Claude Desktop

1. Open `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
2. Add:

```json
{
  "mcpServers": {
    "ghostpilot": {
      "command": "python",
      "args": ["C:\\GhostPilot\\ghostpilot.py", "bridge"]
    }
  }
}
```

3. Restart Claude Desktop. The tools appear under the hammer icon.

#### Cursor / Windsurf / other MCP clients

Point them at `python ghostpilot.py bridge` (stdio) or `http://127.0.0.1:17381/mcp` (HTTP).

### 5. Check it works

Ask your assistant:

> *"Use ghostpilot_status and tell me what you can do here."*

It should answer with the tool list and your machine name.

## Usage

```bash
python kur.py basla          # start + open panel
python kur.py durum          # is it running?
python kur.py doktor         # diagnose the installation
python kur.py kota           # this month's usage
python kur.py lisans         # plan status
python kur.py hata           # son hata kaydı (çökme varsa)
python kur.py dur         # emergency stop — nothing can reach your PC
```

Inside a chat, just ask in plain language:

- *"Organise my Downloads folder by file type"*
- *"Read report.docx and summarise the risks"*
- *"Every day at 18:00, back up Documents to D:\Backup"*
- *"How many calls do I have left this month?"*

## Free plan and support key

| Plan | Scope | Price |
|---|---|---|
| **Free** | **20,000 tool calls per month** | 0 |
| **Support key** | Unlimited | **$10 / month** or **$96 / year** |

**Counting rules — no surprises:**

| Situation | Counted? |
|---|---|
| Successful tool call | ✅ |
| Command that returns an error | ✅ |
| **Call that times out** | ❌ (refunded) |
| Dropped connection | ❌ |
| Status queries (`ghostpilot_status`, `kota_durumu`, `machine`, `schedule_list`) | ❌ |

The counter resets on the **1st of each month, 00:00 UTC**. At **80%** you get a warning in the panel and in chat. Ask *"How much usage do I have left?"* any time.

> GhostPilot is donation-funded, not sold. A support key unlocks unlimited calls; it is never required to keep using the free plan. For comparison: Desktop Commander gives 10,000 calls/month and charges $20/month for unlimited. GhostPilot gives **twice the free calls at half the price**.

## Configuration

Settings live in `~/.ghostpilot/config.json`:

```json
{
  "port": 17381,
  "token": "auto-generated",
  "read_only": false,
  "onay": "riskli",
  "read_roots": ["C:\\Users\\you"],
  "write_roots": ["C:\\Users\\you\\Documents"]
}
```

| Key | Meaning |
|---|---|
| `port` | Local port (default 17381) |
| `read_only` | `true` → nothing can be modified |
| `onay` | `"riskli"` = ask before risky actions, `"hic"` = never ask, `"hepsi"` = ask for everything |
| `read_roots` / `write_roots` | Folder allow-lists |

## Security

- **Nothing is exposed by default.** No open access without an access key.
- **Local only** unless you explicitly start the tunnel.
- **Approval screen** for delete/shell unless you turn it off.
- **Read-only mode** for read-only work.
- **Audit log** at `~/.ghostpilot/audit.log` records every call.
- **Emergency stop:** `python kur.py dur` — the server refuses every connection.

> **Honest note:** the source is open and runs on your machine. Someone who edits the source can always remove limits. The layers above make that a lot of work — not impossible.

See [SECURITY.md](SECURITY.md) · [PRIVACY](GIZLILIK.md) · [TERMS](KOSULLAR.md)

## FAQ

**Does it work with the ChatGPT desktop app?** Yes — `127.0.0.1` URLs work there, no tunnel needed.

**Will it do something without asking?** Only read-only actions. Deleting, shell commands and screen clicks ask first (unless you change the mode).

**Can I use it from my phone?** Yes, with Tailscale: `python kur.py tunel` gives a private HTTPS address.

**Is there a subscription?** No. Free plan, forever. A support key is a donation-based extra, not a requirement.

**The window opens and closes instantly.** Run `python kur.py hata` — every crash is written to `~/.ghostpilot/hata.log` with the file, line and error. Send that text to the developer.

**What if a call fails?** Failed and timed-out calls are refunded to your quota.

## Contributing

Issues and pull requests are welcome. Keep the code dependency-free (standard library only) and add user-facing strings in all four languages (`diller.py`).

```bash
git clone https://github.com/Btmcode/Ghost-Pilot.git
cd Ghost-Pilot
python kur.py basla
```

## Support the project

| | |
|---|---|
| ☕ Buy me a coffee | [buymeacoffee.com/btmcode](https://buymeacoffee.com/btmcode) |
| 🌐 Website | [btmcode.vercel.app](https://btmcode.vercel.app) |
| 💬 Issues | [GitHub Issues](https://github.com/Btmcode/Ghost-Pilot/issues) |

## License

MIT — see [LICENSE](LICENSE).

---

# 🇹🇷 Türkçe

## GhostPilot nedir?

GhostPilot, bilgisayarınızda çalışan yerel bir **MCP sunucusudur**. ChatGPT, Claude, Cursor gibi sohbet programlarına **44 gerçek araç** verir: dosyalar, terminal, ekran, fare ve klavye. Üstelik ekranda bir **hayalet imleç** hareket eder — ne yapıldığını gözünüzle görürsünüz.

**Hiçbir veri bilgisayarınızdan çıkmaz.** Sohbet programı doğrudan `localhost`'a bağlanır. Üçüncü taraf bulut yok, telemetri yok, hesap yok.

## Neden bulut ajanı değil?

| | Bulut ajanı | **GhostPilot** |
|---|---|---|
| Nerede çalışır | Satıcının sandbox'ı | **Sizin bilgisayarınız** |
| Dosyalarınızı görür | Yüklenmiş kopyaları | **Gerçek dosyaları** |
| Programlarınızı görür | Hayır | **Evet — kurulu her program** |
| Veriniz | Cihazınızdan çıkar | **Cihazınızda kalır** |
| İnternetsiz çalışır | Hayır | **Evet** |

## Özellikler

- **44 araç** — dosya okuma/yazma/düzenleme, glob, grep, terminal, süreçler, ekran görüntüsü, tıklama, sürükleme, yazma, kısayol tuşları, pano, pencereler, belgeler (docx/xlsx/pptx/pdf), zamanlanmış görevler
- **Görünür ajan** — hayalet imleç işin nerede olduğunu gösterir; sizin fareniz oynamaz
- **Onay ekranı** — riskli işlemler (silme, terminal) sizin onayınızı bekler
- **Salt okunur mod** — tek anahtar, hiçbir şey değiştirilemez
- **Sizinle birlikte çalışır** — siz çalışırken asistan da yazabilir
- **Zamanlanmış görevler** — "her gün 09:30'da indirilenleri düzenle"
- **4 dil** — Türkçe, İngilizce, Almanca, İspanyolca
- **Sıfır bağımlılık** — saf Python standart kütüphanesi; pip kurulumu gerekmez
- **Tek tık kaldırma** — Programlar listesinden kendini siler

## Hızlı başlangıç (5 dakika)

### 1. Python — kendisi kuruyor (Windows)

**Windows'ta Python kurmanız gerekmez.** `KURULUM.bat` önce Python 3.9+ var mı diye bakar; yoksa python.org'un resmi kurulum dosyasını indirip kendisi kurar (yalnız sizin kullanıcınız için, yönetici izni gerekmez). İlk seferde 5–10 dakika sürebilir.

**macOS / Linux:** önce Python 3.9+ kurun — `brew install python3` veya `sudo apt install -y python3 python3-venv python3-pip`.

### 2. Kurulumu çalıştırın

| Platform | Ne yapmalı |
|---|---|
| **Windows** | Zip'i açın → **`KURULUM.bat`** dosyasına çift tıklayın |
| **macOS** | Zip'i açın → `kurulum_macos.command` dosyasına çift tıklayın |
| **Linux** | Zip'i açın → `./kurulum.sh` |

Kurulum **nereye** kurmak istediğinizi sorar, kendi sanal ortamını oluşturur, masaüstüne kısayol ekler ve Programlar listesine kaydeder. Yaklaşık 30 saniye.

> **İpucu:** `C:\Program Files` altına açmayın — `D:\GhostPilot` veya Masaüstü idealdir.

### 3. GhostPilot'u başlatın

Masaüstündeki 👻 kısayola çift tıklayın — veya:

```bash
python kur.py basla
```

Bir panel açılır. Çalışırken açık kalsın.

### 4. Sohbet programını bağlayın

#### ChatGPT (özel bağlayıcı)

1. **ChatGPT** → **Ayarlar** → **Bağlayıcılar** (Connectors) → **Gelişmiş** → **Geliştirici modu**'nu açın
2. **Oluştur** / **Özel bağlayıcı ekle**'ye tıklayın
3. Doldurun:
   - **Ad:** `GhostPilot`
   - **Adres:** panelde yazan adres, örn. `http://127.0.0.1:17381/mcp`
   - **Kimlik doğrulama:** `Kimlik doğrulama yok` (yerel) veya `API anahtarı` → paneldeki erişim anahtarını yapıştırın
4. Kaydedin, yeni sohbet açın ve sorun: *"Bilgisayarımda neler yapabilirsin?"*

> **ChatGPT'yi tarayıcıda kullanıyorsanız:** `127.0.0.1` web sitesinde OpenAI'nin sunucusunu gösterir, sizin PC'nizi değil. GhostPilot'un sunduğu Tailscale tünelini açın (`python kur.py tunel`) ve size verilen HTTPS adresini yapıştırın.

#### Claude Desktop

1. `%APPDATA%\Claude\claude_desktop_config.json` (Windows) veya `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) dosyasını açın
2. Ekleyin:

```json
{
  "mcpServers": {
    "ghostpilot": {
      "command": "python",
      "args": ["C:\\GhostPilot\\ghostpilot.py", "bridge"]
    }
  }
}
```

3. Claude Desktop'ı yeniden başlatın. Araçlar çekiç simgesinin altında görünür.

#### Cursor / Windsurf / diğer MCP programları

`python ghostpilot.py bridge` (stdio) veya `http://127.0.0.1:17381/mcp` (HTTP) adresini verin.

### 5. Çalıştığını kontrol edin

Asistana sorun:

> *"ghostpilot_status aracını kullan ve burada neler yapabildiğini söyle."*

Araç listesini ve makine adınızı söylemelidir.

## Kullanım

```bash
python kur.py basla          # başlat + paneli aç
python kur.py durum          # çalışıyor mu?
python kur.py doktor         # kurulumu denetle
python kur.py kota           # bu ayki kullanım
python kur.py lisans         # paket durumu
python kur.py dur            # acil durdur — hiçbir şey PC'nize ulaşamaz
```

Sohbette normal cümleyle sorun:

- *"İndirilenler klasörümü dosya türüne göre düzenle"*
- *"rapor.docx dosyasını oku ve riskleri özetle"*
- *"Her gün 18:00'de Belgeler'i D:\Yedek'e yedekle"*
- *"Bu ay kaç çağrı hakkım kaldı?"*

## Ücretsiz plan ve destek anahtarı

| Plan | Kapsam | Fiyat |
|---|---|---|
| **Ücretsiz** | **Ayda 20.000 araç çağrısı** | 0 |
| **Destek anahtarı** | Sınırsız | **$10 / ay** veya **$96 / yıl** |

**Sayım kuralları — sürpriz yok:**

| Durum | Sayılır mı? |
|---|---|
| Başarılı araç çağrısı | ✅ |
| Hata dönen komut | ✅ |
| **Zaman aşımına uğrayan çağrı** | ❌ (geri alınır) |
| Bağlantı kopması | ❌ |
| Durum sorguları (`ghostpilot_status`, `kota_durumu`, `machine`, `schedule_list`) | ❌ |

Sayaç **her ayın 1'inde 00:00 UTC** sıfırlanır. **%80**'e gelince panelde ve sohbette uyarı çıkar. İstediğiniz an *"Ne kadar kullanım hakkım kaldı?"* diye sorabilirsiniz.

> GhostPilot bağışla sürdürülür, satılmaz. Destek anahtarı sınırsız çağrı açar; ücretsiz planı kullanmak için hiç gerekmez. Karşılaştırma: Desktop Commander ayda 10.000 çağrı verir, sınırsız için $20/ay ister. GhostPilot **iki kat ücretsiz çağrıyı yarı fiyata** verir.

## Ayarlar

Ayarlar `~/.ghostpilot/config.json` dosyasında:

```json
{
  "port": 17381,
  "token": "otomatik üretilir",
  "read_only": false,
  "onay": "riskli",
  "read_roots": ["C:\\Users\\siz"],
  "write_roots": ["C:\\Users\\siz\\Belgeler"]
}
```

| Anahtar | Anlamı |
|---|---|
| `port` | Yerel port (varsayılan 17381) |
| `read_only` | `true` → hiçbir şey değiştirilemez |
| `onay` | `"riskli"` = riskli işlemlerde sor, `"hic"` = hiç sorma, `"hepsi"` = hepsinde sor |
| `read_roots` / `write_roots` | İzin verilen klasörler |

## Güvenlik

- **Varsayılan olarak hiçbir şey açık değildir.** Erişim anahtarı olmadan tek istek geçmez.
- **Yalnız yerel** — tüneli siz açmadıkça dışarıya kapalı.
- **Onay ekranı** — silme/terminal için (isterseniz kapatılabilir).
- **Salt okunur mod** — yalnız okuma işleri için.
- **Denetim günlüğü** — `~/.ghostpilot/audit.log` her çağrıyı yazar.
- **Acil durdurma:** `python kur.py dur` — sunucu her bağlantıyı reddeder.

> **Dürüst not:** kaynak açık ve program sizin bilgisayarınızda. Kaynağı değiştiren biri sınırları her zaman kaldırabilir. Yukarıdaki katmanlar bunu zahmetli yapar — imkânsız değil.

Bkz. [GIZLILIK.md](GIZLILIK.md) · [KOSULLAR.md](KOSULLAR.md)

## Sık sorulan

**ChatGPT masaüstü uygulamasıyla çalışır mı?** Evet — `127.0.0.1` adresleri orada çalışır, tünel gerekmez.

**Sormadan bir şey yapar mı?** Yalnız okuma işlemleri. Silme, terminal ve ekran tıklamaları önce onay ister (modu değiştirmediyseniz).

**Telefonumdan kullanabilir miyim?** Evet, Tailscale ile: `python kur.py tunel` size özel bir HTTPS adresi verir.

**Abonelik var mı?** Yok. Ücretsiz plan süresiz. Destek anahtarı bağışa dayalı bir ekstra, zorunluluk değil.

**Pencere açılıp hemen kapanıyor.** `python kur.py hata` komutunu çalıştırın — her çökme dosya, satır ve hata adıyla `~/.ghostpilot/hata.log` içine yazılır. O metni geliştiriciye gönderin.

**Çağrı başarısız olursa?** Başarısız ve zaman aşımına uğrayan çağrılar kotanıza geri eklenir.

## Katkı

Hata bildirimi ve katkı memnuniyetle karşılanır. Kodu bağımlılıksız tutun (yalnız standart kütüphane) ve kullanıcıya görünen metinleri dört dile de ekleyin (`diller.py`).

```bash
git clone https://github.com/Btmcode/Ghost-Pilot.git
cd Ghost-Pilot
python kur.py basla
```

## Projeyi destekleyin

| | |
|---|---|
| ☕ Bir kahve | [buymeacoffee.com/btmcode](https://buymeacoffee.com/btmcode) |
| 🌐 Web sitesi | [btmcode.vercel.app](https://btmcode.vercel.app) |
| 💬 Sorunlar | [GitHub Issues](https://github.com/Btmcode/Ghost-Pilot/issues) |

## Lisans

MIT — bkz. [LICENSE](LICENSE).

---

# 🇩🇪 Deutsch

## Was ist GhostPilot?

GhostPilot ist ein lokaler **MCP-Server**. Er läuft auf Ihrem Computer und gibt Ihrem Chat-Assistenten **44 echte Werkzeuge**: Dateien, Terminal, Bildschirm, Maus und Tastatur. Ein Geister-Cursor zeigt auf dem Bildschirm, was gerade passiert.

**Nichts verlässt Ihren Rechner.** Der Assistent verbindet sich direkt mit `localhost`. Keine fremde Cloud, keine Telemetrie, kein Konto.

## Warum kein Cloud-Agent?

| | Cloud-Agent | **GhostPilot** |
|---|---|---|
| Läuft auf | Sandbox des Anbieters | **Ihrem Computer** |
| Sieht Ihre Dateien | Hochgeladene Kopien | **Die echten Dateien** |
| Sieht Ihre Programme | Nein | **Ja — jedes installierte Programm** |
| Ihre Daten | Verlassen das Gerät | **Bleiben auf dem Gerät** |
| Offline nutzbar | Nein | **Ja** |

## Funktionen

- **44 Werkzeuge** — Dateien lesen/schreiben/bearbeiten, glob, grep, Terminal, Prozesse, Bildschirmfotos, Klicken, Ziehen, Tippen, Tastenkürzel, Zwischenablage, Fenster, Dokumente (docx/xlsx/pptx/pdf), geplante Aufgaben
- **Sichtbarer Agent** — ein Geister-Cursor zeigt die Stelle; Ihre eigene Maus bleibt stehen
- **Bestätigungsfenster** — riskante Aktionen (Löschen, Terminal) warten auf Ihren Klick
- **Nur-Lesen-Modus** — ein Schalter, nichts kann geändert werden
- **Arbeitet parallel mit Ihnen** — der Assistent tippt, während Sie weiterarbeiten
- **Geplante Aufgaben** — „täglich 09:30 Uhr Downloads aufräumen"
- **4 Sprachen** — Türkisch, Englisch, Deutsch, Spanisch
- **Keine Abhängigkeiten** — reine Python-Standardbibliothek
- **Ein-Klick-Deinstallation** — entfernt sich aus der App-Liste

## Schnellstart (5 Minuten)

### 1. Python — wird mitinstalliert (Windows)

**Unter Windows müssen Sie Python nicht selbst installieren.** `KURULUM.bat` prüft auf Python 3.9+ und lädt bei Bedarf das offizielle Installationsprogramm von python.org herunter (nur für Ihren Benutzer, keine Administratorrechte nötig). Beim ersten Mal 5–10 Minuten.

**macOS / Linux:** Python 3.9+ vorher installieren — `brew install python3` bzw. `sudo apt install -y python3 python3-venv python3-pip`.

### 2. Installer starten

| Plattform | Vorgehen |
|---|---|
| **Windows** | Entpacken → **`KURULUM.bat`** doppelklicken |
| **macOS** | Entpacken → `kurulum_macos.command` doppelklicken |
| **Linux** | Entpacken → `./kurulum.sh` |

Der Installer fragt nach dem **Zielordner**, legt eine eigene Umgebung an, erstellt eine Desktop-Verknüpfung und trägt GhostPilot in die App-Liste ein. Etwa 30 Sekunden.

### 3. GhostPilot starten

Desktop-Verknüpfung (👻) doppelklicken — oder:

```bash
python kur.py basla
```

Ein Fenster öffnet sich. Lassen Sie es beim Arbeiten offen.

### 4. Assistenten verbinden

#### ChatGPT (eigener Connector)

1. **ChatGPT** → **Einstellungen** → **Connectors** → **Erweitert** → **Entwicklermodus** aktivieren
2. **Erstellen** / **Eigenen Connector hinzufügen**
3. Eintragen:
   - **Name:** `GhostPilot`
   - **URL:** die Adresse aus dem Panel, z. B. `http://127.0.0.1:17381/mcp`
   - **Authentifizierung:** `Keine Authentifizierung` (lokal) oder `API-Schlüssel` → Zugangsschlüssel aus dem Panel einfügen
4. Speichern, neuen Chat starten und fragen: *„Was kannst du auf meinem Computer tun?"*

> **ChatGPT im Browser?** `127.0.0.1` zeigt dort auf OpenAIs Server, nicht auf Ihren PC. Nutzen Sie den Tailscale-Tunnel (`python kur.py tunel`) und die öffentliche HTTPS-Adresse.

#### Claude Desktop

```json
{
  "mcpServers": {
    "ghostpilot": {
      "command": "python",
      "args": ["C:\\GhostPilot\\ghostpilot.py", "bridge"]
    }
  }
}
```

Datei: `%APPDATA%\Claude\claude_desktop_config.json` (Windows) bzw.
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS). Danach Claude Desktop neu starten.

### 5. Prüfen

Fragen Sie: *„Nutze ghostpilot_status und sage mir, was hier möglich ist."*

## Nutzung

```bash
python kur.py basla          # starten + Panel öffnen
python kur.py durum          # läuft es?
python kur.py doktor         # Installation prüfen
python kur.py kota           # Nutzung dieses Monats
python kur.py lisans         # Paketstatus
python kur.py dur            # Not-Aus — nichts erreicht Ihren PC
```

## Kostenloser Plan und Support-Schlüssel

| Plan | Umfang | Preis |
|---|---|---|
| **Kostenlos** | **20.000 Werkzeugaufrufe pro Monat** | 0 |
| **Support-Schlüssel** | Unbegrenzt | **10 $ / Monat** oder **96 $ / Jahr** |

| Situation | Gezählt? |
|---|---|
| Erfolgreicher Aufruf | ✅ |
| Befehl mit Fehler | ✅ |
| **Zeitüberschreitung** | ❌ (zurückerstattet) |
| Verbindungsabbruch | ❌ |
| Statusabfragen | ❌ |

Der Zähler wird am **1. jedes Monats um 00:00 UTC** zurückgesetzt. Bei **80 %** erscheint eine Warnung im Panel und im Chat.

## Sicherheit

- **Standardmäßig nichts offen.** Ohne Zugangsschlüssel geht keine Anfrage durch.
- **Nur lokal** — ohne Tunnel von außen unerreichbar.
- **Bestätigungsfenster** für Löschen/Terminal.
- **Nur-Lesen-Modus** und **Prüfprotokoll** (`~/.ghostpilot/audit.log`).
- **Not-Aus:** `python kur.py dur`.

> **Ehrlicher Hinweis:** Der Quellcode ist offen und läuft auf Ihrem Rechner. Wer den Code ändert, kann Grenzen entfernen. Die Schichten oben machen das aufwendig — nicht unmöglich.

## Lizenz

MIT — siehe [LICENSE](LICENSE).

---

# 🇪🇸 Español

## ¿Qué es GhostPilot?

GhostPilot es un **servidor MCP local**. Se ejecuta en tu ordenador y da a tu asistente **44 herramientas reales**: archivos, terminal, pantalla, ratón y teclado. Un cursor fantasma en pantalla muestra lo que está ocurriendo.

**Nada sale de tu ordenador.** El asistente se conecta directamente a `localhost`. Sin nube de terceros, sin telemetría, sin cuenta.

## ¿Por qué no un agente en la nube?

| | Agente en la nube | **GhostPilot** |
|---|---|---|
| Dónde se ejecuta | Sandbox del proveedor | **Tu ordenador** |
| Ve tus archivos | Copias subidas | **Los archivos reales** |
| Ve tus programas | No | **Sí — todos los instalados** |
| Tus datos | Salen del dispositivo | **Se quedan en él** |
| Funciona sin internet | No | **Sí** |

## Funciones

- **44 herramientas** — leer/escribir/editar archivos, glob, grep, terminal, procesos, capturas, clic, arrastrar, escribir, atajos, portapapeles, ventanas, documentos (docx/xlsx/pptx/pdf), tareas programadas
- **Agente visible** — un cursor fantasma muestra dónde ocurre el trabajo; tu ratón no se mueve
- **Pantalla de aprobación** — las acciones de riesgo esperan tu clic
- **Modo solo lectura** — un interruptor y nada se puede modificar
- **Trabaja a tu lado** — escribe mientras tú sigues trabajando
- **Tareas programadas** — «cada día a las 09:30, ordena Descargas»
- **4 idiomas** — turco, inglés, alemán, español
- **Cero dependencias** — solo biblioteca estándar de Python
- **Desinstalación en un clic**

## Inicio rápido (5 minutos)

### 1. Python — se instala solo (Windows)

**En Windows no necesitas instalar Python.** `KURULUM.bat` comprueba si hay Python 3.9+ y, si falta, descarga el instalador oficial de python.org y lo instala automáticamente (solo para tu usuario, sin permisos de administrador). La primera vez tarda 5–10 minutos.

**macOS / Linux:** instala Python 3.9+ antes — `brew install python3` o `sudo apt install -y python3 python3-venv python3-pip`.

### 2. Ejecuta el instalador

| Plataforma | Qué hacer |
|---|---|
| **Windows** | Descomprime → doble clic en **`KURULUM.bat`** |
| **macOS** | Descomprime → doble clic en `kurulum_macos.command` |
| **Linux** | Descomprime → `./kurulum.sh` |

El instalador pregunta **dónde** instalar, crea un entorno privado, añade un acceso directo y registra GhostPilot en la lista de aplicaciones. Unos 30 segundos.

### 3. Inicia GhostPilot

Doble clic en el acceso directo 👻 — o:

```bash
python kur.py basla
```

### 4. Conecta tu asistente

#### ChatGPT (conector personalizado)

1. **ChatGPT** → **Ajustes** → **Conectores** → **Avanzado** → activa **Modo desarrollador**
2. **Crear** / **Añadir conector personalizado**
3. Rellena:
   - **Nombre:** `GhostPilot`
   - **URL:** la dirección del panel, p. ej. `http://127.0.0.1:17381/mcp`
   - **Autenticación:** `Sin autenticación` (local) o `Clave API` → pega la clave del panel
4. Guarda, abre un chat nuevo y pregunta: *«¿Qué puedes hacer en mi ordenador?»*

> **¿ChatGPT en el navegador?** `127.0.0.1` apunta al servidor de OpenAI, no a tu PC. Usa el túnel de Tailscale (`python kur.py tunel`) y la dirección HTTPS pública.

#### Claude Desktop

```json
{
  "mcpServers": {
    "ghostpilot": {
      "command": "python",
      "args": ["C:\\GhostPilot\\ghostpilot.py", "bridge"]
    }
  }
}
```

Archivo: `%APPDATA%\Claude\claude_desktop_config.json` (Windows) o
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS). Reinicia Claude Desktop.

### 5. Comprueba

Pregunta: *«Usa ghostpilot_status y dime qué puedo hacer aquí.»*

## Uso

```bash
python kur.py basla          # iniciar + abrir panel
python kur.py durum          # ¿está funcionando?
python kur.py doktor         # diagnosticar la instalación
python kur.py kota           # uso de este mes
python kur.py lisans         # estado del plan
python kur.py dur            # parada de emergencia
```

## Plan gratuito y clave de apoyo

| Plan | Alcance | Precio |
|---|---|---|
| **Gratis** | **20.000 llamadas al mes** | 0 |
| **Clave de apoyo** | Ilimitado | **10 $/mes** o **96 $/año** |

| Situación | ¿Cuenta? |
|---|---|
| Llamada correcta | ✅ |
| Comando con error | ✅ |
| **Llamada con tiempo agotado** | ❌ (se devuelve) |
| Conexión cortada | ❌ |
| Consultas de estado | ❌ |

El contador se reinicia el **día 1 de cada mes a las 00:00 UTC**. Al **80 %** verás un aviso en el panel y en el chat.

## Seguridad

- **Nada expuesto por defecto.** Sin clave de acceso no pasa ninguna petición.
- **Solo local** salvo que actives el túnel.
- **Pantalla de aprobación** para borrar/terminal.
- **Modo solo lectura** y **registro de auditoría** (`~/.ghostpilot/audit.log`).
- **Parada de emergencia:** `python kur.py dur`.

> **Nota honesta:** el código es abierto y se ejecuta en tu ordenador. Quien modifique el código puede quitar los límites. Las capas anteriores lo hacen costoso — no imposible.

## Licencia

MIT — ver [LICENSE](LICENSE).

---

# 🇨🇳 中文

## GhostPilot 是什么？

GhostPilot 是一个本地 **MCP 服务器**。它运行在你的电脑上，为你的聊天助手提供 **44 个真实工具**：文件、终端、屏幕、鼠标和键盘。屏幕上会显示一个幽灵光标，让你看到正在发生什么。

**数据不会离开你的电脑。** 助手直接连接到 `localhost`。没有第三方云、没有遥测、不需要账号。

## 功能

- **44 个工具** — 读写编辑文件、glob、grep、终端、进程、截图、点击、拖拽、输入、快捷键、剪贴板、窗口、文档（docx/xlsx/pptx/pdf）、定时任务
- **可见的执行** — 幽灵光标显示操作位置，你自己的鼠标不会移动
- **确认窗口** — 危险操作（删除、终端）需要你点击确认
- **只读模式** — 一个开关，任何内容都无法修改
- **与你同时工作** — 助手打字时你可以继续工作
- **四种语言** — 土耳其语、英语、德语、西班牙语
- **零依赖** — 仅使用 Python 标准库
- **一键卸载**

## 快速开始

### 1. Python —— 自动安装（Windows）

**Windows 上你不需要自己安装 Python。** `KURULUM.bat` 会先检查是否已有 Python 3.9+，没有就从 python.org 下载官方安装程序并自动安装（仅当前用户，无需管理员权限）。首次可能需要 5–10 分钟。

**macOS / Linux:** 请先安装 Python 3.9+ —— `brew install python3` 或 `sudo apt install -y python3 python3-venv python3-pip`。

### 2. 运行安装程序

| 平台 | 操作 |
|---|---|
| **Windows** | 解压 → 双击 **`KURULUM.bat`** |
| **macOS** | 解压 → 双击 `kurulum_macos.command` |
| **Linux** | 解压 → `./kurulum.sh` |

安装程序会询问**安装位置**，创建独立环境，添加桌面快捷方式并注册到应用列表。约 30 秒。

### 3. 启动 GhostPilot

双击桌面上的 👻 快捷方式，或运行：

```bash
python kur.py basla
```

### 4. 连接你的助手

#### ChatGPT（自定义连接器）

1. **ChatGPT** → **设置** → **连接器** → **高级** → 开启 **开发者模式**
2. 点击 **创建** / **添加自定义连接器**
3. 填写：
   - **名称：** `GhostPilot`
   - **URL：** 面板显示的地址，例如 `http://127.0.0.1:17381/mcp`
   - **身份验证：** `无身份验证`（本地）或 `API 密钥` → 粘贴面板中的访问密钥
4. 保存后开始新对话并提问：*「你能在我的电脑上做什么？」*

> **在浏览器中使用 ChatGPT？** 在网页中 `127.0.0.1` 指向 OpenAI 的服务器，而不是你的电脑。请使用 Tailscale 隧道（`python kur.py tunel`）提供的 HTTPS 地址。

#### Claude Desktop

```json
{
  "mcpServers": {
    "ghostpilot": {
      "command": "python",
      "args": ["C:\\GhostPilot\\ghostpilot.py", "bridge"]
    }
  }
}
```

配置文件：`%APPDATA%\Claude\claude_desktop_config.json`（Windows）或
`~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）。修改后重启 Claude Desktop。

## 使用

```bash
python kur.py basla          # 启动并打开面板
python kur.py durum          # 是否运行中
python kur.py doktor         # 诊断安装
python kur.py kota           # 本月用量
python kur.py lisans         # 套餐状态
python kur.py dur            # 紧急停止
```

## 免费额度与支持密钥

| 套餐 | 范围 | 价格 |
|---|---|---|
| **免费** | **每月 20,000 次工具调用** | 0 |
| **支持密钥** | 无限 | **10 美元/月** 或 **96 美元/年** |

| 情况 | 是否计数 |
|---|---|
| 成功的调用 | ✅ |
| 返回错误的命令 | ✅ |
| **超时的调用** | ❌（退回） |
| 连接中断 | ❌ |
| 状态查询 | ❌ |

计数器在**每月 1 日 00:00 UTC** 重置。达到 **80%** 时，面板和聊天中会出现提醒。

## 安全

- **默认不对外开放。** 没有访问密钥，任何请求都无法通过。
- **仅限本地**，除非你主动开启隧道。
- **确认窗口**用于删除/终端操作。
- **只读模式**和**审计日志**（`~/.ghostpilot/audit.log`）。
- **紧急停止：** `python kur.py dur`。

> **诚实说明：** 源代码是开放的，并且运行在你的电脑上。修改代码的人总能移除限制。上述措施让这变得麻烦——但并非不可能。

## 许可证

MIT — 见 [LICENSE](LICENSE)。

---

# 🇯🇵 日本語

## GhostPilot とは

GhostPilot はローカルで動作する **MCP サーバー**です。お使いのパソコン上で動き、チャットアシスタントに **44 の実際のツール**を提供します — ファイル、ターミナル、画面、マウス、キーボード。画面上にはゴーストカーソルが表示され、何が起きているかを目で確認できます。

**データはパソコンの外に出ません。** アシスタントは `localhost` に直接接続します。第三者のクラウドも、テレメトリーも、アカウントもありません。

## 主な機能

- **44 のツール** — ファイルの読み書き・編集、glob、grep、ターミナル、プロセス、スクリーンショット、クリック、ドラッグ、入力、ショートカット、クリップボード、ウィンドウ、文書（docx/xlsx/pptx/pdf）、スケジュールタスク
- **見えるエージェント** — ゴーストカーソルが作業位置を示します。あなた自身のマウスは動きません
- **承認画面** — 危険な操作（削除・ターミナル）はクリック承認が必要
- **読み取り専用モード** — スイッチひとつで何も変更できません
- **並行作業** — あなたが作業している間もアシスタントが入力できます
- **4 言語対応** — トルコ語・英語・ドイツ語・スペイン語
- **依存関係ゼロ** — Python 標準ライブラリのみ
- **ワンクリックでアンインストール**

## クイックスタート（5 分）

### 1. Python — 自動でインストール（Windows）

**Windows では Python を自分で入れる必要はありません。** `KURULUM.bat` が Python 3.9 以上を確認し、無ければ python.org の公式インストーラーをダウンロードして自動で導入します（現在のユーザーのみ、管理者権限不要）。初回は 5〜10 分かかることがあります。

**macOS / Linux:** 先に Python 3.9 以上をインストールしてください — `brew install python3` または `sudo apt install -y python3 python3-venv python3-pip`。

### 2. インストーラーを実行

| プラットフォーム | 操作 |
|---|---|
| **Windows** | 解凍 → **`KURULUM.bat`** をダブルクリック |
| **macOS** | 解凍 → `kurulum_macos.command` をダブルクリック |
| **Linux** | 解凍 → `./kurulum.sh` |

インストール先を尋ねられ、専用環境の作成、デスクトップショートカットの追加、アプリ一覧への登録まで約 30 秒で完了します。

### 3. GhostPilot を起動

デスクトップの 👻 ショートカットをダブルクリック、または:

```bash
python kur.py basla
```

### 4. アシスタントを接続

#### ChatGPT（カスタムコネクタ）

1. **ChatGPT** → **設定** → **コネクタ** → **詳細設定** → **開発者モード**をオン
2. **作成** / **カスタムコネクタを追加**
3. 入力:
   - **名前:** `GhostPilot`
   - **URL:** パネルに表示されるアドレス（例 `http://127.0.0.1:17381/mcp`）
   - **認証:** `認証なし`（ローカル）または `API キー` → パネルのアクセスキーを貼り付け
4. 保存して新しいチャットを開き、尋ねてください: *「このパソコンで何ができる？」*

> **ブラウザ版 ChatGPT の場合:** ウェブページ上の `127.0.0.1` は OpenAI のサーバーを指します。Tailscale トンネル（`python kur.py tunel`）の HTTPS アドレスを使用してください。

#### Claude Desktop

```json
{
  "mcpServers": {
    "ghostpilot": {
      "command": "python",
      "args": ["C:\\GhostPilot\\ghostpilot.py", "bridge"]
    }
  }
}
```

設定ファイル: `%APPDATA%\Claude\claude_desktop_config.json`（Windows）または
`~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）。変更後は Claude Desktop を再起動してください。

## 使い方

```bash
python kur.py basla          # 起動 + パネルを開く
python kur.py durum          # 動作確認
python kur.py doktor         # インストール診断
python kur.py kota           # 今月の使用量
python kur.py dur            # 緊急停止
```

## 無料プランとサポートキー

| プラン | 範囲 | 価格 |
|---|---|---|
| **無料** | **月 20,000 回のツール呼び出し** | 0 |
| **サポートキー** | 無制限 | **月 10 ドル** / **年 96 ドル** |

| 状況 | カウント |
|---|---|
| 成功した呼び出し | ✅ |
| エラーを返したコマンド | ✅ |
| **タイムアウトした呼び出し** | ❌（返還） |
| 接続切断 | ❌ |
| ステータス問い合わせ | ❌ |

カウンターは**毎月 1 日 00:00 UTC** にリセットされます。**80%** に達するとパネルとチャットに警告が表示されます。

## セキュリティ

- **既定では何も公開されません。** アクセスキーなしではリクエストは通りません。
- **ローカルのみ** — トンネルを自分で開かない限り外部から到達できません。
- **承認画面**（削除・ターミナル）、**読み取り専用モード**、**監査ログ**（`~/.ghostpilot/audit.log`）。
- **緊急停止:** `python kur.py dur`。

> **正直な注記:** ソースコードは公開され、お使いのパソコン上で動きます。コードを書き換えれば制限は取り除けます。上記の仕組みはそれを面倒にしますが、不可能にはしません。

## ライセンス

MIT — [LICENSE](LICENSE) を参照。

---

## 📄 Documents

| Document | |
|---|---|
| [LICENSE](LICENSE) | MIT license |
| [GIZLILIK.md](GIZLILIK.md) | Privacy policy (TR) |
| [KOSULLAR.md](KOSULLAR.md) | Terms of use (TR) |
| [SECURITY.md](SECURITY.md) | Security notes |

---

<p align="center">
<b>GhostPilot</b> — your real computer, not a sandbox.<br>
Made by <a href="https://btmcode.vercel.app">BTM Code</a>
</p>

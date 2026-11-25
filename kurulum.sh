#!/usr/bin/env bash
# ============================================================================
#  GhostPilot — kurulum.sh  ·  macOS + Linux kurulumu (tek komut)
#  Copyright (c) 2026 BTM Code — MIT License
#
#  Kullanım:
#      ./kurulum.sh                    → grafik kurulum (varsa) / konsol
#      ./kurulum.sh --hedef ~/GhostPilot
#      curl -fsSL <url>/kurulum.sh | bash
# ============================================================================
set -e
cd "$(dirname "$0")" 2>/dev/null || true

turkce() { printf '\033[92m%s\033[0m\n' "$1"; }
hata()   { printf '\033[91m%s\033[0m\n' "$1"; }
uyari()  { printf '\033[93m%s\033[0m\n' "$1"; }

echo ""
echo "  ============================================================"
echo "     GhostPilot — Kurulum"
echo "  ============================================================"
echo ""

# ---- 1) dosyalar yerinde mi
if [ ! -f ghostpilot.py ] || [ ! -f kurulum.py ] || [ ! -f lisans.py ]; then
  hata "  [HATA] Kurulum dosyaları bulunamadı."
  echo "  Zip'i açıp KLASÖRÜN İÇİNDEN çalıştırın:"
  echo "     unzip GhostPilot-MCP-*.zip && cd GhostPilot && ./kurulum.sh"
  exit 1
fi

# ---- 2) python bul (3.9+)
PY=""
for aday in python3.13 python3.12 python3.11 python3.10 python3 python; do
  if command -v "$aday" >/dev/null 2>&1; then
    if "$aday" -c 'import sys;sys.exit(0 if sys.version_info>=(3,9) else 1)' 2>/dev/null; then
      PY="$aday"; break
    fi
  fi
done

if [ -z "$PY" ]; then
  uyari "  Python 3.9+ bulunamadı."
  if [ "$(uname)" = "Darwin" ]; then
    echo "  Kurmak için:  brew install python3"
    echo "  (Homebrew yoksa: https://www.python.org/downloads/macos/)"
  else
    echo "  Kurmak için:"
    echo "     Debian/Ubuntu : sudo apt update && sudo apt install -y python3 python3-venv python3-pip"
    echo "     Fedora        : sudo dnf install -y python3 python3-pip"
    echo "     Arch          : sudo pacman -S python"
  fi
  exit 1
fi
turkce "  ✅ Python: $($PY --version 2>&1)"

# ---- 3) tkinter kontrolü (grafik kurulum için)
if ! "$PY" -c "import tkinter" >/dev/null 2>&1; then
  uyari "  ℹ️  tkinter yok — konsol kurulumu kullanılacak."
  if [ "$(uname)" != "Darwin" ]; then
    echo "     Grafik kurulum için: sudo apt install python3-tk"
  fi
  KONSOL="--konsol"
else
  KONSOL=""
fi

# ---- 4) kurulumu çalıştır
exec "$PY" kurulum.py $KONSOL "$@"

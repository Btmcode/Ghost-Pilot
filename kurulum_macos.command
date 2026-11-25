#!/bin/bash
# ============================================================================
#  GhostPilot — macOS çift tıklama kapısı (kurulum_macos.command)
#  Finder'da çift tıklayınca Terminal açılır ve kurulum kendiliğinden başlar.
# ============================================================================
cd "$(dirname "$0")" || exit 1
chmod +x kurulum.sh 2>/dev/null
./kurulum.sh "$@"

#!/usr/bin/env bash
# ============================================================================
#  push_github.sh — Ghost-Pilot deposunu GitHub'a gönderir
#
#  GÜVENLİK
#    · Token DISKE YAZILMAZ: .git/config'e, remote URL'sine, dosyaya girmez.
#    · Yalnız ortam değişkeni + git'in credential yardımcısı üzerinden
#      tek seferlik bellek içi kullanım.
#    · Push bittikten sonra token'ı GitHub'dan İPTAL EDİN.
#
#  KULLANIM
#    GIT_TOKEN=ghp_xxx ./push_github.sh
#      veya
#    ./push_github.sh            (token'ı sorar, ekranda görünmez)
# ============================================================================
set -u

REPO_URL="https://github.com/Btmcode/Ghost-Pilot.git"
DAL="main"

cd "$(dirname "$0")" || exit 1

if [ -z "${GIT_TOKEN:-}" ]; then
  printf "GitHub token (girdi gizli): "
  read -rs GIT_TOKEN
  echo
fi

if [ -z "${GIT_TOKEN:-}" ]; then
  echo "  ✗ Token boş — iptal."
  exit 1
fi

echo "  → yerel durum"
git log --oneline -1
git status --short | head -5

echo
echo "  → gönderiliyor: $DAL → $REPO_URL"
# token yalnız bu alt süreçte, yalnız bellekte
GIT_TERMINAL_PROMPT=0 \
git -c credential.helper='' \
    -c "http.https://github.com/.extraheader=Authorization: Basic $(printf 'x-access-token:%s' "$GIT_TOKEN" | base64 | tr -d '\n')" \
    push "$REPO_URL" "$DAL:$DAL" 2>&1 | tail -12
KOD=${PIPESTATUS[0]}

echo
if [ "$KOD" -eq 0 ]; then
  echo "  ✅ Push tamam."
  echo "     https://github.com/Btmcode/Ghost-Pilot"
  echo
  echo "  ⚠️  ŞİMDİ token'ı iptal edin:"
  echo "     https://github.com/settings/tokens"
else
  echo "  ✗ Push başarısız (kod $KOD)."
  echo "    · Token'ın 'Contents: Read and write' izni var mı?"
  echo "    · Token süresi dolmuş olabilir."
  echo "    · Uzakta korumalı dal kuralı olabilir."
fi
unset GIT_TOKEN
exit "$KOD"

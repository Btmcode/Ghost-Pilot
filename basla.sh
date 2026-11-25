#!/usr/bin/env bash
# ============================================================================
#  GhostPilot — basla.sh   ·   Linux / macOS menü kapısı
#  Python yoksa kendisi kurar (kurulum.sh'ı çağırır), sonra menüyü açar.
# ============================================================================
set -u
cd "$(dirname "$0")" || exit 1

PY=""
for aday in python3 python3.13 python3.12 python3.11 python3.10 python3.9 python; do
  if command -v "$aday" >/dev/null 2>&1 &&
     "$aday" -c 'import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)' 2>/dev/null; then
    PY="$aday"; break
  fi
done

if [ -z "$PY" ]; then
  echo
  echo "  Python bulunamadi. Once kurulum yapilacak."
  echo
  exec ./kurulum.sh
fi

exec "$PY" kur.py "$@"

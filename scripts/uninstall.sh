#!/usr/bin/env sh
set -eu

APP_NAME="spork"
SPORK_ROOT="${SPORK_HOME:-$HOME/.$APP_NAME}"
SHIMS_DIR="$SPORK_ROOT/shims"
SPORK_APP_DIR="$SPORK_ROOT/apps/spork"

KEEP_DATA=0
if [ "${1:-}" = "--keep-data" ]; then
  KEEP_DATA=1
fi

rm -f "$SPORK_ROOT/spork"
rm -f "$SHIMS_DIR/spork"
rm -rf "$SPORK_APP_DIR"

if [ "$KEEP_DATA" -eq 0 ]; then
  rm -rf "$SPORK_ROOT"
fi

echo "Spork uninstalled."
if [ "$KEEP_DATA" -eq 1 ]; then
  echo "User data was kept at $SPORK_ROOT."
fi

#!/usr/bin/env sh
set -eu

APP_NAME="spork"
PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SPORK_ROOT="${SPORK_HOME:-$HOME/.$APP_NAME}"
CONFIG_DIR="$SPORK_ROOT/config"
BUCKETS_DIR="$SPORK_ROOT/buckets"
STATE_DIR="$SPORK_ROOT/state"
CACHE_DIR="$SPORK_ROOT/cache"
APPS_DIR="$SPORK_ROOT/apps"
SHIMS_DIR="$SPORK_ROOT/shims"
SPORK_APP_DIR="$APPS_DIR/spork"
CURRENT_DIR="$SPORK_APP_DIR/current"
COMMAND_LINK="$SHIMS_DIR/spork"
COMMAND_TARGET="$CURRENT_DIR/scripts/spork"
DEFAULT_BUCKET_NAME="${SPORK_DEFAULT_BUCKET_NAME:-main}"
DEFAULT_BUCKET_URL="${SPORK_DEFAULT_BUCKET_URL:-https://github.com/Enkialon/spork-bucket.git}"
DEFAULT_BUCKET_DIR="$BUCKETS_DIR/$DEFAULT_BUCKET_NAME"

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "error: required command not found: $1" >&2
    return 1
  fi
}

write_json_if_missing() {
  file="$1"
  content="$2"
  if [ ! -f "$file" ]; then
    printf '%s\n' "$content" > "$file"
  fi
}

now_iso() {
  date -u '+%Y-%m-%dT%H:%M:%SZ'
}

detect_language() {
  case "${SPORK_LANG:-${SPORK_LANGUAGE:-${LANG:-}}}" in
    zh*|ZH*) printf 'zh' ;;
    *) printf 'en' ;;
  esac
}

normalize_package_manager() {
  case "$1" in
    aptitude|debian|ubuntu) printf 'apt' ;;
    fedora|rhel) printf 'dnf' ;;
    centos) printf 'yum' ;;
    opensuse|suse) printf 'zypper' ;;
    arch) printf 'pacman' ;;
    *) printf '%s' "$1" ;;
  esac
}

detect_package_manager() {
  if [ -n "${SPORK_PACKAGE_MANAGER:-}" ]; then
    normalize_package_manager "$SPORK_PACKAGE_MANAGER"
    return
  fi

  os_id=""
  os_like=""
  if [ -r /etc/os-release ]; then
    os_id=$(sed -n 's/^ID=//p' /etc/os-release | head -n 1 | tr -d '"')
    os_like=$(sed -n 's/^ID_LIKE=//p' /etc/os-release | head -n 1 | tr -d '"')
  fi
  distro="$os_id $os_like"
  case "$distro" in
    *debian*|*ubuntu*|*linuxmint*|*pop*) command -v apt >/dev/null 2>&1 && { printf 'apt'; return; } ;;
    *fedora*|*rhel*|*centos*|*rocky*|*almalinux*) command -v dnf >/dev/null 2>&1 && { printf 'dnf'; return; } ;;
    *suse*|*opensuse*) command -v zypper >/dev/null 2>&1 && { printf 'zypper'; return; } ;;
    *arch*|*manjaro*) command -v pacman >/dev/null 2>&1 && { printf 'pacman'; return; } ;;
  esac

  for manager in apt dnf yum zypper pacman; do
    if command -v "$manager" >/dev/null 2>&1; then
      printf '%s' "$manager"
      return
    fi
  done
  printf 'apt'
}

manager_commands() {
  case "$1" in
    apt|apt-get) printf '%s\n' "$1" sudo dpkg-query dpkg-deb dpkg apt-cache ;;
    dnf|yum) printf '%s\n' "$1" sudo rpm ;;
    zypper) printf '%s\n' zypper sudo rpm ;;
    pacman) printf '%s\n' pacman sudo ;;
    *) printf '%s\n' "$1" sudo ;;
  esac
}

LANGUAGE=$(detect_language)
PACKAGE_MANAGER=$(detect_package_manager)

echo "Installing Spork from: $PROJECT_ROOT"
echo "Detected package manager: $PACKAGE_MANAGER"

missing=0
for cmd in python3 git $(manager_commands "$PACKAGE_MANAGER"); do
  if ! need_cmd "$cmd"; then
    missing=1
  fi
done

if [ "$missing" -ne 0 ]; then
  echo
  echo "Install the missing base packages first with your system package manager."
  exit 1
fi

mkdir -p \
  "$CONFIG_DIR" \
  "$BUCKETS_DIR" \
  "$STATE_DIR" \
  "$CACHE_DIR/index" \
  "$CACHE_DIR/downloads" \
  "$SPORK_APP_DIR" \
  "$SHIMS_DIR"

if [ "$PROJECT_ROOT" != "$CURRENT_DIR" ]; then
  if [ ! -e "$CURRENT_DIR" ]; then
    if git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      SOURCE_URL=$(git -C "$PROJECT_ROOT" config --get remote.origin.url || true)
      if [ -z "$SOURCE_URL" ]; then
        SOURCE_URL=$PROJECT_ROOT
      fi
      if ! git clone "$SOURCE_URL" "$CURRENT_DIR"; then
        ln -sfn "$PROJECT_ROOT" "$CURRENT_DIR"
      fi
    else
      ln -sfn "$PROJECT_ROOT" "$CURRENT_DIR"
    fi
  fi
fi

if [ ! -f "$COMMAND_TARGET" ]; then
  echo "error: spork launcher not found: $COMMAND_TARGET" >&2
  exit 1
fi

write_json_if_missing "$CONFIG_DIR/config.json" "{
  \"schemaVersion\": 1,
  \"arch\": \"amd64\",
  \"autoUpdateBuckets\": true,
  \"downloadTimeoutSeconds\": 120,
  \"installConfirm\": true,
  \"language\": \"$LANGUAGE\",
  \"packageManager\": \"$PACKAGE_MANAGER\"
}"

DEFAULT_BUCKET_ADDED=0
if [ ! -f "$CONFIG_DIR/buckets.json" ]; then
  if [ -d "$DEFAULT_BUCKET_DIR/.git" ] || git clone "$DEFAULT_BUCKET_URL" "$DEFAULT_BUCKET_DIR"; then
    DEFAULT_BUCKET_ADDED=1
    ADDED_AT=$(now_iso)
    write_json_if_missing "$CONFIG_DIR/buckets.json" "{
  \"schemaVersion\": 1,
  \"buckets\": [
    {
      \"name\": \"$DEFAULT_BUCKET_NAME\",
      \"type\": \"git\",
      \"source\": \"$DEFAULT_BUCKET_URL\",
      \"path\": \"$DEFAULT_BUCKET_DIR\",
      \"trusted\": true,
      \"addedAt\": \"$ADDED_AT\"
    }
  ]
}"
  else
    echo "warning: failed to clone default bucket: $DEFAULT_BUCKET_URL" >&2
    echo "warning: add it later with: spork bucket add $DEFAULT_BUCKET_NAME $DEFAULT_BUCKET_URL" >&2
    write_json_if_missing "$CONFIG_DIR/buckets.json" '{
  "schemaVersion": 1,
  "buckets": []
}'
  fi
fi

if [ ! -f "$CONFIG_DIR/trusted-buckets.json" ] && [ "$DEFAULT_BUCKET_ADDED" -eq 1 ]; then
  TRUSTED_AT=$(now_iso)
  write_json_if_missing "$CONFIG_DIR/trusted-buckets.json" "{
  \"schemaVersion\": 1,
  \"trusted\": [
    {
      \"name\": \"$DEFAULT_BUCKET_NAME\",
      \"source\": \"$DEFAULT_BUCKET_URL\",
      \"trustedAt\": \"$TRUSTED_AT\"
    }
  ]
}"
else
  write_json_if_missing "$CONFIG_DIR/trusted-buckets.json" '{
  "schemaVersion": 1,
  "trusted": []
}'
fi

write_json_if_missing "$STATE_DIR/installed.json" '{
  "schemaVersion": 1,
  "apps": []
}'

ln -sfn "$COMMAND_TARGET" "$COMMAND_LINK"

echo
echo "Spork installed:"
echo "  root:    $SPORK_ROOT"
echo "  app:     $CURRENT_DIR"
echo "  shim:    $COMMAND_LINK"
echo "  config:  $CONFIG_DIR/config.json"
if [ "$DEFAULT_BUCKET_ADDED" -eq 1 ]; then
  echo "  bucket:  $DEFAULT_BUCKET_NAME -> $DEFAULT_BUCKET_URL"
fi
echo "  cache:   $CACHE_DIR"
echo
echo "Managed applications are not installed under $SPORK_ROOT."
echo "Install, remove, and purge still go through the configured package manager: $PACKAGE_MANAGER."

case ":$PATH:" in
  *":$SHIMS_DIR:"*) ;;
  *)
    echo
    echo "Add this to your shell profile if spork is not found:"
    echo "  export PATH=\"$SHIMS_DIR:\$PATH\""
    ;;
esac

echo
"$COMMAND_LINK" --version
echo "Run:"
echo "  spork doctor"
echo "  spork update"

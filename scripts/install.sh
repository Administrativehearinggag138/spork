#!/usr/bin/env sh
set -eu

APP_NAME="spork"
DEFAULT_SPORK_REPO_URL="https://github.com/spork-linux/spork.git"
SPORK_REPO_URL="${SPORK_REPO_URL:-$DEFAULT_SPORK_REPO_URL}"
SPORK_REF="${SPORK_REF:-}"
SPORK_ROOT="${SPORK_HOME:-$HOME/.$APP_NAME}"
CONFIG_DIR="$SPORK_ROOT/config"
BUCKETS_DIR="$SPORK_ROOT/buckets"
STATE_DIR="$SPORK_ROOT/state"
CACHE_DIR="$SPORK_ROOT/cache"
APPS_DIR="$SPORK_ROOT/apps"
SHIMS_DIR="$SPORK_ROOT/shims"
USER_BIN_DIR="$HOME/.local/bin"
SPORK_APP_DIR="$APPS_DIR/spork"
CURRENT_DIR="$SPORK_APP_DIR/current"
COMMAND_LINK="$SHIMS_DIR/spork"
USER_COMMAND_LINK="$USER_BIN_DIR/spork"
COMMAND_TARGET="$CURRENT_DIR/scripts/spork"
DEFAULT_BUCKET_NAME="${SPORK_DEFAULT_BUCKET_NAME:-main}"
DEFAULT_BUCKET_URL="${SPORK_DEFAULT_BUCKET_URL:-https://github.com/spork-linux/spork-bucket.git}"
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

detect_arch() {
  machine=$(uname -m 2>/dev/null || printf unknown)
  case "$machine" in
    x86_64|amd64) printf 'amd64' ;;
    i386|i686|x86) printf 'i386' ;;
    aarch64|arm64) printf 'arm64' ;;
    armv7l|armv7) printf 'armhf' ;;
    armel) printf 'armel' ;;
    riscv64) printf 'riscv64' ;;
    ppc64le|ppc64el) printf 'ppc64el' ;;
    s390x) printf 's390x' ;;
    *) printf '%s' "$machine" ;;
  esac
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

install_spork_source() {
  if [ -f "$COMMAND_TARGET" ]; then
    return 0
  fi

  if [ -e "$CURRENT_DIR" ]; then
    echo "error: $CURRENT_DIR already exists but $COMMAND_TARGET is missing." >&2
    echo "Remove it or set SPORK_HOME to a different install root, then run the installer again." >&2
    exit 1
  fi

  echo "Downloading Spork source from: $SPORK_REPO_URL"
  tmp_dir=$(mktemp -d "$SPORK_APP_DIR/.install.XXXXXX")
  cleanup_tmp_dir() {
    rm -rf "$tmp_dir"
  }
  trap cleanup_tmp_dir EXIT INT HUP TERM

  git clone "$SPORK_REPO_URL" "$tmp_dir"

  if [ -n "$SPORK_REF" ]; then
    git -C "$tmp_dir" checkout "$SPORK_REF"
  fi

  if [ ! -f "$tmp_dir/scripts/spork" ]; then
    echo "error: downloaded Spork source is missing scripts/spork." >&2
    exit 1
  fi

  mv "$tmp_dir" "$CURRENT_DIR"
  trap - EXIT INT HUP TERM
}

append_path_profile() {
  profile_file=$1

  if [ ! -e "$profile_file" ]; then
    : > "$profile_file" || return 1
  fi

  if grep -F "$SHIMS_DIR" "$profile_file" >/dev/null 2>&1; then
    return 0
  fi

  {
    printf '\n# Spork command shims\n'
    printf 'case ":$PATH:" in\n'
    printf '  *":%s:"*) ;;\n' "$SHIMS_DIR"
    printf '  *) export PATH="%s:$PATH" ;;\n' "$SHIMS_DIR"
    printf 'esac\n'
  } >> "$profile_file"
  PATH_PROFILE_UPDATED=1
}

ensure_shell_path() {
  PATH_PROFILE_UPDATED=0
  failed=0

  for profile_file in "$HOME/.profile" "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ "$profile_file" = "$HOME/.profile" ] || [ -e "$profile_file" ]; then
      if append_path_profile "$profile_file"; then
        :
      else
        failed=1
        echo "warning: failed to update shell profile: $profile_file" >&2
      fi
    fi
  done

  if [ "$PATH_PROFILE_UPDATED" -eq 1 ]; then
    echo "Updated shell profiles for Spork command lookup."
  fi
  if [ "$failed" -eq 1 ]; then
    echo "warning: add $SHIMS_DIR to PATH manually if spork is not found." >&2
  fi
}

LANGUAGE=$(detect_language)
PACKAGE_MANAGER=$(detect_package_manager)
ARCH=$(detect_arch)

echo "Installing Spork into: $SPORK_ROOT"
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
  "$SHIMS_DIR" \
  "$USER_BIN_DIR"

install_spork_source

if [ ! -f "$COMMAND_TARGET" ]; then
  echo "error: spork launcher not found: $COMMAND_TARGET" >&2
  exit 1
fi

write_json_if_missing "$CONFIG_DIR/config.json" "{
  \"schemaVersion\": 1,
  \"arch\": \"$ARCH\",
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
if [ ! -e "$USER_COMMAND_LINK" ] || [ -L "$USER_COMMAND_LINK" ]; then
  ln -sfn "$COMMAND_TARGET" "$USER_COMMAND_LINK"
else
  echo "warning: not replacing existing command: $USER_COMMAND_LINK" >&2
fi

ensure_shell_path

echo
echo "Spork installed:"
echo "  root:    $SPORK_ROOT"
echo "  app:     $CURRENT_DIR"
echo "  shim:    $COMMAND_LINK"
echo "  command: $USER_COMMAND_LINK"
echo "  config:  $CONFIG_DIR/config.json"
echo "  arch:    $ARCH"
if [ "$DEFAULT_BUCKET_ADDED" -eq 1 ]; then
  echo "  bucket:  $DEFAULT_BUCKET_NAME -> $DEFAULT_BUCKET_URL"
fi
echo "  cache:   $CACHE_DIR"
echo
echo "Managed applications are not installed under $SPORK_ROOT."
echo "Install, remove, and purge still go through the configured package manager: $PACKAGE_MANAGER."

case ":$PATH:" in
  *":$SHIMS_DIR:"*|*":$USER_BIN_DIR:"*) ;;
  *)
    echo
    echo "Open a new shell if spork is not found in this one."
    ;;
esac

echo
"$COMMAND_LINK" --version
echo "Run:"
echo "  spork checkup"
echo "  spork update"

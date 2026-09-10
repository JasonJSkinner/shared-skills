#!/usr/bin/env bash
# install.sh - standalone installer for the shared-skills repository.

set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]}"
while [ -h "$SCRIPT_PATH" ]; do
    DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" && pwd)"
    SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
    if [[ $SCRIPT_PATH != /* ]]; then SCRIPT_PATH="$DIR/$SCRIPT_PATH"; fi
done
SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/skills"
PUBLISHER="$SCRIPT_DIR/publish-skill.py"

DRY_RUN=0
TARGET_BASE=""
declare -a CREATE_PROVIDERS=()
ACTION_COUNT=0
SKIP_COUNT=0
PROVIDER_COUNT=0
SKILL_COUNT=0
ASSET_COUNT=0

usage() {
    sed -n '2,33p' "$0"
    cat <<'EOF'

Usage:
  ./install.sh [--dry-run] [--create-provider=claude|codex|gemini] [--target=DIR]

Provider targets:
  claude -> $HOME/.claude/skills
  codex  -> $HOME/.codex/skills
  gemini -> $HOME/.gemini/skills

--target=DIR uses DIR/<provider> as the provider skill target, useful for
previewing or testing installs away from live provider directories.
EOF
}

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --target=*) TARGET_BASE="${arg#--target=}" ;;
        --create-provider=*) CREATE_PROVIDERS+=("${arg#--create-provider=}") ;;
        -h|--help) usage; exit 0 ;;
        *) echo "install.sh: unknown argument: $arg" >&2; usage >&2; exit 1 ;;
    esac
done

info() { printf "[install.sh] %s\n" "$*"; }
skip() { SKIP_COUNT=$((SKIP_COUNT + 1)); printf "  [SKIP] %s\n" "$*"; }
act() {
    local desc="$1"; shift
    ACTION_COUNT=$((ACTION_COUNT + 1))
    if [ "$DRY_RUN" = "1" ]; then
        printf "  [DRY-RUN] %s\n           %s\n" "$desc" "$*"
    else
        printf "  [INSTALL] %s\n" "$desc"
        "$@"
    fi
}

provider_target() {
    local name="$1"
    if [ -n "$TARGET_BASE" ]; then
        printf "%s/%s\n" "$TARGET_BASE" "$name"
        return
    fi
    case "$name" in
        claude) printf "%s/.claude/skills\n" "$HOME" ;;
        codex) printf "%s/.codex/skills\n" "$HOME" ;;
        gemini) printf "%s/.gemini/skills\n" "$HOME" ;;
        *) return 1 ;;
    esac
}

create_requested() {
    local want="$1" p
    for p in "${CREATE_PROVIDERS[@]+"${CREATE_PROVIDERS[@]}"}"; do
        [ "$p" = "$want" ] && return 0
    done
    return 1
}

read_header_field() {
    local file="$1" field="$2" line
    [ -f "$file" ] || return 1
    while IFS= read -r line; do
        case "$line" in
            "$field: "*) printf "%s\n" "${line#"$field: "}"; return 0 ;;
            "-->") return 1 ;;
        esac
    done < "$file"
    return 1
}

publish_skill() {
    local src="$1" dst="$2" provider="$3" tmp existing_at
    local target_dir="$(dirname "$dst")"
    if [ "$DRY_RUN" = "1" ]; then
        ACTION_COUNT=$((ACTION_COUNT + 1))
        printf "  [DRY-RUN] publish %s for %s\n" "$src" "$provider"
        printf "           PYTHONPATH=%s/lib python3 %s %s --provider %s > %s\n" "$SCRIPT_DIR" "$PUBLISHER" "$src" "$provider" "$dst"
        return 0
    fi
    mkdir -p "$target_dir"
    tmp="$(mktemp "$target_dir/.SKILL.md.tmp.XXXXXX")"
    existing_at="$(read_header_field "$dst" "Generated at" || true)"
    if [ -n "$existing_at" ]; then
        PYTHONPATH="$SCRIPT_DIR/lib${PYTHONPATH:+:$PYTHONPATH}" python3 "$PUBLISHER" "$src" --provider "$provider" --generated-at "$existing_at" > "$tmp"
        if [ -f "$dst" ] && cmp -s "$tmp" "$dst"; then
            rm -f "$tmp"
            skip "unchanged published SKILL.md: $dst"
            return 0
        fi
    fi
    PYTHONPATH="$SCRIPT_DIR/lib${PYTHONPATH:+:$PYTHONPATH}" python3 "$PUBLISHER" "$src" --provider "$provider" > "$tmp"
    mv -f "$tmp" "$dst"
    ACTION_COUNT=$((ACTION_COUNT + 1))
    printf "  [INSTALL] published SKILL.md: %s\n" "$dst"
}

install_version() {
    local src="$1" target="$2"
    if [ "$DRY_RUN" = "1" ]; then
        printf "  [DRY-RUN] derive installed metadata: %s/VERSION.json\n" "$target"
        return 0
    fi
    python3 - "$src" "$target" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

source, target = Path(sys.argv[1]), Path(sys.argv[2])
metadata = json.loads(source.read_text(encoding="utf-8"))
if not isinstance(metadata, dict):
    raise ValueError("VERSION.json must contain an object")
metadata["content_hash_sha256"] = hashlib.sha256((target / "SKILL.md").read_bytes()).hexdigest()
content = (json.dumps(metadata, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
destination = target / "VERSION.json"
if not destination.exists() or destination.read_bytes() != content:
    fd, name = tempfile.mkstemp(prefix=".VERSION.json.", dir=target)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
        os.replace(name, destination)
    finally:
        Path(name).unlink(missing_ok=True)
PY
}

provider_asset_is_tagged() {
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$SCRIPT_DIR/lib${PYTHONPATH:+:$PYTHONPATH}" python3 - "$1" "$2" <<'PY'
from pathlib import Path
import sys
from provider_blocks import ProviderBlockError, render_for_provider

try:
    source = Path(sys.argv[1]).read_text(encoding="utf-8")
    rendered = render_for_provider(source, sys.argv[2])
except (OSError, UnicodeError, ProviderBlockError) as exc:
    print(f"invalid Markdown asset: {sys.argv[1]}: {exc}", file=sys.stderr)
    sys.exit(2)
sys.exit(0 if rendered != source else 1)
PY
}

copy_entry() {
    local src="$1" dst="$2" provider="$3" base entry
    base="$(basename "$src")"
    case "$base" in
        SKILL.md|REFRESH.md|_archive|__pycache__|.pytest_cache|.mypy_cache|.git|.DS_Store|*.pyc) skip "excluded: $src"; return 0 ;;
    esac
    if [ -d "$src" ]; then
        act "ensure directory: $dst" mkdir -p "$dst"
        for entry in "$src"/* "$src"/.[!.]*; do
            [ -e "$entry" ] || continue
            copy_entry "$entry" "$dst/$(basename "$entry")" "$provider"
        done
    elif [ -f "$src" ]; then
        if [[ "$src" == *.md ]]; then
            if provider_asset_is_tagged "$src" "$provider"; then
                publish_skill "$src" "$dst" "$provider"
                return
            else
                local rc=$?
                [ "$rc" = "1" ] || return "$rc"
            fi
        fi
        if [ "$DRY_RUN" = "0" ] && [ -f "$dst" ] && cmp -s "$src" "$dst"; then
            skip "unchanged asset: $dst"
        else
            ASSET_COUNT=$((ASSET_COUNT + 1))
            act "copy asset: $src -> $dst" cp -p "$src" "$dst"
        fi
    fi
}

[ -d "$SKILLS_DIR" ] || { echo "install.sh: missing skills directory: $SKILLS_DIR" >&2; exit 2; }
[ -f "$PUBLISHER" ] || { echo "install.sh: missing publisher: $PUBLISHER" >&2; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "install.sh: python3 not found" >&2; exit 2; }

for p in "${CREATE_PROVIDERS[@]+"${CREATE_PROVIDERS[@]}"}"; do
    case "$p" in claude|codex|gemini) ;; *) echo "install.sh: unknown provider for --create-provider: $p" >&2; exit 1 ;; esac
done

info "source skills: $SKILLS_DIR"
for provider in claude codex gemini; do
    target="$(provider_target "$provider")"
    if [ ! -d "$target" ] && ! create_requested "$provider"; then
        skip "provider '$provider' target does not exist: $target (pass --create-provider=$provider to opt in)"
        continue
    fi
    [ -d "$target" ] || act "create provider target: $target" mkdir -p "$target"
    PROVIDER_COUNT=$((PROVIDER_COUNT + 1))
    info "installing provider '$provider' at $target"
    for skill_dir in "$SKILLS_DIR"/*; do
        [ -d "$skill_dir" ] || continue
        skill="$(basename "$skill_dir")"
        SKILL_COUNT=$((SKILL_COUNT + 1))
        publish_skill "$skill_dir/SKILL.md" "$target/$skill/SKILL.md" "$provider"
        for entry in "$skill_dir"/* "$skill_dir"/.[!.]*; do
            [ -e "$entry" ] || continue
            if [ "$(basename "$entry")" = "VERSION.json" ]; then
                install_version "$entry" "$target/$skill"
            else
                copy_entry "$entry" "$target/$skill/$(basename "$entry")" "$provider"
            fi
        done
    done
done

info "summary: providers=$PROVIDER_COUNT skill-publishes=$SKILL_COUNT asset-copies=$ASSET_COUNT actions=$ACTION_COUNT skips=$SKIP_COUNT"
if [ "$DRY_RUN" = "1" ]; then
    info "DRY-RUN complete. No filesystem changes performed."
else
    info "install complete."
fi

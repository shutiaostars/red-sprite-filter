#!/bin/zsh
set -euo pipefail

APP_DIR="${0:A:h:h}"
RESOURCE_DIR="$APP_DIR/Resources/app"
cd "$RESOURCE_DIR"

PORT="${RED_SPRITE_PORT:-0}"
python3 -m red_sprite_app.backend --port "$PORT" --open

#!/usr/bin/env bash
# crew — deploy script for a fresh Ubuntu 22.04+ server.
#
# Idempotent: safe to re-run. Run AS the `bot` user (not root) after creating it.
#
# Usage (on the server):
#   curl -sSL https://raw.githubusercontent.com/fendora-io/crew/main/deploy.sh | bash
#   # OR if you've already cloned:
#   bash deploy.sh
#
# Prerequisites (do these as root first):
#   adduser bot && usermod -aG sudo bot && su - bot

set -euo pipefail

REPO_URL="${CREW_REPO_URL:-git@github.com:fendora-io/crew.git}"
INSTALL_DIR="${CREW_INSTALL_DIR:-/opt/crew}"
LOG_FILE="${CREW_LOG_FILE:-/var/log/crew.log}"

# --- Pretty output helpers ---
say()  { printf "\033[1;34m[crew]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[crew]\033[0m %s\n" "$*" >&2; }
die()  { printf "\033[1;31m[crew]\033[0m %s\n" "$*" >&2; exit 1; }

# --- Sanity checks ---
[ "$(id -u)" -eq 0 ] && die "Don't run as root. Run as the 'bot' user (or any non-root user)."
command -v python3 >/dev/null || die "python3 not found. Run: sudo apt install python3 python3-pip python3-venv git"
command -v git     >/dev/null || die "git not found. Run: sudo apt install git"

# --- Clone or update ---
if [ -d "$INSTALL_DIR/.git" ]; then
  say "Updating existing checkout at $INSTALL_DIR"
  cd "$INSTALL_DIR"
  git pull --ff-only
else
  say "Cloning $REPO_URL → $INSTALL_DIR"
  sudo mkdir -p "$INSTALL_DIR"
  sudo chown "$(id -u):$(id -g)" "$INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
fi

# --- Python venv ---
if [ ! -d venv ]; then
  say "Creating Python virtualenv"
  python3 -m venv venv
fi
say "Installing dependencies"
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r requirements.txt

# --- .env ---
if [ ! -f .env ]; then
  say "Creating .env from .env.example"
  cp .env.example .env
  chmod 600 .env
  warn ".env created with placeholder values."
  warn "  → nano $INSTALL_DIR/.env and fill in your real keys before running."
else
  chmod 600 .env
  say ".env already present (permissions set to 600)"
fi

# --- Log file ---
if [ ! -f "$LOG_FILE" ]; then
  say "Creating log file at $LOG_FILE"
  sudo touch "$LOG_FILE"
  sudo chown "$(id -u):$(id -g)" "$LOG_FILE"
fi

# --- Cron ---
CRON_LINE="0 6 * * * cd $INSTALL_DIR && . .env && ./venv/bin/python crew.py >> $LOG_FILE 2>&1"
if crontab -l 2>/dev/null | grep -Fq "$INSTALL_DIR/crew.py"; then
  say "Cron job already installed"
else
  say "Installing cron job (06:00 UTC daily)"
  ( crontab -l 2>/dev/null; echo "$CRON_LINE" ) | crontab -
fi

# --- Done ---
say ""
say "✅ Deployment complete."
say ""
say "Next steps:"
say "  1. Fill in real keys: nano $INSTALL_DIR/.env"
say "     - Infisical (recommended): set the INFISICAL_* block."
say "       crew will pull ANTHROPIC_API_KEY / TELEGRAM_* at startup."
say "     - Plain env: uncomment and fill ANTHROPIC_API_KEY / TELEGRAM_* directly."
say "  2. Test now: cd $INSTALL_DIR && . .env && ./venv/bin/python crew.py"
say "  3. Watch tomorrow at 07:00 CET for your first scheduled digest."
say ""
say "Cron line installed:"
say "  $CRON_LINE"

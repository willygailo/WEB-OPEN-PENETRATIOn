#!/usr/bin/env bash
# ============================================================
#  OPEN PENETRATION — Run Script (Kali Linux)
#  Activates the venv and launches Phish.py
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

VENV_DIR=".venv"
SCRIPT="Phish.py"

# Check venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}[!] Virtual environment not found.${NC}"
    echo -e "${CYAN}[*] Run './install.sh' first to set up the tool.${NC}"
    exit 1
fi

# Launch tool with all arguments passed through
"$VENV_DIR/bin/python3" "$SCRIPT" "$@"

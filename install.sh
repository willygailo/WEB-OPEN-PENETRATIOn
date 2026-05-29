#!/usr/bin/env bash
# ============================================================
#  OPEN PENETRATION — Kali Linux Setup Script
#  Handles PEP 668 externally-managed-environment
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

VENV_DIR=".venv"

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}   📡 OPEN PENETRATION — Kali Linux Installer         ${NC}"
echo -e "${CYAN}======================================================${NC}"

# Check Python3
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}[!] Python3 not found. Install it with: sudo apt install python3${NC}"
    exit 1
fi

PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}[+] Python version  : ${PYTHON_VER}${NC}"
echo -e "${GREEN}[+] OS              : $(uname -sr)${NC}"

# Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}[*] Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}[!] Failed to create venv. Try: sudo apt install python3-venv${NC}"
        exit 1
    fi
    echo -e "${GREEN}[+] Virtual environment created at ./${VENV_DIR}${NC}"
else
    echo -e "${YELLOW}[*] Virtual environment already exists — skipping creation.${NC}"
fi

# Activate and install
echo -e "${YELLOW}[*] Installing dependencies...${NC}"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e ""
    echo -e "${GREEN}[+] All dependencies installed successfully!${NC}"
    echo -e "${CYAN}======================================================${NC}"
    echo -e "${CYAN}   ✅  Setup complete. Run the tool with:             ${NC}"
    echo -e "${CYAN}       ./run.sh -d https://target-site.com            ${NC}"
    echo -e "${CYAN}======================================================${NC}"
else
    echo -e "${RED}[!] Installation failed. Check errors above.${NC}"
    exit 1
fi

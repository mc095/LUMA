#!/bin/bash

# ANSI color codes
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${CYAN}🎙️ LUMA Voice Assistant - Installation Script${NC}"
echo -e "${CYAN}================================================${NC}"

# Create installation directory
INSTALL_DIR="LUMA"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Download latest release
echo -e "\n${YELLOW}📦 Downloading LUMA...${NC}"
curl -L -o LUMA.exe "https://github.com/mc095/LUMA/releases/latest/download/LUMA.exe"

# Get API keys from user
echo -e "\n${YELLOW}🔑 Setting up configuration...${NC}"
read -p "Enter your GROQ API key: " GROQ_KEY
read -p "Enter your Google (Gemini) API key (optional, press Enter to skip): " GEMINI_KEY

# Create config file
cat > build_config.py << EOF
"""Build configuration with embedded API keys."""

# API Keys
GROQ_API_KEY = "${GROQ_KEY}"
GEMINI_API_KEY = "${GEMINI_KEY}"
EOF

echo -e "\n${GREEN}✅ Installation complete!${NC}"
echo -e "${YELLOW}To start LUMA, run:${NC}"
echo "cd $INSTALL_DIR"
echo "./LUMA.exe"

read -n 1 -s -r -p "Press any key to continue..."
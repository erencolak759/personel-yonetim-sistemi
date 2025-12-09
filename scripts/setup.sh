#!/usr/bin/env bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Personnel Management System Setup    ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Project Root: ${PROJECT_ROOT}"
echo ""

OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo -e "${YELLOW}Detected OS: ${MACHINE}${NC}"
echo ""

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

install_nodejs() {
    echo -e "${YELLOW}Installing Node.js...${NC}"
    if [ "$MACHINE" = "Mac" ]; then
        if command_exists brew; then
            brew install node
        else
            echo -e "${RED}Homebrew not found. Please install Homebrew first:${NC}"
            echo -e "${RED}  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"${NC}"
            exit 1
        fi
    elif [ "$MACHINE" = "Linux" ]; then
        if command_exists apt-get; then
            curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
            sudo apt-get install -y nodejs
        elif command_exists dnf; then
            sudo dnf install -y nodejs npm
        elif command_exists yum; then
            curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
            sudo yum install -y nodejs
        elif command_exists pacman; then
            sudo pacman -S nodejs npm
        else
            echo -e "${RED}Could not detect package manager. Please install Node.js manually.${NC}"
            exit 1
        fi
    fi
}

install_python() {
    echo -e "${YELLOW}Installing Python3...${NC}"
    if [ "$MACHINE" = "Mac" ]; then
        if command_exists brew; then
            brew install python3
        else
            echo -e "${RED}Homebrew not found. Please install Homebrew first.${NC}"
            exit 1
        fi
    elif [ "$MACHINE" = "Linux" ]; then
        if command_exists apt-get; then
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv
        elif command_exists dnf; then
            sudo dnf install -y python3 python3-pip python3-venv
        elif command_exists yum; then
            sudo yum install -y python3 python3-pip python3-venv
        elif command_exists pacman; then
            sudo pacman -S python python-pip
        else
            echo -e "${RED}Could not detect package manager. Please install Python3 manually.${NC}"
            exit 1
        fi
    fi
}

install_pnpm() {
    echo -e "${YELLOW}Installing pnpm...${NC}"
    npm install -g pnpm
}

echo -e "${GREEN}Step 1: Checking Node.js...${NC}"
if command_exists node; then
    NODE_VERSION=$(node --version)
    echo -e "  Node.js is installed: ${NODE_VERSION}"
else
    echo -e "  ${YELLOW}Node.js not found. Installing...${NC}"
    install_nodejs
    echo -e "  ${GREEN}Node.js installed successfully!${NC}"
fi
echo ""

echo -e "${GREEN}Step 2: Checking npm...${NC}"
if command_exists npm; then
    NPM_VERSION=$(npm --version)
    echo -e "  npm is installed: v${NPM_VERSION}"
else
    echo -e "  ${RED}npm not found. It should come with Node.js. Please reinstall Node.js.${NC}"
    exit 1
fi
echo ""

echo -e "${GREEN}Step 3: Checking pnpm...${NC}"
if command_exists pnpm; then
    PNPM_VERSION=$(pnpm --version)
    echo -e "  pnpm is installed: v${PNPM_VERSION}"
else
    echo -e "  ${YELLOW}pnpm not found. Installing...${NC}"
    install_pnpm
    echo -e "  ${GREEN}pnpm installed successfully!${NC}"
fi
echo ""

echo -e "${GREEN}Step 4: Checking Python3...${NC}"
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "  Python3 is installed: ${PYTHON_VERSION}"
else
    echo -e "  ${YELLOW}Python3 not found. Installing...${NC}"
    install_python
    echo -e "  ${GREEN}Python3 installed successfully!${NC}"
fi
echo ""

echo -e "${GREEN}Step 5: Creating Python virtual environment...${NC}"
cd "$PROJECT_ROOT/apps/backend"
if [ -d "venv" ]; then
    echo -e "  ${YELLOW}Virtual environment already exists. Skipping creation.${NC}"
else
    python3 -m venv venv
    echo -e "  ${GREEN}Virtual environment created!${NC}"
fi
echo ""

echo -e "${GREEN}Step 6: Installing Python packages...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "  ${GREEN}Python packages installed!${NC}"
echo ""

echo -e "${GREEN}Step 7: Checking .env configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "  ${YELLOW}.env file created from .env.example. Please update with your database credentials.${NC}"
    else
        echo -e "  ${RED}.env.example not found! Please create .env file manually.${NC}"
    fi
else
    echo -e "  ${GREEN}.env file exists.${NC}"
fi
echo ""

echo -e "${GREEN}Step 8: Initializing database...${NC}"
if [ "${SKIP_DB_INIT}" = "1" ]; then
    echo -e "  ${YELLOW}SKIP_DB_INIT=1 set; skipping DB init/seed.${NC}"
else
    echo -e "  ${YELLOW}Checking remote database for existing schema...${NC}"
    DB_CHECK_OUTPUT=$(python3 -c "from utils.db import check_schema_exists; print('EXISTS' if check_schema_exists() else 'MISSING')" 2>/dev/null || true)
    if [ "$DB_CHECK_OUTPUT" = "EXISTS" ]; then
        echo -e "  ${YELLOW}Database already initialized; skipping init/seed.${NC}"
    else
        echo -e "  ${GREEN}No existing schema detected; creating tables and seeding.${NC}"
        python3 -c "from utils.db import init_db, seed_db; init_db(); seed_db(); print('Database initialized!')"
    fi
fi
echo ""

deactivate
cd "$PROJECT_ROOT"

echo -e "${GREEN}Step 9: Installing Node.js dependencies...${NC}"
pnpm install
echo -e "  ${GREEN}Node.js dependencies installed!${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Complete!                      ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "To start the application, run:"
echo -e "  ${YELLOW}pnpm dev${NC}"
echo ""
echo -e "Default admin credentials:"
echo -e "  Username: ${YELLOW}admin${NC}"
echo -e "  Password: ${YELLOW}admin123${NC}"
echo ""
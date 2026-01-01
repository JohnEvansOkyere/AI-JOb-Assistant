#!/bin/bash
# Backend startup script with better error handling and process management

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Backend Server...${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BACKEND_DIR"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
else
    echo -e "${YELLOW}No virtual environment found. Using system Python...${NC}"
fi

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}Port 8000 is already in use!${NC}"
    echo -e "${YELLOW}Current processes using port 8000:${NC}"
    lsof -i :8000
    echo ""
    read -p "Kill existing process? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Killing process on port 8000...${NC}"
        kill -9 $(lsof -t -i:8000) 2>/dev/null || true
        sleep 2
    else
        echo -e "${RED}Exiting. Please free port 8000 or use a different port.${NC}"
        exit 1
    fi
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Copying from .env.example if available...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}Please update .env with your configuration.${NC}"
    else
        echo -e "${RED}Error: No .env or .env.example file found!${NC}"
        exit 1
    fi
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}Python version: ${PYTHON_VERSION}${NC}"

# Check if dependencies are installed
if ! python3 -c "import uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}uvicorn not found. Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Start the server
echo -e "${GREEN}Starting uvicorn server on http://127.0.0.1:8000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Run with better error handling
python3 -m uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --reload \
    --log-level info \
    --access-log \
    --timeout-keep-alive 30 \
    --timeout-graceful-shutdown 10


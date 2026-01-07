#!/bin/bash

# VIRAAT Military AI - Quick Start Script
# This script helps you get started with the application

set -e

echo "🛡️  VIRAAT Military AI Assistant - Quick Start"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running in correct directory
if [ ! -f "README.md" ]; then
    echo -e "${RED}Error: Please run this script from the viraat-military-ai directory${NC}"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."
echo ""

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓${NC} Python 3 found (version $PYTHON_VERSION)"
else
    echo -e "${RED}✗${NC} Python 3 not found. Please install Python 3.10 or higher"
    exit 1
fi

# Check PostgreSQL
if command_exists psql; then
    echo -e "${GREEN}✓${NC} PostgreSQL found"
else
    echo -e "${YELLOW}⚠${NC}  PostgreSQL not found. You'll need to install it manually"
fi

echo ""
echo "Setting up backend..."
echo ""

# Create virtual environment
if [ ! -d "backend/venv" ]; then
    echo "Creating virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "Installing Python dependencies (this may take a few minutes)..."
cd backend
source venv/bin/activate

if [ ! -f "venv/installed.txt" ]; then
    pip install --upgrade pip -q
    pip install -r requirements.txt
    touch venv/installed.txt
    echo -e "${GREEN}✓${NC} Dependencies installed"
else
    echo -e "${GREEN}✓${NC} Dependencies already installed"
fi

cd ..

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    
    # Generate secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    
    # Update .env with secret key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/your-secret-key-here-change-in-production/$SECRET_KEY/" .env
    else
        sed -i "s/your-secret-key-here-change-in-production/$SECRET_KEY/" .env
    fi
    
    echo -e "${GREEN}✓${NC} Environment file created"
    echo -e "${YELLOW}⚠${NC}  Please review and update .env file with your settings"
else
    echo -e "${GREEN}✓${NC} Environment file exists"
fi

# Check for LLM model
echo ""
echo "Checking for LLM model..."

if [ ! -d "backend/models/llm" ]; then
    mkdir -p backend/models/llm
fi

MODEL_COUNT=$(ls backend/models/llm/*.gguf 2>/dev/null | wc -l)

if [ "$MODEL_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠${NC}  No GGUF model found in backend/models/llm/"
    echo ""
    echo "You need to download a GGUF format model."
    echo "Recommended: Mistral-7B-Instruct-v0.2 (Q4_K_M)"
    echo ""
    echo "Download from:"
    echo "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
    echo ""
    echo "Or run:"
    echo "cd backend/models/llm"
    echo "wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    echo ""
else
    echo -e "${GREEN}✓${NC} LLM model found"
fi

# Ingest knowledge base
echo ""
echo "Setting up knowledge base..."

cd knowledge-base
if python3 ingest.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Knowledge base initialized"
else
    echo -e "${YELLOW}⚠${NC}  Knowledge base setup needs attention (run manually: cd knowledge-base && python3 ingest.py)"
fi
cd ..

# Summary
echo ""
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "1. If you haven't already, download an LLM model:"
echo "   See: docs/SETUP.md for instructions"
echo ""
echo "2. Start the backend server:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "3. In a new terminal, start the web server:"
echo "   cd web"
echo "   python3 -m http.server 3000"
echo ""
echo "4. Open your browser:"
echo "   http://localhost:3000"
echo ""
echo "For detailed setup instructions, see: docs/SETUP.md"
echo ""

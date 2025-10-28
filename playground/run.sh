#!/bin/bash
# Helper para rodar testes no playground

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== CortexDB Playground ===${NC}\n"

# Check if gateway is running
echo -e "${BLUE}Checking gateway...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Gateway is running${NC}\n"
else
    echo -e "${RED}✗ Gateway not running!${NC}"
    echo "Start it with: docker compose up -d"
    exit 1
fi

# Install dependencies if needed
if ! python3 -c "import cortexdb" 2>/dev/null; then
    echo -e "${BLUE}Installing SDK...${NC}"
    pip3 install -e clients/python/ --quiet
    echo -e "${GREEN}✓ SDK installed${NC}\n"
fi

# Menu
echo "Select test to run:"
echo "  1) Basic CRUD (test_basic.py)"
echo "  2) File Upload/Download (test_files.py)"
echo "  3) Docling Document Processing (test_docling.py) 🆕"
echo "  4) RAG - Semantic Search (test_rag.py) 🔥"
echo "  5) Semantic Search (test_search.py)"
echo "  6) Advanced Filters (test_filters.py)"
echo "  7) Backend Example (backend_example.py)"
echo "  8) Run all tests"
echo ""
read -p "Choice [1-8]: " choice

case $choice in
    1)
        echo -e "\n${BLUE}Running Basic CRUD Test...${NC}\n"
        python3 playground/test_basic.py
        ;;
    2)
        echo -e "\n${BLUE}Running File Test...${NC}\n"
        python3 playground/test_files.py
        ;;
    3)
        echo -e "\n${BLUE}Running Docling Test...${NC}\n"
        python3 playground/test_docling.py
        ;;
    4)
        echo -e "\n${BLUE}Running RAG Test...${NC}\n"
        python3 playground/test_rag.py
        ;;
    5)
        echo -e "\n${BLUE}Running Search Test...${NC}\n"
        python3 playground/test_search.py
        ;;
    6)
        echo -e "\n${BLUE}Running Filters Test...${NC}\n"
        python3 playground/test_filters.py
        ;;
    7)
        echo -e "\n${BLUE}Starting Backend Example...${NC}\n"
        if ! python3 -c "import fastapi" 2>/dev/null; then
            pip3 install fastapi uvicorn --quiet
        fi
        python3 playground/backend_example.py
        ;;
    8)
        echo -e "\n${BLUE}Running all tests...${NC}\n"
        python3 playground/test_basic.py
        echo ""
        python3 playground/test_files.py
        echo ""
        python3 playground/test_docling.py
        echo ""
        python3 playground/test_rag.py
        echo ""
        python3 playground/test_search.py
        echo ""
        python3 playground/test_filters.py
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "\n${GREEN}Done!${NC}"

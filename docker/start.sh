#!/bin/bash
# Social-Hunt Universal Startup Wrapper (Linux/macOS)
# This script calls the Python startup script

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Try python3 first, then python
if command -v python3 &> /dev/null; then
    python3 start.py
    exit $?
elif command -v python &> /dev/null; then
    python start.py
    exit $?
else
    echo ""
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3 or run: docker compose up -d"
    echo ""
    exit 1
fi

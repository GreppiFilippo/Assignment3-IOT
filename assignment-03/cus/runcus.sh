#!/bin/sh
# Script to run the CUS backend

# Check if uvicorn is installed
if command -v uv > /dev/null 2>&1; then
    echo "uv is installed. Starting with uv..."
    uv run src/main.py
else
    echo "uv is not installed. Creating virtual environment and installing dependencies..."
    
    # Create virtualenv
    python3 -m venv .venv
    source .venv/bin/activate
    
    # Update pip
    pip install --upgrade pip
    
    # Install Poetry if not present
    if ! command -v poetry > /dev/null 2>&1; then
        pip install poetry
    fi
    
    # Install all dependencies from pyproject.toml
    poetry install
    
    # Run the script with the virtualenv managed by Poetry
    poetry run python src/main.py
fi
#!/bin/sh
# Script per eseguire il backend CUS

# Controlla se uvicorn è installato
if command -v uv > /dev/null 2>&1; then
    echo "uv è installato. Avvio con uv..."
    uv run src/main.py
else
    echo "uv non è installato. Creo ambiente virtuale e installo dipendenze..."
    
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
#!/bin/bash

# Alexandria Press - Development Launcher
# Starts the API with hot-reload enabled.

# Ensure we are in the project root
cd "$(dirname "$0")"

# Check for virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Warning: .venv not found. Running with system python."
fi

# Set environment variables from .env if present
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Initialize pids variable
pids=""

if [ "$1" == "prod" ]; then
    echo "Starting Alexandria Press API (PROD)..."
    uvicorn api.index:app --host 0.0.0.0 --port 8000 &
    pids="$pids $!"
else
    echo "Starting Alexandria Press API (http://localhost:8000)..."
    echo "Hot-reload enabled for backend changes."
    # Run uvicorn
    # --reload: watches for python file changes
    # --reload-dir: explicitly watch api and entities/prompts if needed
    uvicorn api.index:app --host 0.0.0.0 --port 8000 --reload --reload-dir api --reload-dir db &
    pids="$pids $!"
fi

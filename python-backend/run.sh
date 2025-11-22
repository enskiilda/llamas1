#!/bin/bash

# Startup script for Python backend

echo "==================================="
echo "Computer Control AI - Python Backend"
echo "==================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "Starting FastAPI server on port 5000..."
echo "API will be available at: http://0.0.0.0:5000"
echo "Docs available at: http://0.0.0.0:5000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "==================================="
echo ""

# Run the server
python main.py

#!/bin/bash

echo "================================"
echo "Hima Informatika Web App"
echo "================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv/bin/activate" ]; then
    echo "Virtual environment not found."
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Checking dependencies..."
pip install -r requirements.txt

# Initialize database if it doesn't exist
if [ ! -f "instance/hima.db" ]; then
    echo "Initializing database..."
    python3 init_db.py
    echo ""
fi

echo "Starting Flask development server..."
echo ""
python3 run.py

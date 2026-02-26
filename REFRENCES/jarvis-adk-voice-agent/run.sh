#!/bin/bash

# Voice Streaming AI Agent Run Script
echo "🎤 Starting Voice Streaming AI Agent..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run ./setup.sh first."
    exit 1
fi

# Navigate to app directory
cd app

# Start the server
echo "🚀 Starting FastAPI server on http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000

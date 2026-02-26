#!/bin/bash

# Voice Streaming AI Agent Setup Script
echo "🚀 Setting up Voice Streaming AI Agent..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
echo "✅ Python $python_version detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Set up SSL certificate
echo "🔒 Setting up SSL certificate..."
export SSL_CERT_FILE=$(python -m certifi)

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.template .env
    echo "⚠️  Please edit .env file and add your Google AI Studio API key"
    echo "   Get your API key from: https://aistudio.google.com/app/apikey"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your Google AI Studio API key"
echo "2. Run: cd app && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo "3. Open http://localhost:8000 in your browser"
echo ""
echo "For more information, see README.md"

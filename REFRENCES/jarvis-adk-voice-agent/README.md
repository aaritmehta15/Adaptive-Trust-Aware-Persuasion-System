# Jarvis ADK Voice Agent

A real-time voice and text AI agent built with Google's ADK (Agent Development Kit), featuring bidirectional audio streaming, Google Search integration, and PDF reading capabilities.

📖 **[Read the Architecture Documentation](ARCHITECTURE.md)** for detailed technical insights into how the voice interaction system works.

## What's Inside

This repository contains a FastAPI-based web application that enables voice and text conversations with a Gemini-powered AI agent. The agent can search Google for information and read PDF files from your filesystem.

**Key Components:**
- FastAPI WebSocket server for real-time communication
- Web Audio API-based voice streaming (16kHz PCM)
- Google ADK integration with Gemini 2.0 Flash
- Custom tools for Google Search and PDF reading
- Modern web interface with voice/text mode switching

## Prerequisites

- Python 3.8 or higher
- Google AI Studio API key ([Get one here](https://aistudio.google.com/app/apikey))
- Modern web browser (Chrome/Edge recommended)

## Setup

1. **Install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp env.template .env
   ```
   
   Edit `.env` and set:
   ```
   GOOGLE_API_KEY=your_api_key_here
   CONTENT_FOLDER=/path/to/your/files
   ```

3. **Run the application:**
   ```bash
   ./run.sh
   ```

4. **Open in browser:**
   ```
   http://localhost:8000
   ```

## Usage

- **Text Mode**: Type questions and get streaming responses
- **Voice Mode**: Click 🎤 to enable voice interaction (requires microphone access)

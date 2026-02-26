#!/usr/bin/env python3
"""
Test script to verify the Voice Streaming AI Agent setup.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required packages can be imported."""
    print("🔍 Testing package imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn imported successfully")
    except ImportError as e:
        print(f"❌ Uvicorn import failed: {e}")
        return False
    
    try:
        import websockets
        print("✅ Websockets imported successfully")
    except ImportError as e:
        print(f"❌ Websockets import failed: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ Python-dotenv imported successfully")
    except ImportError as e:
        print(f"❌ Python-dotenv import failed: {e}")
        return False
    
    try:
        import certifi
        print("✅ Certifi imported successfully")
    except ImportError as e:
        print(f"❌ Certifi import failed: {e}")
        return False
    
    # Test ADK import (this might fail if not properly configured)
    try:
        from google.adk import Runner
        from google.adk.runners import LiveRequestQueue
        from google.adk.agents import Agent
        from google.adk.tools import google_search
        from google.adk.sessions import InMemorySessionService
        print("✅ Google ADK imported successfully")
    except ImportError as e:
        print(f"⚠️  Google ADK import failed: {e}")
        print("   This is expected if you haven't set up your API key yet")
    
    return True

def test_file_structure():
    """Test if all required files exist."""
    print("\n📁 Testing file structure...")
    
    required_files = [
        "app/main.py",
        "app/static/index.html",
        "app/static/js/app.js",
        "app/static/js/pcm-recorder-processor.js",
        "app/static/js/pcm-player-processor.js",
        "app/jarvis/__init__.py",
        "app/jarvis/agent.py",
        "app/jarvis/prompts.py",
        "app/jarvis/tools/__init__.py",
        "app/jarvis/tools/pdf_reader_tool.py",
        "requirements.txt",
        "env.template",
        "README.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing!")
            all_exist = False
    
    return all_exist

def test_env_file():
    """Test if .env file exists and has required variables."""
    print("\n🔧 Testing environment configuration...")
    
    if not Path(".env").exists():
        print("⚠️  .env file not found")
        print("   Please copy env.template to .env and add your API key")
        return False
    
    # Load and check .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "PASTE_YOUR_ACTUAL_API_KEY_HERE":
        print("⚠️  GOOGLE_API_KEY not set in .env file")
        print("   Please add your Google AI Studio API key to .env")
        return False
    
    print("✅ .env file configured with API key")
    return True

def main():
    """Run all tests."""
    print("🧪 Voice Streaming AI Agent Setup Test")
    print("=" * 50)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Run tests
    imports_ok = test_imports()
    files_ok = test_file_structure()
    env_ok = test_env_file()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Package imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"   File structure:  {'✅ PASS' if files_ok else '❌ FAIL'}")
    print(f"   Environment:     {'✅ PASS' if env_ok else '⚠️  NEEDS SETUP'}")
    
    if imports_ok and files_ok:
        print("\n🎉 Basic setup is complete!")
        if env_ok:
            print("🚀 Ready to run! Use: ./run.sh")
        else:
            print("⚠️  Please configure your API key in .env file")
            print("   Get your key from: https://aistudio.google.com/app/apikey")
    else:
        print("\n❌ Setup incomplete. Please run ./setup.sh first")
        sys.exit(1)

if __name__ == "__main__":
    main()

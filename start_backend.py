"""
Startup script for the FastAPI backend
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    
    # Check for HF_TOKEN
    if not os.getenv("HF_TOKEN"):
        print("WARNING: HF_TOKEN environment variable not set!")
        print("Please set it before running the server.")
        print("\nWindows PowerShell:")
        print('  $env:HF_TOKEN="your_token_here"')
        print("\nWindows CMD:")
        print('  set HF_TOKEN=your_token_here')
        print("\nLinux/Mac:")
        print('  export HF_TOKEN="your_token_here"')
        sys.exit(1)
    
    print("=" * 60)
    print("Starting Adaptive Persuasion System Backend...")
    print("=" * 60)
    print("\nBackend URL: http://localhost:8000")
    print("API Docs:    http://localhost:8000/docs")
    print("Health:      http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    try:
        # Use import string format for reload to work properly
        uvicorn.run(
            "backend.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=[os.path.dirname(os.path.abspath(__file__))],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
    except Exception as e:
        print(f"\n\nERROR: Failed to start server: {e}")
        print("\nTry using start_backend_simple.py instead:")
        print("  python start_backend_simple.py")
        import traceback
        traceback.print_exc()
        sys.exit(1)

"""
Simple startup script for the FastAPI backend (no reload)
Use this if start_backend.py has issues
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    
    # Check for HF_TOKEN
    if not os.getenv("HF_TOKEN"):
        print("=" * 60)
        print("ERROR: HF_TOKEN environment variable not set!")
        print("=" * 60)
        print("\nPlease set it before running the server:")
        print("\nWindows PowerShell:")
        print('  $env:HF_TOKEN="your_token_here"')
        print("\nWindows CMD:")
        print('  set HF_TOKEN=your_token_here')
        print("\nLinux/Mac:")
        print('  export HF_TOKEN="your_token_here"')
        print("\n" + "=" * 60)
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
        # Import and run directly (no reload for simplicity)
        from backend.main import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
    except Exception as e:
        print(f"\n\nERROR: Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

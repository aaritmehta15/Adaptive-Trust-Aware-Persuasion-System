# Quick Start Guide

## Prerequisites

1. Python 3.8 or higher
2. HuggingFace account with API token
3. Web browser

## Setup Steps

### 1. Install Dependencies

```bash
pip install -r requirements_web.txt
```

### 2. Set HuggingFace Token

**Windows (PowerShell):**
```powershell
$env:HF_TOKEN="your_huggingface_token_here"
```

**Linux/Mac:**
```bash
export HF_TOKEN="your_huggingface_token_here"
```

### 3. Start Backend Server

In one terminal:
```bash
python start_backend.py
```

**If you get errors, try the simple version:**
```bash
python start_backend_simple.py
```

You should see:
```
============================================================
Starting Adaptive Persuasion System Backend...
============================================================

Backend URL: http://localhost:8000
API Docs:    http://localhost:8000/docs
Health:      http://localhost:8000/health

Press Ctrl+C to stop the server
============================================================
```

**Verify it's running:**
- Open http://localhost:8000 in your browser - should show JSON response
- Or run: `python test_backend.py`

### 4. Start Frontend Server

In another terminal:
```bash
python start_frontend.py
```

Or simply open `frontend/index.html` in your browser.

### 5. Use the Application

1. The frontend should open automatically in your browser
2. Click "Setup Scenario" to configure campaign parameters (optional - defaults are provided)
3. Use the toggle switch to switch between "Regular" and "Adaptive" modes
4. Start chatting! The agent will greet you automatically
5. View real-time metrics on the right panel

## Features

- **Mode Toggle**: Switch between Regular Chatbot (C1) and Adaptive Persuasion System (C3) modes
- **Real-time Metrics**: See trust score, donation probability, strategy weights, and more
- **Scenario Setup**: Configure organization, cause, donation amounts, and impact
- **Reset**: Start a new conversation at any time

## Troubleshooting

**Backend won't start:**
- Check that `HF_TOKEN` is set:
  - Windows PowerShell: `echo $env:HF_TOKEN`
  - Windows CMD: `echo %HF_TOKEN%`
  - Linux/Mac: `echo $HF_TOKEN`
- If `start_backend.py` has issues, try `start_backend_simple.py`
- Make sure port 8000 is not in use (check with `netstat -an | findstr 8000` on Windows)

**Backend starts but exits immediately:**
- Check the error message in the terminal
- Make sure HF_TOKEN is set correctly
- Try `start_backend_simple.py` instead
- Check if there are import errors

**Frontend can't connect:**
- Ensure backend is actually running (check terminal - it should stay open)
- Verify backend is accessible: Open http://localhost:8000 in browser
- Run `python test_backend.py` to test connection
- Check browser console for errors (F12)
- Look at the connection status indicator in the header

**CORS errors:**
- Make sure you're accessing the frontend via HTTP server, not file://
- Use `python start_frontend.py` to serve the frontend properly
- Backend CORS is configured to allow all origins, so this shouldn't be an issue

**"Backend Not Connected" error:**
1. Make sure backend terminal is still running (not exited)
2. Check http://localhost:8000 works in browser
3. Click "Retry Connection" button in the frontend
4. Check browser console (F12) for detailed error messages

## API Documentation

Once the backend is running, visit:
- API Docs: http://localhost:8000/docs
- API Root: http://localhost:8000

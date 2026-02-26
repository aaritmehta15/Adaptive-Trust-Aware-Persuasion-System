# Jarvis Voice Agent - Architecture Guide

**A beginner-friendly explanation of how this voice AI assistant works**

This guide explains how the Jarvis voice agent system is built, how it works, and why certain technical choices were made.

---

## Table of Contents

- [What Is This System?](#what-is-this-system)
- [The Big Picture](#the-big-picture)
- [The Three Main Components](#the-three-main-components)
  - [1. The Frontend (What You See)](#1-the-frontend-what-you-see)
  - [2. The Backend Server (The Middleman)](#2-the-backend-server-the-middleman)
  - [3. The AI Agent (The Brain)](#3-the-ai-agent-the-brain)
- [Why This Specific Model?](#why-this-specific-model)
- [How Voice Interaction Works](#how-voice-interaction-works)
  - [Understanding Audio Processing](#understanding-audio-processing)
  - [The Complete Voice Journey](#the-complete-voice-journey)
- [Text vs Audio: What Does the Model Receive?](#text-vs-audio-what-does-the-model-receive)
- [Technical Deep Dives](#technical-deep-dives)
- [Common Questions](#common-questions)

---

## What Is This System?

Jarvis is a **voice-capable AI assistant** that you can talk to (like Siri or Alexa) or chat with via text. It can:
- Have natural voice conversations with you
- Search Google for information
- Read files from your computer
- Read PDF documents
- Remember context throughout the conversation

Think of it like having a helpful assistant that lives in your browser and can speak with you in real-time.

---

## The Big Picture

Before diving into details, let's understand the overall structure. The system has **three main parts** that work together:

```
┌─────────────────────────────────────────────────────────────────┐
│                           CLIENT                                │
│                                                                 │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓    │
│  ┃  FRONTEND                                               ┃    │
│  ┃  - Web page                                             ┃    │
│  ┃  - User interface buttons and chat                      ┃    │
│  ┃  - Microphone capture & speaker playback                ┃    │
│  ┃  - JavaScript code managing everything                  ┃    │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛    │
│                             ↕                                   │
│                    WebSocket Connection                         │
│                  (Real-time 2-way communication)                │
└─────────────────────────────┬───────────────────────────────────┘
                              ↕
┌─────────────────────────────┴───────────────────────────────────┐
│                           SERVER                                │
│                                                                 │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓    │
│  ┃  BACKEND                                                ┃    │
│  ┃  - FastAPI web server                                   ┃    │
│  ┃  - Manages connections from browser                     ┃    │
│  ┃  - Forwards messages to/from the agent                  ┃    │
│  ┃  - Handles audio encoding/decoding                      ┃    │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛    │
│                             ↕                                   │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓    │
│  ┃  AI AGENT                                               ┃    │
│  ┃  - Built with Google ADK (Agent Development Kit)        ┃    │
│  ┃  - Powered by Gemini                                    ┃    │
│  ┃  - Has access to tools (search, file reader, etc.)      ┃    │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛    │
│                             ↕                                   │
└─────────────────────────────┴───────────────────────────────────┘
                              ↕
                    ┌─────────────────┐
                    │  GOOGLE CLOUD   │
                    │  Gemini API     │
                    │  (LLM)          │
                    └─────────────────┘
```

**How they work together:**
1. **You** speak into your microphone or type a message in the browser
2. **Frontend** captures your voice/text and sends it to the backend server
3. **Backend Server** receives it and passes it to the AI agent
4. **AI Agent** processes your request using Google's Gemini model
5. The response flows back through the same chain in reverse

---

## In-Depth: How the WebServer Works and Is Built

### What is FastAPI and Why Do We Use It?

**FastAPI** is a modern Python web framework. Think of it as a toolkit that handles all the complex parts of building a web server, so you can focus on your application logic.

**Why FastAPI specifically?**

1. **Native async/await support**: FastAPI is built on top of `asyncio`, Python's system for concurrent programming. This is crucial for our application because we need to handle multiple things happening at the same time (receiving audio from the user while sending audio back, managing multiple users, etc.)

2. **WebSocket support**: FastAPI has built-in support for WebSocket connections, which we need for real-time bidirectional communication.

3. **Fast performance**: Despite being Python, FastAPI is very fast because it's built on `Starlette` (for web parts) and `Pydantic` (for data validation).

4. **Easy to use**: The code is readable and straightforward, which matters for maintainability.

### Understanding WebSocket Connections in Detail

Before diving into the code, let's understand what WebSockets are and why we need them.

#### What is HTTP (the traditional web)?

When you visit a normal website, here's what happens:

```
You (Client):  "Hey server, give me the homepage"
                    ↓ HTTP REQUEST
Server:        "Here's the homepage HTML"
                    ↓ HTTP RESPONSE
[Connection closes]

You (Client):  "Now give me this image"
                    ↓ NEW HTTP REQUEST
Server:        "Here's the image"
                    ↓ HTTP RESPONSE
[Connection closes again]
```

Every interaction requires:
1. Opening a new connection
2. Sending request
3. Receiving response
4. Closing connection

This is like hanging up and calling someone back for every sentence in a conversation - very inefficient for real-time applications.

#### What is WebSocket?

WebSocket is like keeping the phone line open:

```
You (Client):  "Hey server, let's open a WebSocket connection"
                    ↓ WEBSOCKET HANDSHAKE
Server:        "Connection established!"
                    
[Connection stays open]

You (Client):  "Here's some audio data"
                    → MESSAGE 1
Server:        "Got it. Here's the AI's response"
                    ← MESSAGE 2
You (Client):  "Here's more audio"
                    → MESSAGE 3
Server:        "Processing..."
                    ← MESSAGE 4

[Connection stays open until someone closes it]
```

**Key differences:**
- **Persistent**: Connection stays open
- **Bidirectional**: Both client and server can send messages anytime
- **Low latency**: No overhead of opening/closing connections
- **Efficient**: Perfect for real-time applications like chat, gaming, or voice calls

### The FastAPI WebServer Architecture

Let's break down how our server is structured, starting from the basics and building up.

#### Server Initialization

```python
# app/main.py

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Create the FastAPI application instance
app = FastAPI()

# Mount static files (HTML, CSS, JavaScript)
# This tells FastAPI: "When someone requests /static/something, 
# serve files from the 'static' directory"
app.mount("/static", StaticFiles(directory="static"), name="static")
```

**What's happening:**
1. We create a `FastAPI()` instance - this is our web server
2. We mount the static files directory - this allows the browser to load HTML, CSS, and JavaScript files

#### The Root Route

```python
from fastapi.responses import FileResponse

@app.get("/")
async def get_index():
    """When someone visits http://localhost:8000/, serve them index.html"""
    return FileResponse("static/index.html")
```

This is the simplest route - when you visit the website, it returns the HTML page.

#### The WebSocket Endpoint - Where the Magic Happens

Now for the interesting part - the WebSocket connection:

```python
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    This function handles WebSocket connections.
    URL format: ws://localhost:8000/ws/session_12345?is_audio=true
    
    - /ws/ is the WebSocket path
    - {session_id} is a variable (e.g., "session_12345")
    - ?is_audio=true is a query parameter
    """
    
    # Step 1: Accept the connection
    # This completes the WebSocket handshake
    await websocket.accept()
```

**Understanding `await websocket.accept()`:**

When the browser initiates a WebSocket connection, there's a "handshake" process:

```
Browser:  "I want to upgrade this HTTP connection to WebSocket"
          (Sends HTTP request with special headers)
          
Server:   "Okay, upgrade accepted!"
          (Sends HTTP 101 Switching Protocols response)
          
[Connection is now WebSocket, not HTTP]
```

The `await websocket.accept()` performs the server's side of this handshake.

#### Extracting Connection Parameters

```python
    # Step 2: Determine if this is audio or text mode
    # Query parameters are accessed via websocket.query_params
    is_audio = websocket.query_params.get("is_audio", "false").lower() == "true"
    
    # The session_id comes from the URL path parameter
    logger.info(f"Client {session_id} connected, audio mode: {is_audio}")
```

**How parameters work:**

URL: `ws://localhost:8000/ws/session_abc123?is_audio=true`
- `session_id` = "session_abc123" (from path)
- `is_audio` = "true" (from query parameter)

#### Starting an Agent Session

```python
    # Step 3: Initialize the AI agent for this client
    try:
        live_events, live_request_queue = await start_agent_session(
            session_id, 
            is_audio
        )
```

Let's dive into what `start_agent_session` does:

```python
async def start_agent_session(session_id: str, is_audio: bool = False):
    """
    This function sets up everything needed for an AI conversation.
    It's called once per client connection.
    """
    
    logger.info(f"Starting agent session for {session_id}, audio: {is_audio}")
    
    # Step 1: Create a session in the ADK session service
    # This creates a space for storing conversation history
    session = await session_service.create_session(
        app_name="jarvis",      # Application name
        user_id="user",         # User identifier (could be customized per user)
        session_id=session_id   # Unique session ID for this conversation
    )
```

**What is a session?** Think of it as a notebook where the AI writes down everything that happens in the conversation:
- What the user said
- How the AI responded
- Context and state

This allows the AI to remember previous messages and maintain context.

```python
    # Step 2: Create a Runner
    # The Runner is the orchestrator - it manages the AI agent
    runner = Runner(
        app_name="jarvis",
        agent=root_agent,              # The AI agent we defined
        session_service=session_service # The session manager
    )
```

**What is the Runner?** It's like a stage manager in a theater:
- It coordinates the AI agent
- It manages the conversation flow
- It handles the session lifecycle

```python
    # Step 3: Create a LiveRequestQueue
    # This is how we send messages TO the AI
    live_request_queue = LiveRequestQueue()
```

**Understanding LiveRequestQueue:**

Think of this as a mailbox:
- We (the server) put messages into this mailbox
- The AI continuously checks this mailbox for new messages
- When it finds a message, it processes it

In technical terms, it's a **queue** - a first-in-first-out (FIFO) data structure:

```
You speak:  "Hello" → [Queue: "Hello"               ] → AI reads "Hello"
You speak:  "How are you?" → [Queue: "How are you?" ] → AI reads "How are you?"
```

```python
    # Step 4: Configure response modality (audio or text)
    response_modalities = ["AUDIO"] if is_audio else ["TEXT"]
    run_config = RunConfig(response_modalities=response_modalities)
```

**What are response modalities?**

This tells the AI: "When you respond, do you want to send audio or text?"

- `["AUDIO"]`: AI will generate voice audio + text transcriptions
- `["TEXT"]`: AI will only generate text

```python
    # Step 5: Start the live runner
    # This starts the AI in "live mode" - real-time streaming
    live_events = runner.run_live(
        user_id="user",
        session_id=session_id,
        live_request_queue=live_request_queue,  # Where we send messages
        run_config=run_config                    # Configuration
    )
```

**Understanding `run_live()`:**

This is the key method that enables real-time streaming with Gemini. When you call this:

1. It establishes a connection to Google's Gemini API
2. It starts listening to the `live_request_queue` for input
3. It returns `live_events` - an **async generator** that yields responses

**What is an async generator?**

It's like a stream of events that you can iterate over:

```python
async for event in live_events:
    # Each time the AI has something to say, you get an event here
    print(f"New event: {event}")
```

Events could be:
- User's speech transcription
- AI's speech transcription
- Audio chunks
- Tool calls
- Turn completion signals

```python
    # Step 6: Store session information
    # We keep track of all active sessions in a global dictionary
    sessions[session_id] = {
        "runner": runner,
        "live_request_queue": live_request_queue,
        "live_events": live_events,
        "is_audio": is_audio,
        "session": session
    }
    
    return live_events, live_request_queue
```

**Why store sessions?** 

We maintain a global dictionary of all active sessions:

```python
sessions = {
    "session_abc123": {
        "runner": <Runner object>,
        "live_request_queue": <Queue>,
        # ... etc
    },
    "session_xyz789": {
        "runner": <Runner object>,
        "live_request_queue": <Queue>,
        # ... etc
    }
}
```

This allows us to:
- Support multiple simultaneous users
- Clean up sessions when users disconnect
- Access session info if needed

#### Bidirectional Message Handling

Now back to the WebSocket endpoint:

```python
        # Step 4: Run both message handlers concurrently
        await asyncio.gather(
            agent_to_client_messaging(websocket, live_events),
            client_to_agent_messaging(websocket, live_request_queue),
            return_exceptions=True
        )
```

**Understanding `asyncio.gather()`:**

This is where Python's async magic happens. `asyncio.gather()` runs multiple async functions **concurrently** (at the same time).

Imagine you're cooking dinner and you need to:
1. Boil water for pasta
2. Chop vegetables

**Sequential approach (bad):**
```
Start boiling water → Wait 10 minutes → Water boils → Start chopping → Wait 5 minutes → Done
Total time: 15 minutes
```

**Concurrent approach (good):**
```
Start boiling water + Start chopping → Wait 10 minutes → Both done
Total time: 10 minutes (you chop while water boils)
```

In our case:
- **Task 1**: `agent_to_client_messaging` - listens for AI responses and sends to browser
- **Task 2**: `client_to_agent_messaging` - listens for browser messages and sends to AI

Both run simultaneously, enabling full-duplex communication.

**What is `return_exceptions=True`?**

Normally, if one task crashes, it would stop everything. With `return_exceptions=True`, if one task fails, the other continues and the exception is returned as a value instead of being raised. This provides better error handling.

#### Client to Agent Messaging (Browser → AI)

Let's examine this function in detail:

```python
async def client_to_agent_messaging(websocket: WebSocket, live_request_queue: LiveRequestQueue):
    """
    This function continuously listens for messages from the browser
    and forwards them to the AI agent.
    
    It's an infinite loop that only stops when:
    - The WebSocket connection closes
    - An error occurs
    """
    
    try:
        logger.info("Starting client_to_agent_messaging loop")
        message_count = 0
```

**The main loop:**

```python
        # This is an async for loop - it waits for messages
        # websocket.iter_text() is an async generator that yields messages
        async for message in websocket.iter_text():
            message_count += 1
            logger.info(f"[MESSAGE #{message_count}] Received message")
```

**How does `websocket.iter_text()` work?**

It's an async iterator that:
1. Waits for a message to arrive on the WebSocket
2. When a message arrives, it yields the message as text
3. Goes back to step 1

It's like having a mailbox where you wait for letters:

```python
# Pseudo-code for how iter_text() works internally
async def iter_text():
    while connection_is_open:
        message = await wait_for_next_message()
        yield message  # Give the message to your code
```

**Parsing the message:**

```python
            try:
                # Messages come as JSON strings, so we parse them
                data = json.loads(message)
                mime_type = data.get("mime_type")
                content_data = data.get("data")
                
                logger.info(f"Parsed: mime_type={mime_type}")
```

Messages from the browser look like:
```json
{
  "mime_type": "audio/pcm",
  "data": "AAECAwQFBgcICQ..."
}
```

or

```json
{
  "mime_type": "text/plain",
  "data": "Hello, what's the weather?"
}
```

**Handling audio messages:**

```python
                if mime_type == "audio/pcm":
                    # The audio data is Base64 encoded, so we decode it
                    audio_data = base64.b64decode(content_data)
                    
                    logger.info(f"Decoded {len(audio_data)} bytes of audio")
```

**What is Base64?**

Binary data (like audio) is a series of bytes that can have any value (0-255). JSON, however, is text and can only contain certain characters. Base64 encoding converts binary data into text using only safe characters (A-Z, a-z, 0-9, +, /).

Example:
```
Binary:  [0xFF, 0xA1, 0x3C, 0x00]  (4 bytes)
Base64:  "/6E8AA=="  (8 characters)
```

**Why decode?** We need the actual binary audio bytes to send to Gemini, not the text representation.

```python
                    # Create a Blob object - this is ADK's format for audio
                    audio_blob = types.Blob(
                        mime_type="audio/pcm;rate=16000",  # Include sample rate
                        data=audio_data
                    )
```

**What is a Blob?**

In the context of Google ADK, a `Blob` is a structured object that contains:
- `mime_type`: What kind of data this is (e.g., "audio/pcm;rate=16000")
- `data`: The actual binary data

The mime type `"audio/pcm;rate=16000"` tells Gemini:
- Format: PCM (raw audio)
- Sample rate: 16,000 samples per second

```python
                    # Send to the AI agent's input queue
                    live_request_queue.send_realtime(audio_blob)
                    
                    logger.info("✅ Audio sent to agent")
```

**Understanding `send_realtime()`:**

This method puts the audio into the queue that the AI is monitoring. The method name `send_realtime` indicates this is for real-time streaming audio (as opposed to `send_content` for text or complete audio files).

Internally, it:
1. Adds the audio to the queue
2. The AI's streaming processor picks it up
3. Gemini processes it in real-time

**Handling text messages:**

```python
                elif mime_type == "text/plain":
                    logger.info(f"Processing text: {content_data}")
                    
                    # Create a Content object for text
                    content = types.Content(
                        role="user",  # This message is from the user
                        parts=[types.Part(text=content_data)]
                    )
                    
                    live_request_queue.send_content(content)
                    logger.info("✅ Text sent to agent")
```

**Understanding Content and Part:**

These are ADK's structured formats for messages:

- `Content`: Represents a complete message with:
  - `role`: Who sent it ("user" or "model")
  - `parts`: A list of parts (a message can have multiple parts)

- `Part`: A piece of content, can be:
  - Text (`Part(text="...")`)
  - Inline data (`Part(inline_data=blob)`)
  - Function call (`Part(function_call=...)`)
  - etc.

Example of a multi-part message:
```python
Content(
    role="user",
    parts=[
        Part(text="Look at this image:"),
        Part(inline_data=Blob(mime_type="image/jpeg", data=image_bytes))
    ]
)
```

**Error handling:**

```python
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Raw message: {message[:200]}...")
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
```

This catches and logs errors without crashing the entire connection.

```python
    except Exception as e:
        logger.error(f"Error in client_to_agent_messaging: {e}", exc_info=True)
        raise  # Re-raise to trigger cleanup
```

The outer try-except catches fatal errors and re-raises them so the connection cleanup code runs.

#### Agent to Client Messaging (AI → Browser)

Now let's examine the reverse direction:

```python
async def agent_to_client_messaging(websocket: WebSocket, live_events: AsyncGenerator):
    """
    This function continuously listens for events from the AI agent
    and forwards them to the browser.
    """
    
    try:
        logger.info("Starting agent_to_client_messaging loop")
        
        # Track state for handling streaming
        has_sent_partial = False
        last_input_transcription = None
        last_output_transcription = None
```

**Why track state?**

The AI sends responses in chunks (streaming). We need to track:
- Have we already sent partial chunks? (to avoid duplicating the final message)
- What was the last transcription? (to avoid sending duplicates)

**The event loop:**

```python
        # Iterate over events from the AI
        async for event in live_events:
```

**What is `live_events`?**

Remember, this was returned by `runner.run_live()`. It's an async generator that yields events whenever the AI has something to communicate.

**Event types:**

```python
            # Extract transcription information from the event
            input_transcription = getattr(event, 'input_transcription', None)
            output_transcription = getattr(event, 'output_transcription', None)
            
            logger.info(
                f"Event: turn_complete={event.turn_complete}, "
                f"has_content={event.content is not None}, "
                f"input_transcription={input_transcription}, "
                f"output_transcription={output_transcription}"
            )
```

**Understanding `getattr()`:**

`getattr(object, 'attribute', default)` safely gets an attribute from an object:
- If the attribute exists, return its value
- If it doesn't exist, return the default

This is safer than `event.input_transcription` which would crash if the attribute doesn't exist.

**Handling input transcriptions (what the user said):**

```python
            if input_transcription:
                # Log the transcription object structure
                logger.info(f"Input transcription object: {input_transcription}")
                
                # Extract text and finished status
                transcription_text = None
                is_finished = None
                
                if hasattr(input_transcription, 'text'):
                    transcription_text = input_transcription.text
                    is_finished = getattr(input_transcription, 'finished', None)
                elif isinstance(input_transcription, str):
                    transcription_text = input_transcription
                    is_finished = True
```

**Why check `hasattr` and `isinstance`?**

The transcription could come in different formats:
1. As an object with `.text` and `.finished` attributes
2. As a simple string

We handle both cases to be robust.

**Understanding the `finished` flag:**

When Gemini processes your voice, it sends partial transcriptions as you speak:

```
You say: "What's the weather today?"

Gemini sends:
- Transcription: "What", finished=False
- Transcription: "What's the", finished=False
- Transcription: "What's the weather", finished=False
- Transcription: "What's the weather today?", finished=True
```

We only want to display the final transcription to avoid showing:
```
User: What
User: What's the
User: What's the weather
User: What's the weather today?
```

Instead, we wait for `finished=True` and show just:
```
User: What's the weather today?
```

**Sending transcriptions to the browser:**

```python
                if transcription_text:
                    last_input_transcription = transcription_text
                    
                    logger.info(f"Input transcription: '{transcription_text}', finished={is_finished}")
                    
                    # Only send when finished
                    if is_finished is True or is_finished is None:
                        logger.info("✅ Sending FINAL input transcription")
                        
                        await websocket.send_json({
                            "mime_type": "text/plain",
                            "data": transcription_text,
                            "turn_complete": False,
                            "is_user_transcription": True
                        })
                    else:
                        logger.info("⏭️ Skipping partial transcription")
```

**Understanding `websocket.send_json()`:**

This method:
1. Converts a Python dictionary to JSON string
2. Sends it over the WebSocket

It's equivalent to:
```python
json_string = json.dumps(data)
await websocket.send_text(json_string)
```

**Handling output transcriptions** works the same way but with `is_agent_transcription`:

```python
            if output_transcription:
                # ... similar logic ...
                if is_finished is True or is_finished is None:
                    await websocket.send_json({
                        "mime_type": "text/plain",
                        "data": transcription_text,
                        "turn_complete": False,
                        "is_agent_transcription": True
                    })
```

**Handling content (text or audio responses):**

```python
            # Skip events from user (echoes)
            if hasattr(event, 'author') and event.author == 'user':
                logger.info("Skipping user echo event")
                continue
```

**Why skip user echoes?**

Sometimes the AI system echoes back the user's input. We don't want to process these as AI responses.

```python
            # Handle content
            if event.content:
                # Check if this is a partial event (streaming)
                is_partial = getattr(event, 'partial', False)
```

**Understanding `partial` events:**

When the AI generates a response, it can send it:
1. All at once (non-partial): "Here's the complete response"
2. In chunks (partial): "Here's", " the", " complete", " response"

Streaming (partial) creates a better user experience - the user sees the response appearing word by word, like ChatGPT.

```python
                # Handle text content
                if hasattr(event.content, 'parts') and event.content.parts:
                    for idx, part in enumerate(event.content.parts):
                        text_value = getattr(part, 'text', None)
                        
                        if text_value:
                            if is_partial:
                                # Send streaming chunks
                                logger.info(f"Sending partial text: {text_value[:50]}...")
                                await websocket.send_json({
                                    "mime_type": "text/plain",
                                    "data": text_value,
                                    "turn_complete": False
                                })
                                has_sent_partial = True
                            elif not has_sent_partial:
                                # Only send final text if we didn't stream
                                await websocket.send_json({
                                    "mime_type": "text/plain",
                                    "data": text_value,
                                    "turn_complete": False
                                })
```

**The streaming strategy:**

```
Scenario 1 - Streaming mode:
Event 1: text="Hello", partial=True → Send "Hello"
Event 2: text=" there", partial=True → Send " there"
Event 3: text="Hello there", partial=False → Skip (already sent)

Result: User sees "Hello" then " there" appears

Scenario 2 - Non-streaming mode:
Event 1: text="Hello there", partial=False → Send "Hello there"

Result: User sees "Hello there" appear all at once
```

**Handling audio content:**

```python
                        # Check for inline data (audio)
                        elif getattr(part, 'inline_data', None):
                            inline_data = part.inline_data
                            mime_type = getattr(inline_data, 'mime_type', '')
                            
                            # Check if it's audio
                            if mime_type and mime_type.startswith('audio/pcm'):
                                data = getattr(inline_data, 'data', None)
                                if data:
                                    # Encode binary audio to Base64
                                    base64_audio = base64.b64encode(data).decode('utf-8')
                                    
                                    logger.info(f"Sending audio: {len(data)} bytes")
                                    
                                    await websocket.send_json({
                                        "mime_type": "audio/pcm",
                                        "data": base64_audio,
                                        "turn_complete": False
                                    })
```

**Why encode to Base64?**

We're sending over WebSocket as JSON (text), so we convert binary audio to text using Base64.

**Handling turn completion:**

```python
            # Signal when AI finishes responding
            if event.turn_complete is True:
                logger.info("Sending turn completion signal")
                await websocket.send_json({
                    "mime_type": "text/plain",
                    "data": "",
                    "turn_complete": True
                })
                # Reset for next turn
                has_sent_partial = False
```

**What is `turn_complete`?**

A "turn" is one complete interaction:
1. User speaks/types (user's turn)
2. AI responds (AI's turn)
3. `turn_complete=True` signals: "AI is done, user can speak again"

This is important for:
- UI updates (show/hide loading indicators)
- Microphone control (enable microphone button)
- State management (ready for next input)

#### Connection Cleanup

```python
    except WebSocketDisconnect:
        logger.info(f"Client #{session_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        # Always clean up, even if there was an error
        if session_id in sessions:
            del sessions[session_id]
```

**Understanding `finally`:**

The `finally` block **always** runs, whether:
- The code completed successfully
- An exception was raised
- The connection was closed

This ensures we always clean up resources (delete session info, free memory).

#### Running the Server

```python
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

**What is uvicorn?**

Uvicorn is an ASGI server - the actual program that runs your FastAPI application.

- `host="0.0.0.0"`: Listen on all network interfaces (makes server accessible from other devices)
- `port=8000`: Use port 8000
- `reload=True`: Automatically restart when code changes (development mode)

**ASGI vs WSGI:**

- **WSGI** (Web Server Gateway Interface): Old standard, synchronous only
- **ASGI** (Asynchronous Server Gateway Interface): New standard, supports async/await

FastAPI requires ASGI because it uses async/await extensively.

---

## In-Depth: How Audio Interaction Works

Audio interaction is the most complex part of the system. Let's build understanding from the ground up.

### Fundamentals: What is Digital Audio?

Before we can understand the code, we need to understand what audio is in digital form.

#### Sound as a Wave

Sound is a pressure wave in the air. When you speak:
1. Your vocal cords vibrate
2. This creates pressure waves in the air
3. These waves hit the microphone's membrane
4. The membrane vibrates
5. This vibration is converted to an electrical signal

#### Analog to Digital Conversion

The microphone produces an **analog** signal - a continuous electrical voltage that varies with the sound:

```
Voltage over time:
     ___
    /   \___    ___
___/        \__/   \___
```

Computers can't work with continuous signals - they need discrete (separate) values. This is where **sampling** comes in.

**Sampling** means measuring the voltage at regular intervals:

```
Original signal:      ___
                     /   \___    ___
                 ___/        \__/   \___
                 
Samples (points): •   • •  •  •  • •  •   •
                 │   │ │  │  │  │ │  │   │
Values:         [0,  2,4,5,4,3,1,-1,-2]
```

Each **sample** is a number representing the sound pressure at that instant.

#### Sample Rate

**Sample Rate** is how many samples we take per second, measured in Hertz (Hz).

Examples:
- **8,000 Hz**: 8,000 samples per second (phone quality)
- **16,000 Hz**: 16,000 samples per second (voice recognition quality)
- **48,000 Hz**: 48,000 samples per second (professional audio quality)

**Nyquist-Shannon Theorem:** To capture a frequency, you need to sample at **at least twice** that frequency.

Human hearing range: 20 Hz to 20,000 Hz

Therefore:
- To capture all human hearing: Need 40,000 Hz minimum
- For voice (100 Hz to 8,000 Hz): Need 16,000 Hz minimum

This is why voice applications use 16 kHz!

#### Bit Depth

Each sample is a number. **Bit depth** determines how precise that number is.

- **8-bit**: 256 possible values (0 to 255)
- **16-bit**: 65,536 possible values (-32,768 to 32,767)
- **32-bit float**: Billions of possible values (-1.0 to 1.0)

Higher bit depth = more precise = better quality but larger files.

Our system uses:
- **Int16** (16-bit integers) for transmission (efficient)
- **Float32** (32-bit floats) for processing (precise)

#### PCM Format

**PCM** (Pulse Code Modulation) is the simplest audio format - just the raw samples:

```
File contents: [sample1, sample2, sample3, sample4, ...]
Example: [0, 256, 512, 256, 0, -256, -512, -256, 0, ...]
```

No compression, no encoding - just pure data.

**Why PCM for our application?**
1. **No encoding/decoding overhead** - instant processing
2. **Lossless** - perfect quality
3. **Simple** - easy to work with
4. **Efficient for real-time** - no compression delay

### Web Audio API: The Browser's Audio Engine

The **Web Audio API** is a powerful system built into modern browsers for processing and synthesizing audio.

#### AudioContext: The Audio Processing Graph

Think of `AudioContext` as a complete audio studio in your browser:

```javascript
const audioContext = new AudioContext();
```

When you create an AudioContext, you get:
- Sample rate (usually 48000 Hz)
- Audio processing graph system
- Timing and synchronization
- Access to audio hardware

#### Audio Nodes and Connections

Audio in the Web Audio API flows through **nodes** connected like a pipeline:

```
[Source] → [Processor 1] → [Processor 2] → [Destination]
```

Example nodes:
- **MediaStreamSource**: Captures microphone input
- **AudioWorkletNode**: Custom audio processing
- **GainNode**: Volume control
- **Destination**: Speakers

You connect them:
```javascript
source.connect(processor);
processor.connect(destination);
```

Now audio flows: Microphone → Processor → Speakers

#### The Main Thread Problem

JavaScript runs on a **single thread** - one thing at a time:

```
Main Thread:
[Handle click] → [Update UI] → [Process audio] → [Animate] → [Handle click] → ...
```

If [Process audio] takes too long, everything else waits:
- UI freezes
- Animations stutter
- Audio glitches

This is unacceptable for real-time audio!

#### AudioWorklets: Dedicated Audio Threads

**AudioWorklets** solve this by running audio processing on a **separate thread**:

```
Main Thread:  [Handle clicks] → [Update UI] → [Animate] → ...
                    ↕ (messages)
Audio Thread: [Process audio] → [Process audio] → [Process audio] → ...
```

Audio processing runs continuously at high priority, unaffected by what's happening on the main thread.

### The Recording Pipeline: Microphone to Server

Let's trace audio from your microphone to the server, step by step.

#### Step 1: Requesting Microphone Access

```javascript
// app/static/js/app.js

const stream = await navigator.mediaDevices.getUserMedia({ 
    audio: true 
});
```

**What happens:**
1. Browser shows permission prompt: "Allow microphone access?"
2. If user approves, browser returns a `MediaStream`
3. The MediaStream represents the live audio from the microphone

**MediaStream** is like a live TV broadcast - continuous audio data flowing in real-time.

#### Step 2: Creating the Audio Context

```javascript
this.audioContext = new AudioContext();
console.log(`Audio context sample rate: ${this.audioContext.sampleRate} Hz`);
// Usually logs: "Audio context sample rate: 48000 Hz"
```

**Why 48000 Hz?**

This is the default sample rate for most modern audio hardware. It's chosen because:
- High enough quality for professional audio
- Compatible with video (which uses 48 kHz)
- Hardware-optimized

#### Step 3: Loading Audio Worklets

```javascript
await this.audioContext.audioWorklet.addModule(
    '/static/js/pcm-recorder-processor.js'
);
```

**What is addModule doing?**

1. Fetches the JavaScript file
2. Runs it in the **Audio Worklet global scope** (separate from main thread)
3. Registers the processor class defined in that file

After this, you can create instances of the processor.

#### Step 4: Creating the Recorder Worklet Node

```javascript
this.audioRecorderNode = new AudioWorkletNode(
    this.audioContext,
    'pcm-recorder-processor'  // Name registered in the worklet file
);
```

This creates an instance of our custom audio processor running on the audio thread.

#### Step 5: Connecting the Audio Graph

```javascript
const source = this.audioContext.createMediaStreamSource(stream);
source.connect(this.audioRecorderNode);
```

Now audio flows:
```
Microphone → MediaStreamSource → AudioRecorderNode → [We'll send data to server]
```

#### Step 6: Inside the Recorder Worklet

Let's dive deep into `pcm-recorder-processor.js`:

```javascript
// app/static/js/pcm-recorder-processor.js

class PCMRecorderProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.buffer = [];             // Accumulate samples here
        this.downsampleFactor = 3;    // 48000 / 16000 = 3
        this.sampleCounter = 0;
    }
```

**Understanding the class structure:**

- `extends AudioWorkletProcessor`: This makes it an audio processor
- `constructor()`: Runs once when the processor is created
- `buffer`: We accumulate samples here before sending them
- `downsampleFactor`: How much to reduce the sample rate

**The process() method:**

This is the heart of the audio processor. It's called automatically about **375 times per second** (128 samples at 48 kHz = 128/48000 = 2.67ms per call).

```javascript
    process(inputs, outputs, parameters) {
```

**Parameters:**
- `inputs`: Array of input audio (from microphone)
- `outputs`: Array of output audio (we don't use this for recording)
- `parameters`: Audio parameters (we don't use these)

**Structure of inputs:**
```javascript
inputs = [
    [  // Input 0 (our microphone)
        Float32Array(128),  // Channel 0 (left/mono)
        Float32Array(128)   // Channel 1 (right, if stereo)
    ]
]
```

**Getting the audio data:**

```javascript
        const inputChannel = inputs[0][0];  // Get first input, first channel
```

This gives us a Float32Array of 128 samples. Each sample is a number between -1.0 and 1.0 representing the audio amplitude.

**Downsampling logic:**

```javascript
        for (let i = 0; i < inputChannel.length; i++) {
            this.sampleCounter++;
            
            if (this.sampleCounter >= this.downsampleFactor) {
                this.sampleCounter = 0;
                this.buffer.push(inputChannel[i]);
```

**Why downsample?**

We're converting 48 kHz to 16 kHz. The simplest way: **keep every 3rd sample, discard the rest**.

```
48 kHz input samples:  [s1, s2, s3, s4, s5, s6, s7, s8, s9, ...]
Keep every 3rd:        [s1, ---, ---, s4, ---, ---, s7, ---, ---, ...]
16 kHz output:         [s1,           s4,           s7,           ...]
```

This is called **decimation** - a simple form of downsampling.

**More sophisticated downsampling** (not implemented here) would use a low-pass filter first to prevent aliasing, but for voice, simple decimation works fine.

**Buffering samples:**

```javascript
                if (this.buffer.length >= 4096) {
                    this.sendPCMData();
                }
            }
        }
        
        return true;  // Keep processor alive
    }
```

**Why buffer 4096 samples?**

We don't want to send every single sample immediately - that would be inefficient (too many tiny messages). Instead, we accumulate 4096 samples (about 256 milliseconds of audio at 16 kHz) and send them in chunks.

**The `return true` is critical** - if you return `false`, the processor shuts down.

**Converting and sending data:**

```javascript
    sendPCMData() {
        // Convert Float32 to Int16
        const float32Array = new Float32Array(this.buffer);
        const int16Array = new Int16Array(float32Array.length);
        
        for (let i = 0; i < float32Array.length; i++) {
            // Clamp value to [-1.0, 1.0]
            const sample = Math.max(-1, Math.min(1, float32Array[i]));
            
            // Convert to 16-bit integer
            int16Array[i] = sample < 0 
                ? sample * 0x8000  // 0x8000 = 32768
                : sample * 0x7FFF; // 0x7FFF = 32767
        }
```

**Why convert Float32 to Int16?**

- **Float32**: 4 bytes per sample
- **Int16**: 2 bytes per sample

Int16 uses half the bandwidth! For 16 kHz audio:
- Float32: 16000 samples/sec × 4 bytes = 64 KB/sec
- Int16: 16000 samples/sec × 2 bytes = 32 KB/sec

**The conversion formula:**

Float32 audio uses values from -1.0 to +1.0. Int16 uses -32768 to +32767.

For negative values:
```
Float: -1.0 to 0.0
Int16: -32768 to 0

Formula: float × 32768
Example: -0.5 × 32768 = -16384
```

For positive values:
```
Float: 0.0 to +1.0
Int16: 0 to +32767

Formula: float × 32767
Example: 0.5 × 32767 = 16383.5 ≈ 16383
```

**Sending to main thread:**

```javascript
        this.port.postMessage({
            type: 'pcmData',
            pcmData: int16Array.buffer  // Send the ArrayBuffer
        });
        
        this.buffer = [];  // Clear buffer
    }
}

// Register the processor
registerProcessor('pcm-recorder-processor', PCMRecorderProcessor);
```

**Understanding `postMessage`:**

This is how audio worklet (separate thread) communicates with the main thread:

```
Audio Thread:  port.postMessage(data) ───────┐
                                             │
                                             ↓
Main Thread:   port.onmessage = (event) ← event.data
```

It's asynchronous and thread-safe.

#### Step 7: Main Thread Receives and Encodes

Back in the main thread:

```javascript
// app/static/js/app.js

this.audioRecorderNode.port.onmessage = (event) => {
    if (event.data.type === 'pcmData') {
        this.audioRecorderHandler(event.data.pcmData);
    }
};
```

The handler processes the audio:

```javascript
audioRecorderHandler(pcmData) {
    // Convert ArrayBuffer to Base64
    const base64Audio = this.arrayBufferToBase64(pcmData);
    
    // Send to server
    this.sendMessage('audio/pcm', base64Audio);
}
```

**Base64 encoding in detail:**

```javascript
arrayBufferToBase64(buffer) {
    // Step 1: Convert ArrayBuffer to Uint8Array
    const bytes = new Uint8Array(buffer);
    
    // Step 2: Convert to binary string
    let binary = '';
    for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    
    // Step 3: Encode to Base64
    return window.btoa(binary);
}
```

**Why this multi-step process?**

JavaScript's `btoa()` (Binary TO ASCII) expects a string where each character represents one byte. We convert:

```
ArrayBuffer → Uint8Array → Binary String → Base64
[buffer]    → [0,255,128] → "\x00\xFF\x80" → "AP+A"
```

#### Step 8: Sending to Server

```javascript
sendMessage(mimeType, data) {
    this.websocket.send(JSON.stringify({
        mime_type: mimeType,
        data: data
    }));
}
```

This sends a JSON message over the WebSocket:

```json
{
  "mime_type": "audio/pcm",
  "data": "AAECAwQFBgc..."
}
```

### The Playback Pipeline: Server to Speakers

Now let's trace audio coming back from the AI.

#### Step 1: Receiving from Server

```javascript
// app/static/js/app.js

this.websocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    this.handleServerMessage(data);
};

handleServerMessage(data) {
    if (data.mime_type === 'audio/pcm') {
        this.playAudioChunk(data.data);
    }
    // ... handle other message types ...
}
```

#### Step 2: Decoding Base64

```javascript
playAudioChunk(base64Audio) {
    // Convert Base64 to ArrayBuffer
    const audioData = this.base64ToArrayBuffer(base64Audio);
    
    // Send to player worklet
    this.audioPlayerNode.port.postMessage({
        type: 'playAudio',
        audioData: audioData
    });
}

base64ToArrayBuffer(base64) {
    // Step 1: Decode Base64 to binary string
    const binaryString = window.atob(base64);
    
    // Step 2: Convert binary string to Uint8Array
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    
    // Step 3: Return the ArrayBuffer
    return bytes.buffer;
}
```

This is the reverse of encoding:

```
Base64 → Binary String → Uint8Array → ArrayBuffer
"AP+A" → "\x00\xFF\x80" → [0,255,128] → [buffer]
```

#### Step 3: Inside the Player Worklet

Now let's dive into `pcm-player-processor.js`:

```javascript
// app/static/js/pcm-player-processor.js

class PCMPlayerProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.audioQueue = [];           // Queue of pending audio chunks
        this.currentBuffer = null;      // Currently playing buffer
        this.bufferIndex = 0;           // Position in current buffer
        this.sampleRate = 24000;        // Gemini outputs 24 kHz
        this.outputSampleRate = 48000;  // Browser expects 48 kHz
        this.resampleRatio = 2.0;       // 48000 / 24000 = 2
        this.resampleIndex = 0;
```

**Understanding the queue system:**

Multiple audio chunks arrive from the server. We need to:
1. Queue them in order
2. Play them smoothly without gaps
3. Handle chunks arriving while playing

```
Queue: [Chunk1, Chunk2, Chunk3]
       ↓
Currently playing: Chunk1
       ↓
When done: Move to Chunk2
```

**Receiving audio chunks:**

```javascript
        this.port.onmessage = (event) => {
            if (event.data.type === 'playAudio') {
                this.audioQueue.push(event.data.audioData);
            }
        };
    }
```

When a chunk arrives, add it to the queue.

**The process() method:**

```javascript
    process(inputs, outputs, parameters) {
        const outputChannel = outputs[0][0];  // 128 samples to fill
```

**This is called ~375 times per second** to fill the audio output buffer. Each call must fill 128 samples.

**Filling the output buffer:**

```javascript
        for (let i = 0; i < outputChannel.length; i++) {
            // Do we have audio to play?
            if (this.currentBuffer && this.bufferIndex < this.currentBuffer.length) {
```

**The upsampling logic:**

```javascript
                // Get sample from current buffer (Int16)
                const int16Sample = this.currentBuffer[this.bufferIndex];
                
                // Convert Int16 to Float32
                const float32Sample = int16Sample / 32768.0;
                outputChannel[i] = float32Sample;
```

**The conversion:**

```
Int16 range: -32768 to +32767
Float32 range: -1.0 to +1.0

Formula: int16 / 32768
Examples:
  32767 / 32768 ≈ 0.999 (almost 1.0)
  0 / 32768 = 0.0
  -32768 / 32768 = -1.0
```

**The resampling logic:**

```javascript
                // Upsampling: play each sample multiple times
                this.resampleIndex++;
                if (this.resampleIndex >= this.resampleRatio) {
                    this.resampleIndex = 0;
                    this.bufferIndex++;  // Move to next sample
                }
```

**How upsampling works:**

We're converting 24 kHz to 48 kHz. We play each sample **twice**:

```
24 kHz input:  [s1,     s2,     s3,     s4,     ...]
48 kHz output: [s1, s1, s2, s2, s3, s3, s4, s4, ...]
               ↑───↑ ↑───↑ ↑───↑ ↑───↑
               repeat each sample twice
```

This is simple but effective for voice. More sophisticated upsampling would use interpolation:

```javascript
// Linear interpolation (not implemented)
const nextSample = this.currentBuffer[this.bufferIndex + 1];
const interpolated = currentSample + (nextSample - currentSample) * 0.5;
```

**Handling buffer transitions:**

```javascript
            } else {
                // No audio - play silence
                outputChannel[i] = 0;
                
                // Try to load next chunk from queue
                if (this.audioQueue.length > 0) {
                    const nextChunk = this.audioQueue.shift();
                    this.currentBuffer = new Int16Array(nextChunk);
                    this.bufferIndex = 0;
                    this.resampleIndex = 0;
                }
            }
        }
        
        return true;  // Keep processing
    }
}
```

**What happens when we run out of audio?**
1. Play silence (0 values)
2. Check if more chunks are in the queue
3. If yes, load the next chunk
4. If no, keep playing silence until more arrives

**Handling gaps:**

If the network is slow and chunks don't arrive fast enough:
```
Playing: [Chunk1] → silence → silence → [Chunk2 arrives] → [Chunk2]
                    ↑ gap ↑
```

The user hears a brief silence/glitch. This is why low latency matters!

### Gemini Audio Mode: How It All Connects

Now let's understand how Gemini handles audio natively.

#### Traditional Speech Pipeline

Most AI assistants use three separate systems:

```
Your voice → [Speech-to-Text Model] → Text: "What's the weather?"
                                        ↓
                          [Language Model] → Text: "It's sunny, 72°F"
                                        ↓
                          [Text-to-Speech Model] → Audio: "It's sunny..."
                                        ↓
                                    Your speakers
```

**Problems with this approach:**
1. **Three models** = three costs, three latencies
2. **Information loss**: Voice tone → text → voice loses emotional content
3. **Complex integration**: Three different APIs to manage

#### Gemini 2.0 Flash Native Audio

Gemini 2.0 Flash does it differently:

```
Your voice (16 kHz PCM) → [Gemini 2.0 Flash] → Audio (24 kHz PCM) + Transcriptions
                          Single Model
```

**Inside Gemini** (this is abstracted from us, but conceptually):

```
Audio Input (16 kHz PCM)
    ↓
[Audio Encoder]
    ↓
Latent Audio Representation
    ↓
[Language Understanding + Generation]
    ↓
Latent Response Representation
    ↓                     ↓
[Audio Decoder]      [Text Decoder]
    ↓                     ↓
Audio Output         Text Transcriptions
(24 kHz PCM)         (What was said)
```

The model processes audio in its native form, using **multimodal embeddings** that preserve tonal and emotional information.

#### Configuring Audio Mode in ADK

```python
# app/main.py

response_modalities = ["AUDIO"] if is_audio else ["TEXT"]
run_config = RunConfig(response_modalities=response_modalities)

live_events = runner.run_live(
    user_id="user",
    session_id=session_id,
    live_request_queue=live_request_queue,
    run_config=run_config
)
```

**What `response_modalities=["AUDIO"]` does:**

It tells Gemini: "Your responses should include audio." Gemini then:
1. Accepts audio input directly (no STT needed)
2. Generates audio output directly (no TTS needed)
3. Also provides text transcriptions (for UI display)

#### Sending Audio to Gemini

```python
# When audio arrives from the browser
audio_data = base64.b64decode(content_data)

audio_blob = types.Blob(
    mime_type="audio/pcm;rate=16000",  # Specify format and rate
    data=audio_data
)

live_request_queue.send_realtime(audio_blob)
```

**Understanding `send_realtime()`:**

This method is specifically for real-time streaming audio:
- Audio is sent as soon as it arrives
- Gemini starts processing immediately (doesn't wait for complete sentence)
- This enables low-latency interaction

**The mime type `audio/pcm;rate=16000`:**
- `audio/pcm`: Raw PCM format
- `rate=16000`: 16,000 samples per second

This tells Gemini exactly how to interpret the binary data.

#### Receiving Audio from Gemini

Gemini sends back events through the `live_events` stream:

```python
async for event in live_events:
    # Input transcription (what user said)
    if event.input_transcription:
        text = event.input_transcription.text
        # Display: "User: What's the weather?"
    
    # Output transcription (what AI is saying)
    if event.output_transcription:
        text = event.output_transcription.text
        # Display: "Jarvis: It's sunny and 72 degrees"
    
    # Audio chunks (the actual voice)
    if event.content and hasattr(event.content, 'parts'):
        for part in event.content.parts:
            if hasattr(part, 'inline_data'):
                if part.inline_data.mime_type.startswith('audio/pcm'):
                    audio_data = part.inline_data.data
                    # This is binary PCM at 24 kHz
```

**Why 24 kHz output?**

Gemini outputs at 24 kHz because:
1. Higher quality than 16 kHz input (better for speech synthesis)
2. Still efficient (not as large as 48 kHz)
3. Easy to upsample to 48 kHz (exactly 2x)

#### The Complete Audio Journey - Detailed Timeline

Let's trace one complete interaction with precise timing:

```
T=0.000s: User starts speaking "What's the weather?"

T=0.256s: First audio chunk (4096 samples @ 16kHz) ready
          - Downsampled from 48kHz to 16kHz
          - Converted Float32 to Int16
          - Encoded to Base64
          - Sent via WebSocket

T=0.260s: Server receives chunk
          - Decodes Base64
          - Wraps in Blob
          - Sends to Gemini via live_request_queue

T=0.512s: Second audio chunk sent
T=0.768s: Third audio chunk sent
T=1.024s: Fourth audio chunk sent
T=1.024s: User finishes speaking

T=1.100s: Gemini has received enough audio to start processing
          - Internal STT: "What's the weather?"
          - Sends input_transcription event
          
T=1.110s: Server receives input_transcription
          - Forwards to browser via WebSocket
          
T=1.115s: Browser displays: "User: What's the weather?"

T=1.200s: Gemini completes language understanding
          - Decides to use Google Search tool
          - Sends function_call event
          
T=1.250s: Google Search tool executes
          - Finds weather information
          - Returns result to Gemini
          
T=1.300s: Gemini generates response
          - Text: "It's sunny and 72 degrees in San Francisco"
          - Simultaneously generates audio
          
T=1.350s: First audio chunk generated (24kHz PCM)
          - Gemini sends output_transcription event
          - Gemini sends first audio content part
          
T=1.360s: Server receives events
          - Encodes audio to Base64
          - Sends both transcription and audio to browser
          
T=1.365s: Browser receives messages
          - Displays: "Jarvis: It's sunny and 72 degrees..."
          - Decodes audio Base64 to ArrayBuffer
          - Sends to player worklet
          
T=1.366s: Player worklet queues audio
          
T=1.367s: Audio starts playing
          - Upsampled from 24kHz to 48kHz
          - Converted Int16 to Float32
          - Sent to speakers
          
T=1.400s: Second audio chunk arrives
T=1.450s: Third audio chunk arrives
...

T=2.500s: Final audio chunk
          - Gemini sends turn_complete event
          
T=2.510s: Browser receives turn_complete
          - Shows microphone button (ready for next input)
          - User can speak again

Total latency: ~1.37 seconds from speaking to hearing response
```

**Latency breakdown:**
- Recording + transmission: 260ms
- Gemini processing (STT + LLM + TTS): 850ms
- Response transmission + playback start: 70ms
- Total: ~1180ms (1.2 seconds)

This is excellent for a natural conversation!

### Summary: The Audio System

**Recording side:**
1. Microphone → AudioContext (48 kHz)
2. AudioRecorderWorklet downsamples to 16 kHz
3. Converts Float32 → Int16
4. Encodes to Base64
5. WebSocket → Server
6. Server decodes and forwards to Gemini

**Playback side:**
1. Gemini generates audio (24 kHz PCM)
2. Server encodes to Base64
3. WebSocket → Browser
4. Browser decodes Base64
5. AudioPlayerWorklet upsamples to 48 kHz
6. Converts Int16 → Float32
7. Speakers output

**Key optimizations:**
- **AudioWorklets**: Separate threads for glitch-free processing
- **PCM format**: No encoding overhead
- **Streaming**: Audio plays as it arrives
- **Native audio in Gemini**: No separate STT/TTS needed

---

## The Three Main Components

### 1. The Frontend

**File Location:** `app/static/index.html` and `app/static/js/app.js`

#### How the Frontend Handles Audio

The frontend uses **AudioWorklets** - think of these as specialized workers that handle audio in the background without slowing down your browser.

There are **two audio worklets**:

1. **Recorder Worklet** (`pcm-recorder-processor.js`): Captures your voice
   - Takes audio from your microphone
   - Processes it (downsamples from 48kHz to 16kHz - we'll explain this later)
   - Sends it to the server

2. **Player Worklet** (`pcm-player-processor.js`): Plays the AI's voice
   - Receives audio from the server
   - Processes it (upsamples from 24kHz to 48kHz)
   - Plays it through your speakers

**Why use worklets?** Audio processing is very time-sensitive. If you do it on the main thread, your browser could freeze or stutter. Worklets run in separate threads, keeping everything smooth.

---

### 2. The Backend Server

**What is it?**  
It's built using **FastAPI**, which is a modern Python framework for creating web servers.

**File Location:** `app/main.py`

#### How the Backend is Built

```python
# app/main.py (simplified)

from fastapi import FastAPI, WebSocket
from google.adk import Runner
from google.adk.runners import LiveRequestQueue

# Create the web server
app = FastAPI()

# WebSocket endpoint - this is where browsers connect
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    # Accept the connection
    await websocket.accept()
    
    # Check if this is audio or text mode
    is_audio = websocket.query_params.get("is_audio") == "true"
    
    # Start an AI agent session for this user
    live_events, live_request_queue = await start_agent_session(
        session_id, 
        is_audio
    )
    
    # Run two tasks simultaneously:
    # 1. Listen to messages from browser → send to AI
    # 2. Listen to messages from AI → send to browser
    await asyncio.gather(
        client_to_agent_messaging(websocket, live_request_queue),
        agent_to_client_messaging(websocket, live_events)
    )
```

**Key Concepts:**

- **WebSocket**: Unlike regular HTTP (where you request a page and get a response), WebSocket keeps a connection open so both sides can send messages anytime. It's like having a phone call vs sending letters.

- **Session ID**: Each browser tab gets a unique ID. This way, if you open two tabs, they don't interfere with each other.

- **asyncio.gather()**: Runs two functions at the same time - one receiving from browser, one sending to browser.

---

### 3. The AI Agent

**What is it?**  
The AI agent is built using **Google ADK** (Agent Development Kit), which is a framework from Google for building AI assistants that can use tools and have conversations.

**What is Google ADK?**  
Think of ADK as a toolkit that makes it easier to build AI agents. Instead of writing everything from scratch, you get:
- Pre-built connection to Google's AI models (Gemini)
- Session management (remembering conversation history)
- Tool system (giving the AI abilities like searching or reading files)
- Streaming support (getting responses piece by piece, not all at once)

**File Location:** `app/jarvis/agent.py`

#### How the Agent is Configured

```python
# app/jarvis/agent.py

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset

# This creates the AI agent
root_agent = Agent(
    name="jarvis",
    
    # The AI model to use (more on this below)
    model="gemini-2.0-flash-exp",
    
    # What is this agent? (shown to the AI)
    description="A helpful AI assistant named Jarvis",
    
    # Instructions for how to behave
    instruction=get_agent_instruction(CONTENT_FOLDER),
    
    # Tools the agent can use
    tools=[
        # File system access (can read files from your computer)
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command='npx',  # Run a Node.js tool
                    args=[
                        "-y",  # Auto-confirm installation
                        "@modelcontextprotocol/server-filesystem",
                        CONTENT_FOLDER  # Which folder to access
                    ]
                )
            )
        ),
        
        # Google Search ability
        google_search,
        
        # PDF reading ability
        pdf_reader,
    ]
)
```

**Understanding the Tools:**

1. **MCPToolset (Filesystem)**:  
   MCP stands for "Model Context Protocol" - it's a standard way for AI agents to use external tools. This tool lets the AI read files from a folder on your computer. It works by running a small Node.js program that safely provides file access.

2. **google_search**:  
   A pre-built tool from Google ADK that lets the AI search Google for current information.

3. **pdf_reader**:  
   A custom tool we built (in `app/jarvis/tools/pdf_reader_tool.py`) that lets the AI read PDF files.

**How the AI decides when to use tools:**  
You don't tell the AI "use this tool now." Instead, the AI reads the tool descriptions and automatically decides when they're needed. For example, if you ask "What's the weather today?", it might use Google Search. If you ask "What's in document.pdf?", it uses the PDF reader.

---

## Why This Specific Model?

The system uses **Gemini 2.0 Flash Experimental** (`gemini-2.0-flash-exp`). Let's break down why.

### What is Gemini?

**Gemini** is Google's family of AI models - like GPT is OpenAI's family of models. There are different versions:

- **Gemini Pro**: Most capable, but slower and more expensive
- **Gemini Flash**: Fast and efficient, good balance
- **Gemini Nano**: Tiny, runs on your device
- **Gemini 2.0**: Newest generation with more features

### Why Gemini 2.0 Flash Experimental?

There are **three key reasons** we use this specific model:

#### 1. **Native Audio Support** (The Main Reason)

Most AI models work like this:
```
Your voice → [Speech-to-Text] → Text → [AI Model] → Text → [Text-to-Speech] → Audio
```

Gemini 2.0 Flash Experimental can do this:
```
Your voice → [AI Model] → Audio
```

The model **directly understands audio** and can **directly produce audio**. This means:
- ✅ Lower latency (faster responses)
- ✅ Better voice quality (no double conversion)
- ✅ More natural intonation and emotion
- ✅ Can understand tone of voice, not just words

**Code Example:**
```python
# When we start the agent session, we can specify audio mode:

response_modalities = ["AUDIO"] if is_audio else ["TEXT"]
run_config = RunConfig(3=response_modalities)

live_events = runner.run_live(
    user_id="user",
    session_id=session_id,
    live_request_queue=live_request_queue,
    run_config=run_config  # ← This tells it: respond with audio!
)
```

When `response_modalities=["AUDIO"]`, the model:
- Receives your audio directly (no speech-to-text step)
- Generates audio responses (no text-to-speech step)
- Still provides text transcriptions so you can see what was said

#### 2. **Live Streaming Support**

Google ADK has a special mode called `run_live()` that only works with Gemini models:

```python
# ✅ Works with Gemini models:
live_events = runner.run_live(
    user_id="user",
    session_id=session_id,
    live_request_queue=live_request_queue,
    run_config=run_config
)

# ❌ Doesn't work with other models (OpenAI, Claude, etc.):
# They don't support the live streaming protocol
```

**What is live streaming?**  
Instead of:
1. You finish speaking
2. Wait...
3. Get complete response

You get:
1. You start speaking
2. AI starts responding while you might still be talking
3. 3enerated (like a real conversation)

This makes it feel more natural and responsive.

#### 3. **Speed and Cost Balance**

Why "Flash" and not "Pro"?

- **Gemini Pro**: Smarter but slower (2-3 seconds per response)
- **Gemini Flash**: Fast responses (200-500ms) but still very capable
- **Experimental**: Latest features and improvements

For a **voice assistant**, speed matters more than maximum intelligence. Waiting 3 seconds for a response in a voice conversation feels awkward.

### Why Not Other Gemini Models?

| Model | Why Not? |
|-------|----------|
| **Gemini 1.5 Pro/Flash** | Older generation, less capable, no native audio streaming |
| **Gemini 2.0 Pro** | Too slow for real-time voice (when it's released) |
| **Gemini Nano** | Runs locally but less capable, not suitable for complex tasks |

### Why Not Other AI Models (GPT, Claude)?

**Short answer:** Google ADK's `run_live()` only works with Google's Gemini models.

**Longer answer:**  
While you can use OpenAI's GPT or Anthropic's Claude with Google ADK for **text-based** agents, they don't support:
- The live streaming protocol
- Native audio input/output
- Real-time bidirectional communication

You could use them, but you'd lose all the voice features and have to build your own audio pipeline.

**Code Example of Limitation:**
```python
# ❌ This won't work:
from litellm import LiteLLMModel

root_agent = Agent(
    name="jarvis",
    model=LiteLLMModel(model="gpt-4"),  # Not supported for live streaming
    tools=[...]
)

# Then trying to use run_live() will fail
live_events = runner.run_live(...)  # ❌ Error!
```

---

## How Voice Interaction Works

This is the most complex part of the system. Let's break it down step by step.

### Understanding Audio Processing

First, we need to understand some audio basics:

**Sample Rate**: How many audio measurements per second
- Like FPS (frames per second) for video, but for audio
- Higher = better quality but bigger file size
- Measured in Hertz (Hz)

**Common Sample Rates:**
- 🎙️ Phone calls: 8,000 Hz
- 🎤 Voice recognition: 16,000 Hz
- 🎵 Music: 44,100 Hz or 48,000 Hz
- 🎬 Professional audio: 96,000 Hz

**Audio Format (PCM)**: "Pulse Code Modulation"
- The raw, uncompressed audio data
- Each sample is a number representing sound pressure
- Like a RAW photo vs JPEG - no compression, high quality

**Why Different Sample Rates in Our System?**

```
Microphone (48,000 Hz)
    ↓  Why so high?
    │  → Browser's Web Audio API uses 48kHz by default
    ↓
Downsample to (16,000 Hz)
    ↓  Why downsample?
    │  → Gemini expects 16kHz for voice recognition
    │  → Reduces data by 66% (faster transmission)
    │  → 16kHz is perfect for human speech
    ↓
Send to AI
    ↓
AI Responds (24,000 Hz)
    ↓  Why 24kHz?
    │  → Better quality than 16kHz
    │  → Still efficient (not too big)
    ↓
Upsample to (48,000 Hz)
    ↓  Why upsample?
    │  → Browser speakers expect 48kHz
    ↓
Speaker Output (48,000 Hz)
```

### The Complete Voice Journey

Let's follow a single conversation turn from start to finish:

#### **Step 1: You Click the Microphone Button**

```javascript
// app/static/js/app.js

async startAudio() {
    // Ask browser for microphone permission
    const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: true 
    });
    
    // Create an audio context (the audio processing engine)
    this.audioContext = new AudioContext();  // Usually 48kHz
    
    // Load our custom audio processors
    await this.audioContext.audioWorklet.addModule(
        '/static/js/pcm-recorder-processor.js'  // For recording
    );
    await this.audioContext.audioWorklet.addModule(
        '/static/js/pcm-player-processor.js'    // For playback
    );
    
    // Create the recorder
    this.audioRecorderNode = new AudioWorkletNode(
        this.audioContext, 
        'pcm-recorder-processor'
    );
    
    // Create the player
    this.audioPlayerNode = new AudioWorkletNode(
        this.audioContext, 
        'pcm-player-processor'
    );
    
    // Connect microphone → recorder
    const source = this.audioContext.createMediaStreamSource(stream);
    source.connect(this.audioRecorderNode);
    
    // Connect player → speakers
    this.audioPlayerNode.connect(this.audioContext.destination);
    
    // Listen for audio data from recorder
    this.audioRecorderNode.port.onmessage = (event) => {
        this.audioRecorderHandler(event.data.pcmData);
    };
}
```

**What just happened?**
1. Browser asks for microphone permission
2. Create audio processing environment (AudioContext)
3. Load custom audio processors (worklets)
4. Create recorder and player nodes
5. Connect: Microphone → Recorder → [We'll send to server]
6. Connect: [Server sends audio] → Player → Speakers

#### **Step 2: Your Microphone Captures Audio**

Now you start speaking. Your voice enters the microphone and flows into the recorder worklet:

```javascript
// app/static/js/pcm-recorder-processor.js

class PCMRecorderProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.buffer = [];           // Store audio samples
        this.downsampleFactor = 3;  // 48000 ÷ 16000 = 3
        this.sampleCounter = 0;
    }

    // This function is called 128 times per second with audio data
    process(inputs, outputs, parameters) {
        const inputChannel = inputs[0][0];  // Get audio data
        
        // Process each audio sample
        for (let i = 0; i < inputChannel.length; i++) {
            this.sampleCounter++;
            
            // Downsampling: only keep every 3rd sample
            // This converts 48kHz → 16kHz
            if (this.sampleCounter >= this.downsampleFactor) {
                this.sampleCounter = 0;
                this.buffer.push(inputChannel[i]);  // Keep this sample
                
                // When we have enough samples (4096), send them
                if (this.buffer.length >= 4096) {
                    this.sendPCMData();
                }
            }
        }
        
        return true;  // Keep processing
    }

    sendPCMData() {
        // Convert from Float32 (-1.0 to 1.0) to Int16 (-32768 to 32767)
        // Why? Int16 is more efficient to transmit
        const float32Array = new Float32Array(this.buffer);
        const int16Array = new Int16Array(float32Array.length);
        
        for (let i = 0; i < float32Array.length; i++) {
            // Clamp value between -1 and 1
            const sample = Math.max(-1, Math.min(1, float32Array[i]));
            
            // Convert to 16-bit integer
            int16Array[i] = sample < 0 
                ? sample * 0x8000  // Negative: -32768 to 0
                : sample * 0x7FFF; // Positive: 0 to 32767
        }
        
        // Send to main thread
        this.port.postMessage({
            type: 'pcmData',
            pcmData: int16Array.buffer
        });
        
        this.buffer = [];  // Clear buffer
    }
}
```

**What's happening?**
- Audio comes in at 48,000 samples/second
- We only keep every 3rd sample (48,000 ÷ 3 = 16,000)
- Buffer 4,096 samples (about 256ms of audio)
- Convert from Float32 to Int16 (smaller data size)
- Send to main thread

**Why 4,096 samples?**  
Balance between latency and efficiency:
- Too small (e.g., 128 samples): Many tiny messages, inefficient
- Too large (e.g., 32,768 samples): Long delay before sending
- 4,096 samples = ~256ms at 16kHz: Good balance

#### **Step 3: Send Audio to Server**

The main thread receives the audio and sends it via WebSocket:

```javascript
// app/static/js/app.js

audioRecorderHandler(pcmData) {
    // Convert binary data to Base64 string
    // Why Base64? WebSocket sends text, not binary (in our implementation)
    const base64Audio = this.arrayBufferToBase64(pcmData);
    
    // Send to server
    this.sendMessage('audio/pcm', base64Audio);
}

arrayBufferToBase64(buffer) {
    // Convert ArrayBuffer → Uint8Array → Binary string → Base64
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);  // btoa = Binary to ASCII
}

sendMessage(mimeType, data) {
    // Send as JSON over WebSocket
    this.websocket.send(JSON.stringify({
        mime_type: mimeType,  // "audio/pcm"
        data: data            // Base64 encoded audio
    }));
}
```

**The WebSocket Message:**
```json
{
  "mime_type": "audio/pcm",
  "data": "AAAAAQACAAMABAAF..."  // Base64 encoded audio data
}
```

#### **Step 4: Server Receives and Processes**

The FastAPI server receives the WebSocket message:

```python
# app/main.py

async def client_to_agent_messaging(
    websocket: WebSocket, 
    live_request_queue: LiveRequestQueue
):
    """Receives messages from browser and forwards to AI agent"""
    
    # Listen for messages from the WebSocket
    async for message in websocket.iter_text():
        # Parse the JSON message
        data = json.loads(message)
        mime_type = data.get("mime_type")
        content_data = data.get("data")
        
        if mime_type == "audio/pcm":
            # Decode Base64 back to binary
            audio_data = base64.b64decode(content_data)
            
            logger.info(f"Received {len(audio_data)} bytes of audio")
            
            # Create a Blob object (ADK's format for audio)
            audio_blob = types.Blob(
                mime_type="audio/pcm;rate=16000",  # Specify sample rate
                data=audio_data
            )
            
            # Send to the AI agent's input queue
            live_request_queue.send_realtime(audio_blob)
            
        elif mime_type == "text/plain":
            # Text message (typing mode)
            content = types.Content(
                role="user",
                parts=[types.Part(text=content_data)]
            )
            live_request_queue.send_content(content)
```

**What's happening?**
1. Receive JSON message from WebSocket
2. Decode Base64 back to binary audio
3. Wrap in ADK's `Blob` format with sample rate info
4. Send to `live_request_queue` (the input to the AI agent)

**LiveRequestQueue**: Think of this as a mailbox where you put messages for the AI. The AI constantly checks this mailbox for new input.

#### **Step 5: AI Processes Your Voice**

Inside Google's servers (via the ADK):

```
Your Audio (16kHz PCM)
    ↓
┌─────────────────────────────────────┐
│   Gemini 2.0 Flash Model            │
│                                     │
│   1. Speech-to-Text (STT)          │
│      "What's the weather today?"    │
│                                     │
│   2. Language Understanding         │
│      Intent: Get weather info       │
│      Location: Inferred or asked    │
│                                     │
│   3. Tool Selection (if needed)     │
│      → Use Google Search tool       │
│                                     │
│   4. Response Generation            │
│      "It's 72°F and sunny..."       │
│                                     │
│   5. Text-to-Speech (TTS)          │
│      Generate audio of response     │
└─────────────────────────────────────┘
    ↓
Response Events:
- input_transcription: "What's the weather today?"
- (tool_call: search Google)
- (tool_response: weather data)
- output_transcription: "It's 72 degrees and sunny..."
- audio chunks: [binary audio data]
- turn_complete: true
```

The AI sends back multiple events through the `live_events` stream.

#### **Step 6: Server Sends Response to Browser**

The server listens to events from the AI and forwards them to the browser:

```python
# app/main.py

async def agent_to_client_messaging(
    websocket: WebSocket, 
    live_events: AsyncGenerator
):
    """Receives events from AI agent and forwards to browser"""
    
    # Listen to the stream of events from the AI
    async for event in live_events:
        
        # 1. User's speech transcription (what you said)
        if event.input_transcription:
            text = event.input_transcription.text
            logger.info(f"User said: {text}")
            
            await websocket.send_json({
                "mime_type": "text/plain",
                "data": text,
                "is_user_transcription": True
            })
        
        # 2. AI's speech transcription (what it's saying)
        if event.output_transcription:
            text = event.output_transcription.text
            logger.info(f"AI saying: {text}")
            
            await websocket.send_json({
                "mime_type": "text/plain",
                "data": text,
                "is_agent_transcription": True
            })
        
        # 3. Audio content (the actual voice)
        if event.content and hasattr(event.content, 'parts'):
            for part in event.content.parts:
                
                # Check if this part contains audio
                if hasattr(part, 'inline_data'):
                    inline_data = part.inline_data
                    
                    # Is it audio?
                    if inline_data.mime_type.startswith('audio/pcm'):
                        # Encode to Base64
                        base64_audio = base64.b64encode(
                            inline_data.data
                        ).decode('utf-8')
                        
                        logger.info(f"Sending {len(inline_data.data)} bytes of audio")
                        
                        # Send to browser
                        await websocket.send_json({
                            "mime_type": "audio/pcm",
                            "data": base64_audio,
                            "turn_complete": False
                        })
        
        # 4. Turn completion signal
        if event.turn_complete:
            await websocket.send_json({
                "mime_type": "text/plain",
                "data": "",
                "turn_complete": True
            })
```

**What messages get sent?**

1. **User transcription**: Shows what you said
   ```json
   {
     "mime_type": "text/plain",
     "data": "What's the weather today?",
     "is_user_transcription": true
   }
   ```

2. **Agent transcription**: Shows what AI is saying
   ```json
   {
     "mime_type": "text/plain",
     "data": "It's 72 degrees and sunny today.",
     "is_agent_transcription": true
   }
   ```

3. **Audio chunks**: The actual voice (sent multiple times as streaming)
   ```json
   {
     "mime_type": "audio/pcm",
     "data": "AAABAAACAAAD...",
     "turn_complete": false
   }
   ```

4. **Turn complete**: AI finished responding
   ```json
   {
     "mime_type": "text/plain",
     "data": "",
     "turn_complete": true
   }
   ```

#### **Step 7: Browser Plays Audio**

The browser receives audio chunks and plays them:

```javascript
// app/static/js/app.js

handleServerMessage(data) {
    // Check message type
    if (data.mime_type === 'audio/pcm') {
        // It's audio - play it!
        this.playAudioChunk(data.data);
        
    } else if (data.is_user_transcription) {
        // Show what user said
        this.displayMessage(data.data, 'user');
        
    } else if (data.is_agent_transcription) {
        // Show what AI is saying
        this.displayMessage(data.data, 'agent');
        
    } else if (data.turn_complete) {
        // AI finished speaking
        this.onTurnComplete();
    }
}

playAudioChunk(base64Audio) {
    // Decode Base64 → binary
    const audioData = this.base64ToArrayBuffer(base64Audio);
    
    // Send to player worklet
    this.audioPlayerNode.port.postMessage({
        type: 'playAudio',
        audioData: audioData
    });
}

base64ToArrayBuffer(base64) {
    // Decode Base64 → binary string → ArrayBuffer
    const binaryString = window.atob(base64);  // atob = ASCII to Binary
    const bytes = new Uint8Array(binaryString.length);
    
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    
    return bytes.buffer;
}
```

#### **Step 8: Audio Player Worklet**

The player worklet receives audio and plays it:

```javascript
// app/static/js/pcm-player-processor.js

class PCMPlayerProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.audioQueue = [];           // Queue of audio chunks
        this.currentBuffer = null;      // Currently playing chunk
        this.bufferIndex = 0;
        this.sampleRate = 24000;        // Gemini outputs 24kHz
        this.outputSampleRate = 48000;  // Browser expects 48kHz
        this.resampleRatio = 2.0;       // 48000 ÷ 24000 = 2
        this.resampleIndex = 0;
        
        // Listen for new audio chunks
        this.port.onmessage = (event) => {
            if (event.data.type === 'playAudio') {
                this.audioQueue.push(event.data.audioData);
            }
        };
    }

    // Called 128 times per second to fill output buffer
    process(inputs, outputs, parameters) {
        const outputChannel = outputs[0][0];
        
        // Fill each output sample
        for (let i = 0; i < outputChannel.length; i++) {
            
            // Do we have audio to play?
            if (this.currentBuffer && this.bufferIndex < this.currentBuffer.length) {
                
                // Get sample from current buffer
                const int16Sample = this.currentBuffer[this.bufferIndex];
                
                // Convert Int16 → Float32
                const float32Sample = int16Sample / 32768.0;
                outputChannel[i] = float32Sample;
                
                // Upsampling: play each sample twice (24kHz → 48kHz)
                this.resampleIndex++;
                if (this.resampleIndex >= this.resampleRatio) {
                    this.resampleIndex = 0;
                    this.bufferIndex++;  // Move to next sample
                }
                
            } else {
                // No audio - play silence
                outputChannel[i] = 0;
                
                // Try to load next chunk from queue
                if (this.audioQueue.length > 0) {
                    const nextChunk = this.audioQueue.shift();
                    this.currentBuffer = new Int16Array(nextChunk);
                    this.bufferIndex = 0;
                    this.resampleIndex = 0;
                }
            }
        }
        
        return true;
    }
}
```

**What's happening?**
- Receive audio chunks and add to queue
- Play chunks one by one
- Upsample from 24kHz to 48kHz (play each sample twice)
- Convert Int16 → Float32 for speakers
- When chunk finishes, load next from queue

**Why upsampling?**  
The browser's audio output expects 48kHz. If we send 24kHz directly, it would play at half speed (like slow motion). By playing each sample twice, we double the sample rate.

### Complete Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                          USER SPEAKS                             │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Browser)                           │
│                                                                  │
│  Microphone (48kHz) → Recorder Worklet                          │
│                       ├─ Downsample to 16kHz                     │
│                       ├─ Float32 → Int16                         │
│                       └─ Buffer 4096 samples                     │
│                           │                                      │
│                           ↓                                      │
│  Main Thread ← ArrayBuffer                                       │
│      ├─ Convert to Base64                                        │
│      └─ Send via WebSocket                                       │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ↓ {"mime_type":"audio/pcm", "data":"..."}
                               │
┌──────────────────────────────┴───────────────────────────────────┐
│                     BACKEND (FastAPI)                            │
│                                                                  │
│  WebSocket Handler                                               │
│      ├─ Receive JSON message                                     │
│      ├─ Decode Base64 → binary                                   │
│      ├─ Create Blob(mime_type="audio/pcm;rate=16000")           │
│      └─ Send to LiveRequestQueue                                 │
│                           │                                      │
│                           ↓                                      │
│  Google ADK Runner                                               │
│      └─ Forward to Gemini API                                    │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│                    GEMINI 2.0 FLASH                              │
│                                                                  │
│  Audio Input (16kHz PCM)                                         │
│      ↓                                                           │
│  Speech-to-Text: "What's the weather?"                          │
│      ↓                                                           │
│  Understand Intent                                               │
│      ↓                                                           │
│  Use Tools (if needed): Google Search                           │
│      ↓                                                           │
│  Generate Response                                               │
│      ↓                                                           │
│  Text-to-Speech: Audio (24kHz PCM)                              │
│                                                                  │
│  Output Events:                                                  │
│      • input_transcription: "What's the weather?"               │
│      • output_transcription: "It's 72 degrees..."               │
│      • audio chunks: [binary data, binary data, ...]            │
│      • turn_complete: true                                       │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ↓
┌──────────────────────────────┴───────────────────────────────────┐
│                     BACKEND (FastAPI)                            │
│                                                                  │
│  Event Stream Handler                                            │
│      ├─ Receive event from AI                                    │
│      ├─ Extract transcriptions → Send to WebSocket              │
│      ├─ Extract audio → Encode Base64 → Send to WebSocket       │
│      └─ Send turn_complete signal                                │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ↓ Multiple WebSocket messages
                               │
┌──────────────────────────────┴───────────────────────────────────┐
│                     FRONTEND (Browser)                           │
│                                                                  │
│  WebSocket Handler                                               │
│      ├─ Receive transcriptions → Display in chat                │
│      └─ Receive audio → Send to Player Worklet                  │
│                           │                                      │
│                           ↓                                      │
│  Player Worklet ← ArrayBuffer (24kHz Int16)                     │
│      ├─ Queue audio chunks                                       │
│      ├─ Int16 → Float32                                          │
│      ├─ Upsample to 48kHz (repeat each sample 2x)               │
│      └─ Output to speakers                                       │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│                        USER HEARS AI                             │
└──────────────────────────────────────────────────────────────────┘
```

---

## Text vs Audio: What Does the Model Receive?

This is an important question with a nuanced answer.

### In Audio Mode (`is_audio=true`)

**What the model receives:**
- **Raw audio** (16kHz PCM) of your voice

**What the model outputs:**
- **Raw audio** (24kHz PCM) of its voice
- **Text transcriptions** (what you said and what it's saying)

**Code Configuration:**
```python
# app/main.py

# When starting the session in audio mode:
response_modalities = ["AUDIO"]  # ← Tell model to respond with audio
run_config = RunConfig(response_modalities=response_modalities)

# When you speak:
audio_blob = types.Blob(
    mime_type="audio/pcm;rate=16000",
    data=audio_data  # ← Raw audio bytes
)
live_request_queue.send_realtime(audio_blob)  # ← Send audio directly
```

**Important:** The model does Speech-to-Text (STT) **internally** as part of its processing, but we never see this as a separate step. It goes:

```
Audio Input → [Internal STT] → Language Understanding → Generation → [Internal TTS] → Audio Output
```

We get both the audio output AND text transcriptions:

```python
# Events received from the model:
event.input_transcription.text   # "Hello Jarvis"
event.output_transcription.text  # "Hi! How can I help you?"
event.content.parts[0].inline_data.data  # <binary audio data>
```

### In Text Mode (`is_audio=false`)

**What the model receives:**
- **Text** (your typed message)

**What the model outputs:**
- **Text** (its response)
- **No audio**

**Code Configuration:**
```python
# app/main.py

# When starting the session in text mode:
response_modalities = ["TEXT"]  # ← Tell model to respond with text
run_config = RunConfig(response_modalities=response_modalities)

# When you type:
content = types.Content(
    role="user",
    parts=[types.Part(text="Hello Jarvis")]  # ← Text string
)
live_request_queue.send_content(content)  # ← Send text
```

### Key Insight: Native Audio Processing

The magic of Gemini 2.0 Flash is that it can **natively process audio**. This means:

**Old Way (most AI assistants):**
```
Your Voice → [Separate STT Service] → Text → [AI Model] → Text → [Separate TTS Service] → Audio
            (Whisper, etc.)                (GPT, etc.)         (ElevenLabs, etc.)
```

**Gemini 2.0 Way:**
```
Your Voice → [Gemini 2.0 Flash] → Audio + Text Transcriptions
```

**Benefits:**
1. ✅ **Faster**: No separate STT/TTS steps
2. ✅ **Better quality**: One model optimizes the whole pipeline
3. ✅ **More natural**: Can understand tone, emotion, pacing
4. ✅ **Easier code**: One API call instead of three
5. ✅ **Lower cost**: One model instead of three services

**Example of what the model can do that text-only can't:**
- Understand sarcasm from tone of voice
- Respond with appropriate emotional tone
- Maintain natural conversation rhythm
- Handle speech disfluencies ("um", "uh", pauses)

---

## Technical Deep Dives

### How WebSocket Communication Works

**What is WebSocket?**  
Imagine you're having a phone conversation vs exchanging letters:
- **HTTP (traditional web)**: Like sending letters - you send a request, wait for a response, connection closes
- **WebSocket**: Like a phone call - connection stays open, both sides can talk anytime

**Why WebSocket for this project?**
1. **Real-time**: No delay waiting for connection setup
2. **Bidirectional**: Server can send messages without being asked
3. **Efficient**: One connection, many messages (vs many HTTP requests)
4. **Low latency**: Critical for voice (we want <500ms total latency)

**Connection Flow:**
```javascript
// Frontend initiates connection
const wsUrl = `ws://localhost:8000/ws/${sessionId}?is_audio=true`;
const websocket = new WebSocket(wsUrl);

// Connection established
websocket.onopen = () => {
    console.log("Connected!");
};

// Receive messages
websocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Handle message
};

// Send messages
websocket.send(JSON.stringify({
    mime_type: "audio/pcm",
    data: base64Audio
}));
```

**Backend accepts connection:**
```python
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    # Accept the connection
    await websocket.accept()
    
    # Now both sides can send/receive freely
    # ...
```

### Session Management

**What is a session?**  
A session represents one conversation. It includes:
- Conversation history (what was said before)
- User preferences
- Current context

**Why sessions matter:**  
Without sessions, the AI would have no memory:
```
You: "What's the weather?"
AI: "It's sunny."
You: "What about tomorrow?"
AI: "What about tomorrow what?" ← No memory!
```

With sessions:
```
You: "What's the weather?"
AI: "It's sunny."
You: "What about tomorrow?"
AI: "Tomorrow will be partly cloudy." ← Remembers we're talking about weather!
```

**How sessions work in this project:**

```python
# app/main.py

# Global storage for all active sessions
sessions: Dict[str, Dict[str, Any]] = {}

# Shared session service (manages conversation history)
session_service = InMemorySessionService()

async def start_agent_session(session_id: str, is_audio: bool = False):
    # Create a new session in ADK
    session = await session_service.create_session(
        app_name="jarvis",
        user_id="user",
        session_id=session_id
    )
    
    # Create runner for this session
    runner = Runner(
        app_name="jarvis",
        agent=root_agent,
        session_service=session_service  # ← Shares session history
    )
    
    # Store session info
    sessions[session_id] = {
        "runner": runner,
        "live_request_queue": live_request_queue,
        "live_events": live_events,
        "is_audio": is_audio,
        "session": session
    }
```

**Session ID generation:**
```javascript
// Frontend generates unique ID for each tab
generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}
// Example: "session_1704123456789_k3j2h9f1x"
```

**Why unique IDs?**  
If you open two browser tabs, they get different session IDs, so they have separate conversations. Each tab = one conversation.

**Session cleanup:**
```python
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    try:
        # ... handle connection ...
    finally:
        # When user closes tab, clean up
        if session_id in sessions:
            del sessions[session_id]
```

### Concurrent Message Handling

The backend handles two tasks simultaneously:

```python
await asyncio.gather(
    client_to_agent_messaging(websocket, live_request_queue),  # Task 1
    agent_to_client_messaging(websocket, live_events),         # Task 2
    return_exceptions=True
)
```

**Why concurrent?**  
Imagine if it were sequential:

```
Sequential (BAD):
1. Listen to user → Send to AI
2. Wait for AI response
3. Send response to user
4. Go back to step 1

Problem: While AI is thinking, we can't receive more user input!
```

With concurrent:
```
Concurrent (GOOD):
Task 1: Continuously listen to user → Forward to AI
Task 2: Continuously listen to AI → Forward to user

Both happen at the same time!
```

This enables **full-duplex** communication (like a phone call - both can talk at once).

**Real-world example:**
```
0.0s: User starts speaking
0.5s: First audio chunk sent to AI
1.0s: Second audio chunk sent to AI
1.5s: AI starts responding (while user still speaking!)
2.0s: User hears AI response
2.5s: User stops speaking
3.0s: AI finishes response
```

Without concurrent handling, the AI couldn't start responding until the user completely finished.

---

## Common Questions

### Q: Why do we convert audio to Base64?

**Answer:** WebSocket in our implementation sends text messages (JSON). Binary data needs to be encoded as text.

**What is Base64?** A way to represent binary data using only text characters (A-Z, a-z, 0-9, +, /)

**Example:**
```
Binary:  10101111 01010101 11110000
Base64:  r1Xw
```

**Alternative:** We could use WebSocket's binary mode, but JSON with Base64 is simpler and more debuggable (you can see the messages).

### Q: Can I use this with OpenAI's GPT or Anthropic's Claude?

**Short answer:** Not for voice. Yes for text.

**Long answer:**  
For **text-only** agents, you can use Google ADK with other models:

```python
from litellm import LiteLLMModel

text_agent = Agent(
    name="text-only-agent",
    model=LiteLLMModel(model="gpt-4"),  # Works!
    tools=[google_search]
)

# Use with run() (not run_live())
response = runner.run(
    user_id="user",
    session_id="session",
    content="Hello!"
)
```

But `run_live()` (required for voice) only works with Gemini.

### Q: How much latency is there in voice mode?

**Typical latency breakdown:**

| Stage | Time | Notes |
|-------|------|-------|
| Microphone buffering | ~85ms | 4096 samples @ 48kHz |
| Browser processing | ~10ms | Downsample, encode |
| Network to server | ~5-20ms | Local network |
| Server processing | ~5ms | Decode, forward |
| API request to Gemini | ~20-50ms | Internet |
| Gemini processing | ~200-500ms | STT + LLM + TTS |
| API response time | ~20-50ms | Internet |
| Server processing | ~5ms | Encode, forward |
| Network to browser | ~5-20ms | Local network |
| Browser processing | ~10ms | Decode, upsample |
| Speaker buffering | ~20ms | Audio output |
| **Total** | **~385-775ms** | **Usually ~500ms** |

For comparison:
- Human reaction time: ~250ms
- Natural conversation pause: ~200-500ms
- Phone call latency: ~50-150ms

So this feels pretty natural!

### Q: What happens if the network is slow?

**Audio will stutter or pause.** Audio is **real-time** - it can't wait. If data doesn't arrive in time:
- **Recording**: Chunks buffer and send when connection improves
- **Playback**: Gaps of silence while waiting for data

**Potential improvement:** Add buffer on playback side (trade latency for smoothness)

### Q: Can multiple users use this at the same time?

**Yes!** Each user gets their own:
- WebSocket connection
- Session ID
- AI agent session
- Conversation history

The backend handles this with:
```python
sessions: Dict[str, Dict[str, Any]] = {}  # One entry per user
```

**Limit:** Your computer's resources (RAM, CPU, network bandwidth)

**Scalability:** For production, you'd want:
- Multiple backend servers (load balancing)
- Shared session storage (Redis, database)
- Rate limiting per user

### Q: Why PCM format and not MP3?

**PCM (Pulse Code Modulation):**
- ✅ **Uncompressed** - no quality loss
- ✅ **Fast** - no encode/decode CPU time
- ✅ **Simple** - just numbers representing audio
- ❌ **Large** - 16kHz * 2 bytes = 32 KB/second

**MP3:**
- ✅ **Compressed** - much smaller
- ❌ **Lossy** - quality loss
- ❌ **Slow** - encoding/decoding takes CPU time
- ❌ **Complex** - need codec library

**Why PCM wins for real-time:**  
Compression takes time. For voice, we want **minimal latency**, not minimal bandwidth. PCM is instant.

**Bandwidth calculation:**
```
Audio mode (16kHz PCM):
16,000 samples/second × 2 bytes/sample = 32,000 bytes/second = 32 KB/s

For a 1-minute conversation:
32 KB/s × 60s = 1,920 KB ≈ 2 MB

Still manageable on modern internet (even 4G handles this easily)
```

### Q: What if I want to add a new tool for the AI?

**Example:** Let's add a "get current time" tool.

**Step 1:** Define the tool function
```python
# app/jarvis/tools/time_tool.py

from google.adk.tools import FunctionTool
from datetime import datetime

def get_current_time(timezone: str = "UTC") -> str:
    """
    Get the current time in a specific timezone.
    
    Args:
        timezone: The timezone name (e.g., "UTC", "America/New_York")
        
    Returns:
        The current time as a string
    """
    # Import here to avoid global dependency
    from zoneinfo import ZoneInfo
    
    try:
        tz = ZoneInfo(timezone)
        now = datetime.now(tz)
        return f"Current time in {timezone}: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    except Exception as e:
        return f"Error getting time: {str(e)}"

# Create the tool
time_tool = FunctionTool(get_current_time)
```

**Step 2:** Add to agent
```python
# app/jarvis/agent.py

from .tools.time_tool import time_tool

root_agent = Agent(
    name="jarvis",
    model="gemini-2.0-flash-exp",
    tools=[
        MCPToolset(...),
        google_search,
        pdf_reader,
        time_tool,  # ← Add your new tool
    ]
)
```

**Step 3:** That's it! The AI will automatically:
- Read the function description
- Understand when to use it (when user asks about time)
- Call it with appropriate parameters
- Use the result in its response

**Example conversation:**
```
You: "What time is it in New York?"
AI: [Calls get_current_time("America/New_York")]
AI: "It's currently 3:45 PM EST in New York."
```

---

## Summary

### How It All Works Together

1. **Frontend (Browser)**
   - Shows UI, captures voice, plays audio
   - Uses Web Audio API and AudioWorklets for processing
   - Communicates via WebSocket

2. **Backend (FastAPI Server)**
   - Bridges browser and AI
   - Manages WebSocket connections
   - Handles audio encoding/decoding
   - Creates and manages AI agent sessions

3. **AI Agent (Google ADK + Gemini)**
   - Built with Google ADK framework
   - Powered by Gemini 2.0 Flash Experimental
   - Has access to tools (search, files, PDF)
   - Supports native audio input/output

### Why This Model?

- **Gemini 2.0 Flash Experimental** specifically because:
  - Native audio support (direct voice-to-voice)
  - Live streaming capability (`run_live()`)
  - Fast response times (200-500ms)
  - Only Gemini models support ADK's live mode

### How Voice Works

- **You speak** → Microphone (48kHz) → Downsample (16kHz) → Encode → WebSocket → Server → AI
- **AI responds** → Generate audio (24kHz) → Encode → WebSocket → Browser → Upsample (48kHz) → Speakers
- **Processing:** Model handles STT + reasoning + TTS internally
- **Transcriptions:** You see text of what was said
- **Streaming:** Audio comes in chunks for low latency

### Key Technologies

- **WebSocket**: Real-time bidirectional communication
- **Web Audio API**: Browser audio processing
- **AudioWorklets**: Efficient audio processing threads
- **PCM Audio**: Uncompressed format for speed
- **Google ADK**: Framework for building AI agents
- **FastAPI**: Modern Python web framework
- **Async/Await**: Concurrent message handling

This architecture creates a responsive, natural voice interaction experience while maintaining code simplicity and reliability.

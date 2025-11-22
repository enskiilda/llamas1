# Python Backend for Computer Control AI

## Overview

This is a complete Python backend conversion from the original Node.js/TypeScript implementation. It provides a FastAPI-based server that interfaces with:
- **NVIDIA AI API** (Llama-4 Scout model) for AI chat capabilities
- **OnKernel SDK** for browser automation and computer control

## Architecture

### Core Components

1. **main.py** - FastAPI application with endpoints
2. **chat_handler.py** - Main chat loop with CRITICAL PRESERVED LOGIC from TypeScript
3. **tool_executor.py** - Executes computer control actions
4. **text_filter.py** - Aggressive JSON/technical text filtering
5. **instructions.py** - AI system instructions
6. **utils.py** - Desktop session management utilities

### Critical Loop Logic Preservation

The `chat_handler.py` maintains the **EXACT LOOP BEHAVIOR** from the TypeScript version:

```python
while True:  # Infinite loop until !isfinish
    1. Call NVIDIA AI with chat history
    2. Stream and filter text responses
    3. Execute FIRST tool call only
    4. Add result to chat history
    5. For screenshots: inject as USER message for AI analysis
    6. Continue loop automatically
```

This ensures:
- One action per iteration
- Screenshot analysis before next action
- Automatic continuation without delays
- Proper finish condition (!isfinish) detection

## Installation

```bash
cd python-backend
pip install -r requirements.txt
```

### Requirements

- Python 3.10+
- FastAPI
- OpenAI SDK (for NVIDIA API)
- OnKernel SDK
- Uvicorn

## Configuration

⚠️ **HARDCODED API KEYS** - As per user requirements, API keys are hardcoded in the source:

- NVIDIA_API_KEY: `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`
- ONKERNEL_API_KEY: `sk_85dd38ea-b33f-45b5-bc33-0eed2357683a...`
- NVIDIA_MODEL: `meta/llama-4-scout-17b-16e-instruct`

**DO NOT modify these keys or move them to environment variables** per explicit user requirements.

## Running the Server

### Development

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 5000
```

The server will start on `http://0.0.0.0:5000`

## API Endpoints

### POST /api/chat

Streaming chat endpoint with computer control capabilities.

**Request:**
```json
{
  "messages": [...],
  "sandboxId": "optional-existing-session-id"
}
```

**Response:** Server-Sent Events (SSE) stream with:
- Text deltas (filtered)
- Tool invocations
- Tool results
- Screenshots
- Workflow updates

### POST /api/kill-desktop

Terminate a desktop session.

**Query Parameters:**
- `sandboxId`: Session ID to terminate

## Computer Control Actions

Supported actions via `computer_use` tool:
- `screenshot` - Capture screen
- `left_click` - Click at coordinates
- `double_click` - Double click
- `right_click` - Right click
- `mouse_move` - Move cursor
- `type` - Type text
- `key` - Press keyboard key
- `scroll` - Scroll window
- `left_click_drag` - Drag mouse
- `wait` - Pause execution

## Workflow Management

The `update_workflow` tool allows dynamic task planning:

```python
{
  "steps": [
    {"id": 1, "title": "Task 1", "status": "completed"},
    {"id": 2, "title": "Task 2", "status": "in_progress"}
  ],
  "current_step": 2,
  "notes": "Progress notes"
}
```

## Frontend Integration

The Python backend is designed to be a drop-in replacement for the Node.js backend.  The Next.js frontend requires minimal changes:

### Required Frontend Changes

1. **Update API endpoint URLs** (if backend runs on different port):
   ```typescript
   // In app/page.tsx and lib/realtime-session.ts
   api: "/api/chat"  // Keep same if running on port 5000
   ```

2. **NO other changes needed** - The streaming format and event types are identical.

## Key Differences from TypeScript Version

### Preserved Identically:
- All loop logic and flow control
- Text filtering algorithms
- Tool execution order
- Screenshot injection mechanism
- Finish condition detection
- Error handling and suggestions

### Technical Adaptations:
- `AsyncOpenAI` instead of `OpenAI` (for async/await)
- `onkernel` Python SDK instead of `@onkernel/sdk`
- FastAPI instead of Next.js API routes
- Python async generators instead of ReadableStream
- Type hints instead of TypeScript types

### Enhanced:
- Modular structure (separate files for clarity)
- Comprehensive error messages
- Type annotations throughout

## Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Common issues:
1. **OnKernel connection** - Check API key and network
2. **NVIDIA API errors** - Verify API key and model name
3. **Screenshot failures** - Desktop may be loading, add wait
4. **Tool execution errors** - Check detailed error suggestions

## Loop Logic Documentation

### Why the Infinite Loop Matters

The original TypeScript implementation uses a critical `while (true)` loop that:

1. **Ensures AI continuity** - AI doesn't stop after one response
2. **Enables step-by-step execution** - One action → analyze → next action
3. **Forces screenshot analysis** - Screenshots injected as USER messages
4. **Maintains conversation flow** - History builds up naturally

This has been preserved **exactly** in Python to maintain identical behavior.

### Example Flow:

```
User: "Find weather in Warsaw"
  ↓
Loop Iteration 1:
  → AI: "Let me take a screenshot"
  → Tool: screenshot()
  → Result: Screenshot injected as USER message
  ↓
Loop Iteration 2:
  → AI analyzes screenshot: "I see a browser, let me click address bar"
  → Tool: left_click(512, 50)
  ↓
Loop Iteration 3:
  → AI: "Now typing the search"
  → Tool: type("weather warsaw")
  ↓
... continues until ...
  ↓
Final Iteration:
  → AI: "Done! Temperature is 15°C. !isfinish"
  → Loop exits
```

## Security Notes

⚠️ **Per user requirements**, this code contains hardcoded API keys. This is intentional and should NOT be changed. In a production environment, you would normally use environment variables, but this implementation follows explicit user instructions to keep keys hardcoded.

## License

This is a conversion project. Refer to the original repository license.

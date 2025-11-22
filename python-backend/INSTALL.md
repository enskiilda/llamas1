# Installation Guide - Python Backend

## Quick Start

```bash
cd python-backend
./run.sh
```

That's it! The script will:
1. Create a virtual environment (if needed)
2. Install all dependencies
3. Start the server on port 5000

## Manual Installation

If you prefer manual setup:

### Step 1: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Run the Server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

## Verification

Once running, test the endpoints:

### Health Check

```bash
curl http://localhost:5000/
```

Expected response:
```json
{
  "status": "online",
  "service": "Computer Control AI Backend",
  "version": "1.0.0"
}
```

### API Documentation

Open in browser:
```
http://localhost:5000/docs
```

You should see the interactive Swagger/OpenAPI documentation.

## Requirements

- Python 3.10 or higher
- pip (Python package installer)
- Internet connection (for installing dependencies and API calls)

## Dependencies

All dependencies are specified in `requirements.txt`:

- `fastapi==0.115.5` - Web framework
- `uvicorn[standard]==0.32.1` - ASGI server
- `openai==1.57.4` - NVIDIA API client
- `onkernel==0.20.1` - Browser control SDK
- `python-multipart==0.0.19` - Form parsing

## Port Configuration

Default port: **5000**

To change the port, edit `main.py` or `run.sh`:

```python
# In main.py, line ~150
uvicorn.run(
    app,
    host="0.0.0.0",
    port=5000,  # Change this
    log_level="info"
)
```

## Integration with Frontend

The Python backend is designed as a drop-in replacement for the Node.js backend.

### If Frontend is on Port 3000

No changes needed - APIs use relative paths.

### If Frontend is on Different Host

Update CORS settings in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://your-frontend-host:3000"],  # Specify exact origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Troubleshooting

### Import Errors

```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:** Make sure you're in the virtual environment and dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Port Already in Use

```
ERROR: [Errno 48] Address already in use
```

**Solution:** Either:
1. Stop the process using port 5000: `lsof -ti:5000 | xargs kill -9`
2. Or change the port in `main.py`

### OnKernel Connection Errors

```
Error: Failed to connect to OnKernel API
```

**Solution:** 
1. Check your internet connection
2. Verify the API key is correct (hardcoded in source)
3. Check OnKernel service status

### NVIDIA API Errors

```
Error: Invalid API key or rate limit exceeded
```

**Solution:**
1. Verify NVIDIA_API_KEY in source
2. Check rate limits
3. Verify model name is correct

## Development Mode

For development with auto-reload:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

This will restart the server automatically when you make code changes.

## Production Deployment

For production, consider:

### 1. Use a Process Manager

```bash
# Using PM2
pm2 start "uvicorn main:app --host 0.0.0.0 --port 5000" --name "ai-backend"

# Using systemd (create service file)
sudo systemctl start ai-backend
```

### 2. Use Gunicorn with Uvicorn Workers

```bash
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000
```

### 3. Use a Reverse Proxy

Set up Nginx or Apache as a reverse proxy:

```nginx
# Nginx example
location /api/ {
    proxy_pass http://localhost:5000/api/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
}
```

## Environment Variables (Optional)

While the current version has hardcoded API keys per user requirements, you could modify it to use environment variables:

```python
# In main.py (if you want to use env vars - NOT CURRENTLY IMPLEMENTED)
import os
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "fallback-key")
ONKERNEL_API_KEY = os.getenv("ONKERNEL_API_KEY", "fallback-key")
```

Then set them:
```bash
export NVIDIA_API_KEY="your-key"
export ONKERNEL_API_KEY="your-key"
python main.py
```

**Note:** This is NOT currently implemented as per user's explicit requirements to keep keys hardcoded.

## Next Steps

1. ✅ Install and run backend
2. ✅ Verify health check works
3. ✅ Check API documentation
4. ➡️ Start the Next.js frontend
5. ➡️ Test complete flow: screenshot → click → type → finish
6. ➡️ Read `CHANGES.md` to understand what was ported
7. ➡️ Read `README.md` for architecture details

## Support

For issues:
1. Check console logs for errors
2. Verify all dependencies installed
3. Check API keys are valid
4. Review `CHANGES.md` for implementation details

import os
import uvicorn


if __name__ == "__main__":
    port = int(os.getenv("NAS_API_PORT", 8000))
    uvicorn.run('nas_monitor.main:app', host='0.0.0.0', port=port, loop="asyncio")

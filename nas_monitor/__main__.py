# /// script
# dependencies = [
#   "fastapi",
#   "uvicorn",
# ]
# ///
import uvicorn

if __name__ == "__main__":
    uvicorn.run('nas_monitor.main:app', host='0.0.0.0', port=8000, loop="asyncio")

# /// script
# dependencies = [
#   "fastapi",
#   "uvicorn",
# ]
# ///
import uvicorn

uvicorn.run('nas_monitor.main:app', host='0.0.0.0', port=8000)

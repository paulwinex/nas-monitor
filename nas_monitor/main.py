import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from pprint import pprint
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from nas_monitor.config import config
from nas_monitor.api_router import router as api_router

from nas_monitor.models import model_to_dict, init_db, disconnect_db
from nas_monitor import metrics as mt
from nas_monitor.device_inventory import perform_inventory
from nas_monitor.manager import setup_polling
from nas_monitor.metrics import fetch_metrics_data
from nas_monitor.shemas import RequestMetricsPayload


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    await init_db()
    if not config.DISABLE_TASKS:
        setup_polling(scheduler)
    await perform_inventory()
    scheduler.start()
    yield
    scheduler.shutdown(wait=True)
    await disconnect_db()

app = FastAPI(
    title="NAS Monitor",
    lifespan=lifespan
)

# CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

front_dir = Path(__file__, '../../frontend').resolve()

@app.get("/api/status")
async def get_metriks(payload: RequestMetricsPayload):
    if payload.range_name == 'raw':
        return await mt.read_raw_range()
    elif payload.range_name == 'hourly':
        return await mt.read_hourly_range()
    elif payload.range_name == 'history':
        return await mt.read_history_range()
print('FRONT DIR', front_dir)
if front_dir.exists():
    print('USE BUILT FRONTEND')
    app.mount("/assets", StaticFiles(directory=front_dir.joinpath('assets').as_posix()), name="assets")

    @app.get("/")
    async def get_index():
        return FileResponse(front_dir.joinpath("index.html").as_posix())

else:
    print('NO BUILT FRONTEND, USE DUMMY')
    @app.get("/", response_class=HTMLResponse)
    async def get_index(request: Request):
        # html_content = """
        # <a href="/docs">Go to swagger</a>"""
        return RedirectResponse(request.url_for("docs"))
        # return HTMLResponse(content=html_content)


@app.get("/api/get-devices")
async def get_index(request: Request):
    dev = await mt.get_all_devices()
    pprint([model_to_dict(d) for d in dev])


@app.get("/api/metrics")
async def get_metrics_endpoint(
        history_type: str = Query(..., description="Record types: raw, daily or history"),
        device_types: Optional[list[str]] = Query(None, description="Device Types"),
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
):
    if history_type not in ["raw", "hourly", "history"]:
        raise HTTPException(status_code=400, detail="history_type must be raw, hourly or history")
    data = await fetch_metrics_data(
        history_type=history_type,
        device_types=device_types,
        start_time=from_date,
        end_time=to_date
    )
    return {
        "status": "success",
        "count": len(data),
        "data": data
    }



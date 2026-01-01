import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from typing import List, Dict

from storage_monitor import StorageMonitor

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(update_storage_data())
    yield

app = FastAPI(
    title="Storage Sentry",
    lifespan=lifespan
)

state = {
    "zfs": [],
    "smart": [],
    "last_update": '',
    "stats_history": []
}

TEMP_CRITICAL_THRESHOLD = 65

def check_critical_conditions(smart_data: List[Dict]):
    """Функция 2: Проверка критических температур и выключение"""
    for disk in smart_data:
        temp = disk.get("temp")
        if isinstance(temp, int) and temp >= TEMP_CRITICAL_THRESHOLD:
            print(f"!!! CRITICAL TEMP ALERT: {disk['dev']} is {temp}°C. Shutting down...")
            # os.system("shutdown -h now")
            pass

def collect_time_series(zfs_data, smart_data):
    """Функция 3: Сбор метрик для статистики"""
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "disks": [
            {"dev": d["dev"], "temp": d["temp"], "errs": d["errs"]}
            for d in smart_data
        ],
        "pools": [
            {"name": p["name"], "free_percent": p["free_percent"]}
            for p in zfs_data
        ]
    }
    state["stats_history"].append(metrics)
    if len(state["stats_history"]) > 100:
        state["stats_history"].pop(0)
    print(f"Metrics collected at {metrics['timestamp']}")


async def update_storage_data():
    """Фоновая задача: раз в минуту опрашивает железо"""
    monitor = StorageMonitor()
    while True:
        try:
            # 1. Получаем данные
            zfs_info = monitor.get_zfs_data()
            smart_info = monitor.get_smart_data()

            # 2. Обновляем глобальное состояние
            state["zfs"] = zfs_info
            state["smart"] = smart_info
            state["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 3. Цепочка обработки
            check_critical_conditions(smart_info)
            collect_time_series(zfs_info, smart_info)

        except Exception as e:
            print(f"Update error: {e}")

        await asyncio.sleep(10)


@app.get("/api/status")
async def get_status():
    return {
        "last_update": state["last_update"],
        "zfs": state["zfs"],
        "smart": state["smart"]
    }


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """Главная страница со статичным HTML"""
    zfs_rows = "".join([
        f"<tr><td>{p['name']}</td><td>{p['health']}</td><td>{p['free_percent']}%</td></tr>"
        for p in state["zfs"]
    ])

    smart_rows = "".join([
        f"<tr><td>{d['dev']}</td><td>{d['pool']}</td><td>{d['temp']}°C</td><td>{d['errs']}</td><td>{'OK' if d['ok'] else 'FAIL'}</td></tr>"
        for d in state["smart"]
    ])

    html_content = f"""
    <html>
        <head>
            <title>Storage Monitor</title>
            <style>
                body {{ font-family: sans-serif; background: #1a1a1a; color: white; padding: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; background: #2d2d2d; }}
                th, td {{ padding: 12px; border: 1px solid #444; text-align: left; }}
                th {{ background: #3d3d3d; }}
                .status-ok {{ color: #4caf50; }}
                .status-warn {{ color: #ff9800; }}
            </style>
            <meta http-equiv="refresh" content="60">
        </head>
        <body>
            <h1>Storage System Status</h1>
            <p>Last update: {state['last_update']}</p>

            <h2>ZFS Pools</h2>
            <table>
                <tr><th>Name</th><th>Health</th><th>Free %</th></tr>
                {zfs_rows}
            </table>

            <h2>Physical Disks (SMART)</h2>
            <table>
                <tr><th>Device</th><th>Pool</th><th>Temp</th><th>Errors</th><th>SMART</th></tr>
                {smart_rows}
            </table>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


import asyncio
import json
import random
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from rust_telemetry import TelemetryFrame

TICK_SECONDS = 0.05


class ConnectionManager:
    def __init__(self) -> None:
        self.active: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.active.discard(ws)

    async def broadcast(self, message: str) -> None:
        if not self.active:
            return
        targets = list(self.active)
        results = await asyncio.gather(
            *(ws.send_text(message) for ws in targets), return_exceptions=True
        )
        for ws, res in zip(targets, results):
            if isinstance(res, Exception):
                self.disconnect(ws)


manager = ConnectionManager()


async def telemetry_loop() -> None:
    loop = asyncio.get_running_loop()
    next_tick = loop.time()
    while True:
        try:
            frame = TelemetryFrame.process_raw_packet(
                random.randint(64, 65_535), random.uniform(1.0, 50.0)
            )
            await manager.broadcast(json.dumps(frame.to_dict()))
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # keep the stream alive on bad frames
            print(f"telemetry loop error: {exc!r}")
        # Fixed-rate schedule: compensates for processing time / drift.
        next_tick += TICK_SECONDS
        await asyncio.sleep(max(0.0, next_tick - loop.time()))


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(telemetry_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="CyberCyclone3D Telemetry", lifespan=lifespan)


@app.websocket("/v1/telemetry/stream")
async def telemetry_stream(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # detects client disconnect; input ignored
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(ws)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000)

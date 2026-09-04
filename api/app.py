"""FastAPI application — REST API + SSE streaming for the CarbonOps dashboard."""
import json
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from db import init_db, get_connection
from db.seed import seed_all
from policy.audit import get_audit_trail, log_audit_event
from api.stream import StreamingTraceHandler
from config import BASE_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="CarbonOps", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Dashboard endpoints ---

@app.get("/api/dashboard")
def get_dashboard():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) as c FROM exceptions").fetchone()["c"]
    by_status = conn.execute(
        "SELECT status, COUNT(*) as c FROM exceptions GROUP BY status"
    ).fetchall()
    by_type = conn.execute(
        "SELECT exception_type, COUNT(*) as c FROM exceptions GROUP BY exception_type"
    ).fetchall()
    conn.close()
    return {
        "total_exceptions": total,
        "by_status": {r["status"]: r["c"] for r in by_status},
        "by_type": {r["exception_type"]: r["c"] for r in by_type},
    }


@app.get("/api/exceptions")
def list_exceptions(status: str | None = None):
    conn = get_connection()
    if status:
        rows = conn.execute(
            """SELECT e.*, s.name as supplier_name FROM exceptions e
            JOIN suppliers s ON e.supplier_id = s.id
            WHERE e.status = ? ORDER BY e.created_at DESC""",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT e.*, s.name as supplier_name FROM exceptions e
            JOIN suppliers s ON e.supplier_id = s.id
            ORDER BY e.created_at DESC"""
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/exceptions/{exception_id}")
def get_exception(exception_id: str):
    conn = get_connection()
    exc = conn.execute(
        """SELECT e.*, s.name as supplier_name, s.contact_email as supplier_email
        FROM exceptions e JOIN suppliers s ON e.supplier_id = s.id
        WHERE e.id = ?""",
        (exception_id,),
    ).fetchone()
    if not exc:
        conn.close()
        raise HTTPException(404, "Exception not found")

    records = conn.execute(
        """SELECT * FROM activity_records
        WHERE supplier_id = ? AND facility_id IN (
            SELECT facility_id FROM activity_records WHERE id = ?
        )
        ORDER BY reporting_period DESC, source""",
        (exc["supplier_id"], exc["record_id"] or ""),
    ).fetchall()

    evidence = conn.execute(
        "SELECT * FROM evidence WHERE exception_id = ?", (exception_id,)
    ).fetchall()

    conn.close()

    return {
        "exception": dict(exc),
        "records": [dict(r) for r in records],
        "evidence": [dict(e) for e in evidence],
        "audit_trail": get_audit_trail(exception_id),
    }


@app.get("/api/exceptions/{exception_id}/audit")
def get_exception_audit(exception_id: str):
    return get_audit_trail(exception_id)


# --- Investigation endpoint with SSE streaming ---

@app.get("/api/exceptions/{exception_id}/investigate")
async def investigate_exception_stream(exception_id: str):
    conn = get_connection()
    exc = conn.execute("SELECT * FROM exceptions WHERE id = ?", (exception_id,)).fetchone()
    conn.close()
    if not exc:
        raise HTTPException(404, "Exception not found")

    queue: asyncio.Queue = asyncio.Queue()

    async def send_event(event: dict):
        await queue.put(event)

    handler = StreamingTraceHandler(send_event=send_event)

    async def run_investigation():
        loop = asyncio.get_event_loop()
        handler.set_loop(loop)

        log_audit_event(exception_id, "investigation_started", agent="orchestrator")

        from agents.orchestrator import investigate_exception
        try:
            result = await loop.run_in_executor(None, investigate_exception, exception_id, handler)
            await queue.put({"type": "complete", "result": str(result)[:5000]})
        except Exception as e:
            await queue.put({"type": "error", "message": str(e)})

    async def event_generator():
        task = asyncio.create_task(run_investigation())
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=120)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("type") in ("complete", "error"):
                        break
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# --- Seed / Reset ---

@app.post("/api/reset")
def reset_data():
    seed_all()
    return {"status": "ok", "message": "Database reset and reseeded"}


# --- Serve frontend ---

frontend_dir = BASE_DIR / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = frontend_dir / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dir / "index.html"))

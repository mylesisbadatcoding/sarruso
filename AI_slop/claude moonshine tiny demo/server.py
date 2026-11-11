"""Moonshine Tiny live speech-to-text UI.

Run:  ./run.sh   then open http://127.0.0.1:8000
"""
import asyncio
import csv
import io
import json
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import db
from engine import load_engine
from metrics import rate_metrics, wer_cer

SR = 16000
TICK_S = 1.0          # live re-transcription interval
MIN_PASS_S = 0.5      # don't run a pass on less audio than this
MIN_FINAL_S = 0.3     # don't save an entry shorter than this
MAX_SEGMENT_S = 30.0  # auto-split long speech into separate entries
BASE = Path(__file__).parent

app = FastAPI(title="Moonshine Tiny STT")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

engine = load_engine()
db.init()
engine.transcribe(np.zeros(SR, dtype=np.float32))  # warm-up pass
_model_lock = asyncio.Lock()


async def run_pass(audio: np.ndarray):
    async with _model_lock:
        return await asyncio.to_thread(engine.transcribe, audio)


def build_entry(*, source, text, audio_s, infer_s, tokens, reference=None,
                live_passes=None, avg_pass_ms=None, first_text_ms=None):
    rtf, tps = rate_metrics(audio_s, infer_s, tokens)
    wer, cer = wer_cer(reference, text) if reference else (None, None)
    row = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": source,
        "model": engine.name,
        "text": text,
        "reference": reference or None,
        "audio_seconds": audio_s,
        "infer_ms": infer_s * 1000,
        "rtf": rtf,
        "tokens": tokens,
        "tokens_per_sec": tps,
        "wer": wer,
        "cer": cer,
        "live_passes": live_passes,
        "avg_pass_ms": avg_pass_ms,
        "first_text_ms": first_text_ms,
    }
    return db.insert(row)


def decode_audio(data: bytes) -> np.ndarray:
    """Decode any audio file to 16 kHz mono float32. Uses ffmpeg if present, else soundfile."""
    if shutil.which("ffmpeg"):
        p = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", "pipe:0", "-f", "f32le",
             "-ac", "1", "-ar", str(SR), "pipe:1"],
            input=data, capture_output=True,
        )
        if p.returncode == 0 and p.stdout:
            return np.frombuffer(p.stdout, dtype=np.float32).copy()
    try:
        import soundfile as sf
        audio, sr = sf.read(io.BytesIO(data), dtype="float32")
    except Exception as e:
        raise HTTPException(400, f"Could not decode audio (install ffmpeg for more formats): {e}")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != SR:
        raise HTTPException(400, f"Audio is {sr} Hz; install ffmpeg to resample to 16 kHz")
    return audio.astype(np.float32)


# ---------- pages & status ----------

@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/status")
def status():
    return {"model": engine.name, "stub": engine.stub, "sample_rate": SR,
            "max_segment_seconds": MAX_SEGMENT_S}


# ---------- entries ----------

@app.get("/api/entries")
def list_entries():
    entries = db.list_entries()
    return {"entries": entries, "summary": db.summary(entries)}


class ReferenceBody(BaseModel):
    reference: str | None = None


@app.patch("/api/entries/{entry_id}")
def set_reference(entry_id: int, body: ReferenceBody):
    entry = db.set_reference(entry_id, body.reference)
    if not entry:
        raise HTTPException(404, "No such entry")
    return entry


@app.delete("/api/entries/{entry_id}")
def delete_entry(entry_id: int):
    if not db.delete(entry_id):
        raise HTTPException(404, "No such entry")
    return {"ok": True}


@app.delete("/api/entries")
def clear_entries():
    db.clear()
    return {"ok": True}


@app.get("/api/entries.csv")
def export_csv():
    entries = list(reversed(db.list_entries()))
    buf = io.StringIO()
    if entries:
        writer = csv.DictWriter(buf, fieldnames=list(entries[0].keys()))
        writer.writeheader()
        writer.writerows(entries)
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=entries.csv"})


# ---------- file upload ----------

@app.post("/api/upload")
async def upload(file: UploadFile = File(...), reference: str = Form("")):
    audio = decode_audio(await file.read())
    if len(audio) < MIN_FINAL_S * SR:
        raise HTTPException(400, "Audio is too short")
    chunk = int(MAX_SEGMENT_S * SR)
    texts, infer_total, tokens_total = [], 0.0, 0
    for start in range(0, len(audio), chunk):
        piece = audio[start:start + chunk]
        if len(piece) < MIN_FINAL_S * SR:
            continue
        res = await run_pass(piece)
        texts.append(res.text)
        infer_total += res.seconds
        tokens_total += res.tokens
    audio_s = len(audio) / SR
    entry = build_entry(
        source=f"upload:{file.filename}", text=" ".join(t for t in texts if t),
        audio_s=audio_s, infer_s=infer_total, tokens=tokens_total,
        reference=reference.strip() or None,
    )
    return entry


# ---------- live microphone ----------

@app.websocket("/ws/live")
async def live(ws: WebSocket):
    """Protocol:
    client -> {"type":"start","reference":optional}, then binary Float32 PCM @16 kHz, then {"type":"stop"}
    server -> {"type":"partial",...} every second while speaking,
              {"type":"entry","entry":{...}} each saved segment, {"type":"done"} at the end.
    """
    await ws.accept()
    loop = asyncio.get_running_loop()
    inbox: asyncio.Queue = asyncio.Queue()

    async def reader():
        try:
            while True:
                msg = await ws.receive()
                await inbox.put(msg)
                if msg["type"] == "websocket.disconnect":
                    return
        except Exception:
            await inbox.put({"type": "websocket.disconnect"})

    reader_task = asyncio.create_task(reader())

    reference = None
    chunks: list[np.ndarray] = []
    n = 0
    session_started = None      # perf_counter of first audio frame in current segment
    first_text_ms = None
    pass_ms: list[float] = []
    new_since_pass = 0
    next_tick = loop.time() + TICK_S

    def reset_segment():
        nonlocal chunks, n, session_started, first_text_ms, pass_ms, new_since_pass
        chunks, n, session_started, first_text_ms = [], 0, None, None
        pass_ms, new_since_pass = [], 0

    async def finalize(reason: str):
        """Snapshot and reset the segment synchronously, then transcribe it and save an entry."""
        audio = np.concatenate(chunks) if chunks else np.zeros(0, np.float32)
        snap = dict(first_text_ms=first_text_ms, pass_ms=list(pass_ms))
        reset_segment()
        if len(audio) < MIN_FINAL_S * SR:
            return
        res = await run_pass(audio)
        if not res.text:
            return
        avg = sum(snap["pass_ms"]) / len(snap["pass_ms"]) if snap["pass_ms"] else None
        entry = build_entry(
            source="mic", text=res.text, audio_s=len(audio) / SR, infer_s=res.seconds,
            tokens=res.tokens, reference=reference, live_passes=len(snap["pass_ms"]),
            avg_pass_ms=avg, first_text_ms=snap["first_text_ms"],
        )
        await ws.send_text(json.dumps({"type": "entry", "reason": reason, "entry": entry}))

    async def partial():
        nonlocal first_text_ms, new_since_pass
        audio = np.concatenate(chunks)
        new_since_pass = 0
        res = await run_pass(audio)
        pass_ms.append(res.seconds * 1000)
        if res.text and first_text_ms is None and session_started is not None:
            first_text_ms = (time.perf_counter() - session_started) * 1000
        await ws.send_text(json.dumps({
            "type": "partial", "text": res.text,
            "audio_seconds": len(audio) / SR, "infer_ms": res.seconds * 1000,
        }))

    try:
        while True:
            timeout = max(0.0, next_tick - loop.time())
            try:
                msg = await asyncio.wait_for(inbox.get(), timeout)
            except asyncio.TimeoutError:
                msg = None

            if msg is not None:
                if msg["type"] == "websocket.disconnect":
                    break
                if msg.get("bytes"):
                    frame = np.frombuffer(msg["bytes"], dtype=np.float32).copy()
                    if session_started is None:
                        session_started = time.perf_counter()
                    chunks.append(frame)
                    n += len(frame)
                    new_since_pass += len(frame)
                    if n >= MAX_SEGMENT_S * SR:
                        await finalize("auto-split")
                elif msg.get("text"):
                    cmd = json.loads(msg["text"])
                    if cmd.get("type") == "start":
                        reference = (cmd.get("reference") or "").strip() or None
                    elif cmd.get("type") == "stop":
                        break

            if loop.time() >= next_tick:
                next_tick = loop.time() + TICK_S
                if n >= MAX_SEGMENT_S * SR:
                    await finalize("auto-split")
                elif new_since_pass and n >= MIN_PASS_S * SR:
                    await partial()

        await finalize("stop")
        await ws.send_text(json.dumps({"type": "done"}))
    except Exception:
        pass  # client went away mid-pass
    finally:
        reader_task.cancel()

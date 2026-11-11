# Moonshine Tiny · live speech-to-text UI

> **Testing on a Linux laptop?** Follow [TESTING.md](TESTING.md) step by step.

A small local web app for [Moonshine Tiny](https://github.com/usefulsensors/moonshine) (~27M params, ONNX).
Speak into your mic and see text appear live. Each finished utterance is saved as an entry with benchmarks:
WER/CER (if you give reference text), real-time factor (RTF), tokens/sec, inference time, and latency to first text.

Everything runs on your machine. The only network access is the one-time model download.

## Quick start (Linux)

```bash
./run.sh
```

Then open **http://127.0.0.1:8000** in Chrome or Firefox and click **Start recording**.

`run.sh` creates `.venv`, installs `requirements.txt`, and starts the server. On the first run, the Moonshine Tiny weights download from Hugging Face (needs internet once). They are cached afterward.

Requirements: Python 3.10+, a microphone, and a browser. `ffmpeg` is optional. It lets you upload MP3/M4A/etc. and resamples non-16 kHz files. Without it, only WAV/FLAC at 16 kHz work for uploads.

Want to try the UI without downloading the model?

```bash
MOONSHINE_STUB=1 ./run.sh
```

The stub returns fake text, so you can check the layout and plumbing.

## Using it

- **Record:** click Start, speak, click Stop. The live line updates about once per second. Each segment is saved as an entry when you stop, or automatically every 30 s.
- **Reference text (WER):** type the correct transcript into the reference box next to Start, or into the reference column of any entry afterwards. WER and CER are computed against it.
- **Upload:** pick an audio file. It is transcribed as one entry (long files are split into 30 s chunks).
- **Export:** Export CSV downloads every entry with all metrics.

## What the metrics mean

| Metric | Definition | Better |
|---|---|---|
| Inference | Wall time of the final transcription pass for the entry | lower |
| RTF | inference time ÷ audio duration (0.1 means 10× faster than real time) | lower, <1 required for live |
| Tok/s | generated text tokens ÷ inference time | higher |
| WER | word error rate vs. your reference, after lowercasing and removing punctuation | lower |
| CER | character error rate, same normalization | lower |
| First text | time from first audio frame until the first partial result | lower |
| Avg pass | average inference time of the live partial passes | lower |

Notes on fairness: RTF and tok/s depend on your CPU and whether anything else is running. Compare runs on the same machine. Tiny is English-only.

## How the live path works

The browser captures the mic at 16 kHz (AudioWorklet) and streams Float32 PCM over a WebSocket. Moonshine's ONNX API transcribes whole buffers, not streams, so every second the server re-transcribes the current segment to produce partial text. The final pass on each segment produces the saved entry. That keeps the code small. The trade-off is that live passes cost more as a segment grows, which is why segments are capped at 30 s.

## Files

- `server.py` — FastAPI app: WebSocket live session, upload, entries API, CSV export
- `engine.py` — Moonshine wrapper (and the stub engine)
- `metrics.py` — WER/CER and rate calculations
- `db.py` — SQLite storage (`data/entries.db`, override with `STT_DB`)
- `static/` — the page, styles, mic worklet and app logic
- `run.sh` — setup and launch

## Limits

- English only (Moonshine Tiny).
- Live text is re-transcribed each second, so it can change as more audio arrives. The saved entry is the final pass.
- Mic access needs `localhost` (or HTTPS) — the default `127.0.0.1` qualifies. For access from another machine, put it behind HTTPS.

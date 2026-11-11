"""Moonshine Tiny wrapper.

Set MOONSHINE_STUB=1 to use a fake engine (for testing the UI without model weights).
Set MOONSHINE_MODEL to change the model (default: moonshine/tiny).
"""
import os
import time
from dataclasses import dataclass

import numpy as np

MODEL_NAME = os.environ.get("MOONSHINE_MODEL", "moonshine/tiny")
USE_STUB = os.environ.get("MOONSHINE_STUB") == "1"


@dataclass
class TranscribeResult:
    text: str
    tokens: int      # generated text tokens (start/end tokens excluded)
    seconds: float   # wall-clock inference time


class MoonshineEngine:
    stub = False

    def __init__(self):
        from moonshine_onnx import MoonshineOnnxModel
        from moonshine_onnx.transcribe import load_tokenizer

        self.name = MODEL_NAME
        self.model = MoonshineOnnxModel(model_name=MODEL_NAME)
        self.tokenizer = load_tokenizer()

    def transcribe(self, audio: np.ndarray) -> TranscribeResult:
        x = np.asarray(audio, dtype=np.float32).reshape(1, -1)
        t0 = time.perf_counter()
        batch = self.model.generate(x)
        dt = time.perf_counter() - t0
        special = {self.model.decoder_start_token_id, self.model.eos_token_id}
        ids = [t for t in batch[0] if t not in special]
        text = self.tokenizer.decode(ids, skip_special_tokens=True).strip()
        return TranscribeResult(text=text, tokens=len(ids), seconds=dt)


class StubEngine:
    """Fake engine for UI testing: returns a fake transcript and sleeps proportionally."""
    stub = True
    name = "stub (no model)"

    def transcribe(self, audio: np.ndarray) -> TranscribeResult:
        secs = len(audio) / 16000
        words = max(1, int(secs * 2.5))
        text = " ".join(["stub"] * words)
        dt = max(0.001, secs * 0.03)  # pretend RTF ~0.03
        time.sleep(dt)
        return TranscribeResult(text=text, tokens=words, seconds=dt)


def load_engine():
    if USE_STUB:
        return StubEngine()
    return MoonshineEngine()

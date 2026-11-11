"""Benchmark helpers: WER/CER against a reference, real-time factor, tokens/sec."""
import re

import jiwer


def normalize(text: str) -> str:
    """Lowercase, drop punctuation, collapse whitespace (so WER ignores casing/punctuation)."""
    text = text.lower()
    text = re.sub(r"[^\w\s']", " ", text)
    text = text.replace("'", "")
    return re.sub(r"\s+", " ", text).strip()


def wer_cer(reference: str, hypothesis: str):
    ref = normalize(reference or "")
    hyp = normalize(hypothesis or "")
    if not ref:
        return None, None
    if not hyp:
        return 1.0, 1.0
    return float(jiwer.wer(ref, hyp)), float(jiwer.cer(ref, hyp))


def rate_metrics(audio_seconds: float, infer_seconds: float, tokens: int):
    rtf = infer_seconds / audio_seconds if audio_seconds > 0 else None
    tps = tokens / infer_seconds if infer_seconds > 0 else None
    return rtf, tps

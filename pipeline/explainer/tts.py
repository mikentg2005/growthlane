"""Narrator voice (Kokoro, local, Apache-2.0). Per-sentence synthesis, cached on disk.

Voice.lay(text) -> (words, clips, end)
  words: [(word, start, end)] relative to the section start (NARR_START offset applied)
  clips: [(start, samples @ 44.1k)] for the audio mixer
  end:   time the last sentence finishes
"""
import hashlib
import re
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CACHE = HERE / "out" / "tts_cache"
SR_OUT = 44100
VOICE = "am_adam"
SPEED = 0.95
PAUSE = 0.38          # between sentences
COMMA_PAUSE = 0.12    # extra weight inside a sentence at , : ;
_kokoro = None


def _model():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(str(HERE / "models" / "kokoro-v1.0.onnx"), str(HERE / "models" / "voices-v1.0.bin"))
    return _kokoro


def _trim(x, sr, thr=0.01, keep=0.03):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    a, b = max(0, idx[0] - int(keep * sr)), min(len(x), idx[-1] + int(keep * sr))
    return x[a:b]


def synth(sentence, voice=VOICE, speed=SPEED):
    key = hashlib.sha1(f"{voice}|{speed}|{sentence}".encode()).hexdigest()[:16]
    f = CACHE / f"{key}.npy"
    if f.exists():
        return np.load(f)
    CACHE.mkdir(parents=True, exist_ok=True)
    samples, sr = _model().create(sentence, voice=voice, speed=speed, lang="en-us")
    x = _trim(np.asarray(samples, dtype=np.float32), sr)
    n = int(len(x) * SR_OUT / sr)
    x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)
    peak = float(np.max(np.abs(x))) or 1.0
    x = x * (0.85 / peak)
    np.save(f, x)
    return x


def split_sentences(text):
    return [s.strip() for s in re.findall(r"[^.?!]+[.?!]+(?:[\"”’']+)?|[^.?!]+$", text) if s.strip()]


def _words_in(sentence, t0, dur):
    """Spread the words over the spoken sentence by length; commas get a little extra weight."""
    raws = sentence.split()
    ws = []
    for r in raws:
        w = re.sub(r"[^\w']", "", r).lower()
        weight = 0.6 + len(w) + (3.0 if r[-1:] in ",:;" else 0.0)
        ws.append((w, weight))
    total = sum(w for _, w in ws) or 1.0
    out, t = [], t0
    for w, wt in ws:
        d = dur * wt / total
        out.append((w, t, t + d * 0.9 if wt > 3 + 0.6 + len(w) - 0.1 else t + d))
        t += d
    return out


class Voice:
    def __init__(self, start=0.55, voice=VOICE, speed=SPEED):
        self.start, self.voice, self.speed = start, voice, speed

    def lay(self, text):
        words, clips, t = [], [], self.start
        for s in split_sentences(text):
            x = synth(s, self.voice, self.speed)
            dur = len(x) / SR_OUT
            words += _words_in(s, t, dur)
            clips.append((t, x))
            t += dur + PAUSE
        return words, clips, t - PAUSE

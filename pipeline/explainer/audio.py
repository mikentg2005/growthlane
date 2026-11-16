"""Original, royalty-free audio for the explainer videos, synthesised with numpy.

A soft lo-fi loop (pad, bass, plucks, light drums) plus sound effects placed on the
video timeline. Nothing is sampled or downloaded, so there is no copyright issue.
"""
import wave

import numpy as np

SR = 44100
rng = np.random.default_rng(7)


def t_arr(dur):
    return np.arange(int(dur * SR)) / SR


def adsr(n, a=0.01, d=0.1, s=0.6, r=0.1):
    e = np.ones(n)
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na, nd, nr = min(na, n), min(nd, max(0, n - na)), min(nr, n)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nd:
        e[na:na + nd] = np.linspace(1, s, nd)
    e[na + nd:] = s
    if nr:
        e[n - nr:] *= np.linspace(1, 0, nr)
    return e


def note_hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def lowpass(x, k):
    if k <= 1:
        return x
    return np.convolve(x, np.ones(k) / k, mode="same")


def tone(freq, dur, kind="sine", vol=1.0, env=None):
    t = t_arr(dur)
    ph = 2 * np.pi * freq * t
    if kind == "sine":
        w = np.sin(ph)
    elif kind == "tri":
        w = 2 / np.pi * np.arcsin(np.sin(ph))
    elif kind == "saw":
        w = 2 * ((freq * t) % 1) - 1
    elif kind == "square":
        w = np.sign(np.sin(ph))
    else:
        w = np.sin(ph)
    return w * vol * (env if env is not None else adsr(len(t)))


def place(mix, snd, at, gain=1.0):
    i = int(at * SR)
    if i < 0:
        snd = snd[-i:]
        i = 0
    if i >= len(mix) or len(snd) == 0:
        return
    j = min(len(mix), i + len(snd))
    mix[i:j] += snd[: j - i] * gain


# ---------- sound effects ----------
def sfx_pop(vol=0.8, pitch=1.0):
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    f = (700 * np.exp(-t * 14) + 220) * pitch
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22) * vol


def sfx_whoosh(dur=0.55, vol=0.5):
    n = int(dur * SR)
    noise = rng.normal(0, 1, n)
    out = np.zeros(n)
    t = np.arange(n) / SR
    for k, w in ((8, 0.5), (40, 0.35), (160, 0.25)):
        out += lowpass(noise, k) * w
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    sweep = np.sin(2 * np.pi * np.cumsum(180 + 900 * (t / dur)) / SR) * 0.08
    return (out * 3.2 + sweep) * env * vol


def sfx_tick(vol=0.25):
    n = int(0.03 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 180) * vol


def sfx_buzz(dur=0.28, vol=0.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    w = (np.sign(np.sin(2 * np.pi * 160 * t)) * 0.5 + np.sin(2 * np.pi * 320 * t) * 0.3)
    am = (np.sin(2 * np.pi * 38 * t) > -0.3).astype(float)
    return lowpass(w * am, 4) * adsr(n, 0.005, 0.02, 0.9, 0.04) * vol


def sfx_ding(freq=880, dur=0.9, vol=0.4):
    t = t_arr(dur)
    w = np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 2.01 * t) + 0.15 * np.sin(2 * np.pi * freq * 3.02 * t)
    return w * np.exp(-t * 4.5) * vol / 1.5


def sfx_success(vol=0.4):
    out = np.zeros(int(1.4 * SR))
    for i, m in enumerate((72, 76, 79, 84)):
        place(out, sfx_ding(note_hz(m), 0.9, vol), i * 0.09)
    return out


def sfx_confetti(vol=0.35):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    crackle = lowpass(noise, 3) * np.exp(-t * 7)
    return crackle * vol * (rng.random(n) > 0.55)


def sfx_down(dur=0.9, vol=0.3):
    t = t_arr(dur)
    f = 520 * np.exp(-t * 1.4) + 120
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2) * vol


def sfx_thump(vol=0.7):
    t = t_arr(0.35)
    f = 130 * np.exp(-t * 9) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11) * vol


def sfx_zip(dur=0.4, vol=0.25):
    t = t_arr(dur)
    f = 300 + 1700 * (t / dur) ** 2
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * adsr(len(t), 0.01, 0.05, 0.6, 0.1) * vol


def sfx_shine(vol=0.3):
    out = np.zeros(int(1.2 * SR))
    for i, m in enumerate((88, 91, 95, 100)):
        place(out, sfx_ding(note_hz(m), 0.7, vol * 0.7), i * 0.07)
    return out


def sfx_pull(dur=3.2, vol=0.12):
    t = t_arr(dur)
    f = 110 + 90 * (t / dur) ** 2
    w = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(2 * np.pi * np.cumsum(f) * 2 / SR)
    return w * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7 * vol


# ---------- music ----------
def music(total):
    bpm = 96
    beat = 60 / bpm
    out = np.zeros(int((total + 2) * SR))
    chords = [(57, (57, 60, 64, 67)), (53, (53, 57, 60, 64)), (48, (48, 55, 59, 64)), (55, (55, 59, 62, 64))]
    arp = [0, 2, 3, 2, 1, 2, 3, 1]
    bars = int(total / (4 * beat)) + 2
    for b in range(bars):
        root, tones = chords[b % 4]
        t0 = b * 4 * beat
        # pad
        dur = 4 * beat + 0.4
        for m in tones:
            for det in (-0.8, 0.8):
                w = tone(note_hz(m) * (1 + det / 1200 * 4), dur, "tri", 0.05, adsr(int(dur * SR), 0.5, 0.2, 0.8, 0.5))
                place(out, w, t0, 1.0)
        # bass
        for q in (0, 2):
            w = tone(note_hz(root - 12), 1.6 * beat, "sine", 0.22, adsr(int(1.6 * beat * SR), 0.01, 0.2, 0.5, 0.25))
            place(out, w, t0 + q * beat)
        # arpeggio pluck
        for i in range(8):
            m = tones[arp[i]] + 12
            w = tone(note_hz(m), 0.55, "tri", 0.07, np.exp(-t_arr(0.55) * 7))
            place(out, w, t0 + i * beat / 2)
        # drums
        for q in (0, 2):
            n = int(0.25 * SR)
            tt = np.arange(n) / SR
            kick = np.sin(2 * np.pi * np.cumsum(120 * np.exp(-tt * 18) + 46) / SR) * np.exp(-tt * 12) * 0.5
            place(out, kick, t0 + q * beat)
        for q in (1, 3):
            n = int(0.18 * SR)
            tt = np.arange(n) / SR
            sn = lowpass(rng.normal(0, 1, n), 5) * np.exp(-tt * 22) * 0.16
            place(out, sn, t0 + q * beat)
        for i in range(8):
            n = int(0.05 * SR)
            tt = np.arange(n) / SR
            hat = (rng.normal(0, 1, n) - lowpass(rng.normal(0, 1, n), 8)) * np.exp(-tt * 70) * (0.05 if i % 2 else 0.03)
            place(out, hat, t0 + i * beat / 2)
    return out[: int(total * SR)]


def build_audio(path, total, scenes):
    n = int(total * SR)
    mix = music(total) * 0.62
    s0 = {name: t for name, t in scenes}
    # scene transitions
    for name, t in scenes[1:]:
        place(mix, sfx_whoosh(), t - 0.05, 0.8)
    # hook
    for i in range(int(4.9 / 0.5)):
        place(mix, sfx_tick(), 0.2 + i * 0.5, 0.7)
    place(mix, sfx_pop(), 0.45, 0.6)
    for i, tt in enumerate((3.0, 3.5, 4.0, 4.5)):
        place(mix, sfx_buzz(), tt, 0.8)
    place(mix, sfx_pop(), 3.55, 0.8)
    # formula
    f0 = s0["formula"]
    for tt in (1.2, 1.7, 3.2, 3.7):
        place(mix, sfx_pop(), f0 + tt, 0.8)
    place(mix, sfx_zip(), f0 + 2.4, 0.9)
    place(mix, sfx_ding(660, 0.6, 0.3), f0 + 2.0)
    place(mix, sfx_ding(440, 0.6, 0.3), f0 + 4.3)
    # expectancy
    e0 = s0["expect"]
    place(mix, sfx_thump(), e0 + 0.5, 0.8)
    place(mix, sfx_whoosh(0.5, 0.6), e0 + 2.0, 0.9)
    for i in range(4):
        place(mix, sfx_ding(note_hz(72 + i * 4), 0.7, 0.35), e0 + 3.0 + (i + 1.4) / 4.5 * 2.2)
    place(mix, sfx_confetti(), e0 + 5.2, 1.0)
    place(mix, sfx_success(), e0 + 5.2, 0.7)
    # value
    v0 = s0["value"]
    place(mix, sfx_whoosh(0.4, 0.5), v0 + 2.2, 0.8)
    place(mix, sfx_shine(), v0 + 2.55, 0.9)
    # impulsiveness
    i0 = s0["impulse"]
    for k in range(5):
        place(mix, sfx_buzz(), i0 + 1.2 + k * 0.55, 0.9)
    for k in range(4):
        place(mix, sfx_pop(), i0 + 1.8 + k * 0.35, 0.8)
        place(mix, sfx_ding(1100 + k * 120, 0.5, 0.18), i0 + 1.8 + k * 0.35)
    place(mix, sfx_down(), i0 + 2.2, 0.9)
    # delay
    d0 = s0["delay"]
    place(mix, sfx_pull(), d0 + 1.0, 1.0)
    place(mix, sfx_ding(784, 0.8, 0.35), d0 + 4.1)
    place(mix, sfx_ding(988, 0.8, 0.35), d0 + 4.35)
    # tip
    p0 = s0["tip"]
    place(mix, sfx_thump(), p0 + 1.6, 0.9)
    place(mix, sfx_ding(880, 0.8, 0.4), p0 + 1.65)
    place(mix, sfx_pop(), p0 + 3.0, 0.8)
    place(mix, sfx_pop(), p0 + 3.9, 0.8)
    place(mix, sfx_confetti(), p0 + 4.3, 1.0)
    place(mix, sfx_success(), p0 + 4.3, 0.8)
    # end
    n0 = s0["end"]
    place(mix, sfx_success(), n0 + 0.1, 0.5)
    place(mix, sfx_pop(), n0 + 2.0, 0.9)
    # master: fades, soft limit
    fade_in = np.minimum(1, np.arange(n) / (0.6 * SR))
    fade_out = np.minimum(1, (n - np.arange(n)) / (1.8 * SR))
    mix = mix[:n] * fade_in * fade_out
    mix = np.tanh(mix * 1.1) * 0.9
    peak = np.max(np.abs(mix))
    if peak > 0.95:
        mix = mix / peak * 0.95
    st = np.stack([mix, mix], axis=1)
    pcm = (st * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    return path


# ---------- notebook-style videos: very quiet ambient bed + effects only on important moments ----------
def sfx_flip(vol=0.45):
    n = int(0.62 * SR)
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    body = lowpass(noise, 14) * 1.8 + (noise - lowpass(noise, 6)) * 0.35
    env = np.sin(np.pi * np.clip(t / 0.62, 0, 1)) ** 1.5 * (0.6 + 0.4 * np.sin(t * 40))
    return body * env * vol


def ambient(total, vol=1.0):
    out = np.zeros(int((total + 2) * SR))
    chords = [(57, 60, 64, 67, 71), (53, 57, 60, 64, 67), (48, 55, 59, 64, 67), (55, 59, 62, 64, 69)]
    bar = 6.0
    for b in range(int(total / bar) + 2):
        notes = chords[b % 4]
        dur = bar + 2.0
        for m in notes:
            for det in (-0.6, 0.6):
                w = tone(note_hz(m - 12) * (1 + det / 1200 * 4), dur, "sine", 0.018,
                         adsr(int(dur * SR), 2.2, 0.5, 0.8, 2.4))
                place(out, w, b * bar - 0.5)
        rnd = np.random.default_rng(b + 3)
        for k in range(3):
            m = notes[int(rnd.integers(0, len(notes)))] + 12
            w = tone(note_hz(m), 2.2, "sine", 0.02, np.exp(-t_arr(2.2) * 1.8))
            place(out, w, b * bar + 1.2 + k * 1.9 + float(rnd.uniform(-0.2, 0.2)))
    return out[: int(total * SR)] * vol


def build_story_audio(story, path):
    total = story.total
    n = int(total * SR)
    mix = ambient(total)
    lib = {"pop": lambda: sfx_pop(0.5), "ding": lambda: sfx_ding(880, 0.9, 0.3), "chime": lambda: sfx_success(0.3),
           "tick": sfx_tick, "flip": sfx_flip, "buzz": lambda: sfx_buzz(0.3, 0.3), "down": lambda: sfx_down(0.7, 0.3),
           "whoosh": lambda: sfx_whoosh(0.5, 0.4)}
    pop_pitches = [1.0, 1.22, 0.86, 1.1]  # a little variety so repeated auto-pops don't all sound identical
    pop_i = 0
    for i, s0 in enumerate(story.starts):
        if i > 0:
            place(mix, sfx_flip(), s0 + 0.02, 1.0)
        for t_clip, clip in getattr(story.sections[i], "clips", []):
            place(mix, clip, s0 + t_clip, 1.0)
        events = story.sections[i].events
        explicit_ts = [e["t0"] for e in events if e["type"] == "sfx"]
        for e in sorted(events, key=lambda e: e["t0"]):
            name = e.get("sfx") if e["type"] == "draw" else (e["name"] if e["type"] == "sfx" else None)
            if name in lib:
                place(mix, lib[name](), s0 + e["t0"], e.get("gain", 1.0))
            elif e["type"] in ("write", "draw", "highlight") and not any(abs(e["t0"] - t) < 0.15 for t in explicit_ts):
                # auto-pop on every appearance, quiet enough to sit under an explicit cue
                place(mix, sfx_pop(0.22, pop_pitches[pop_i % len(pop_pitches)]), s0 + e["t0"], 0.5)
                pop_i += 1
    fade_in = np.minimum(1, np.arange(n) / (0.8 * SR))
    fade_out = np.minimum(1, (n - np.arange(n)) / (2.0 * SR))
    mix = np.tanh(mix[:n] * fade_in * fade_out * 1.0) * 0.9
    st = np.stack([mix, mix], axis=1)
    pcm = (st * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    return path

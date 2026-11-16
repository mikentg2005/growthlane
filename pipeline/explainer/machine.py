"""The explainer machine: a storyboard (sections with narration and events) -> a 9:16 video.

A storyboard is a list of Sections. Each section is one notebook page:
    question -> example -> explanation -> try this (+ reference).
Events are timed either in seconds or anchored to a word of the narration ("Friday", "Friday+0.3").
Narration timing is estimated from the text until a real voice track is added; when a voice is
available, only the word-time table changes and every event follows the speaker.

Run a storyboard module:  python pipeline/explainer/stories/<name>.py [--sheet | --still t | --transcript]
"""
import math
import re
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paperlib as pl  # noqa: E402
from engine2 import FPS, H, W, TH, SH, clamp, ease, lerp, out_back, out_cubic, pose_mix  # noqa: E402

FLIP = 0.75            # seconds of page flip at the start of every section but the first
NARR_START = 0.55      # narrator starts a little after the page starts to turn
TAIL = 0.9

DOODLES = {
    "lightbulb": pl.D_lightbulb, "calendar": pl.D_calendar, "circle_day": pl.D_circle_day, "clock": pl.D_clock,
    "phone": pl.D_phone, "laptop": pl.D_laptop, "desk": pl.D_desk, "chair": pl.D_chair, "check": pl.D_check,
    "heart": pl.D_heart, "bolt": pl.D_bolt, "hourglass": pl.D_hourglass, "question": pl.D_question,
    "cross": pl.D_cross, "bar": pl.D_bar, "ground": pl.D_ground, "up": pl.D_up_arrow, "down": pl.D_down_arrow,
    "receipt": pl.D_receipt, "candy": pl.D_candy,
}
PENS = {"ink": pl.INK, "red": pl.RED, "green": pl.GREEN_PEN, "dark": pl.INK_DARK}


# ---------- narration timing ----------
def word_times(text, start=NARR_START, rate=1.0):
    """Estimated start/end time of each spoken word. Replace with TTS timestamps later."""
    out, t = [], start
    for raw in text.split():
        w = re.sub(r"[^\w']", "", raw).lower()
        dur = (0.12 + 0.045 * len(w)) / rate
        out.append((w, t, t + dur))
        t += dur
        if raw[-1:] in ".?!":
            t += 0.38
        elif raw[-1:] in ",:;":
            t += 0.2
    return out


VOICE = None
if "--novoice" not in sys.argv and "--transcript" not in sys.argv:
    try:
        import tts
        VOICE = tts.Voice(start=NARR_START)
    except Exception:  # model not installed -> estimated timing, silent narration
        VOICE = None


class Section:
    def __init__(self, kind, narration, events, min_dur=0.0):
        self.kind, self.narration, self.events, self.min_dur = kind, narration, events, min_dur
        self.clips = []
        if VOICE:
            self.words, self.clips, self.narr_end = VOICE.lay(narration)
        else:
            self.words = word_times(narration)
            self.narr_end = self.words[-1][2] if self.words else NARR_START
        for e in events:
            if e["type"] in ("alex", "mate"):
                for k in e["keys"]:
                    k["at"] = self.resolve(k["at"])
                e["at"] = e["keys"][0]["at"]
            e["t0"] = self.resolve(e.get("at", 0.0))
            if "until" in e:
                e["until"] = self.resolve(e["until"])
            if e.get("drop_at") is not None:
                e["drop_at"] = self.resolve(e["drop_at"])
        last = max([e["t0"] + e.get("dur", 0.0) for e in events] + [0.0])
        self.dur = max(self.narr_end + TAIL, last + 0.7, min_dur)

    def resolve(self, at):
        if isinstance(at, (int, float)):
            return float(at)
        m = re.match(r"^([\w']+)(?:#(\d+))?([+-][\d.]+)?$", at)
        word, nth, off = m.group(1).lower(), int(m.group(2) or 1), float(m.group(3) or 0)
        hits = [w for w in self.words if w[0] == word]
        if len(hits) < nth:
            raise ValueError(f"word '{word}' (#{nth}) not in narration: {self.narration}")
        return hits[nth - 1][1] + off


class Story:
    def __init__(self, title, sections):
        self.title, self.sections = title, sections
        self.starts, t = [], 0.0
        for i, s in enumerate(sections):
            self.starts.append(t)
            t += s.dur + (0 if i == 0 else 0)
        self.total = t

    def locate(self, t):
        idx = 0
        for i, s0 in enumerate(self.starts):
            if t >= s0:
                idx = i
        return idx, t - self.starts[idx]

    def transcript(self):
        return "\n\n".join(f"[{s.kind}] {s.narration}" for s in self.sections)


# ---------- authoring helpers ----------
def draw(name, pos, at=0.0, s=1.0, dur=1.0, pen="ink", width=7, sfx=None, until=None):
    e = dict(type="draw", name=name, pos=pos, at=at, s=s, dur=dur, pen=pen, width=width, sfx=sfx)
    if until is not None:
        e["until"] = until
    return e


def hold(name, at, s=1.0, pen="ink", width=7, off=(40, -40)):
    """A doodle carried in Alex's front hand from time `at` on."""
    return dict(type="hold", name=name, at=at, s=s, pen=pen, width=width, off=off, dur=0.0)


def write(text, pos, at=0.0, size=60, dur=None, pen="ink", anchor="mm"):
    return dict(type="write", text=text, pos=pos, at=at, size=size, pen=pen, anchor=anchor,
                dur=dur if dur is not None else max(0.5, 0.045 * len(text)))


def bubble(text, pos, at, size=46, dur=3.0, tail="alex"):
    return dict(type="bubble", text=text, pos=pos, at=at, size=size, vis=dur, tail=tail, dur=0.4)


def meter(pos, keys, h=360, w=64, at=0.0, label="motivation"):
    return dict(type="meter", pos=pos, keys=keys, h=h, w=w, at=at, label=label, dur=0.6)


def gauge(pos, at, h=440, w=150, ceiling=0.7, rise=1.4, label=None,
          drop_at=None, drop_to=0.35, drop_dur=0.8):
    """A thermometer-style tube with a bulb at the bottom: fills from `at`, rising over `rise`
    seconds, then stays capped at `ceiling` (0..1 of the tube height) -- a visual for "there's a
    ceiling on how high this can go". `pos` is the bulb's center (bottom of the tube).
    If `drop_at` is given, the level later sinks from `ceiling` down to `drop_to` over `drop_dur`
    seconds, starting at that anchor -- for "and then something pulls it down lower still"."""
    return dict(type="gauge", pos=pos, at=at, h=h, w=w, ceiling=ceiling, rise=rise, label=label,
                drop_at=drop_at, drop_to=drop_to, drop_dur=drop_dur, dur=rise)


def actor(keys):
    """keys: dicts with at, x, foot, pose, (flip, gaze, scale, move). x/foot = hip x and ground y."""
    return dict(type="alex", keys=keys, at=keys[0]["at"], dur=0.5)


def mate(keys):
    """A second, neutral-grey character (a colleague), same keyframe format as actor()."""
    return dict(type="mate", keys=keys, at=keys[0]["at"], dur=0.5)


def sfx(name, at, gain=1.0):
    return dict(type="sfx", name=name, at=at, gain=gain, dur=0.0)


def highlight(pos, at, w=300, h=64, dur=0.5, color=(255, 225, 90)):
    """A highlighter-marker swipe behind a word -- a pastel bar that grows left to right.
    Place right before the write() it highlights so it renders underneath."""
    return dict(type="highlight", pos=pos, at=at, w=w, h=h, dur=dur, color=color)


# ---------- rendering ----------
def _off(pose):
    sit = isinstance(pose, str) and (pose.startswith("sit") or pose == "type")
    return SH if sit else (TH + SH)


def _alex_state(e, lt):
    keys = e["keys"]
    t0 = keys[0]["at"]
    if lt < t0:
        return None
    prev = keys[0]
    for k in keys[1:]:
        mv = k.get("move", 0.5)
        start = k["at"] - mv
        if lt < start:
            break
        if lt < k["at"]:
            u = ease((lt - start) / mv)
            moving = abs(k["x"] - prev["x"]) > 4
            pose = pose_mix("walkA", "walkB", (math.sin(lt * 9) + 1) / 2) if moving else pose_mix(prev["pose"], k["pose"], u)
            return dict(x=lerp(prev["x"], k["x"], u), foot=lerp(prev["foot"], k["foot"], u), pose=pose,
                        flip=k.get("flip", prev.get("flip", False)), gaze=k.get("gaze", prev.get("gaze", (1, 0))),
                        scale=lerp(prev.get("scale", 1.0), k.get("scale", 1.0), u), appear=1.0,
                        off=lerp(_off(prev["pose"]) if not moving else TH + SH, _off(k["pose"]) if not moving else TH + SH, u))
        prev = k
    return dict(x=prev["x"], foot=prev["foot"], pose=prev["pose"], flip=prev.get("flip", False),
                gaze=prev.get("gaze", (1, 0)), scale=prev.get("scale", 1.0),
                appear=clamp((lt - t0) / 0.35) if prev is keys[0] else 1.0, off=_off(prev["pose"]))


OUTRO_DUR = 1.3
OUTRO_FADE = 0.25


def render_outro(t):
    """The closing brand card: GrowthLane's diamond mark and wordmark, popping up big and
    centered. `t` is seconds since the card started (0..OUTRO_DUR)."""
    c = pl.new_page()
    k = 0.4 + 0.6 * out_back(clamp(t / 0.5))
    cx, cy = W / 2, H / 2
    size = 30 * k
    dy = cy - 70 * k
    c.line([(cx, dy - size), (cx + size, dy), (cx, dy + size), (cx - size, dy), (cx, dy - size)],
           max(1.0, 5 * k), pl.GREEN_PEN)
    pl.write(c, "GrowthLane", cx, cy + 40 * k, max(1.0, 76 * k), pl.INK_DARK, 1.0, anchor="mm")
    return c.frame()


def render_page(story, idx, lt):
    sec = story.sections[idx]
    is_last = idx == len(story.sections) - 1
    if is_last and lt >= sec.dur - OUTRO_DUR:
        t = lt - (sec.dur - OUTRO_DUR)
        outro = render_outro(t)
        if t < OUTRO_FADE:
            content = render_page(story, idx, sec.dur - OUTRO_DUR - 1e-3)
            return Image.blend(content, outro, ease(t / OUTRO_FADE))
        return outro
    c = pl.new_page()
    # small brand mark, bottom left
    pl.write(c, "GrowthLane", 168, H - 70, 36, (120, 128, 150), 1.0, anchor="lm")
    c.line([(86, H - 70), (104, H - 52), (86, H - 34), (68, H - 52), (86, H - 70)], 3, pl.GREEN_PEN)
    alex_events = []
    mate_events = []
    for e in sec.events:
        t0 = e["t0"]
        if lt < t0 and e["type"] not in ("alex", "mate"):
            continue
        kind = e["type"]
        if kind == "draw":
            if "until" in e and lt >= e["until"]:
                continue
            strokes = DOODLES[e["name"]]()
            p = ease((lt - t0) / max(e["dur"], 0.05))
            settle = clamp((lt - t0 - e["dur"]) / 0.25)
            bump = 1.0 + 0.12 * math.sin(math.pi * settle) if 0 < settle < 1 else 1.0
            pl.draw_strokes(c, strokes, p, e["pos"][0], e["pos"][1], e["s"] * bump, PENS[e["pen"]], e["width"])
        elif kind == "highlight":
            x, y = e["pos"]
            w, h = e["w"], e["h"]
            p = ease(clamp((lt - t0) / max(e["dur"], 0.05)))
            if p > 0:
                c.rrect(x - w / 2, y - h / 2, x - w / 2 + w * p, y + h / 2, h * 0.32, fill=e["color"])
        elif kind == "write":
            p = (lt - t0) / max(e["dur"], 0.05)
            pl.write(c, e["text"], e["pos"][0], e["pos"][1], e["size"], PENS[e["pen"]], p, e["anchor"])
        elif kind == "meter":
            x, y = e["pos"]
            w, h = e["w"], e["h"]
            a = clamp((lt - t0) / 0.6)
            pl.write(c, e["label"], x, y - 36, 34, pl.INK_DARK, a)
            pl.draw_strokes(c, [(pl.wobble(pl.rect(x - w / 2, y, x + w / 2, y + h), 1.2, 11), 7)], a, 0, 0, 1.0, pl.INK)
            ks = e["keys"]
            level = ks[0][1]
            for (ta, la), (tb, lb) in zip(ks, ks[1:]):
                if lt >= ta:
                    level = lerp(la, lb, ease((lt - ta) / max(tb - ta, 0.01)))
            if lt >= ks[-1][0]:
                level = ks[-1][1]
            if a >= 1:
                fh = max(6, (h - 14) * clamp(level))
                col = pl.GREEN_PEN if level > 0.45 else pl.RED
                c.rrect(x - w / 2 + 7, y + h - 7 - fh, x + w / 2 - 7, y + h - 7, 10, fill=col)
        elif kind == "gauge":
            x, yb = e["pos"]
            h, w, ceil_f = e["h"], e["w"], e["ceiling"]
            bulb_r = w * 0.62
            top = yb - h
            ceil_y = top + (1 - ceil_f) * h
            appear = clamp((lt - t0) / 0.5)
            # tube outline + bulb, drawing on
            tube_pts = [(x - w / 2, top), (x - w / 2, yb - bulb_r * 0.3), (x, yb - bulb_r * 0.3)]
            tube_pts2 = [(x + w / 2, top), (x + w / 2, yb - bulb_r * 0.3), (x, yb - bulb_r * 0.3)]
            if appear > 0:
                c.shadow(x, yb + bulb_r * 0.95, bulb_r * 1.1, bulb_r * 0.32, opacity=0.14 * appear)
                pl.draw_strokes(c, [(pl.wobble(tube_pts, 0.8, 21), 7), (pl.wobble(tube_pts2, 0.8, 22), 7),
                                     ([(x - w / 2 - 8, top), (x + w / 2 + 8, top)], 6)], appear, 0, 0, 1.0, pl.INK)
            if appear > 0:
                c.circle(x, yb, bulb_r, fill=pl.PAPER_TOP, outline=pl.INK, w=7)
            # tick marks along the right side
            if appear >= 1:
                for i in range(1, 5):
                    ty = top + h * i / 5
                    c.line([(x + w / 2 + 10, ty), (x + w / 2 + 28, ty)], 4, pl.INK)
            # ceiling cap: a red line a little wider than the tube, drawn once the tube exists
            if appear >= 1:
                k = clamp((lt - t0 - 0.5) / 0.4)
                if k > 0:
                    cx0, cx1 = x - w / 2 - 26, x + w / 2 + 26
                    c.line([(lerp(x, cx0, k), ceil_y), (lerp(x, cx1, k), ceil_y)], 9, pl.RED)
            # the fill: rises from the bulb to the ceiling, then stays capped -- or, if drop_at
            # is set and we've reached it, sinks further down from there.
            fh = clamp((lt - t0) / max(e["rise"], 0.05)) * (ceil_f * h)
            fh = min(fh, ceil_f * h - 6)
            drop_at = e.get("drop_at")
            if drop_at is not None and lt >= drop_at:
                k = ease(clamp((lt - drop_at) / max(e["drop_dur"], 0.05)))
                fh = lerp(ceil_f * h - 6, e["drop_to"] * h, k)
            if fh > 4 and appear >= 1:
                c.rrect(x - w / 2 + 9, yb - bulb_r * 0.3 - fh, x + w / 2 - 9, yb - bulb_r * 0.3 + 12,
                        14, fill=pl.GREEN_PEN)
                c.circle(x, yb, bulb_r - 9, fill=pl.GREEN_PEN)
            if e.get("label") and appear >= 1:
                pl.write(c, e["label"], x, top - 40, 36, pl.INK_DARK, 1.0)
        elif kind == "alex":
            alex_events.append(e)
        elif kind == "mate":
            mate_events.append(e)
    for e in alex_events:
        st = _alex_state(e, lt)
        if st:
            k = st["scale"] * (0.5 + 0.5 * out_back(st["appear"]))
            hip = st["foot"] - st["off"] * k
            c.shadow(st["x"], st["foot"] + 8, 85 * k, 20 * k, opacity=0.15 * st["appear"])
            res = pl.alex(c, st["x"], hip, st["pose"], t=lt, flip=st["flip"], gaze=st["gaze"], scale=k)
            e["_head"] = res["head"]
            e["_hand"] = res["hands"]["af"]
    for e in mate_events:
        st = _alex_state(e, lt)
        if st:
            k = st["scale"] * (0.5 + 0.5 * out_back(st["appear"]))
            c.shadow(st["x"], st["foot"] + 8, 85 * k, 20 * k, opacity=0.15 * st["appear"])
            hip = st["foot"] - st["off"] * k
            res = pl.mate(c, st["x"], hip, st["pose"], t=lt, flip=st["flip"], gaze=st["gaze"], scale=k)
            e["_head"] = res["head"]
            e["_hand"] = res["hands"]["af"]
    for e in sec.events:
        if e["type"] == "hold" and lt >= e["t0"]:
            hand = None
            for a in alex_events:
                hand = a.get("_hand", hand)
            if hand:
                pl.draw_strokes(c, DOODLES[e["name"]](), 1.0, hand[0] + e["off"][0], hand[1] + e["off"][1],
                                e["s"], PENS[e["pen"]], e["width"])
    for e in sec.events:
        if e["type"] == "bubble" and e["t0"] <= lt < e["t0"] + e["vis"] + 0.4:
            src = alex_events if e["tail"] == "alex" else (mate_events if e["tail"] == "mate" else [])
            head = None
            for a in src:
                head = a.get("_head")
            tail = (head[0] + 25, head[1] - 60) if (e["tail"] in ("alex", "mate") and head) else None
            u = (lt - e["t0"]) / 0.4 if lt < e["t0"] + e["vis"] else 1 - (lt - e["t0"] - e["vis"]) / 0.4
            pl.bubble(c, e["pos"][0], e["pos"][1], e["text"], e["size"], tail, u)
    return c.frame()


def draw_at(story, t):
    t = min(t, story.total - 1e-3)
    idx, lt = story.locate(t)
    img = render_page(story, idx, lt)
    if idx > 0 and lt < FLIP:
        prev = render_page(story, idx - 1, story.sections[idx - 1].dur)
        img = pl.flip_page(prev, img, lt / FLIP)
    return img


# ---------- cli ----------
_STORY = None


def _init_worker(story):
    global _STORY
    _STORY = story


def _frame(i):
    return draw_at(_STORY, i / FPS)


def main(story, name, build_audio=None):
    from engine2 import render_video, Image
    out = Path(__file__).resolve().parent / "out"
    out.mkdir(exist_ok=True)
    if "--transcript" in sys.argv:
        print(story.transcript())
        print("\nestimated length: %.1f s" % story.total)
        return
    if "--still" in sys.argv:
        t = float(sys.argv[sys.argv.index("--still") + 1])
        draw_at(story, t).save(out / f"{name}-still-{t:g}.png")
        return
    if "--sheet" in sys.argv:
        n = 16
        ts = [story.total * (i + 0.5) / n for i in range(n)]
        sheet = Image.new("RGB", (8 * 270, 2 * 480), "white")
        for i, t in enumerate(ts):
            sheet.paste(draw_at(story, t).resize((265, 470)), ((i % 8) * 270, (i // 8) * 480))
        sheet.save(out / f"{name}-sheet.png")
        print("sheet saved; total %.1f s" % story.total)
        return
    wav = None
    if build_audio:
        wav = out / f"{name}.wav"
        build_audio(story, wav)
    target = out / f"{name}.mp4"
    n = render_video(_frame, story.total, target, audio=wav, initializer=_init_worker, initargs=(story,))
    print("rendered", n, "frames ->", target)

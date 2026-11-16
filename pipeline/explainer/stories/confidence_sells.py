"""Storyboard: your self-image is your sales ceiling (confidence in sales).

Format: statement -> explanation (narrator, no character scene) -> close + reference. This is
Brian Tracy's own argument in "The Psychology of Selling" (covered in our Sales & Persuasion
article) -- framed honestly as his argument, not as a proven research finding, since the book
itself is "upbeat and self-help flavored" rather than research-driven (our article's own
description). No characters in this one: just text, a simple ceiling/thermostat graphic, and a
calm voice.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import machine as m
from machine import Section, Story, draw, gauge, highlight, sfx, write

CX = 570

Q = Section(
    "statement",
    "Your self-image is your sales ceiling.",
    [
        write("Your self-image", (CX, 420), at=0.6, size=92, dur=1.1),
        write("is your sales ceiling.", (CX, 550), at="ceiling", size=76, pen="red", dur=1.2),
        gauge((CX, 1350), at="ceiling+0.3", h=340, w=120, ceiling=0.6, rise=1.0),
    ],
    min_dur=5.5,
)

EXPLAIN = Section(
    "explanation",
    "Brian Tracy says your self-concept works like a thermostat, it sets a ceiling on how well "
    "you can sell, no matter your skill. What keeps that ceiling low, more than anything, is the "
    "fear of being told no.",
    [
        write("Brian Tracy says:", (CX, 280), at="tracy", size=64, dur=1.0),
        write("self-concept", (CX, 400), at="selfconcept", size=82, pen="green", dur=1.0),
        write("= thermostat", (CX, 490), at="thermostat", size=68, pen="dark", dur=1.0),
        gauge((CX, 1170), at="sets", h=430, w=150, ceiling=0.72, rise=1.3,
              drop_at="low", drop_to=0.32, drop_dur=0.9),
        sfx("tick", at="sets+1.3"),
        write("no matter", (CX, 1310), at="matter", size=56, dur=0.8),
        write("your skill.", (CX, 1390), at="skill", size=56, dur=0.8),
        write("The real limit:", (CX, 1540), at="low", size=58, pen="dark", dur=1.0),
        draw("down", (CX + 220, 1480), at="low+0.9", s=0.55, dur=0.4, pen="red", width=6),
        highlight((CX, 1650), at="no#2", w=620, h=76, dur=0.45),
        write("fear of being told no.", (CX, 1650), at="no#2", size=52, pen="red", dur=1.3),
        sfx("down", at="low"),
    ],
)

TRY = Section(
    "close",
    "Next time you hear a no, remember: rejection was never personal. Based on The Psychology of "
    "Selling, by Brian Tracy.",
    [
        write("Next time", (CX, 320), at="next", size=84, dur=0.9),
        write("you hear a \"no,\"", (CX, 440), at="no", size=68, dur=0.9),
        write("remember:", (CX, 560), at="remember", size=62, pen="dark", dur=0.8),
        write("rejection was", (CX, 760), at="rejection", size=86, pen="green", dur=1.0),
        write("never personal.", (CX, 870), at="personal", size=86, pen="green", dur=1.1),
        write("Based on", (CX, 1560), at="based", size=48, pen="dark", dur=0.6),
        write("The Psychology of Selling, by Brian Tracy", (CX, 1635), at="psychology", size=46, pen="dark", dur=1.4),
        sfx("chime", at="based"),
    ],
)

STORY = Story("confidence-sells", [Q, EXPLAIN, TRY])

if __name__ == "__main__":
    from audio import build_story_audio
    m.main(STORY, "confidence-sells", build_audio=build_story_audio)

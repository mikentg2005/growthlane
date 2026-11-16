"""Storyboard: why avoiding hard feedback hurts your team (Radical Candor).

Format: statement -> example, told as two takes of the same moment (same page background, two
pages with a flip between them) -> explanation (narrator) -> try this + reference. Facts are from
Kim Scott's "Radical Candor" (covered in our Leadership article). Alex and Sam are fictional.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import machine as m
from machine import Section, Story, actor, bubble, draw, mate, sfx, write

CX = 570

Q = Section(
    "statement",
    "Being nice isn't leadership. Being honest is.",
    [
        write("Being nice", (CX, 500), at="being", size=100, dur=1.1),
        draw("cross", (870, 500), at="nice", s=0.7, dur=0.4, pen="red", width=7),
        write("isn't leadership.", (CX, 630), at="leadership", size=84, pen="red", dur=1.2),
        write("Being honest", (CX, 800), at="being#2", size=100, dur=1.1),
        draw("check", (900, 800), at="honest", s=0.7, dur=0.4, pen="green", width=9),
        write("is.", (CX, 930), at="is", size=84, pen="green", dur=0.6),
    ],
    min_dur=5.5,
)

TAKE1 = Section(
    "example take one",
    "Sam is late to the meeting again. She rushes in, apologizing. Alex just says, don't worry "
    "about it. The next meeting, Sam is late again.",
    [
        draw("ground", (CX, 1540), at=0.6, s=1.25, dur=0.8),
        draw("clock", (800, 420), at=0.6, s=1.1, dur=1.0),
        actor([dict(at=0.2, x=320, foot=1540, pose="stand", gaze=(1, 0), scale=1.3),
               dict(at="worry", x=320, foot=1540, pose="shrug", gaze=(1, -0.1), move=2.2, scale=1.3)]),
        mate([dict(at=0.3, x=1050, foot=1540, pose="walkB", flip=True, gaze=(-1, 0), scale=1.3),
              dict(at="rushes", x=760, foot=1540, pose="worry", flip=True, gaze=(-1, -0.1), move=2.2, scale=1.3),
              dict(at="next", x=1050, foot=1540, pose="walkB", flip=True, move=3.5, scale=1.3),
              dict(at="again#2", x=760, foot=1540, pose="worry", flip=True, gaze=(-1, -0.1), move=1.2, scale=1.3)]),
        bubble("don't worry about it!", (620, 820), at="worry", size=50, dur=1.8),
        write("...", (900, 760), at="worry+1.4", size=60, pen="dark", dur=0.6),
        write("...nothing changes.", (CX, 1700), at="again#2", size=64, pen="red", dur=1.0),
    ],
)

TAKE2 = Section(
    "example take two",
    "Same pattern. This time, Alex says it directly: the lateness is a problem, and it needs to "
    "change. Sam looks stung, then nods. The next meeting, Sam is on time.",
    [
        draw("ground", (CX, 1540), at=0.6, s=1.25, dur=0.8),
        draw("clock", (800, 420), at=0.6, s=1.1, dur=1.0),
        actor([dict(at=0.2, x=320, foot=1540, pose="stand", gaze=(1, 0), scale=1.3),
               dict(at="directly", x=320, foot=1540, pose="point", gaze=(1, -0.1), move=2.0, scale=1.3),
               dict(at="time#2", x=320, foot=1540, pose="cheer", gaze=(1, 0), move=0.4, scale=1.3)]),
        mate([dict(at=0.3, x=1050, foot=1540, pose="walkB", flip=True, gaze=(-1, 0), scale=1.3),
              dict(at="pattern", x=760, foot=1540, pose="worry", flip=True, gaze=(-1, -0.1), move=0.5, scale=1.3),
              dict(at="stung", x=760, foot=1540, pose="scared", flip=True, gaze=(-1, -0.1), move=2.0, scale=1.3),
              dict(at="nods", x=760, foot=1540, pose="stand", flip=True, gaze=(-1, 0), move=0.9, scale=1.3),
              dict(at="time#2", x=760, foot=1540, pose="cheer", flip=True, gaze=(-1, 0), move=0.5, scale=1.3)]),
        bubble("this needs to change", (620, 820), at="change", size=48, dur=1.8),
        write("...", (900, 760), at="pattern+3.3", size=60, pen="dark", dur=0.6),
        draw("check", (960, 870), at="time#2", s=0.9, dur=0.5, pen="green", width=9),
        write("...and it gets better.", (CX, 1700), at="time#2+0.3", size=64, pen="green", dur=1.1),
    ],
)

EXPLAIN = Section(
    "explanation",
    "Psychologist and former Google executive Kim Scott calls this ruinous empathy. When you care "
    "but don't challenge, feedback just disappears. Her answer is radical candor: care personally, "
    "and challenge directly, at the same time.",
    [
        write("Kim Scott calls it", (CX, 300), at="scott", size=84, dur=1.1),
        write("ruinous empathy", (CX, 420), at="empathy", size=90, pen="red", dur=1.2),
        draw("heart", (320, 620), at="care", s=1.0, dur=0.9, pen="dark"),
        write("care,", (720, 570), at="care", size=52, dur=0.6),
        write("no challenge", (720, 650), at="challenge", size=52, pen="red", dur=0.9),
        write("Her answer:", (CX, 850), at="answer", size=56, dur=0.8),
        write("radical candor", (CX, 960), at="radical", size=94, pen="green", dur=1.3),
        draw("heart", (330, 1180), at="care#2", s=1.0, dur=0.8, pen="dark"),
        draw("bolt", (660, 1180), at="challenge#2", s=0.9, dur=0.8, pen="green"),
        write("care + challenge", (CX, 1380), at="time", size=52, pen="green", dur=1.0),
        sfx("ding", at="radical"),
    ],
)

TRY = Section(
    "try this",
    "That's radical candor: caring enough to be honest. Based on Radical Candor, by Kim Scott.",
    [
        write("That's radical candor:", (CX, 420), at="radical", size=78, dur=1.3),
        write("caring enough", (CX, 560), at="caring", size=80, pen="green", dur=1.0),
        write("to be honest.", (CX, 660), at="honest", size=80, pen="green", dur=1.0),
        draw("heart", (320, 850), at="caring", s=1.0, dur=0.9, pen="dark"),
        draw("bolt", (650, 850), at="honest", s=0.9, dur=0.9, pen="green"),
        actor([dict(at=0.3, x=300, foot=1500, pose="stand", gaze=(1, 0), scale=1.3),
               dict(at="based+0.3", x=300, foot=1500, pose="wave", move=0.5, scale=1.3)]),
        write("Based on", (CX, 1560), at="based", size=48, pen="dark", dur=0.6),
        write("Radical Candor, by Kim Scott", (CX, 1635), at="radical#2", size=54, pen="dark", dur=1.3),
        sfx("chime", at="based"),
    ],
)

STORY = Story("radical-candor", [Q, TAKE1, TAKE2, EXPLAIN, TRY])

if __name__ == "__main__":
    from audio import build_story_audio
    m.main(STORY, "radical-candor", build_audio=build_story_audio)

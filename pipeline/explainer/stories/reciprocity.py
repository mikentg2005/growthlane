"""Storyboard: why a free piece of candy makes you tip more (reciprocity).

Format: question -> example (Alex) -> explanation (narrator) -> try this + reference.
Facts are from Cialdini's "Influence: The Psychology of Persuasion" (covered in our Sales &
Persuasion article) and the restaurant-tipping study by Strohmetz, Rind, Fisher & Lynn (2002,
Journal of Applied Social Psychology). Alex is a fictional character. The tip is labelled as our
suggestion, not the study's.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import machine as m
from machine import Section, Story, actor, bubble, draw, sfx, write

CX = 570

Q = Section(
    "question",
    "Why does a free piece of candy make you tip more?",
    [
        write("Why does a", (CX, 320), at=0.7, size=104, dur=1.0),
        write("free candy make", (CX, 450), at="free", size=92, dur=1.2),
        write("you tip more?", (CX, 570), at="you", size=92, dur=1.0),
        draw("question", (800, 1060), at="tip", s=3.2, dur=1.4, pen="red", width=9),
        actor([dict(at=1.2, x=300, foot=1640, pose="stand", gaze=(1, 0), scale=1.5),
               dict(at="tip+0.3", x=300, foot=1640, pose="shrug", gaze=(1, -0.2), move=0.6, scale=1.5)]),
        bubble("huh?", (430, 1050), at="tip+0.5", size=56, dur=2.0),
    ],
)

EX = Section(
    "example",
    "Meet Alex, at the end of dinner. The waiter leaves the check. On the tray, one piece of candy. "
    "Then, a second piece of candy. Alex didn't ask for anything. He just leaves a bigger tip.",
    [
        write("Meet Alex", (CX, 300), at="meet", size=108, dur=1.0),
        draw("ground", (CX, 1540), at=0.6, s=1.25, dur=0.8),
        draw("desk", (770, 1274), at=0.9, s=1.4, dur=0.9),
        draw("chair", (370, 1425), at=1.0, s=1.4, dur=0.7),
        actor([dict(at="dinner+0.2", x=370, foot=1540, pose="sit", gaze=(1, 0), scale=1.4),
               dict(at="check", x=370, foot=1540, pose="sitlook", gaze=(1, -0.1), move=0.5, scale=1.4),
               dict(at="candy#2+0.3", x=370, foot=1540, pose="cheer", gaze=(1, -0.1), move=0.6, scale=1.4)]),
        draw("receipt", (760, 1160), at="check", s=1.1, dur=0.9),
        draw("candy", (840, 1050), at="candy#1", s=0.6, dur=0.6, pen="red", sfx="pop"),
        draw("candy", (955, 1130), at="candy#2", s=0.6, dur=0.6, pen="red", sfx="pop"),
        bubble("for me?", (640, 940), at="candy#2+0.4", size=50, dur=2.4),
        write("+ bigger tip", (CX, 1700), at="bigger", size=60, pen="green", dur=1.0),
    ],
)

EXPLAIN = Section(
    "explanation",
    "Psychologists call this reciprocity. When someone gives us something, even something small, "
    "we feel a pull to give something back. A classic study tested it in real restaurants. With no "
    "candy, tips averaged about nineteen percent. With two pieces of candy, one on the tray, then a "
    "surprise second one, tips rose to almost twenty two percent.",
    [
        write("It's called", (CX, 300), at="psychologists", size=96, dur=1.0),
        write("reciprocity", (CX, 420), at="reciprocity", size=100, pen="green", dur=1.2),
        draw("heart", (CX, 600), at="pull", s=1.3, dur=1.0, pen="red"),
        write("give something,", (310, 870), at="give", size=56, dur=0.9),
        write("get something back", (310, 940), at="back", size=56, dur=1.0),
        write("~19%", (300, 1180), at="nineteen", size=100, pen="dark", dur=0.9),
        write("no candy", (300, 1270), at="nineteen+0.3", size=44, pen="dark", dur=0.8),
        draw("up", (570, 1180), at="rose", s=1.0, dur=0.8, pen="green", width=9),
        write("~22%", (840, 1180), at="twenty", size=100, pen="green", dur=0.9),
        write("two candies", (840, 1270), at="twenty+0.3", size=44, pen="dark", dur=0.8),
        sfx("ding", at="twenty"),
    ],
)

TRY = Section(
    "try this",
    "Try this: do someone a small favor before you ask them for one. It won't guarantee a yes, but "
    "it shifts the odds in your favor. Based on Influence, by Robert Cialdini, and a 2002 "
    "restaurant study on tipping.",
    [
        write("Try this", (CX, 300), at=0.3, size=112, dur=1.0),
        draw("heart", (310, 650), at="favor", s=1.3, dur=1.1, pen="red"),
        write("give first,", (760, 600), at="favor", size=58, dur=0.9),
        write("ask later", (760, 680), at="ask", size=58, dur=0.8),
        write("(our suggestion)", (CX, 820), at="guarantee", size=46, dur=1.0),
        actor([dict(at=0.3, x=300, foot=1500, pose="stand", gaze=(1, 0), scale=1.3),
               dict(at="shifts+0.3", x=300, foot=1500, pose="wave", move=0.5, scale=1.3)]),
        write("Based on", (CX, 1560), at="based", size=48, pen="dark", dur=0.6),
        write("Influence, by Robert Cialdini", (CX, 1635), at="cialdini", size=58, pen="dark", dur=1.3),
        write("restaurant study: Strohmetz et al., 2002", (CX, 1710), at="cialdini+0.9", size=36, pen="dark", dur=1.4),
        sfx("chime", at="based"),
    ],
)

STORY = Story("reciprocity-candy", [Q, EX, EXPLAIN, TRY])

if __name__ == "__main__":
    from audio import build_story_audio
    m.main(STORY, "reciprocity-candy", build_audio=build_story_audio)

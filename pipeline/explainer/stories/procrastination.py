"""Storyboard: why we put things off (Steel's procrastination equation).

Format: question -> example (Alex) -> explanation (narrator) -> try this + reference.
All facts are from _posts/2026-11-13-best-books-on-procrastination.md and its sources.
Alex is a fictional character. The tip is labelled as our suggestion.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import machine as m
from machine import Section, Story, actor, bubble, draw, hold, sfx, write

CX = 570

Q = Section(
    "question",
    "Why do we keep putting off the things that matter?",
    [
        write("Why do we", (CX, 340), at=0.7, size=112, dur=1.0),
        write("keep putting off?", (CX, 480), at="keep", size=112, dur=1.4),
        draw("question", (790, 1060), at="matter", s=3.4, dur=1.6, pen="red", width=9),
        actor([dict(at=1.2, x=310, foot=1640, pose="stand", gaze=(1, 0), scale=1.5),
               dict(at="matter+0.5", x=310, foot=1640, pose="worry", gaze=(1, -0.3), move=0.7, scale=1.5)]),
        bubble("later…", (400, 790), at="matter+0.9", size=64, dur=2.4),
    ],
)

EX = Section(
    "example",
    "Meet Alex. His report is due Friday. He opens the laptop, then picks up the phone. Just five more minutes.",
    [
        write("Meet Alex", (CX, 320), at="meet", size=112, dur=1.0),
        draw("ground", (CX, 1540), at=0.6, s=1.25, dur=0.8),
        draw("desk", (770, 1274), at=0.9, s=1.4, dur=0.9),
        draw("chair", (370, 1425), at=1.0, s=1.4, dur=0.7),
        draw("laptop", (800, 1176), at="opens", s=1.4, dur=1.0),
        actor([dict(at="alex+0.2", x=370, foot=1540, pose="sit", gaze=(1, 0.1), scale=1.4),
               dict(at="opens+0.7", x=370, foot=1540, pose="type", gaze=(1, 0.1), move=0.5, scale=1.4),
               dict(at="phone+0.3", x=370, foot=1540, pose="sitphone", gaze=(1, -0.2), move=0.9, scale=1.4)]),
        draw("calendar", (830, 640), at="report", s=1.6, dur=1.2),
        draw("circle_day", (830, 640), at="friday", s=1.6, dur=0.6, pen="red", width=8),
        write("Friday", (830, 826), at="friday+0.1", size=64, pen="red", dur=0.7),
        sfx("ding", at="friday+0.2"),
        draw("clock", (320, 640), at="friday+0.9", s=1.3, dur=1.0),
        draw("phone", (590, 1186), at="picks-0.4", s=1.1, dur=0.8, sfx="pop", until="phone+0.3"),
        hold("phone", at="phone+0.3", s=0.9, off=(45, -45)),
        bubble("Just five more minutes…", (590, 935), at="just", size=50, dur=3.2),
    ],
)

EXPLAIN = Section(
    "explanation",
    "Researcher Piers Steel sums it up in one equation. Motivation equals expectancy times value, divided by "
    "impulsiveness times delay. Expectancy: do you believe you can do it? Value: does it matter to you? "
    "Impulsiveness: how easily are you distracted? Delay: how far away does the reward feel? "
    "The top two raise your motivation. The bottom two pull it down.",
    [
        write("Motivation =", (CX, 310), at="researcher+0.6", size=104, dur=1.0),
        write("Expectancy  ×  Value", (CX, 450), at="expectancy", size=84, pen="green", dur=1.4),
        draw("bar", (CX, 520), at="value+0.2", dur=0.7),
        write("Impulsiveness  ×  Delay", (CX, 610), at="impulsiveness", size=84, pen="red", dur=1.6),
        draw("check", (330, 880), at="expectancy#2", s=1.1, dur=0.8, pen="green", width=9),
        write("Expectancy", (330, 1000), at="expectancy#2", size=60, pen="green", dur=0.9),
        write("can I do it?", (330, 1065), at="believe", size=48, dur=0.9),
        draw("heart", (810, 880), at="value#2", s=1.1, dur=0.8, pen="green", width=8),
        write("Value", (810, 1000), at="value#2", size=60, pen="green", dur=0.6),
        write("does it matter?", (810, 1065), at="matter", size=48, dur=0.9),
        draw("bolt", (330, 1290), at="impulsiveness#2", s=1.1, dur=0.8, pen="red", width=8),
        write("Impulsiveness", (330, 1410), at="impulsiveness#2", size=60, pen="red", dur=1.0),
        write("easily distracted?", (330, 1475), at="distracted", size=48, dur=1.0),
        draw("hourglass", (810, 1290), at="delay#2", s=1.1, dur=0.8, pen="red", width=8),
        write("Delay", (810, 1410), at="delay#2", size=60, pen="red", dur=0.6),
        write("reward far away?", (810, 1475), at="reward", size=48, dur=1.0),
        draw("up", (170, 450), at="top", s=0.7, dur=0.6, pen="green", width=8),
        draw("down", (170, 610), at="bottom", s=0.7, dur=0.6, pen="red", width=8),
        sfx("ding", at="expectancy+0.1"),
    ],
)

TRY = Section(
    "try",
    "Try this. It is our suggestion, not the author's: set a deadline sooner than the real one, and tell "
    "someone. That shrinks the delay. Based on The Procrastination Equation, by Piers Steel.",
    [
        write("Try this", (CX, 330), at="try", size=130, pen="green", dur=1.0),
        draw("calendar", (310, 700), at="deadline", s=1.5, dur=1.1),
        write("Friday", (310, 880), at="deadline", size=64, pen="red", dur=0.6),
        draw("cross", (310, 880), at="sooner", s=1.3, dur=0.5, pen="red", width=7),
        write("Wednesday", (800, 760), at="than", size=84, pen="green", dur=1.1),
        sfx("ding", at="than+0.3"),
        write("(our suggestion)", (700, 1010), at="our", size=48, dur=1.0),
        actor([dict(at="someone", x=260, foot=1500, pose="stand", gaze=(1, 0), scale=1.3),
               dict(at="shrinks", x=260, foot=1500, pose="cheer", move=0.5, scale=1.3)]),
        write("Based on", (CX, 1560), at="based", size=48, pen="dark", dur=0.6),
        write("The Procrastination Equation", (CX, 1635), at="procrastination", size=64, pen="dark", dur=1.4),
        write("by Piers Steel", (CX, 1710), at="by", size=50, pen="dark", dur=0.8),
        sfx("chime", at="based"),
    ],
)

STORY = Story("procrastination-equation", [Q, EX, EXPLAIN, TRY])

if __name__ == "__main__":
    from audio import build_story_audio
    m.main(STORY, "procrastination-notebook", build_audio=build_story_audio)

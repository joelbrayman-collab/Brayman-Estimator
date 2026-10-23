"""How long each training module takes to sit (Joel, 23 Oct 2026): "a module is a 30 to 45 minute session".

A display aid only. Nothing here changes a lesson, a lesson key or an acceptance-test key, so every trainee's saved
progress and acceptance results stay exactly as they are.

The rule (the same for Contractor, Field Crew and Supplier training), on the lessons and acceptance tests the
trainee's role actually sees:

- 2 minutes for each step (read it, do it on the training site, tick it);
- 4 minutes for each lesson (what and why, the practice exercise, Finish this lesson);
- 3 minutes for each acceptance test of the module (do it, record Pass, Fail or Blocked).

A sitting is never shown as less than 30 minutes (signing in, finding your place, a question to the Tutor and a
note are part of every sitting) and is rounded to the nearest 5 minutes. A module whose total, rounded to the
nearest 5 minutes, is more than 45 minutes is shown as Session 1, Session 2, ... : the fewest sessions of at most 45 minutes each, cut only between
lessons, as evenly as the lessons allow. The acceptance tests belong to the last session.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import ceil
from typing import List, Sequence, Tuple

MINUTES_PER_STEP = 2
MINUTES_PER_LESSON = 4
MINUTES_PER_TEST = 3
SITTING_MIN = 30
SITTING_MAX = 45


@dataclass(frozen=True)
class Session:
    number: int                 # 1-based
    lesson_keys: Tuple[str, ...]
    minutes: int                # shown, rounded to 5 and never below SITTING_MIN

    @property
    def label(self) -> str:
        return f"About {self.minutes} minutes"


@dataclass(frozen=True)
class ModuleEstimate:
    module_key: str
    raw_minutes: int            # the rule's total before rounding
    sessions: Tuple[Session, ...]

    @property
    def minutes(self) -> int:
        return sum(s.minutes for s in self.sessions)

    @property
    def split(self) -> bool:
        return len(self.sessions) > 1

    @property
    def label(self) -> str:
        if not self.split:
            return self.sessions[0].label
        return f"{len(self.sessions)} sessions, about {self.minutes} minutes in all"

    def session_starts(self) -> dict:
        """{lesson key: session number} for the first lesson of each session after the first."""
        return {s.lesson_keys[0]: s.number for s in self.sessions[1:] if s.lesson_keys}


def _shown(minutes: int) -> int:
    return max(SITTING_MIN, int(5 * round(minutes / 5)))


def lesson_minutes(lesson) -> int:
    return MINUTES_PER_LESSON + MINUTES_PER_STEP * len(lesson.steps)


def _best_cuts(loads: Sequence[int], tail: int, parts: int) -> Tuple[int, ...]:
    """Cut points (lesson indexes) giving ``parts`` contiguous groups with the smallest largest group."""
    n = len(loads)
    best, best_cuts = None, ()
    for cuts in combinations(range(1, n), parts - 1):
        bounds = (0,) + cuts + (n,)
        groups = [sum(loads[a:b]) for a, b in zip(bounds, bounds[1:])]
        groups[-1] += tail
        worst = max(groups)
        if best is None or worst < best:
            best, best_cuts = worst, cuts
    return best_cuts


def estimate(module, uat_count: int) -> ModuleEstimate:
    """The module as the trainee sees it (lessons already filtered for their role) and its acceptance tests."""
    lessons = list(module.lessons)
    loads = [lesson_minutes(lesson) for lesson in lessons]
    tail = MINUTES_PER_TEST * uat_count
    raw = sum(loads) + tail
    parts = 1
    if lessons and int(5 * round(raw / 5)) > SITTING_MAX:  # more than about 45 minutes: split
        parts = max(2, min(len(lessons), ceil(raw / SITTING_MAX)))
    cuts = _best_cuts(loads, tail, parts) if parts > 1 else ()
    bounds = (0,) + tuple(cuts) + (len(lessons),)
    sessions: List[Session] = []
    for number, (a, b) in enumerate(zip(bounds, bounds[1:]), start=1):
        minutes = sum(loads[a:b]) + (tail if b == len(lessons) else 0)
        sessions.append(Session(number, tuple(lesson.key for lesson in lessons[a:b]), _shown(minutes)))
    return ModuleEstimate(module.key, raw, tuple(sessions))


def for_track(pathway: str, role: str) -> List[Tuple[object, ModuleEstimate]]:
    """[(module, estimate)] for one pathway and role, in module order."""
    from app.training import content as C

    cases = C.uat_for(pathway, role)
    return [(m, estimate(m, sum(1 for c in cases if c.module_key == m.key))) for m in C.modules_for(pathway, role)]

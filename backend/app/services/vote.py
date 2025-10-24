from __future__ import annotations

from collections import Counter


def tally(ballots: dict[int, int | None]) -> dict[int, int]:
    c = Counter(v for v in ballots.values() if v is not None)
    return dict(c)


def leaders_of(counts: dict[int, int]) -> tuple[list[int], int]:
    if not counts:
        return ([], 0)
    top = max(counts.values())
    leaders = [k for k, v in counts.items() if v == top]
    return leaders, top


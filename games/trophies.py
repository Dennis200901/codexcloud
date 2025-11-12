from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


TROPHY_FILE = Path("trophies.json")


@dataclass
class TrophyEntry:
    game: str
    mode: str
    difficulty: str
    result: str


@dataclass
class TrophyData:
    trophies: int = 0
    history: List[TrophyEntry] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict) -> "TrophyData":
        entries = [
            TrophyEntry(
                game=item.get("game", "Unbekannt"),
                mode=item.get("mode", ""),
                difficulty=item.get("difficulty", ""),
                result=item.get("result", ""),
            )
            for item in payload.get("history", [])
        ]
        return cls(trophies=payload.get("trophies", 0), history=entries)

    def to_dict(self) -> dict:
        return {
            "trophies": self.trophies,
            "history": [entry.__dict__ for entry in self.history[-25:]],
        }


class TrophyHall:
    LEAGUE_NAMES = [
        "Arcade-Anfänger",
        "Highscore-Jäger",
        "Neon-Champion",
        "Retro-Legende",
        "Synthwave-Ikone",
    ]

    def __init__(self):
        self.data = TrophyData()
        self.load()

    def load(self):
        if TROPHY_FILE.exists():
            try:
                payload = json.loads(TROPHY_FILE.read_text(encoding="utf-8"))
                self.data = TrophyData.from_dict(payload)
            except Exception:
                self.data = TrophyData()
        else:
            self.save()

    def save(self):
        TROPHY_FILE.write_text(json.dumps(self.data.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def add_win(self, game: str, mode: str, difficulty: str, result: str = "Sieg"):
        self.data.trophies += 10
        self.data.history.append(TrophyEntry(game=game, mode=mode, difficulty=difficulty, result=result))
        self.save()

    @property
    def trophies(self) -> int:
        return self.data.trophies

    def league_index(self) -> int:
        return min(len(self.LEAGUE_NAMES) - 1, self.data.trophies // 50)

    def league_name(self) -> str:
        return self.LEAGUE_NAMES[self.league_index()]

    def progress_to_next_league(self) -> tuple[int, int]:
        current = self.data.trophies % 50
        return current, 50

    def recent_entries(self) -> List[TrophyEntry]:
        return list(reversed(self.data.history[-15:]))

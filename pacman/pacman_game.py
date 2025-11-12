"""Terminal Pac-Man clone implemented with the curses module."""
from __future__ import annotations

import curses
import os
import sys
import time
from typing import Dict

if __package__ in (None, ""):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from pacman.common import DIRECTIONS, Direction, MAZE_LAYOUT, PacmanLogic
else:
    from .common import DIRECTIONS, Direction, MAZE_LAYOUT, PacmanLogic


# Mapping is defined lazily to allow importing without curses on other platforms.
KEY_TO_DIRECTION: Dict[int, Direction] = {
    curses.KEY_UP: DIRECTIONS["UP"],
    curses.KEY_DOWN: DIRECTIONS["DOWN"],
    curses.KEY_LEFT: DIRECTIONS["LEFT"],
    curses.KEY_RIGHT: DIRECTIONS["RIGHT"],
    ord("w"): DIRECTIONS["UP"],
    ord("W"): DIRECTIONS["UP"],
    ord("s"): DIRECTIONS["DOWN"],
    ord("S"): DIRECTIONS["DOWN"],
    ord("a"): DIRECTIONS["LEFT"],
    ord("A"): DIRECTIONS["LEFT"],
    ord("d"): DIRECTIONS["RIGHT"],
    ord("D"): DIRECTIONS["RIGHT"],
}


class PacmanGame(PacmanLogic):
    """Encapsulates the Pac-Man game logic."""

    def __init__(self, screen: "curses._CursesWindow") -> None:
        super().__init__()
        self.screen = screen

    # Rendering -----------------------------------------------------------
    def draw(self) -> None:
        self.screen.clear()
        # Draw maze background
        for r, row in enumerate(MAZE_LAYOUT):
            for c, char in enumerate(row):
                ch = " "
                if (r, c) in self.walls:
                    ch = "#"
                elif (r, c) in self.power_pellets:
                    ch = "o"
                elif (r, c) in self.pellets:
                    ch = "."
                try:
                    self.screen.addch(r, c, ch)
                except curses.error:
                    pass  # Ignore drawing outside of screen bounds

        # Draw ghost(s)
        for ghost in self.ghosts:
            char = "g" if ghost.frightened() else "G"
            try:
                self.screen.addch(ghost.position[0], ghost.position[1], char)
            except curses.error:
                pass

        # Draw Pac-Man last so he appears on top
        try:
            self.screen.addch(self.pacman.position[0], self.pacman.position[1], "C")
        except curses.error:
            pass

        # Scoreboard
        status_line = f"Score: {self.score}   Lives: {self.lives}   Level: {self.level}"
        instructions = "Arrows/WASD to move, q to quit"
        try:
            self.screen.addstr(self.height + 1, 0, status_line)
            self.screen.addstr(self.height + 2, 0, instructions)
        except curses.error:
            pass

        self.screen.refresh()

    # Game loop -----------------------------------------------------------
    def game_loop(self) -> None:
        self.screen.nodelay(True)
        self.screen.timeout(100)  # 100 ms tick
        while self.is_alive() and not self.is_level_cleared():
            key = self.screen.getch()
            if key in (ord("q"), ord("Q")):
                break
            if key in KEY_TO_DIRECTION:
                self.set_desired_direction(KEY_TO_DIRECTION[key])

            event = self.tick()
            self.draw()
            if event == "life_lost":
                time.sleep(1.0)

        self._game_over_screen()

    def _game_over_screen(self) -> None:
        self.screen.nodelay(False)
        message = "You Win!" if self.is_level_cleared() else "Game Over"
        try:
            self.screen.addstr(self.height // 2, (self.width // 2) - len(message) // 2, message)
            self.screen.addstr(self.height // 2 + 2, (self.width // 2) - 8, "Press any key")
        except curses.error:
            pass
        self.screen.refresh()
        self.screen.getch()


def run(screen: "curses._CursesWindow") -> None:
    game = PacmanGame(screen)
    game.draw()
    game.game_loop()


def main() -> None:
    curses.wrapper(run)


if __name__ == "__main__":
    main()

"""Terminal Pac-Man clone implemented with the curses module.

The game uses a simple grid-based maze with a single ghost that alternates
between chasing Pac-Man and roaming randomly. The objective is to eat all
pellets without losing all lives.
"""
from __future__ import annotations

import curses
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Sequence, Set, Tuple


Coordinate = Tuple[int, int]
Direction = Tuple[int, int]

DIRECTIONS: Dict[str, Direction] = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
}

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

REVERSE_DIRECTION: Dict[Direction, Direction] = {
    DIRECTIONS["UP"]: DIRECTIONS["DOWN"],
    DIRECTIONS["DOWN"]: DIRECTIONS["UP"],
    DIRECTIONS["LEFT"]: DIRECTIONS["RIGHT"],
    DIRECTIONS["RIGHT"]: DIRECTIONS["LEFT"],
}

MAZE_LAYOUT: Sequence[str] = (
    "#####################",
    "#........#........#.#",
    "#.###.###.#.###.###.#",
    "#o#.#.....P.....#.#o#",
    "#.###.#.###.#.###.#.#",
    "#.....#..G..#.....#.#",
    "#.###.#.###.#.###.#.#",
    "#o...#.......#...o#.#",
    "###.#.#######.#.###.#",
    "#...#...#.#...#.....#",
    "#.#####.#.#.#####.###",
    "#.................#.#",
    "#####################",
)

PELLET_POINTS = 10
POWER_POINTS = 50
GHOST_POINTS = 200
FRIGHTENED_DURATION = 80  # Frames, roughly 8 seconds with 100ms tick
GHOST_CHASE_PROBABILITY = 0.75


@dataclass
class Entity:
    position: Coordinate
    direction: Direction


@dataclass
class Ghost(Entity):
    home: Coordinate
    frightened_timer: int = 0

    def frightened(self) -> bool:
        return self.frightened_timer > 0


class PacmanGame:
    """Encapsulates the Pac-Man game logic."""

    def __init__(self, screen: "curses._CursesWindow") -> None:
        self.screen = screen
        self.height = len(MAZE_LAYOUT)
        self.width = len(MAZE_LAYOUT[0])
        self.walls: Set[Coordinate] = set()
        self.pellets: Set[Coordinate] = set()
        self.power_pellets: Set[Coordinate] = set()
        self.score = 0
        self.lives = 3
        self.level = 1
        self.pacman = Entity((0, 0), DIRECTIONS["LEFT"])
        self.ghosts: List[Ghost] = []
        self._load_map()
        self.desired_direction: Direction = self.pacman.direction

    def _load_map(self) -> None:
        ghost_positions: List[Coordinate] = []
        for r, row in enumerate(MAZE_LAYOUT):
            for c, char in enumerate(row):
                coordinate = (r, c)
                if char == "#":
                    self.walls.add(coordinate)
                elif char == ".":
                    self.pellets.add(coordinate)
                elif char == "o":
                    self.power_pellets.add(coordinate)
                elif char == "P":
                    self.pacman.position = coordinate
                elif char == "G":
                    ghost_positions.append(coordinate)

        if not ghost_positions:
            raise ValueError("Maze layout must contain at least one ghost start")

        for position in ghost_positions:
            self.ghosts.append(Ghost(position=position, direction=DIRECTIONS["LEFT"], home=position))

    # Utility helpers -----------------------------------------------------
    def wrap_position(self, position: Coordinate) -> Coordinate:
        return (position[0] % self.height, position[1] % self.width)

    def blocked(self, position: Coordinate) -> bool:
        return position in self.walls

    def can_move(self, origin: Coordinate, direction: Direction) -> bool:
        new_position = self.wrap_position((origin[0] + direction[0], origin[1] + direction[1]))
        return not self.blocked(new_position)

    # Game update methods -------------------------------------------------
    def update_pacman(self) -> None:
        # Update direction if possible
        if self.can_move(self.pacman.position, self.desired_direction):
            self.pacman.direction = self.desired_direction

        next_position = self.wrap_position(
            (self.pacman.position[0] + self.pacman.direction[0],
             self.pacman.position[1] + self.pacman.direction[1])
        )

        if not self.blocked(next_position):
            self.pacman.position = next_position

        # Collect pellets and power pellets
        if self.pacman.position in self.pellets:
            self.pellets.remove(self.pacman.position)
            self.score += PELLET_POINTS
        elif self.pacman.position in self.power_pellets:
            self.power_pellets.remove(self.pacman.position)
            self.score += POWER_POINTS
            for ghost in self.ghosts:
                ghost.frightened_timer = FRIGHTENED_DURATION

    def update_ghosts(self) -> None:
        for ghost in self.ghosts:
            if ghost.frightened_timer > 0:
                ghost.frightened_timer -= 1

            direction = self._choose_ghost_direction(ghost)
            ghost.direction = direction

            next_position = self.wrap_position(
                (ghost.position[0] + direction[0], ghost.position[1] + direction[1])
            )
            if not self.blocked(next_position):
                ghost.position = next_position

    def _choose_ghost_direction(self, ghost: Ghost) -> Direction:
        possible = self._available_directions(ghost.position)
        if not possible:
            return ghost.direction

        reverse = REVERSE_DIRECTION.get(ghost.direction)
        if reverse in possible and len(possible) > 1:
            possible.remove(reverse)

        if ghost.frightened():
            return random.choice(possible)

        # When not frightened, bias towards chasing Pac-Man.
        chase = random.random() < GHOST_CHASE_PROBABILITY
        if chase:
            target = self.pacman.position
            best_direction = min(
                possible,
                key=lambda d: manhattan_distance(
                    self.wrap_position((ghost.position[0] + d[0], ghost.position[1] + d[1])),
                    target,
                ),
            )
            return best_direction
        return random.choice(possible)

    def _available_directions(self, position: Coordinate) -> List[Direction]:
        options: List[Direction] = []
        for direction in DIRECTIONS.values():
            next_position = self.wrap_position((position[0] + direction[0], position[1] + direction[1]))
            if not self.blocked(next_position):
                options.append(direction)
        return options

    def handle_collisions(self) -> None:
        for ghost in self.ghosts:
            if ghost.position == self.pacman.position:
                if ghost.frightened():
                    self.score += GHOST_POINTS
                    ghost.position = ghost.home
                    ghost.direction = DIRECTIONS["LEFT"]
                    ghost.frightened_timer = 0
                else:
                    self.lives -= 1
                    self._reset_after_loss()
                    break

    def _reset_after_loss(self) -> None:
        self.pacman.position = next(
            (r, c)
            for r, row in enumerate(MAZE_LAYOUT)
            for c, char in enumerate(row)
            if char == "P"
        )
        self.pacman.direction = DIRECTIONS["LEFT"]
        for ghost in self.ghosts:
            ghost.position = ghost.home
            ghost.direction = DIRECTIONS["LEFT"]
            ghost.frightened_timer = 0
        time.sleep(1.0)

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
        while self.lives > 0 and (self.pellets or self.power_pellets):
            key = self.screen.getch()
            if key in (ord("q"), ord("Q")):
                break
            if key in KEY_TO_DIRECTION:
                self.desired_direction = KEY_TO_DIRECTION[key]

            self.update_pacman()
            self.update_ghosts()
            self.handle_collisions()
            self.draw()

        self._game_over_screen()

    def _game_over_screen(self) -> None:
        self.screen.nodelay(False)
        message = "You Win!" if not (self.pellets or self.power_pellets) else "Game Over"
        try:
            self.screen.addstr(self.height // 2, (self.width // 2) - len(message) // 2, message)
            self.screen.addstr(self.height // 2 + 2, (self.width // 2) - 8, "Press any key")
        except curses.error:
            pass
        self.screen.refresh()
        self.screen.getch()


def manhattan_distance(a: Coordinate, b: Coordinate) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def run(screen: "curses._CursesWindow") -> None:
    game = PacmanGame(screen)
    game.draw()
    game.game_loop()


def main() -> None:
    curses.wrapper(run)


if __name__ == "__main__":
    main()

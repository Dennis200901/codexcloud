"""Shared game data structures and logic for the Pac-Man clone."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

Coordinate = Tuple[int, int]
Direction = Tuple[int, int]

DIRECTIONS: Dict[str, Direction] = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
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


class PacmanLogic:
    """Core game logic shared by different front-ends."""

    def __init__(self) -> None:
        self.height = len(MAZE_LAYOUT)
        self.width = len(MAZE_LAYOUT[0])
        self.score = 0
        self.lives = 3
        self.level = 1
        self.walls: Set[Coordinate] = set()
        self.pellets: Set[Coordinate] = set()
        self.power_pellets: Set[Coordinate] = set()
        self.pacman = Entity((0, 0), DIRECTIONS["LEFT"])
        self.pacman_start: Coordinate = (0, 0)
        self.ghosts: List[Ghost] = []
        self.desired_direction: Direction = self.pacman.direction
        self._load_map()

    def reset(self) -> None:
        """Reset the entire game state back to the initial configuration."""
        self.score = 0
        self.lives = 3
        self.level = 1
        self.walls.clear()
        self.pellets.clear()
        self.power_pellets.clear()
        self.ghosts.clear()
        self.pacman = Entity((0, 0), DIRECTIONS["LEFT"])
        self.pacman_start = (0, 0)
        self.desired_direction = self.pacman.direction
        self._load_map()

    # Map management -----------------------------------------------------
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
                    self.pacman_start = coordinate
                elif char == "G":
                    ghost_positions.append(coordinate)

        if not ghost_positions:
            raise ValueError("Maze layout must contain at least one ghost start")

        self.ghosts = [
            Ghost(position=position, direction=DIRECTIONS["LEFT"], home=position)
            for position in ghost_positions
        ]

    # Utility helpers ----------------------------------------------------
    def wrap_position(self, position: Coordinate) -> Coordinate:
        return (position[0] % self.height, position[1] % self.width)

    def blocked(self, position: Coordinate) -> bool:
        return position in self.walls

    def can_move(self, origin: Coordinate, direction: Direction) -> bool:
        new_position = self.wrap_position((origin[0] + direction[0], origin[1] + direction[1]))
        return not self.blocked(new_position)

    def set_desired_direction(self, direction: Direction) -> None:
        self.desired_direction = direction

    # Game update methods ------------------------------------------------
    def update_pacman(self) -> None:
        if self.can_move(self.pacman.position, self.desired_direction):
            self.pacman.direction = self.desired_direction

        next_position = self.wrap_position(
            (self.pacman.position[0] + self.pacman.direction[0],
             self.pacman.position[1] + self.pacman.direction[1])
        )

        if not self.blocked(next_position):
            self.pacman.position = next_position

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

    def handle_collisions(self) -> Optional[str]:
        for ghost in self.ghosts:
            if ghost.position == self.pacman.position:
                if ghost.frightened():
                    self.score += GHOST_POINTS
                    ghost.position = ghost.home
                    ghost.direction = DIRECTIONS["LEFT"]
                    ghost.frightened_timer = 0
                    return "ghost_eaten"
                self.lives -= 1
                self._reset_after_loss()
                return "life_lost"
        return None

    def _reset_after_loss(self) -> None:
        self.pacman.position = self.pacman_start
        self.pacman.direction = DIRECTIONS["LEFT"]
        self.desired_direction = self.pacman.direction
        for ghost in self.ghosts:
            ghost.position = ghost.home
            ghost.direction = DIRECTIONS["LEFT"]
            ghost.frightened_timer = 0

    # Game state helpers -------------------------------------------------
    def tick(self) -> Optional[str]:
        if not self.is_alive() or self.is_level_cleared():
            return None

        self.update_pacman()
        self.update_ghosts()
        return self.handle_collisions()

    def is_alive(self) -> bool:
        return self.lives > 0

    def is_level_cleared(self) -> bool:
        return not self.pellets and not self.power_pellets

    def remaining_pellets(self) -> int:
        return len(self.pellets) + len(self.power_pellets)


def manhattan_distance(a: Coordinate, b: Coordinate) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

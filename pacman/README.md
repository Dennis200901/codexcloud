# Pacman

A lightweight terminal Pac-Man clone implemented with Python's `curses` module. The
implementation keeps the original maze feel while remaining playable from a
terminal window.

## Requirements

* Python 3.8 or newer
* A terminal that supports ANSI escape codes and cursor movement

## Running the game

```bash
python pacman/pacman_game.py
```

### Controls

* Arrow keys or `W`, `A`, `S`, `D` — move Pac-Man
* `q` — quit the game

## Gameplay notes

* Eat all pellets to win the level.
* Power pellets make ghosts vulnerable for a short period; colliding with a
  frightened ghost sends it back to the ghost house and awards bonus points.
* Colliding with a non-frightened ghost costs one life. Lose all lives and the
  game is over.

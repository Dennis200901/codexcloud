# Pacman

A lightweight Pac-Man clone implemented in Python. Two front-ends are
available:

* A curses-based terminal version for quick play from any terminal window.
* A fully graphical pygame version inspired by the classic arcade look.

## Requirements

* Python 3.8 or newer
* A terminal that supports ANSI escape codes and cursor movement (for the
  curses edition)
* [`pygame`](https://www.pygame.org/) for the graphical edition (`pip install pygame`)

## Running the games

### Terminal edition

Run the terminal edition from the repository root so Python can resolve the
package:

```bash
python -m pacman.pacman_game
```

Controls: Arrow keys or `W`, `A`, `S`, `D` to move, `q` to quit.

### Graphical edition

```bash
python -m pacman.pacman_gui
```

Controls: Arrow keys or `W`, `A`, `S`, `D` to move, `Esc` to quit, `Enter`
to restart after a game over.

## Gameplay notes

* Eat all pellets to win the level.
* Power pellets make ghosts vulnerable for a short period; colliding with a
  frightened ghost sends it back to the ghost house and awards bonus points.
* Colliding with a non-frightened ghost costs one life. Lose all lives and the
  game is over.

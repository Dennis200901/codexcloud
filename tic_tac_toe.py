"""Simple two-player Tic Tac Toe game played in the terminal.

The game presents a numbered 3x3 board and alternates between
players ``X`` and ``O`` until someone wins or the board fills up.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GameState:
    """Represents the current state of the Tic Tac Toe board."""

    board: List[Optional[str]]
    current_player: str

    def __post_init__(self) -> None:
        if len(self.board) != 9:
            raise ValueError("Board must contain exactly 9 cells")
        if self.current_player not in {"X", "O"}:
            raise ValueError("Current player must be 'X' or 'O'")


WINNING_COMBINATIONS = [
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
]


def format_board(board: List[Optional[str]]) -> str:
    """Return a string representation of the board."""

    def cell_value(index: int) -> str:
        return board[index] if board[index] is not None else str(index + 1)

    rows = [
        " | ".join(cell_value(col + row * 3) for col in range(3))
        for row in range(3)
    ]
    return "\n---------\n".join(rows)


def check_winner(board: List[Optional[str]]) -> Optional[str]:
    """Return the winning player's symbol if there is a winner."""

    for a, b, c in WINNING_COMBINATIONS:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


def is_draw(board: List[Optional[str]]) -> bool:
    """Return ``True`` if all cells are filled and there is no winner."""

    return all(cell is not None for cell in board)


def switch_player(player: str) -> str:
    """Return the symbol for the next player."""

    return "O" if player == "X" else "X"


def prompt_move(state: GameState) -> int:
    """Prompt the current player for a move and return the chosen index."""

    while True:
        try:
            raw_input = input(
                f"Player {state.current_player}, enter a position (1-9): "
            )
            choice = int(raw_input)
            if not 1 <= choice <= 9:
                raise ValueError
        except ValueError:
            print("Invalid input. Please enter a number between 1 and 9.")
            continue

        index = choice - 1
        if state.board[index] is not None:
            print("That position is already taken. Try another one.")
            continue

        return index


def play_game() -> None:
    """Play a full game of Tic Tac Toe."""

    state = GameState(board=[None] * 9, current_player="X")

    while True:
        print("\n" + format_board(state.board))
        move_index = prompt_move(state)
        state.board[move_index] = state.current_player

        winner = check_winner(state.board)
        if winner:
            print("\n" + format_board(state.board))
            print(f"Player {winner} wins! Congratulations!")
            break

        if is_draw(state.board):
            print("\n" + format_board(state.board))
            print("It's a draw!")
            break

        state.current_player = switch_player(state.current_player)


if __name__ == "__main__":
    play_game()

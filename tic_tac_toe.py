"""Tkinter-based games including Tic Tac Toe and a simple Tetris clone."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import tkinter as tk
from tkinter import messagebox


TETROMINOS: Dict[str, List[List[Tuple[int, int]]]] = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(0, 1), (1, 1), (2, 1), (2, 0)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (0, 2), (1, 1), (2, 1)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "S": [
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
    ],
}


TETROMINO_COLORS: Dict[str, str] = {
    "I": "#7FFFD4",
    "J": "#1E90FF",
    "L": "#FF8C00",
    "O": "#FFD700",
    "S": "#32CD32",
    "T": "#BA55D3",
    "Z": "#DC143C",
}


@dataclass
class GameState:
    """Represents the current state of the Tic Tac Toe board."""

    board: List[Optional[str]]
    current_player: str
    size: int

    def __post_init__(self) -> None:
        expected_length = self.size * self.size
        if len(self.board) != expected_length:
            raise ValueError(
                f"Board must contain exactly {expected_length} cells for size {self.size}"
            )
        if self.current_player not in {"X", "O"}:
            raise ValueError("Current player must be 'X' or 'O'")

    def available_moves(self) -> List[int]:
        """Return all indices that are not yet filled."""

        return [index for index, cell in enumerate(self.board) if cell is None]


def winning_lines(size: int) -> List[Sequence[int]]:
    """Generate all possible winning line combinations for a square board."""

    lines: List[Sequence[int]] = []

    # Rows and columns
    for row in range(size):
        start = row * size
        lines.append(tuple(start + col for col in range(size)))
    for col in range(size):
        lines.append(tuple(col + row * size for row in range(size)))

    # Diagonals
    lines.append(tuple(i * (size + 1) for i in range(size)))
    lines.append(tuple((i + 1) * (size - 1) for i in range(size)))

    return lines


def check_winner(
    board: Sequence[Optional[str]],
    size: int,
    precomputed_lines: Optional[Sequence[Sequence[int]]] = None,
) -> Optional[str]:
    """Return the winning player's symbol if a line is completed."""

    lines = precomputed_lines or winning_lines(size)
    for line in lines:
        first = board[line[0]]
        if first and all(board[index] == first for index in line):
            return first
    return None


def is_draw(board: Sequence[Optional[str]]) -> bool:
    """Return ``True`` if all cells are filled."""

    return all(cell is not None for cell in board)


def switch_player(player: str) -> str:
    """Return the symbol for the next player."""

    return "O" if player == "X" else "X"


def _winning_move(
    board: Sequence[Optional[str]],
    size: int,
    lines: Sequence[Sequence[int]],
    player: str,
    move: int,
) -> bool:
    """Check whether placing ``player`` at ``move`` results in a win."""

    temp_board = list(board)
    temp_board[move] = player
    return check_winner(temp_board, size, lines) == player


def choose_ai_move(
    state: GameState,
    difficulty: str,
    human_symbol: str,
    lines: Sequence[Sequence[int]],
) -> int:
    """Select a move for the computer according to the chosen difficulty."""

    available = state.available_moves()
    if not available:
        raise ValueError("No moves available for the AI")

    ai_symbol = state.current_player

    if difficulty.lower() == "leicht":
        return random.choice(available)

    # Medium and hard share the immediate win check.
    for move in available:
        if _winning_move(state.board, state.size, lines, ai_symbol, move):
            return move

    if difficulty.lower() == "mittel":
        return random.choice(available)

    # Hard difficulty attempts to block the opponent and prefers strong positions.
    for move in available:
        if _winning_move(state.board, state.size, lines, human_symbol, move):
            return move

    # Prefer the center on odd-sized boards.
    if state.size % 2 == 1:
        center_index = (state.size * state.size) // 2
        if center_index in available:
            return center_index

    # Prefer corners if available.
    corners = [
        0,
        state.size - 1,
        state.size * (state.size - 1),
        state.size * state.size - 1,
    ]
    random.shuffle(corners)
    for corner in corners:
        if corner in available:
            return corner

    return random.choice(available)


class TicTacToeApp:
    """Tkinter application that supports multiple Tic Tac Toe modes."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Tic Tac Toe")

        self.current_frame: Optional[tk.Frame] = None
        self.status_var = tk.StringVar()
        self.status_var.set("Willkommen zu Tic Tac Toe!")

        self.trophies: Dict[str, int] = {
            "Single Player": 0,
            "Player X": 0,
            "Player O": 0,
        }

        self.game_state: Optional[GameState] = None
        self.game_mode: str = ""
        self.board_buttons: List[tk.Button] = []
        self.game_over = False
        self.difficulty: Optional[str] = None
        self.winning_lines_cache: Sequence[Sequence[int]] = []
        self.human_symbol = "X"
        self.computer_symbol = "O"
        self.board_size = 3
        self.play_again_button: Optional[tk.Button] = None

        self.show_main_menu()

    def _switch_frame(self, frame: tk.Frame) -> None:
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = frame
        self.current_frame.pack(fill="both", expand=True)

    def show_main_menu(self) -> None:
        """Display the main menu with the available modes."""

        frame = tk.Frame(self.root, padx=20, pady=20)

        tk.Label(frame, text="Tic Tac Toe", font=("Helvetica", 24, "bold")).pack(pady=10)

        tk.Button(
            frame,
            text="Single Player",
            width=20,
            command=self.show_single_player_menu,
        ).pack(pady=5)

        tk.Button(
            frame,
            text="Multiplayer",
            width=20,
            command=self.show_multiplayer_menu,
        ).pack(pady=5)

        tk.Button(
            frame,
            text="Trophäenhalle",
            width=20,
            command=self.show_trophy_hall,
        ).pack(pady=5)

        tk.Button(
            frame,
            text="Beenden",
            width=20,
            command=self.root.destroy,
        ).pack(pady=5)

        self._switch_frame(frame)

    def show_single_player_menu(self) -> None:
        """Configure single-player settings."""

        frame = tk.Frame(self.root, padx=20, pady=20)

        tk.Label(frame, text="Single Player", font=("Helvetica", 20, "bold")).pack(pady=(0, 10))

        board_var = tk.IntVar(value=3)
        tk.Label(frame, text="Spielfeldgröße").pack()
        for size in (3, 5):
            tk.Radiobutton(
                frame,
                text=f"{size} x {size}",
                variable=board_var,
                value=size,
            ).pack(anchor="w")

        difficulty_var = tk.StringVar(value="leicht")
        tk.Label(frame, text="Schwierigkeit").pack(pady=(10, 0))
        for difficulty in ("leicht", "mittel", "schwer"):
            tk.Radiobutton(
                frame,
                text=difficulty.title(),
                variable=difficulty_var,
                value=difficulty,
            ).pack(anchor="w")

        tk.Button(
            frame,
            text="Spiel starten",
            command=lambda: self.start_game(
                mode="single",
                board_size=board_var.get(),
                difficulty=difficulty_var.get(),
            ),
        ).pack(pady=(15, 5))

        tk.Button(frame, text="Zurück", command=self.show_main_menu).pack()

        self._switch_frame(frame)

    def show_multiplayer_menu(self) -> None:
        """Configure multiplayer settings."""

        frame = tk.Frame(self.root, padx=20, pady=20)

        tk.Label(frame, text="Multiplayer", font=("Helvetica", 20, "bold")).pack(pady=(0, 10))

        board_var = tk.IntVar(value=3)
        tk.Label(frame, text="Spielfeldgröße").pack()
        for size in (3, 5):
            tk.Radiobutton(
                frame,
                text=f"{size} x {size}",
                variable=board_var,
                value=size,
            ).pack(anchor="w")

        tk.Button(
            frame,
            text="Spiel starten",
            command=lambda: self.start_game(
                mode="multi",
                board_size=board_var.get(),
                difficulty=None,
            ),
        ).pack(pady=(15, 5))

        tk.Button(frame, text="Zurück", command=self.show_main_menu).pack()

        self._switch_frame(frame)

    def show_trophy_hall(self) -> None:
        """Display the trophy counts for each mode/player."""

        frame = tk.Frame(self.root, padx=20, pady=20)

        tk.Label(frame, text="Trophäenhalle", font=("Helvetica", 20, "bold")).pack(pady=(0, 10))

        tk.Label(
            frame,
            text=f"Single Player: {self.trophies['Single Player']} Trophäen",
            font=("Helvetica", 14),
        ).pack(anchor="w", pady=2)
        tk.Label(
            frame,
            text=f"Player X: {self.trophies['Player X']} Trophäen",
            font=("Helvetica", 14),
        ).pack(anchor="w", pady=2)
        tk.Label(
            frame,
            text=f"Player O: {self.trophies['Player O']} Trophäen",
            font=("Helvetica", 14),
        ).pack(anchor="w", pady=2)

        tk.Button(frame, text="Zurück", command=self.show_main_menu).pack(pady=(15, 0))

        self._switch_frame(frame)

    def start_game(self, mode: str, board_size: int, difficulty: Optional[str]) -> None:
        """Initialize and display the game board."""

        self.game_mode = mode
        self.board_size = board_size
        self.difficulty = difficulty
        self.game_state = GameState(
            board=[None] * (board_size * board_size),
            current_player="X",
            size=board_size,
        )
        self.winning_lines_cache = winning_lines(board_size)
        self.game_over = False
        self.board_buttons = []
        self.status_var.set("Spieler X ist am Zug")

        frame = tk.Frame(self.root, padx=20, pady=20)

        title = "Single Player" if mode == "single" else "Multiplayer"
        tk.Label(frame, text=title, font=("Helvetica", 20, "bold")).pack(pady=(0, 10))

        board_frame = tk.Frame(frame)
        board_frame.pack()

        button_font = ("Helvetica", 20 if board_size == 3 else 16)
        button_size = 3 if board_size == 3 else 2

        for index in range(board_size * board_size):
            button = tk.Button(
                board_frame,
                text=" ",
                font=button_font,
                width=button_size,
                height=button_size,
                command=lambda idx=index: self.handle_player_move(idx),
            )
            row, col = divmod(index, board_size)
            button.grid(row=row, column=col, padx=5, pady=5)
            self.board_buttons.append(button)

        status_label = tk.Label(frame, textvariable=self.status_var, font=("Helvetica", 14))
        status_label.pack(pady=(10, 0))

        controls = tk.Frame(frame)
        controls.pack(pady=10)

        tk.Button(controls, text="Zurück zum Menü", command=self.show_main_menu).pack(
            side=tk.LEFT, padx=5
        )

        self.play_again_button = tk.Button(
            controls,
            text="Nochmal spielen",
            state=tk.DISABLED,
            command=lambda: self.start_game(mode, board_size, difficulty),
        )
        self.play_again_button.pack(side=tk.LEFT, padx=5)

        self._switch_frame(frame)

        if self.game_mode == "single" and self.game_state.current_player != self.human_symbol:
            self._queue_ai_move()

    def handle_player_move(self, index: int) -> None:
        """Process a move triggered by a button press."""

        if self.game_over or self.game_state is None:
            return

        if self.game_state.board[index] is not None:
            return

        if self.game_mode == "single" and self.game_state.current_player != self.human_symbol:
            return

        self._apply_move(index)

        if (
            self.game_mode == "single"
            and not self.game_over
            and self.game_state.current_player == self.computer_symbol
        ):
            self._queue_ai_move()

    def _queue_ai_move(self) -> None:
        if self.game_state is None:
            return

        self.status_var.set("Computer ist am Zug...")
        self.root.after(400, self._perform_ai_move)

    def _perform_ai_move(self) -> None:
        if self.game_over or self.game_state is None:
            return

        if self.game_state.current_player != self.computer_symbol:
            return

        move = choose_ai_move(
            state=self.game_state,
            difficulty=self.difficulty or "leicht",
            human_symbol=self.human_symbol,
            lines=self.winning_lines_cache,
        )
        self._apply_move(move)

    def _apply_move(self, index: int) -> None:
        if self.game_state is None:
            return

        player = self.game_state.current_player
        self.game_state.board[index] = player
        self.board_buttons[index].config(text=player, state=tk.DISABLED)

        winner = check_winner(
            self.game_state.board,
            self.game_state.size,
            self.winning_lines_cache,
        )
        if winner:
            self._handle_game_end(winner)
            return

        if is_draw(self.game_state.board):
            self._handle_game_end(None)
            return

        self.game_state.current_player = switch_player(player)
        self.status_var.set(f"Spieler {self.game_state.current_player} ist am Zug")

    def _handle_game_end(self, winner: Optional[str]) -> None:
        if self.game_state is None:
            return

        self.game_over = True
        if self.play_again_button is not None:
            self.play_again_button.config(state=tk.NORMAL)

        for button in self.board_buttons:
            button.config(state=tk.DISABLED)

        if winner:
            self.status_var.set(f"Spieler {winner} gewinnt!")
            self._award_trophies(winner)
            messagebox.showinfo("Spielende", f"Spieler {winner} gewinnt und erhält 10 Trophäen!")
        else:
            self.status_var.set("Unentschieden!")
            messagebox.showinfo("Spielende", "Unentschieden!")

    def _award_trophies(self, winner: str) -> None:
        if self.game_mode == "single" and winner == self.human_symbol:
            self.trophies["Single Player"] += 10
        elif self.game_mode == "multi":
            key = "Player X" if winner == "X" else "Player O"
            self.trophies[key] += 10

    def run(self) -> None:
        """Start the Tkinter main loop."""

        self.root.mainloop()


def show_start_screen() -> Optional[str]:
    """Display a start screen that lets the user choose a game."""

    selection: Dict[str, Optional[str]] = {"choice": None}

    def choose(game: Optional[str]) -> None:
        selection["choice"] = game
        root.destroy()

    root = tk.Tk()
    root.title("Spielauswahl")

    frame = tk.Frame(root, padx=30, pady=30)
    frame.pack()

    tk.Label(frame, text="Willkommen!", font=("Helvetica", 22, "bold")).pack(pady=(0, 10))
    tk.Label(frame, text="Bitte wähle ein Spiel", font=("Helvetica", 14)).pack(pady=(0, 20))

    tk.Button(
        frame,
        text="Tic Tac Toe",
        width=20,
        command=lambda: choose("tic_tac_toe"),
    ).pack(pady=5)

    tk.Button(
        frame,
        text="Tetris",
        width=20,
        command=lambda: choose("tetris"),
    ).pack(pady=5)

    tk.Button(
        frame,
        text="Beenden",
        width=20,
        command=lambda: choose(None),
    ).pack(pady=(15, 0))

    root.mainloop()
    return selection["choice"]


def play_tictactoe() -> None:
    """Launch only the Tic Tac Toe game."""

    TicTacToeApp().run()


def play_tetris() -> None:
    """Launch only the Tetris game."""

    TetrisApp().run()


def play_gui() -> None:
    """Launch the start screen and run the selected game."""

    choice = show_start_screen()
    if choice == "tic_tac_toe":
        play_tictactoe()
    elif choice == "tetris":
        play_tetris()


class TetrisApp:
    """Very small Tkinter Tetris implementation."""

    width = 10
    height = 20
    cell_size = 30
    initial_speed_ms = 500

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Tetris")

        self.after_id: Optional[str] = None
        self.board: List[List[Optional[str]]] = []
        self.current_piece: Optional[Dict[str, object]] = None
        self.score = 0
        self.speed = self.initial_speed_ms
        self.game_over = False

        self.frame = tk.Frame(self.root, padx=15, pady=15)
        self.frame.pack()

        tk.Label(self.frame, text="Tetris", font=("Helvetica", 20, "bold")).pack(pady=(0, 10))

        self.score_var = tk.StringVar(value="Punkte: 0")
        tk.Label(self.frame, textvariable=self.score_var, font=("Helvetica", 14)).pack()

        self.canvas = tk.Canvas(
            self.frame,
            width=self.width * self.cell_size,
            height=self.height * self.cell_size,
            bg="#111111",
            highlightthickness=0,
        )
        self.canvas.pack(pady=10)
        self.canvas.focus_set()

        tk.Label(
            self.frame,
            text="Steuerung: Pfeiltasten zum Bewegen/Rotieren, Leertaste = Fallen lassen",
            font=("Helvetica", 10),
        ).pack(pady=(0, 10))

        controls = tk.Frame(self.frame)
        controls.pack(pady=(0, 5))
        tk.Button(controls, text="Neues Spiel", command=self.reset_game).pack(side=tk.LEFT, padx=5)
        tk.Button(controls, text="Beenden", command=self.root.destroy).pack(side=tk.LEFT, padx=5)

        self.root.bind("<Left>", self.move_left)
        self.root.bind("<Right>", self.move_right)
        self.root.bind("<Down>", self.soft_drop)
        self.root.bind("<Up>", self.rotate_piece)
        self.root.bind("<space>", self.hard_drop)

        self.reset_game()

    def reset_game(self) -> None:
        """Start or restart the game."""

        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        self.board = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.score = 0
        self.speed = self.initial_speed_ms
        self.game_over = False
        self.current_piece = None
        self.score_var.set("Punkte: 0")

        self._spawn_piece()
        self.draw()
        self._schedule_tick()

    def move_left(self, _event: object = None) -> None:
        if self._move(-1, 0):
            self.draw()

    def move_right(self, _event: object = None) -> None:
        if self._move(1, 0):
            self.draw()

    def soft_drop(self, _event: object = None) -> None:
        if self.game_over:
            return
        if not self._move(0, 1):
            self._lock_piece()
        self.draw()

    def hard_drop(self, _event: object = None) -> None:
        if self.game_over:
            return
        while self._move(0, 1):
            pass
        self._lock_piece()
        self.draw()

    def rotate_piece(self, _event: object = None) -> None:
        if self.game_over or self.current_piece is None:
            return
        shape = self.current_piece["shape"]
        rotations = len(TETROMINOS[shape])
        new_rotation = (int(self.current_piece["rotation"]) + 1) % rotations
        if not self._collides(int(self.current_piece["x"]), int(self.current_piece["y"]), new_rotation):
            self.current_piece["rotation"] = new_rotation
            self.draw()

    def _schedule_tick(self) -> None:
        if self.game_over:
            return
        self.after_id = self.root.after(self.speed, self._tick)

    def _tick(self) -> None:
        if self.game_over:
            return
        if not self._move(0, 1):
            self._lock_piece()
        self.draw()
        self._schedule_tick()

    def _move(self, dx: int, dy: int) -> bool:
        if self.current_piece is None:
            return False
        new_x = int(self.current_piece["x"]) + dx
        new_y = int(self.current_piece["y"]) + dy
        rotation = int(self.current_piece["rotation"])
        if self._collides(new_x, new_y, rotation):
            return False
        self.current_piece["x"] = new_x
        self.current_piece["y"] = new_y
        return True

    def _collides(self, x: int, y: int, rotation: int) -> bool:
        if self.current_piece is None:
            return True
        shape = str(self.current_piece["shape"])
        for dx, dy in TETROMINOS[shape][rotation]:
            board_x = x + dx
            board_y = y + dy
            if board_x < 0 or board_x >= self.width or board_y < 0 or board_y >= self.height:
                return True
            if self.board[board_y][board_x] is not None:
                return True
        return False

    def _spawn_piece(self) -> None:
        shape = random.choice(list(TETROMINOS.keys()))
        self.current_piece = {
            "shape": shape,
            "rotation": 0,
            "x": self.width // 2 - 2,
            "y": 0,
        }
        if self._collides(int(self.current_piece["x"]), int(self.current_piece["y"]), 0):
            self.game_over = True
            self.current_piece = None
            self._end_game()

    def _lock_piece(self) -> None:
        if self.current_piece is None:
            return
        shape = str(self.current_piece["shape"])
        rotation = int(self.current_piece["rotation"])
        base_x = int(self.current_piece["x"])
        base_y = int(self.current_piece["y"])
        color = TETROMINO_COLORS[shape]

        for dx, dy in TETROMINOS[shape][rotation]:
            x = base_x + dx
            y = base_y + dy
            if 0 <= y < self.height:
                self.board[y][x] = color

        cleared = self._clear_lines()
        if cleared:
            self.score += cleared * 100
            self.score_var.set(f"Punkte: {self.score}")
            self.speed = max(120, int(self.speed * 0.9))

        self._spawn_piece()

    def _clear_lines(self) -> int:
        cleared = 0
        new_board: List[List[Optional[str]]] = []
        for row in self.board:
            if all(cell is not None for cell in row):
                cleared += 1
            else:
                new_board.append(row)

        while len(new_board) < self.height:
            new_board.insert(0, [None for _ in range(self.width)])

        self.board = new_board
        return cleared

    def _end_game(self) -> None:
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        messagebox.showinfo("Tetris", f"Spiel beendet! Punkte: {self.score}")

    def draw(self) -> None:
        self.canvas.delete("all")
        for y, row in enumerate(self.board):
            for x, color in enumerate(row):
                if color:
                    self._draw_cell(x, y, color)

        if self.current_piece is not None:
            shape = str(self.current_piece["shape"])
            rotation = int(self.current_piece["rotation"])
            base_x = int(self.current_piece["x"])
            base_y = int(self.current_piece["y"])
            color = TETROMINO_COLORS[shape]
            for dx, dy in TETROMINOS[shape][rotation]:
                self._draw_cell(base_x + dx, base_y + dy, color)

        # draw grid lines for guidance
        for x in range(self.width + 1):
            pixel = x * self.cell_size
            self.canvas.create_line(
                pixel,
                0,
                pixel,
                self.height * self.cell_size,
                fill="#222222",
            )
        for y in range(self.height + 1):
            pixel = y * self.cell_size
            self.canvas.create_line(
                0,
                pixel,
                self.width * self.cell_size,
                pixel,
                fill="#222222",
            )

    def _draw_cell(self, x: int, y: int, color: str) -> None:
        size = self.cell_size
        x1 = x * size
        y1 = y * size
        x2 = x1 + size
        y2 = y1 + size
        self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=color,
            outline="#000000",
        )

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    play_gui()

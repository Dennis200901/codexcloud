"""Tkinter-based Tic Tac Toe application supporting multiple modes."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import tkinter as tk
from tkinter import messagebox


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

    def __init__(self, on_exit: Optional[Callable[[], None]] = None) -> None:
        self.on_exit = on_exit
        self.root = tk.Tk()
        self.root.title("Tic Tac Toe")
        self.root.protocol("WM_DELETE_WINDOW", self._return_to_launcher)

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
            text="Zurück zur Auswahl",
            width=20,
            command=self._return_to_launcher,
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

    def _return_to_launcher(self) -> None:
        self.root.destroy()
        if self.on_exit is not None:
            self.on_exit()


TETROMINOES: Tuple[Tuple[str, Tuple[Tuple[int, int], ...], str], ...] = (
    ("I", ((-1, 0), (0, 0), (1, 0), (2, 0)), "#5BC0EB"),
    ("J", ((-1, 0), (0, 0), (1, 0), (-1, 1)), "#F25F5C"),
    ("L", ((-1, 0), (0, 0), (1, 0), (1, 1)), "#FFE066"),
    ("O", ((0, 0), (1, 0), (0, 1), (1, 1)), "#247BA0"),
    ("S", ((-1, 1), (0, 1), (0, 0), (1, 0)), "#70C1B3"),
    ("T", ((-1, 0), (0, 0), (1, 0), (0, 1)), "#50514F"),
    ("Z", ((-1, 0), (0, 0), (0, 1), (1, 1)), "#FF8066"),
)


class TetrisApp:
    """Simple Tetris implementation using Tkinter."""

    def __init__(self, on_exit: Optional[Callable[[], None]] = None) -> None:
        self.on_exit = on_exit
        self.root = tk.Tk()
        self.root.title("Tetris")
        self.root.protocol("WM_DELETE_WINDOW", self._return_to_launcher)

        self.width = 10
        self.height = 20
        self.cell_size = 28

        self.score = 0
        self.lines_cleared = 0
        self.level = 1

        self.board: List[List[Optional[str]]] = []
        self.current_shape: List[Tuple[int, int]] = []
        self.current_color = ""
        self.current_piece_name = ""
        self.piece_x = 0
        self.piece_y = 0
        self.game_running = False
        self.after_id: Optional[str] = None

        info_frame = tk.Frame(self.root, padx=10, pady=10)
        info_frame.pack()

        self.score_var = tk.StringVar()
        self.level_var = tk.StringVar()
        self.lines_var = tk.StringVar()

        tk.Label(info_frame, textvariable=self.score_var, font=("Helvetica", 12)).grid(
            row=0, column=0, padx=5
        )
        tk.Label(info_frame, textvariable=self.level_var, font=("Helvetica", 12)).grid(
            row=0, column=1, padx=5
        )
        tk.Label(info_frame, textvariable=self.lines_var, font=("Helvetica", 12)).grid(
            row=0, column=2, padx=5
        )

        self.canvas = tk.Canvas(
            self.root,
            width=self.width * self.cell_size,
            height=self.height * self.cell_size,
            bg="black",
            highlightthickness=0,
        )
        self.canvas.pack(padx=10, pady=10)

        tk.Label(
            self.root,
            text="Steuerung: Pfeiltasten bewegen, Pfeil hoch dreht, Leertaste Hard Drop",
            font=("Helvetica", 10),
        ).pack(pady=(0, 10))

        controls = tk.Frame(self.root, pady=5)
        controls.pack()

        tk.Button(controls, text="Neustart", command=self.start_game).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(controls, text="Zurück zur Auswahl", command=self._return_to_launcher).pack(
            side=tk.LEFT, padx=5
        )

        self.root.bind("<Left>", self._handle_left)
        self.root.bind("<Right>", self._handle_right)
        self.root.bind("<Down>", self._handle_down)
        self.root.bind("<Up>", self._handle_rotate)
        self.root.bind("<space>", self._handle_drop)

        self.start_game()

    def run(self) -> None:
        self.root.mainloop()

    def start_game(self) -> None:
        self._cancel_drop()
        self.board = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_running = True
        self.current_shape = []
        self.current_color = ""
        self.current_piece_name = ""
        self._update_info()
        if not self._spawn_piece():
            self._handle_game_over()
            return
        self._draw()
        self._schedule_drop()

    def _handle_left(self, event: tk.Event) -> None:  # pragma: no cover - UI callback
        if self.game_running:
            self._move_piece(-1, 0)

    def _handle_right(self, event: tk.Event) -> None:  # pragma: no cover - UI callback
        if self.game_running:
            self._move_piece(1, 0)

    def _handle_down(self, event: tk.Event) -> None:  # pragma: no cover - UI callback
        if self.game_running:
            if self._move_piece(0, 1):
                self.score += 1
                self._update_info()

    def _handle_rotate(self, event: tk.Event) -> None:  # pragma: no cover - UI callback
        if self.game_running:
            self._rotate_piece()

    def _handle_drop(self, event: tk.Event) -> None:  # pragma: no cover - UI callback
        if not self.game_running:
            return
        moved = False
        while self._move_piece(0, 1):
            moved = True
            self.score += 2
        if moved:
            self._update_info()
        self.step()

    def step(self) -> None:
        if not self.game_running:
            return
        if not self._move_piece(0, 1):
            if not self._lock_piece():
                self._handle_game_over()
                return
            cleared = self._clear_lines()
            if cleared:
                self.score += (cleared ** 2) * 100
                self.lines_cleared += cleared
                self.level = 1 + self.lines_cleared // 10
                self._update_info()
            if not self._spawn_piece():
                self._handle_game_over()
                return
        self._schedule_drop()

    def _schedule_drop(self) -> None:
        self._cancel_drop()
        if not self.game_running:
            return
        interval = max(120, 700 - (self.level - 1) * 60)
        self.after_id = self.root.after(interval, self.step)

    def _cancel_drop(self) -> None:
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def _spawn_piece(self) -> bool:
        name, offsets, color = random.choice(TETROMINOES)
        self.current_piece_name = name
        self.current_shape = [tuple(offset) for offset in offsets]
        self.current_color = color
        self.piece_x = self.width // 2
        self.piece_y = 0
        if not self._piece_fits(self.current_shape, self.piece_x, self.piece_y):
            return False
        self._draw()
        return True

    def _move_piece(self, dx: int, dy: int) -> bool:
        if not self.current_shape:
            return False
        new_x = self.piece_x + dx
        new_y = self.piece_y + dy
        if self._piece_fits(self.current_shape, new_x, new_y):
            self.piece_x = new_x
            self.piece_y = new_y
            self._draw()
            return True
        return False

    def _rotate_piece(self) -> None:
        if not self.current_shape:
            return
        if self.current_piece_name == "O":
            return
        rotated = [(-y, x) for x, y in self.current_shape]
        if self._piece_fits(rotated, self.piece_x, self.piece_y):
            self.current_shape = rotated
            self._draw()
            return
        for dx in (-1, 1, -2, 2):
            if self._piece_fits(rotated, self.piece_x + dx, self.piece_y):
                self.piece_x += dx
                self.current_shape = rotated
                self._draw()
                return

    def _piece_fits(
        self, shape: Sequence[Tuple[int, int]], offset_x: int, offset_y: int
    ) -> bool:
        for x_offset, y_offset in shape:
            x = offset_x + x_offset
            y = offset_y + y_offset
            if x < 0 or x >= self.width:
                return False
            if y >= self.height:
                return False
            if y >= 0 and self.board[y][x] is not None:
                return False
        return True

    def _current_blocks(self) -> List[Tuple[int, int]]:
        return [
            (self.piece_x + x_offset, self.piece_y + y_offset)
            for x_offset, y_offset in self.current_shape
        ]

    def _lock_piece(self) -> bool:
        top_out = False
        for x, y in self._current_blocks():
            if y < 0:
                top_out = True
                continue
            self.board[y][x] = self.current_color
        self.current_shape = []
        return not top_out

    def _clear_lines(self) -> int:
        new_board: List[List[Optional[str]]] = []
        cleared = 0
        for row in self.board:
            if all(cell is not None for cell in row):
                cleared += 1
            else:
                new_board.append(row)
        while len(new_board) < self.height:
            new_board.insert(0, [None for _ in range(self.width)])
        if cleared:
            self.board = new_board
            self._draw()
        return cleared

    def _draw(self) -> None:
        self.canvas.delete("all")
        for y, row in enumerate(self.board):
            for x, color in enumerate(row):
                if color:
                    self._draw_cell(x, y, color)
        for x, y in self._current_blocks():
            if y >= 0:
                self._draw_cell(x, y, self.current_color)
        self._draw_grid()

    def _draw_cell(self, x: int, y: int, color: str) -> None:
        size = self.cell_size
        x1 = x * size
        y1 = y * size
        x2 = x1 + size
        y2 = y1 + size
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#1a1a1a")

    def _draw_grid(self) -> None:
        size = self.cell_size
        for x in range(self.width + 1):
            self.canvas.create_line(x * size, 0, x * size, self.height * size, fill="#222")
        for y in range(self.height + 1):
            self.canvas.create_line(0, y * size, self.width * size, y * size, fill="#222")

    def _update_info(self) -> None:
        self.score_var.set(f"Punkte: {self.score}")
        self.level_var.set(f"Level: {self.level}")
        self.lines_var.set(f"Linien: {self.lines_cleared}")

    def _handle_game_over(self) -> None:
        self.game_running = False
        self._cancel_drop()
        self._draw()
        messagebox.showinfo("Tetris", "Spiel vorbei! Starte neu oder kehre zurück.")

    def _return_to_launcher(self) -> None:
        self.game_running = False
        self._cancel_drop()
        self.root.destroy()
        if self.on_exit is not None:
            self.on_exit()


class GameLauncher:
    """Startbildschirm zur Auswahl zwischen Tic Tac Toe und Tetris."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Spielauswahl")
        self.next_action: Optional[str] = None

        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack()

        tk.Label(frame, text="Willkommen!", font=("Helvetica", 24, "bold")).pack(pady=10)
        tk.Label(frame, text="Wähle ein Spiel:", font=("Helvetica", 14)).pack(pady=(0, 10))

        tk.Button(
            frame,
            text="Tic Tac Toe",
            width=20,
            command=lambda: self._start("tic_tac_toe"),
        ).pack(pady=5)

        tk.Button(
            frame,
            text="Tetris",
            width=20,
            command=lambda: self._start("tetris"),
        ).pack(pady=5)

        tk.Button(frame, text="Beenden", width=20, command=self.root.destroy).pack(pady=5)

    def _start(self, action: str) -> None:
        self.next_action = action
        self.root.quit()

    def run(self) -> None:
        self.root.mainloop()
        action = self.next_action
        if self.root.winfo_exists():
            self.root.destroy()

        if action == "tic_tac_toe":
            TicTacToeApp(on_exit=play_gui).run()
        elif action == "tetris":
            TetrisApp(on_exit=play_gui).run()


def play_gui() -> None:
    """Launch the game launcher to pick between Tic Tac Toe and Tetris."""

    GameLauncher().run()


if __name__ == "__main__":
    play_gui()

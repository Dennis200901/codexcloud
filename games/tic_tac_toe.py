import math
import random
from typing import List, Optional, Tuple

import pygame

from .trophies import TrophyHall
from .ui import BackButton, NEON_BLUE, NEON_PINK, NEON_PURPLE


class TicTacToeGame:
    def __init__(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        go_back,
        single_player: bool = False,
        difficulty: str = "mittel",
        trophy_hall: TrophyHall | None = None,
    ):
        self.screen = screen
        self.font = font
        self.board: List[List[Optional[str]]] = [[None for _ in range(3)] for _ in range(3)]
        self.current_player = "X"
        self.winner: Optional[str] = None
        self.single_player = single_player
        self.difficulty = difficulty
        self.trophy_hall = trophy_hall
        self.human_symbol = "X"
        self.ai_symbol = "O"
        self.status_message = ""
        self.back_button = BackButton(font, go_back)
        self.grid_size = min(screen.get_width(), screen.get_height()) * 0.6
        self.cell_size = self.grid_size / 3
        self.offset_x = (screen.get_width() - self.grid_size) / 2
        self.offset_y = (screen.get_height() - self.grid_size) / 2

    def handle_events(self, events):
        for event in events:
            self.back_button.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.winner:
                mx, my = event.pos
                if self.offset_x <= mx <= self.offset_x + self.grid_size and self.offset_y <= my <= self.offset_y + self.grid_size:
                    col = int((mx - self.offset_x) // self.cell_size)
                    row = int((my - self.offset_y) // self.cell_size)
                    if self.board[row][col] is None and (not self.single_player or self.current_player == self.human_symbol):
                        self.board[row][col] = self.current_player
                        self._post_move(row, col)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()

    def _post_move(self, row: int, col: int):
        if self.check_winner(row, col):
            self.winner = self.current_player
            self.status_message = f"{self.current_player} gewinnt!"
            self._record_trophy(self.current_player)
        elif all(all(cell is not None for cell in row_data) for row_data in self.board):
            self.winner = "Unentschieden"
            self.status_message = "Unentschieden"
        else:
            self.current_player = "O" if self.current_player == "X" else "X"
            if self.single_player and self.current_player == self.ai_symbol and not self.winner:
                self._ai_move()

    def _ai_move(self):
        if self.difficulty == "leicht":
            move = random.choice(self.available_moves())
        elif self.difficulty == "mittel":
            move = self._find_best_move_medium()
        else:
            move = self._minimax_move()
        if move:
            row, col = move
            self.board[row][col] = self.ai_symbol
            if self.check_winner(row, col):
                self.winner = self.ai_symbol
                self.status_message = "Computer gewinnt"
            elif all(all(cell is not None for cell in row_data) for row_data in self.board):
                self.winner = "Unentschieden"
                self.status_message = "Unentschieden"
            else:
                self.current_player = self.human_symbol

    def available_moves(self) -> List[Tuple[int, int]]:
        return [(r, c) for r in range(3) for c in range(3) if self.board[r][c] is None]

    def _find_best_move_medium(self) -> Optional[Tuple[int, int]]:
        # Win if possible
        for move in self.available_moves():
            r, c = move
            self.board[r][c] = self.ai_symbol
            if self.check_winner(r, c):
                self.board[r][c] = None
                return move
            self.board[r][c] = None
        # Block opponent win
        for move in self.available_moves():
            r, c = move
            self.board[r][c] = self.human_symbol
            if self.check_winner(r, c):
                self.board[r][c] = None
                return move
            self.board[r][c] = None
        # Center priority, then corners
        if (1, 1) in self.available_moves():
            return (1, 1)
        corners = [move for move in self.available_moves() if move in [(0, 0), (0, 2), (2, 0), (2, 2)]]
        if corners:
            return random.choice(corners)
        moves = self.available_moves()
        return random.choice(moves) if moves else None

    def _minimax_move(self) -> Optional[Tuple[int, int]]:
        best_score = -math.inf
        best_move = None
        for r, c in self.available_moves():
            self.board[r][c] = self.ai_symbol
            score = self._minimax(False)
            self.board[r][c] = None
            if score > best_score:
                best_score = score
                best_move = (r, c)
        return best_move

    def _minimax(self, is_maximizing: bool) -> int:
        winner = self._determine_winner_state()
        if winner == self.ai_symbol:
            return 1
        if winner == self.human_symbol:
            return -1
        if winner == "draw":
            return 0
        if is_maximizing:
            best_score = -math.inf
            for r, c in self.available_moves():
                self.board[r][c] = self.ai_symbol
                score = self._minimax(False)
                self.board[r][c] = None
                best_score = max(best_score, score)
            return best_score
        else:
            best_score = math.inf
            for r, c in self.available_moves():
                self.board[r][c] = self.human_symbol
                score = self._minimax(True)
                self.board[r][c] = None
                best_score = min(best_score, score)
            return best_score

    def _determine_winner_state(self) -> Optional[str]:
        for player in (self.ai_symbol, self.human_symbol):
            for r in range(3):
                if all(self.board[r][c] == player for c in range(3)):
                    return player
            for c in range(3):
                if all(self.board[r][c] == player for r in range(3)):
                    return player
            if all(self.board[i][i] == player for i in range(3)):
                return player
            if all(self.board[i][2 - i] == player for i in range(3)):
                return player
        if all(all(cell is not None for cell in row) for row in self.board):
            return "draw"
        return None

    def _record_trophy(self, player: str):
        if not self.trophy_hall:
            return
        if self.single_player and player == self.human_symbol:
            self.trophy_hall.add_win("Tic Tac Toe", "Singleplayer", self.difficulty, result="Spieler X")
        elif not self.single_player:
            winner_mode = "Multiplayer"
            difficulty = "freundschaft"
            self.trophy_hall.add_win("Tic Tac Toe", winner_mode, difficulty, result=f"Sieger: {player}")

    def reset(self):
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current_player = "X"
        self.winner = None
        self.status_message = ""

    def check_winner(self, row, col):
        player = self.board[row][col]
        win_row = all(self.board[row][c] == player for c in range(3))
        win_col = all(self.board[r][col] == player for r in range(3))
        diag1 = row == col and all(self.board[i][i] == player for i in range(3))
        diag2 = row + col == 2 and all(self.board[i][2 - i] == player for i in range(3))
        return win_row or win_col or diag1 or diag2

    def update(self):
        pass

    def draw(self):
        self.screen.fill((10, 5, 30))
        board_rect = pygame.Rect(self.offset_x - 40, self.offset_y - 40, self.grid_size + 80, self.grid_size + 80)
        pygame.draw.rect(self.screen, (25, 10, 60), board_rect, border_radius=18)
        pygame.draw.rect(self.screen, NEON_PURPLE, board_rect, width=4, border_radius=18)
        for i in range(4):
            start_pos = (self.offset_x + i * self.cell_size, self.offset_y)
            end_pos = (self.offset_x + i * self.cell_size, self.offset_y + self.grid_size)
            pygame.draw.line(self.screen, NEON_BLUE, start_pos, end_pos, 6)
            start_pos = (self.offset_x, self.offset_y + i * self.cell_size)
            end_pos = (self.offset_x + self.grid_size, self.offset_y + i * self.cell_size)
            pygame.draw.line(self.screen, NEON_BLUE, start_pos, end_pos, 6)

        for row in range(3):
            for col in range(3):
                center = (
                    self.offset_x + col * self.cell_size + self.cell_size / 2,
                    self.offset_y + row * self.cell_size + self.cell_size / 2,
                )
                if self.board[row][col] == "X":
                    size = self.cell_size / 2.8
                    pygame.draw.line(self.screen, (255, 100, 200), (center[0] - size, center[1] - size), (center[0] + size, center[1] + size), 10)
                    pygame.draw.line(self.screen, (255, 100, 200), (center[0] + size, center[1] - size), (center[0] - size, center[1] + size), 10)
                elif self.board[row][col] == "O":
                    pygame.draw.circle(self.screen, NEON_PINK, center, self.cell_size / 2.6, 10)

        info_text = self.font.render(f"Am Zug: {self.current_player}", True, (200, 230, 255))
        self.screen.blit(info_text, (self.offset_x, self.offset_y - 90))
        hint_text = self.font.render("R = Neustart", True, (180, 200, 220))
        self.screen.blit(hint_text, (self.offset_x, self.offset_y + self.grid_size + 30))
        if self.status_message:
            win_text = self.font.render(self.status_message, True, (255, 215, 0))
            rect = win_text.get_rect(center=(self.screen.get_width() / 2, self.offset_y - 140))
            self.screen.blit(win_text, rect)
        self.back_button.draw(self.screen)

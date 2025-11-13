import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame

from .theme import NEON_PINK, draw_neon_background, draw_panel
from .ui import BackButton, Button


@dataclass
class Token:
    index: int
    progress: int = -1  # -1 = home
    finished_order: Optional[int] = None

    def is_home(self) -> bool:
        return self.progress == -1

    def is_finished(self, path_length: int, goal_length: int) -> bool:
        return self.progress == path_length + goal_length


class LudoGame:
    COLORS = [(220, 60, 60), (60, 200, 60), (250, 210, 70), (80, 140, 255)]
    PLAYER_NAMES = ["Rot", "Grün", "Gelb", "Blau"]
    PATH = [
        (6, 13), (6, 12), (6, 11), (6, 10), (6, 9), (5, 8), (4, 8), (3, 8), (2, 8), (1, 8), (0, 8),
        (0, 7), (0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 5), (6, 5), (6, 4), (6, 3), (6, 2),
        (6, 1), (6, 0), (7, 0), (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (9, 6), (10, 6),
        (11, 6), (12, 6), (13, 6), (14, 6), (14, 7), (14, 8), (13, 8), (12, 8), (11, 8), (10, 8),
        (9, 9), (8, 9), (8, 10), (8, 11), (8, 12), (8, 13), (8, 14), (7, 14), (7, 13), (7, 12),
        (7, 11), (7, 10), (7, 9)
    ]
    START_INDICES = [0, 14, 28, 42]
    HOME_POSITIONS = [
        [(1, 10), (3, 10), (1, 12), (3, 12)],
        [(1, 1), (3, 1), (1, 3), (3, 3)],
        [(10, 1), (12, 1), (10, 3), (12, 3)],
        [(10, 10), (12, 10), (10, 12), (12, 12)],
    ]
    GOAL_PATHS = [
        [(6, 12), (6, 11), (6, 10), (6, 9)],
        [(2, 6), (3, 6), (4, 6), (5, 6)],
        [(8, 2), (8, 3), (8, 4), (8, 5)],
        [(12, 8), (11, 8), (10, 8), (9, 8)],
    ]
    FINISH_POSITIONS = [
        [(6.2, 7.8), (6.6, 7.8), (6.2, 7.4), (6.6, 7.4)],
        [(7.4, 6.2), (7.8, 6.2), (7.4, 6.6), (7.8, 6.6)],
        [(7.4, 7.8), (7.8, 7.8), (7.4, 7.4), (7.8, 7.4)],
        [(6.2, 6.2), (6.6, 6.2), (6.2, 6.6), (6.6, 6.6)],
    ]

    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, go_back):
        self.screen = screen
        self.font = font
        self.board_size = min(screen.get_width(), screen.get_height()) * 0.8
        self.cell_size = self.board_size / 15
        self.offset_x = (screen.get_width() - self.board_size) / 2
        self.offset_y = (screen.get_height() - self.board_size) / 2

        self.tokens: List[List[Token]] = [[Token(i) for i in range(4)] for _ in range(4)]
        self.finished_count = [0, 0, 0, 0]
        self.current_player = 0
        self.dice_value: Optional[int] = None
        self.awaiting_roll = True
        self.movable_tokens: List[int] = []
        self.message = ""
        self.winner: Optional[int] = None

        self.back_button = BackButton(font, go_back)
        button_rect = (
            screen.get_width() - 220,
            screen.get_height() - 100,
            200,
            60,
        )
        self.roll_button = Button(button_rect, "Würfeln", font, self.roll_dice)

    @property
    def path_length(self) -> int:
        return len(self.PATH)

    @property
    def goal_length(self) -> int:
        return len(self.GOAL_PATHS[0])

    def grid_to_pixel(self, grid: Tuple[float, float]) -> Tuple[float, float]:
        x, y = grid
        return (
            self.offset_x + (x + 0.5) * self.cell_size,
            self.offset_y + (y + 0.5) * self.cell_size,
        )

    def roll_dice(self):
        if not self.awaiting_roll or self.winner is not None:
            return
        self.dice_value = random.randint(1, 6)
        self.awaiting_roll = False
        self.message = f"{self.PLAYER_NAMES[self.current_player]} würfelt eine {self.dice_value}"
        self.movable_tokens = [i for i in range(4) if self.can_move(self.current_player, i, self.dice_value)]
        if not self.movable_tokens:
            self.message += " - keine Züge möglich"
            self.next_player()

    def token_at_board_index(self, index: int) -> Optional[Tuple[int, int]]:
        for player in range(4):
            for token_index, token in enumerate(self.tokens[player]):
                if 0 <= token.progress < self.path_length:
                    board_index = (self.START_INDICES[player] + token.progress) % self.path_length
                    if board_index == index:
                        return player, token_index
        return None

    def can_move(self, player: int, token_index: int, steps: int) -> bool:
        token = self.tokens[player][token_index]
        if token.is_finished(self.path_length, self.goal_length):
            return False
        if token.is_home():
            if steps != 6:
                return False
            entry_index = self.START_INDICES[player]
            occupant = self.token_at_board_index(entry_index)
            if occupant and occupant[0] == player:
                return False
            return True
        new_progress = token.progress + steps
        if new_progress > self.path_length + self.goal_length:
            return False
        if new_progress < self.path_length:
            board_index = (self.START_INDICES[player] + new_progress) % self.path_length
            occupant = self.token_at_board_index(board_index)
            if occupant and occupant[0] == player:
                return False
            return True
        # goal path
        for other in self.tokens[player]:
            if other is token:
                continue
            if other.progress >= self.path_length:
                if token.progress < self.path_length:
                    # entering goal, check target only
                    goal_idx = new_progress - self.path_length
                    if other.progress == self.path_length + goal_idx:
                        return False
                else:
                    # already in goal: ensure no jump over
                    for step in range(token.progress + 1, new_progress + 1):
                        goal_idx = step - self.path_length
                        if other.progress == self.path_length + goal_idx:
                            return False
        return True

    def move_token(self, player: int, token_index: int):
        if self.awaiting_roll or self.dice_value is None:
            return
        token = self.tokens[player][token_index]
        if not self.can_move(player, token_index, self.dice_value):
            return
        steps = self.dice_value
        if token.is_home():
            entry_index = self.START_INDICES[player]
            occupant = self.token_at_board_index(entry_index)
            if occupant and occupant[0] != player:
                captured = self.tokens[occupant[0]][occupant[1]]
                captured.progress = -1
                captured.finished_order = None
                self.message = f"{self.PLAYER_NAMES[player]} schlägt {self.PLAYER_NAMES[occupant[0]]}!"
            token.progress = 0
        else:
            new_progress = token.progress + steps
            if new_progress < self.path_length:
                board_index = (self.START_INDICES[player] + new_progress) % self.path_length
                occupant = self.token_at_board_index(board_index)
                if occupant and occupant[0] != player:
                    captured = self.tokens[occupant[0]][occupant[1]]
                    captured.progress = -1
                    captured.finished_order = None
                    self.message = f"{self.PLAYER_NAMES[player]} schlägt {self.PLAYER_NAMES[occupant[0]]}!"
                token.progress = new_progress
            else:
                if new_progress == self.path_length + self.goal_length:
                    token.progress = new_progress
                    token.finished_order = self.finished_count[player]
                    self.finished_count[player] += 1
                    if self.finished_count[player] == 4:
                        self.winner = player
                        self.message = f"{self.PLAYER_NAMES[player]} gewinnt!"
                else:
                    token.progress = new_progress
        if self.winner is None:
            if self.dice_value == 6:
                self.awaiting_roll = True
                self.movable_tokens = []
                self.message += " - Noch einmal!" if self.message else "Nochmal würfeln!"
            else:
                self.next_player()
        else:
            self.awaiting_roll = False
            self.movable_tokens = []
        self.dice_value = None if self.awaiting_roll else self.dice_value

    def next_player(self):
        self.current_player = (self.current_player + 1) % 4
        self.awaiting_roll = True
        self.dice_value = None
        self.movable_tokens = []

    def handle_events(self, events):
        for event in events:
            self.back_button.handle_event(event)
            self.roll_button.handle_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.roll_dice()
                elif event.key == pygame.K_r and self.winner is not None:
                    self.reset()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.awaiting_roll and self.dice_value is not None and self.movable_tokens and self.winner is None:
                    mx, my = event.pos
                    for token_index in self.movable_tokens:
                        if self.is_token_clicked(self.current_player, token_index, (mx, my)):
                            self.move_token(self.current_player, token_index)
                            break

    def is_token_clicked(self, player: int, token_index: int, pos: Tuple[int, int]) -> bool:
        token_pos = self.get_token_screen_position(player, token_index)
        radius = self.cell_size * 0.4
        return (token_pos[0] - pos[0]) ** 2 + (token_pos[1] - pos[1]) ** 2 <= radius ** 2

    def reset(self):
        self.tokens = [[Token(i) for i in range(4)] for _ in range(4)]
        self.finished_count = [0, 0, 0, 0]
        self.current_player = 0
        self.dice_value = None
        self.awaiting_roll = True
        self.movable_tokens = []
        self.message = ""
        self.winner = None

    def update(self, delta: float = 0.0):
        pass

    def get_token_screen_position(self, player: int, token_index: int) -> Tuple[float, float]:
        token = self.tokens[player][token_index]
        if token.is_home():
            grid = self.HOME_POSITIONS[player][token.index]
        elif token.is_finished(self.path_length, self.goal_length):
            order = token.finished_order or 0
            order = min(order, len(self.FINISH_POSITIONS[player]) - 1)
            grid = self.FINISH_POSITIONS[player][order]
        elif token.progress < self.path_length:
            board_index = (self.START_INDICES[player] + token.progress) % self.path_length
            grid = self.PATH[board_index]
        else:
            goal_idx = token.progress - self.path_length
            grid = self.GOAL_PATHS[player][goal_idx]
        return self.grid_to_pixel(grid)

    def draw_board(self):
        board_rect = pygame.Rect(self.offset_x, self.offset_y, self.board_size, self.board_size)
        board_surface = pygame.Surface(board_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(board_surface, (5, 5, 30, 220), board_surface.get_rect(), border_radius=24)
        self.screen.blit(board_surface, board_rect.topleft)
        # Home squares
        home_rects = [
            pygame.Rect(self.offset_x, self.offset_y + self.board_size / 2, self.board_size / 3, self.board_size / 3),
            pygame.Rect(self.offset_x, self.offset_y, self.board_size / 3, self.board_size / 3),
            pygame.Rect(self.offset_x + self.board_size * 2 / 3, self.offset_y, self.board_size / 3, self.board_size / 3),
            pygame.Rect(self.offset_x + self.board_size * 2 / 3, self.offset_y + self.board_size / 2, self.board_size / 3, self.board_size / 3),
        ]
        for idx, rect in enumerate(home_rects):
            pygame.draw.rect(self.screen, self.COLORS[idx], rect)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 3)

        # Draw path squares
        for coord in self.PATH:
            rect = pygame.Rect(
                self.offset_x + coord[0] * self.cell_size,
                self.offset_y + coord[1] * self.cell_size,
                self.cell_size,
                self.cell_size,
            )
            pygame.draw.rect(self.screen, (35, 35, 70), rect)
            pygame.draw.rect(self.screen, (90, 90, 150), rect, 1)

        # Goal paths coloring
        for player, path in enumerate(self.GOAL_PATHS):
            for coord in path:
                rect = pygame.Rect(
                    self.offset_x + coord[0] * self.cell_size,
                    self.offset_y + coord[1] * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                pygame.draw.rect(self.screen, self.COLORS[player], rect)
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 1)

        # Center goal
        center_rect = pygame.Rect(
            self.offset_x + 6 * self.cell_size,
            self.offset_y + 6 * self.cell_size,
            3 * self.cell_size,
            3 * self.cell_size,
        )
        pygame.draw.rect(self.screen, (10, 10, 35), center_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), center_rect, 2)

    def draw_tokens(self):
        for player in range(4):
            for token_index in range(4):
                pos = self.get_token_screen_position(player, token_index)
                radius = self.cell_size * 0.35
                color = self.COLORS[player]
                pygame.draw.circle(self.screen, color, pos, radius)
                if not self.tokens[player][token_index].is_home():
                    pygame.draw.circle(self.screen, (0, 0, 0), pos, radius, 3)
                if player == self.current_player and token_index in self.movable_tokens:
                    pygame.draw.circle(self.screen, NEON_PINK, pos, radius + 6, 3)

    def draw_hud(self):
        panel_width = min(360, self.screen.get_width() - (self.offset_x + self.board_size + 80))
        panel_rect = pygame.Rect(
            self.offset_x + self.board_size + 40,
            self.offset_y,
            max(280, panel_width),
            self.board_size,
        )
        dice_text = str(self.dice_value) if self.dice_value is not None else "-"
        lines = [
            f"Am Zug: {self.PLAYER_NAMES[self.current_player]}",
            f"Wurf: {dice_text}",
            "SPACE oder Button: würfeln",
            "Klicke einen Stein zum Ziehen",
        ]
        if self.message:
            lines.append(self.message)
        if self.winner is not None:
            lines.append(f"{self.PLAYER_NAMES[self.winner]} gewinnt! R = Neustart")
        draw_panel(self.screen, panel_rect, "Mensch ärgere dich nicht", lines)

    def draw(self):
        draw_neon_background(self.screen)
        self.draw_board()
        self.draw_tokens()
        self.draw_hud()
        self.roll_button.draw(self.screen)
        self.back_button.draw(self.screen)

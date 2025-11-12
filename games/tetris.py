import random
from typing import List, Tuple

import pygame

from .ui import BackButton


class TetrisGame:
    COLS = 10
    ROWS = 20
    SHAPES = {
        "I": [[(0, 1), (1, 1), (2, 1), (3, 1)]],
        "J": [[(0, 0), (0, 1), (1, 1), (2, 1)]],
        "L": [[(0, 1), (1, 1), (2, 1), (2, 0)]],
        "O": [[(0, 0), (1, 0), (0, 1), (1, 1)]],
        "S": [[(0, 1), (1, 1), (1, 0), (2, 0)]],
        "T": [[(0, 1), (1, 1), (2, 1), (1, 0)]],
        "Z": [[(0, 0), (1, 0), (1, 1), (2, 1)]],
    }
    COLORS = {
        "I": (0, 255, 255),
        "J": (0, 0, 255),
        "L": (255, 127, 0),
        "O": (255, 255, 0),
        "S": (0, 255, 0),
        "T": (160, 0, 240),
        "Z": (255, 0, 0),
    }

    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, go_back):
        self.screen = screen
        self.font = font
        self.block_size = min(screen.get_width() // (self.COLS + 10), screen.get_height() // (self.ROWS + 2))
        self.play_width = self.block_size * self.COLS
        self.play_height = self.block_size * self.ROWS
        self.offset_x = (screen.get_width() - self.play_width) // 2
        self.offset_y = (screen.get_height() - self.play_height) // 2

        self.board: List[List[Tuple[int, int, int] | None]] = [
            [None for _ in range(self.COLS)] for _ in range(self.ROWS)
        ]
        self.current_piece = None
        self.next_piece = self._get_new_piece()
        self.fall_time = 0
        self.fall_speed = 500
        self.last_drop_time = pygame.time.get_ticks()
        self.level = 1
        self.score = 0
        self.lines_cleared = 0
        self.game_over = False

        self.back_button = BackButton(font, go_back)
        self.spawn_piece()

    def _get_new_piece(self):
        shape_type = random.choice(list(self.SHAPES.keys()))
        layout = self.SHAPES[shape_type][0]
        return {
            "shape": [(x, y) for x, y in layout],
            "type": shape_type,
            "rotation": 0,
            "x": self.COLS // 2 - 2,
            "y": 0,
        }

    def spawn_piece(self):
        self.current_piece = self.next_piece
        self.next_piece = self._get_new_piece()
        if not self.valid_space(self.current_piece):
            self.game_over = True

    def rotate(self):
        if self.current_piece["type"] == "O":
            return
        rotated = [(y, -x) for x, y in self.current_piece["shape"]]
        original_shape = self.current_piece["shape"]
        self.current_piece["shape"] = rotated
        if not self.valid_space(self.current_piece):
            self.current_piece["shape"] = original_shape

    def valid_space(self, piece):
        formatted = self.convert_shape_format(piece)
        for x, y in formatted:
            if x < 0 or x >= self.COLS or y >= self.ROWS:
                return False
            if y >= 0 and self.board[y][x]:
                return False
        return True

    def convert_shape_format(self, piece):
        positions = []
        for x, y in piece["shape"]:
            positions.append((x + piece["x"], y + piece["y"]))
        return positions

    def lock_piece(self):
        for x, y in self.convert_shape_format(self.current_piece):
            if 0 <= y < self.ROWS:
                self.board[y][x] = self.COLORS[self.current_piece["type"]]
        self.clear_rows()
        self.spawn_piece()

    def clear_rows(self):
        rows_to_clear = [i for i in range(self.ROWS) if all(self.board[i])]
        for i in rows_to_clear:
            del self.board[i]
            self.board.insert(0, [None for _ in range(self.COLS)])
        if rows_to_clear:
            lines = len(rows_to_clear)
            self.lines_cleared += lines
            self.score += (100 * lines) * self.level
            if self.lines_cleared // 10 >= self.level:
                self.level += 1
                self.fall_speed = max(100, int(self.fall_speed * 0.85))

    def hard_drop(self):
        while True:
            self.current_piece["y"] += 1
            if not self.valid_space(self.current_piece):
                self.current_piece["y"] -= 1
                self.lock_piece()
                break

    def handle_events(self, events):
        for event in events:
            self.back_button.handle_event(event)
            if event.type == pygame.KEYDOWN and not self.game_over:
                if event.key == pygame.K_LEFT:
                    self.current_piece["x"] -= 1
                    if not self.valid_space(self.current_piece):
                        self.current_piece["x"] += 1
                elif event.key == pygame.K_RIGHT:
                    self.current_piece["x"] += 1
                    if not self.valid_space(self.current_piece):
                        self.current_piece["x"] -= 1
                elif event.key == pygame.K_DOWN:
                    self.current_piece["y"] += 1
                    if not self.valid_space(self.current_piece):
                        self.current_piece["y"] -= 1
                        self.lock_piece()
                elif event.key == pygame.K_UP:
                    self.rotate()
                elif event.key == pygame.K_SPACE:
                    self.hard_drop()
            if event.type == pygame.KEYDOWN and self.game_over:
                if event.key == pygame.K_RETURN:
                    self.reset()

    def reset(self):
        self.board = [[None for _ in range(self.COLS)] for _ in range(self.ROWS)]
        self.current_piece = None
        self.next_piece = self._get_new_piece()
        self.fall_time = 0
        self.fall_speed = 500
        self.last_drop_time = pygame.time.get_ticks()
        self.level = 1
        self.score = 0
        self.lines_cleared = 0
        self.game_over = False
        self.spawn_piece()

    def update(self):
        if self.game_over:
            return
        current_time = pygame.time.get_ticks()
        if current_time - self.last_drop_time > self.fall_speed:
            self.current_piece["y"] += 1
            if not self.valid_space(self.current_piece):
                self.current_piece["y"] -= 1
                self.lock_piece()
            self.last_drop_time = current_time

    def draw_grid(self):
        for y in range(self.ROWS):
            for x in range(self.COLS):
                rect = pygame.Rect(
                    self.offset_x + x * self.block_size,
                    self.offset_y + y * self.block_size,
                    self.block_size,
                    self.block_size,
                )
                pygame.draw.rect(self.screen, (40, 40, 40), rect, 1)

    def draw_board(self):
        for y in range(self.ROWS):
            for x in range(self.COLS):
                color = self.board[y][x]
                if color:
                    rect = pygame.Rect(
                        self.offset_x + x * self.block_size,
                        self.offset_y + y * self.block_size,
                        self.block_size,
                        self.block_size,
                    )
                    pygame.draw.rect(self.screen, color, rect)
                    pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

    def draw_piece(self, piece):
        color = self.COLORS[piece["type"]]
        for x, y in self.convert_shape_format(piece):
            if y >= 0:
                rect = pygame.Rect(
                    self.offset_x + x * self.block_size,
                    self.offset_y + y * self.block_size,
                    self.block_size,
                    self.block_size,
                )
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

    def draw_next_piece(self):
        label = self.font.render("Nächstes", True, (255, 255, 255))
        self.screen.blit(label, (self.offset_x + self.play_width + 40, self.offset_y))
        piece = self.next_piece
        color = self.COLORS[piece["type"]]
        for x, y in piece["shape"]:
            rect = pygame.Rect(
                self.offset_x + self.play_width + 40 + (x + 1) * self.block_size,
                self.offset_y + 40 + (y + 1) * self.block_size,
                self.block_size,
                self.block_size,
            )
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

    def draw_sidebar(self):
        lines_text = self.font.render(f"Linien: {self.lines_cleared}", True, (255, 255, 255))
        level_text = self.font.render(f"Level: {self.level}", True, (255, 255, 255))
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(lines_text, (self.offset_x + self.play_width + 40, self.offset_y + 200))
        self.screen.blit(level_text, (self.offset_x + self.play_width + 40, self.offset_y + 260))
        self.screen.blit(score_text, (self.offset_x + self.play_width + 40, self.offset_y + 320))

    def draw_game_over(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        title = self.font.render("Game Over - Enter für Neustart", True, (255, 255, 255))
        rect = title.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
        self.screen.blit(title, rect)

    def draw(self):
        self.screen.fill((10, 10, 30))
        self.draw_board()
        self.draw_piece(self.current_piece)
        self.draw_grid()
        self.draw_next_piece()
        self.draw_sidebar()
        self.back_button.draw(self.screen)
        if self.game_over:
            self.draw_game_over()

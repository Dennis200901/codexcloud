import pygame

from .ui import BackButton


class TicTacToeGame:
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, go_back):
        self.screen = screen
        self.font = font
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current_player = "X"
        self.winner = None
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
                    if self.board[row][col] is None:
                        self.board[row][col] = self.current_player
                        if self.check_winner(row, col):
                            self.winner = self.current_player
                        elif all(all(cell is not None for cell in row_data) for row_data in self.board):
                            self.winner = "Unentschieden"
                        else:
                            self.current_player = "O" if self.current_player == "X" else "X"
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()

    def reset(self):
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current_player = "X"
        self.winner = None

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
        self.screen.fill((20, 20, 20))
        for i in range(4):
            start_pos = (self.offset_x + i * self.cell_size, self.offset_y)
            end_pos = (self.offset_x + i * self.cell_size, self.offset_y + self.grid_size)
            pygame.draw.line(self.screen, (200, 200, 200), start_pos, end_pos, 4)
            start_pos = (self.offset_x, self.offset_y + i * self.cell_size)
            end_pos = (self.offset_x + self.grid_size, self.offset_y + i * self.cell_size)
            pygame.draw.line(self.screen, (200, 200, 200), start_pos, end_pos, 4)

        for row in range(3):
            for col in range(3):
                center = (
                    self.offset_x + col * self.cell_size + self.cell_size / 2,
                    self.offset_y + row * self.cell_size + self.cell_size / 2,
                )
                if self.board[row][col] == "X":
                    size = self.cell_size / 2.5
                    pygame.draw.line(self.screen, (255, 80, 80), (center[0] - size, center[1] - size), (center[0] + size, center[1] + size), 8)
                    pygame.draw.line(self.screen, (255, 80, 80), (center[0] + size, center[1] - size), (center[0] - size, center[1] + size), 8)
                elif self.board[row][col] == "O":
                    pygame.draw.circle(self.screen, (80, 180, 255), center, self.cell_size / 2.5, 8)

        info_text = self.font.render(f"Spieler: {self.current_player}", True, (255, 255, 255))
        self.screen.blit(info_text, (self.offset_x, self.offset_y - 60))
        hint_text = self.font.render("R = Neustart", True, (200, 200, 200))
        self.screen.blit(hint_text, (self.offset_x, self.offset_y + self.grid_size + 20))

        if self.winner:
            message = "Unentschieden" if self.winner == "Unentschieden" else f"Gewinner: {self.winner}"
            win_text = self.font.render(message, True, (255, 215, 0))
            rect = win_text.get_rect(center=(self.screen.get_width() / 2, self.offset_y - 120))
            self.screen.blit(win_text, rect)

        self.back_button.draw(self.screen)

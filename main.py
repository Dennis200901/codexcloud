import sys
from typing import Callable, Optional

import pygame

from games.chess import ChessGame
from games.ludo import LudoGame
from games.pacman import PacmanGame
from games.tetris import TetrisGame
from games.theme import NEON_PINK, draw_neon_background, draw_panel
from games.tic_tac_toe import TicTacToeGame
from games.ui import Button


class StartScreen:
    def __init__(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        title_font: pygame.font.Font,
        launch_game: Callable[[str], None],
    ) -> None:
        self.screen = screen
        self.font = font
        self.title_font = title_font
        self.launch_game = launch_game
        self.buttons: list[Button] = []
        self.pulse_time = 0.0
        self._create_buttons()

    def _create_buttons(self) -> None:
        labels = [
            ("Tetris", "tetris"),
            ("Pac-Man", "pacman"),
            ("Tic Tac Toe", "tic_tac_toe"),
            ("Schach", "chess"),
            ("Mensch ärgere dich nicht", "ludo"),
        ]
        button_width = self.screen.get_width() * 0.35
        button_height = 90
        spacing = 28
        total_height = len(labels) * button_height + (len(labels) - 1) * spacing
        start_y = (self.screen.get_height() - total_height) / 2
        for i, (label, key) in enumerate(labels):
            rect = (
                (self.screen.get_width() - button_width) / 2,
                start_y + i * (button_height + spacing),
                button_width,
                button_height,
            )
            self.buttons.append(Button(rect, label, self.font, lambda k=key: self.launch_game(k)))

    def handle_events(self, events) -> None:
        for event in events:
            for button in self.buttons:
                button.handle_event(event)

    def update(self, delta: float = 0.0) -> None:
        self.pulse_time = (self.pulse_time + delta) % 1000

    def draw(self) -> None:
        draw_neon_background(self.screen)
        time_ms = pygame.time.get_ticks()
        pulse = 0.6 + 0.4 * pygame.math.Vector2(1, 0).rotate(time_ms / 8).x
        title_color = tuple(int(200 + 55 * pulse) for _ in range(3))
        title = self.title_font.render('80s Arcade Sammlung', True, title_color)
        title_rect = title.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() * 0.18))
        shadow = self.title_font.render('80s Arcade Sammlung', True, NEON_PINK)
        self.screen.blit(shadow, title_rect.move(0, 6))
        self.screen.blit(title, title_rect)

        subtitle = self.font.render('Wähle dein Retro-Abenteuer', True, (235, 245, 255))
        sub_rect = subtitle.get_rect(center=(self.screen.get_width() / 2, title_rect.bottom + 50))
        self.screen.blit(subtitle, sub_rect)

        for button in self.buttons:
            button.draw(self.screen)

        info_rect = pygame.Rect(
            self.screen.get_width() * 0.1,
            self.screen.get_height() * 0.72,
            self.screen.get_width() * 0.8,
            160,
        )
        draw_panel(
            self.screen,
            info_rect,
            'Tipps',
            ['ESC = zurück', 'Vollbild aktiv', 'Alle Spiele lokal spielbar'],
        )



class GameApp:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        display_info = pygame.display.Info()
        self.screen = pygame.display.set_mode((display_info.current_w, display_info.current_h), pygame.FULLSCREEN)
        pygame.display.set_caption("Arcade Sammlung")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 42)
        self.title_font = pygame.font.SysFont("arial", 96, bold=True)
        self.current_screen: Optional[object] = None
        self.running = True
        self.start_screen = StartScreen(self.screen, self.font, self.title_font, self.launch_game)
        self.current_screen = self.start_screen

    def launch_game(self, key: str):
        def go_back():
            self.current_screen = self.start_screen

        if key == "tetris":
            self.current_screen = TetrisGame(self.screen, self.font, go_back)
        elif key == "pacman":
            self.current_screen = PacmanGame(self.screen, self.font, go_back)
        elif key == "tic_tac_toe":
            self.current_screen = TicTacToeGame(self.screen, self.font, go_back)
        elif key == "chess":
            self.current_screen = ChessGame(self.screen, self.font, go_back)
        elif key == "ludo":
            self.current_screen = LudoGame(self.screen, self.font, go_back)
        else:
            self.current_screen = self.start_screen

    def run(self):
        while self.running:
            delta = self.clock.tick(60) / 1000.0
            events = list(pygame.event.get())
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.current_screen is not self.start_screen:
                        self.current_screen = self.start_screen
                    else:
                        self.running = False
            if self.current_screen:
                if hasattr(self.current_screen, "handle_events"):
                    self.current_screen.handle_events(events)
                if hasattr(self.current_screen, "update"):
                    self.current_screen.update(delta)
                if hasattr(self.current_screen, "draw"):
                    self.current_screen.draw()
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    GameApp().run()

import sys
from typing import Callable, Optional

import pygame

from games.chess import ChessGame
from games.ludo import LudoGame
from games.tetris import TetrisGame
from games.tic_tac_toe import TicTacToeGame
from games.trophies import TrophyHall
from games.ui import BackButton, Button, OptionGroup, NEON_BLUE, NEON_PINK, NEON_PURPLE

DIFFICULTY_LABELS = ["Leicht", "Mittel", "Schwer"]
DIFFICULTY_KEYS = ["leicht", "mittel", "schwer"]


def draw_retro_background(surface: pygame.Surface):
    width, height = surface.get_size()
    surface.fill((6, 8, 24))
    grid_color = (40, 120, 200)
    horizon = height * 0.55
    # Draw glowing gradient horizon
    for i in range(120):
        alpha = 1 - i / 120
        color = (int(20 + 90 * alpha), int(20 + 40 * alpha), int(60 + 140 * alpha))
        pygame.draw.line(surface, color, (0, int(horizon) + i), (width, int(horizon) + i), 1)
    # Draw perspective grid lines
    for x in range(-width, width * 2, 80):
        pygame.draw.line(
            surface,
            grid_color,
            (x, height),
            (width / 2 + (x - width / 2) * 0.2, horizon),
            1,
        )
    for y in range(int(horizon), height, 45):
        factor = (y - horizon) / (height - horizon + 1)
        color = (
            min(255, int(grid_color[0] + 120 * factor)),
            min(255, int(grid_color[1] + 40 * factor)),
            min(255, int(grid_color[2] + 40 * factor)),
        )
        pygame.draw.line(surface, color, (0, y), (width, y), 1)


class StartScreen:
    def __init__(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        title_font: pygame.font.Font,
        small_font: pygame.font.Font,
        open_setup: Callable[[str], None],
        open_trophy: Callable[[], None],
        trophy_hall: TrophyHall,
    ):
        self.screen = screen
        self.font = font
        self.small_font = small_font
        self.title_font = title_font
        self.open_setup = open_setup
        self.open_trophy = open_trophy
        self.trophy_hall = trophy_hall
        self.game_buttons: list[Button] = []
        self.trophy_button = None
        self._create_buttons()

    def _create_buttons(self):
        labels = [
            ("Tetris", "tetris"),
            ("Tic Tac Toe", "tic_tac_toe"),
            ("Schach", "chess"),
            ("Mensch ärgere dich nicht", "ludo"),
        ]
        button_width = self.screen.get_width() * 0.4
        button_height = 90
        spacing = 30
        total_height = len(labels) * button_height + (len(labels) - 1) * spacing
        start_y = (self.screen.get_height() - total_height) / 2
        for i, (label, key) in enumerate(labels):
            rect = (
                (self.screen.get_width() - button_width) / 2,
                start_y + i * (button_height + spacing),
                button_width,
                button_height,
            )
            button = Button(rect, label, self.font, lambda g=key: self.open_setup(g))
            self.game_buttons.append(button)
        trophy_rect = (
            self.screen.get_width() - 260,
            self.screen.get_height() - 120,
            240,
            70,
        )
        self.trophy_button = Button(
            trophy_rect,
            "Trophäenhalle",
            self.font,
            self.open_trophy,
            bg_color=NEON_PINK,
            hover_color=NEON_BLUE,
            text_color=(20, 10, 40),
            accent_color=NEON_PURPLE,
        )

    def handle_events(self, events):
        for event in events:
            for button in self.game_buttons:
                button.handle_event(event)
            if self.trophy_button:
                self.trophy_button.handle_event(event)

    def update(self):
        pass

    def draw(self):
        draw_retro_background(self.screen)
        title = self.title_font.render("Arcade Sammlung", True, (255, 240, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() * 0.2))
        self.screen.blit(title, title_rect)
        subtitle = self.font.render("Wähle dein Retro-Abenteuer", True, (180, 210, 255))
        sub_rect = subtitle.get_rect(center=(self.screen.get_width() / 2, title_rect.bottom + 60))
        self.screen.blit(subtitle, sub_rect)
        for button in self.game_buttons:
            button.draw(self.screen)
        if self.trophy_button:
            self.trophy_button.draw(self.screen)
        total_trophies = self.trophy_hall.trophies
        league = self.trophy_hall.league_name()
        progress, target = self.trophy_hall.progress_to_next_league()
        info_text = self.small_font.render(
            f"Pokale: {total_trophies}  |  Liga: {league}  |  Fortschritt: {progress}/{target}",
            True,
            (200, 240, 255),
        )
        info_rect = info_text.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() - 60))
        self.screen.blit(info_text, info_rect)


class GameSetupScreen:
    def __init__(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        title_font: pygame.font.Font,
        small_font: pygame.font.Font,
        game_key: str,
        start_game: Callable[[str, str, str], None],
        go_back: Callable[[], None],
    ):
        self.screen = screen
        self.font = font
        self.small_font = small_font
        self.title_font = title_font
        self.game_key = game_key
        self.start_game = start_game
        self.back_button = BackButton(font, go_back)
        self.mode = "single"
        self.difficulty = DIFFICULTY_KEYS[1]
        self.mode_group: Optional[OptionGroup] = None
        self.difficulty_group: Optional[OptionGroup] = None
        self._build_ui()

    def _build_ui(self):
        width = self.screen.get_width()
        height = self.screen.get_height()
        if self.game_key != "tetris":
            rect = (width * 0.3, height * 0.45, width * 0.4, 70)
            self.mode_group = OptionGroup(
                rect,
                ["Singleplayer", "Multiplayer"],
                self.font,
                self._set_mode,
                initial_index=0,
            )
        if self.game_key in {"ludo", "tic_tac_toe", "chess"}:
            diff_rect = (width * 0.3, height * 0.6, width * 0.4, 70)
            self.difficulty_group = OptionGroup(
                diff_rect,
                DIFFICULTY_LABELS,
                self.font,
                self._set_difficulty,
                initial_index=1,
            )
            self.difficulty_group.select(DIFFICULTY_KEYS.index(self.difficulty))

        start_rect = (width * 0.4, height * 0.75, width * 0.2, 80)
        self.start_button = Button(start_rect, "Spiel starten", self.font, self._launch)

    def _set_mode(self, index: int):
        self.mode = "single" if index == 0 else "multi"

    def _set_difficulty(self, index: int):
        self.difficulty = DIFFICULTY_KEYS[index]

    def _launch(self):
        if self.mode == "multi" and self.game_key == "tetris":
            self.mode = "single"
        if self.game_key != "ludo" and self.mode == "multi":
            # difficulty irrelevant in multiplayer for other games
            difficulty = "mittel"
        else:
            difficulty = self.difficulty
        self.start_game(self.game_key, self.mode, difficulty)

    def handle_events(self, events):
        for event in events:
            self.back_button.handle_event(event)
            if self.mode_group:
                self.mode_group.handle_events([event])
            if self.difficulty_group and self._should_show_difficulty():
                self.difficulty_group.handle_events([event])
            self.start_button.handle_event(event)

    def _should_show_difficulty(self) -> bool:
        if self.game_key == "ludo":
            return True
        if self.game_key in {"tic_tac_toe", "chess"}:
            return self.mode == "single"
        return False

    def update(self):
        pass

    def draw(self):
        draw_retro_background(self.screen)
        titles = {
            "tetris": "Tetris",
            "tic_tac_toe": "Tic Tac Toe",
            "chess": "Schach",
            "ludo": "Mensch ärgere dich nicht",
        }
        title = self.title_font.render(f"{titles.get(self.game_key, 'Spiel')} Setup", True, (255, 240, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() * 0.25))
        self.screen.blit(title, title_rect)
        hint_lines: list[str] = []
        if self.mode_group:
            hint_lines.append("Wähle deinen Spielmodus")
        if self.difficulty_group:
            if self.game_key == "ludo":
                hint_lines.append("Schwierigkeit steuert die KI der Gegner")
            else:
                hint_lines.append("Schwierigkeit beeinflusst Computerzüge im Singleplayer")
        if not hint_lines:
            hint_lines.append("Drücke Start für den Neon-Spaß")
        for i, text in enumerate(hint_lines):
            hint = self.small_font.render(text, True, (180, 220, 255))
            self.screen.blit(hint, (self.screen.get_width() * 0.3, self.screen.get_height() * (0.35 + i * 0.04)))
        if self.mode_group:
            self.mode_group.draw(self.screen)
        if self.difficulty_group and self._should_show_difficulty():
            self.difficulty_group.draw(self.screen)
        start_label = self.small_font.render("Bereit?", True, (200, 240, 255))
        self.screen.blit(start_label, (self.screen.get_width() * 0.45, self.screen.get_height() * 0.7))
        self.start_button.draw(self.screen)
        self.back_button.draw(self.screen)


class TrophyHallScreen:
    def __init__(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        title_font: pygame.font.Font,
        small_font: pygame.font.Font,
        trophy_hall: TrophyHall,
        go_back: Callable[[], None],
    ):
        self.screen = screen
        self.font = font
        self.title_font = title_font
        self.small_font = small_font
        self.trophy_hall = trophy_hall
        self.back_button = BackButton(font, go_back)

    def handle_events(self, events):
        for event in events:
            self.back_button.handle_event(event)

    def update(self):
        pass

    def draw(self):
        draw_retro_background(self.screen)
        title = self.title_font.render("Trophäenhalle", True, (255, 240, 255))
        rect = title.get_rect(center=(self.screen.get_width() / 2, self.screen.get_height() * 0.18))
        self.screen.blit(title, rect)
        trophies = self.trophy_hall.trophies
        league = self.trophy_hall.league_name()
        progress, target = self.trophy_hall.progress_to_next_league()
        info_text = self.font.render(f"Pokale: {trophies}", True, (255, 210, 255))
        self.screen.blit(info_text, (self.screen.get_width() * 0.2, self.screen.get_height() * 0.32))
        league_text = self.font.render(f"Liga: {league}", True, (200, 255, 255))
        self.screen.blit(league_text, (self.screen.get_width() * 0.2, self.screen.get_height() * 0.38))
        bar_width = self.screen.get_width() * 0.6
        bar_rect = pygame.Rect(
            self.screen.get_width() * 0.2,
            self.screen.get_height() * 0.46,
            bar_width,
            30,
        )
        pygame.draw.rect(self.screen, (20, 30, 70), bar_rect, border_radius=12)
        progress_width = bar_width * (progress / target if target else 0)
        progress_rect = pygame.Rect(bar_rect.x, bar_rect.y, progress_width, bar_rect.height)
        pygame.draw.rect(self.screen, NEON_BLUE, progress_rect, border_radius=12)
        bar_caption = self.small_font.render(f"Fortschritt zur nächsten Liga: {progress}/{target}", True, (200, 240, 255))
        self.screen.blit(bar_caption, (bar_rect.x, bar_rect.y - 30))
        history_title = self.font.render("Letzte Siege", True, (255, 240, 240))
        self.screen.blit(history_title, (self.screen.get_width() * 0.2, self.screen.get_height() * 0.55))
        for idx, entry in enumerate(self.trophy_hall.recent_entries()):
            line = f"{entry.game} - {entry.mode.title()} - {entry.difficulty.title()} ({entry.result})"
            text = self.small_font.render(line, True, (190, 220, 255))
            self.screen.blit(text, (self.screen.get_width() * 0.2, self.screen.get_height() * 0.62 + idx * 32))
        self.back_button.draw(self.screen)


class GameApp:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        display_info = pygame.display.Info()
        self.screen = pygame.display.set_mode((display_info.current_w, display_info.current_h), pygame.FULLSCREEN)
        pygame.display.set_caption("Arcade Sammlung")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("bahnschrift", 42)
        self.title_font = pygame.font.SysFont("bahnschrift", 96, bold=True)
        self.small_font = pygame.font.SysFont("bahnschrift", 30)
        self.current_screen: Optional[object] = None
        self.running = True
        self.trophies = TrophyHall()
        self.start_screen = StartScreen(
            self.screen,
            self.font,
            self.title_font,
            self.small_font,
            self.open_setup,
            self.show_trophies,
            self.trophies,
        )
        self.current_screen = self.start_screen

    def open_setup(self, game_key: str):
        self.current_screen = GameSetupScreen(
            self.screen,
            self.font,
            self.title_font,
            self.small_font,
            game_key,
            self.launch_game,
            self.go_to_start,
        )

    def show_trophies(self):
        self.current_screen = TrophyHallScreen(
            self.screen,
            self.font,
            self.title_font,
            self.small_font,
            self.trophies,
            self.go_to_start,
        )

    def go_to_start(self):
        self.trophies.load()
        self.start_screen = StartScreen(
            self.screen,
            self.font,
            self.title_font,
            self.small_font,
            self.open_setup,
            self.show_trophies,
            self.trophies,
        )
        self.current_screen = self.start_screen

    def launch_game(self, key: str, mode: str, difficulty: str):
        def go_back():
            self.go_to_start()

        single_player = mode == "single"
        if key == "tetris":
            self.current_screen = TetrisGame(self.screen, self.font, go_back, self.trophies)
        elif key == "tic_tac_toe":
            self.current_screen = TicTacToeGame(
                self.screen,
                self.font,
                go_back,
                single_player=single_player,
                difficulty=difficulty,
                trophy_hall=self.trophies,
            )
        elif key == "chess":
            self.current_screen = ChessGame(
                self.screen,
                self.font,
                go_back,
                single_player=single_player,
                difficulty=difficulty,
                trophy_hall=self.trophies,
            )
        elif key == "ludo":
            self.current_screen = LudoGame(
                self.screen,
                self.font,
                go_back,
                single_player=single_player,
                difficulty=difficulty,
                trophy_hall=self.trophies,
            )
        else:
            self.current_screen = self.start_screen

    def run(self):
        while self.running:
            events = [event for event in pygame.event.get()]
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if not isinstance(self.current_screen, StartScreen):
                        self.go_to_start()
                    else:
                        self.running = False
            if self.current_screen:
                if hasattr(self.current_screen, "handle_events"):
                    self.current_screen.handle_events(events)
                if hasattr(self.current_screen, "update"):
                    self.current_screen.update()
                if hasattr(self.current_screen, "draw"):
                    self.current_screen.draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    GameApp().run()

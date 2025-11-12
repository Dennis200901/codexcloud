from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame

from .ui import BackButton

BOARD_SIZE = 8
WHITE = "white"
BLACK = "black"


@dataclass
class Move:
    start: Tuple[int, int]
    end: Tuple[int, int]
    promotion: Optional[str] = None


class Piece:
    def __init__(self, color: str):
        self.color = color
        self.has_moved = False

    def get_moves(self, board: "ChessBoard", pos: Tuple[int, int]) -> List[Move]:
        raise NotImplementedError

    def enemy_color(self):
        return BLACK if self.color == WHITE else WHITE


class Pawn(Piece):
    def get_moves(self, board: "ChessBoard", pos: Tuple[int, int]) -> List[Move]:
        moves = []
        direction = -1 if self.color == WHITE else 1
        start_row = 6 if self.color == WHITE else 1
        x, y = pos
        forward = (x, y + direction)
        if board.is_empty(forward):
            if forward[1] in (0, 7):
                moves.append(Move(pos, forward, promotion="queen"))
            else:
                moves.append(Move(pos, forward))
            two_forward = (x, y + 2 * direction)
            if y == start_row and board.is_empty(two_forward):
                moves.append(Move(pos, two_forward))
        for dx in (-1, 1):
            target = (x + dx, y + direction)
            if board.is_enemy(target, self.color):
                if target[1] in (0, 7):
                    moves.append(Move(pos, target, promotion="queen"))
                else:
                    moves.append(Move(pos, target))
        return moves


class Knight(Piece):
    OFFSETS = [
        (1, 2),
        (2, 1),
        (2, -1),
        (1, -2),
        (-1, -2),
        (-2, -1),
        (-2, 1),
        (-1, 2),
    ]

    def get_moves(self, board: "ChessBoard", pos: Tuple[int, int]) -> List[Move]:
        moves = []
        x, y = pos
        for dx, dy in self.OFFSETS:
            target = (x + dx, y + dy)
            if board.is_empty(target) or board.is_enemy(target, self.color):
                moves.append(Move(pos, target))
        return moves


class King(Piece):
    OFFSETS = [
        (1, 0),
        (1, 1),
        (0, 1),
        (-1, 1),
        (-1, 0),
        (-1, -1),
        (0, -1),
        (1, -1),
    ]

    def get_moves(self, board: "ChessBoard", pos: Tuple[int, int]) -> List[Move]:
        moves = []
        x, y = pos
        for dx, dy in self.OFFSETS:
            target = (x + dx, y + dy)
            if board.is_empty(target) or board.is_enemy(target, self.color):
                moves.append(Move(pos, target))
        # Castling omitted for simplicity
        return moves


class SlidingPiece(Piece):
    DIRECTIONS: List[Tuple[int, int]] = []

    def get_moves(self, board: "ChessBoard", pos: Tuple[int, int]) -> List[Move]:
        moves = []
        x, y = pos
        for dx, dy in self.DIRECTIONS:
            step = 1
            while True:
                target = (x + dx * step, y + dy * step)
                if not board.is_on_board(target):
                    break
                if board.is_empty(target):
                    moves.append(Move(pos, target))
                elif board.is_enemy(target, self.color):
                    moves.append(Move(pos, target))
                    break
                else:
                    break
                step += 1
        return moves


class Rook(SlidingPiece):
    DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


class Bishop(SlidingPiece):
    DIRECTIONS = [(1, 1), (-1, -1), (1, -1), (-1, 1)]


class Queen(SlidingPiece):
    DIRECTIONS = Rook.DIRECTIONS + Bishop.DIRECTIONS


class ChessBoard:
    def __init__(self):
        self.board: List[List[Optional[Piece]]] = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.setup()

    def setup(self):
        for i in range(BOARD_SIZE):
            self.board[1][i] = Pawn(BLACK)
            self.board[6][i] = Pawn(WHITE)
        placement = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for i, piece_cls in enumerate(placement):
            self.board[0][i] = piece_cls(BLACK)
            self.board[7][i] = piece_cls(WHITE)

    def clone(self) -> "ChessBoard":
        new_board = ChessBoard.__new__(ChessBoard)
        new_board.board = [[piece if piece is None else type(piece)(piece.color) for piece in row] for row in self.board]
        return new_board

    def is_on_board(self, pos: Tuple[int, int]) -> bool:
        x, y = pos
        return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE

    def get(self, pos: Tuple[int, int]) -> Optional[Piece]:
        if not self.is_on_board(pos):
            return None
        x, y = pos
        return self.board[y][x]

    def is_empty(self, pos: Tuple[int, int]) -> bool:
        return self.is_on_board(pos) and self.get(pos) is None

    def is_enemy(self, pos: Tuple[int, int], color: str) -> bool:
        piece = self.get(pos)
        return piece is not None and piece.color != color

    def move_piece(self, move: Move):
        start_x, start_y = move.start
        end_x, end_y = move.end
        piece = self.board[start_y][start_x]
        self.board[start_y][start_x] = None
        if move.promotion and isinstance(piece, Pawn):
            promoted_cls = {"queen": Queen}[move.promotion]
            piece = promoted_cls(piece.color)
        self.board[end_y][end_x] = piece
        if piece:
            piece.has_moved = True

    def find_king(self, color: str) -> Optional[Tuple[int, int]]:
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                piece = self.board[y][x]
                if isinstance(piece, King) and piece.color == color:
                    return (x, y)
        return None

    def in_check(self, color: str) -> bool:
        king_pos = self.find_king(color)
        if not king_pos:
            return False
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                piece = self.board[y][x]
                if piece and piece.color != color:
                    for move in piece.get_moves(self, (x, y)):
                        if move.end == king_pos:
                            return True
        return False

    def legal_moves(self, color: str) -> List[Move]:
        moves: List[Move] = []
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                piece = self.board[y][x]
                if piece and piece.color == color:
                    for move in piece.get_moves(self, (x, y)):
                        if not self._move_puts_in_check(move, color):
                            moves.append(move)
        return moves

    def _move_puts_in_check(self, move: Move, color: str) -> bool:
        board_copy = self.clone()
        board_copy.move_piece(move)
        return board_copy.in_check(color)


class ChessGame:
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, go_back):
        self.screen = screen
        self.font = font
        self.board = ChessBoard()
        self.turn = WHITE
        self.selected: Optional[Tuple[int, int]] = None
        self.valid_moves: List[Tuple[int, int]] = []
        self.winner: Optional[str] = None
        self.back_button = BackButton(font, go_back)
        self.board_size = min(screen.get_height() * 0.8, screen.get_width() * 0.8)
        self.square_size = self.board_size / BOARD_SIZE
        self.offset_x = (screen.get_width() - self.board_size) / 2
        self.offset_y = (screen.get_height() - self.board_size) / 2

    def handle_events(self, events):
        for event in events:
            self.back_button.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.winner:
                mx, my = event.pos
                if self.offset_x <= mx <= self.offset_x + self.board_size and self.offset_y <= my <= self.offset_y + self.board_size:
                    col = int((mx - self.offset_x) // self.square_size)
                    row = int((my - self.offset_y) // self.square_size)
                    self.process_click((col, row))
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()

    def process_click(self, pos: Tuple[int, int]):
        if self.selected and pos in self.valid_moves:
            self.make_move(Move(self.selected, pos))
            self.selected = None
            self.valid_moves = []
            return
        piece = self.board.get(pos)
        if piece and piece.color == self.turn:
            self.selected = pos
            self.valid_moves = [move.end for move in piece.get_moves(self.board, pos) if not self.board._move_puts_in_check(move, self.turn)]
        else:
            self.selected = None
            self.valid_moves = []

    def make_move(self, move: Move):
        piece = self.board.get(move.start)
        if isinstance(piece, Pawn) and (move.end[1] == 0 or move.end[1] == 7):
            move = Move(move.start, move.end, promotion="queen")
        self.board.move_piece(move)
        self.turn = BLACK if self.turn == WHITE else WHITE
        if not self.board.legal_moves(self.turn):
            if self.board.in_check(self.turn):
                self.winner = WHITE if self.turn == BLACK else BLACK
            else:
                self.winner = "Remis"

    def reset(self):
        self.board = ChessBoard()
        self.turn = WHITE
        self.selected = None
        self.valid_moves = []
        self.winner = None

    def update(self):
        pass

    def draw_board(self):
        colors = [(235, 235, 208), (119, 148, 85)]
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = colors[(row + col) % 2]
                rect = pygame.Rect(
                    self.offset_x + col * self.square_size,
                    self.offset_y + row * self.square_size,
                    self.square_size,
                    self.square_size,
                )
                pygame.draw.rect(self.screen, color, rect)
                if self.selected == (col, row):
                    pygame.draw.rect(self.screen, (255, 215, 0), rect, 5)
                elif (col, row) in self.valid_moves:
                    pygame.draw.circle(
                        self.screen,
                        (0, 0, 0),
                        rect.center,
                        self.square_size / 6,
                        width=0,
                    )

    def draw_pieces(self):
        piece_symbols = {
            Pawn: {WHITE: "♙", BLACK: "♟"},
            Rook: {WHITE: "♖", BLACK: "♜"},
            Knight: {WHITE: "♘", BLACK: "♞"},
            Bishop: {WHITE: "♗", BLACK: "♝"},
            Queen: {WHITE: "♕", BLACK: "♛"},
            King: {WHITE: "♔", BLACK: "♚"},
        }
        piece_font = pygame.font.SysFont("arial", int(self.square_size * 0.8))
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board.board[row][col]
                if piece:
                    symbol = piece_symbols[type(piece)][piece.color]
                    text = piece_font.render(symbol, True, (10, 10, 10))
                    rect = text.get_rect(center=(self.offset_x + col * self.square_size + self.square_size / 2,
                                                 self.offset_y + row * self.square_size + self.square_size / 2))
                    self.screen.blit(text, rect)

    def draw_status(self):
        status = f"Am Zug: {'Weiß' if self.turn == WHITE else 'Schwarz'}"
        text = self.font.render(status, True, (255, 255, 255))
        self.screen.blit(text, (self.offset_x, self.offset_y - 60))
        hint = self.font.render("R = Neustart", True, (200, 200, 200))
        self.screen.blit(hint, (self.offset_x, self.offset_y + self.board_size + 20))
        if self.winner:
            if self.winner == "Remis":
                message = "Remis"
            else:
                message = f"Schachmatt - {'Weiß' if self.winner == WHITE else 'Schwarz'} gewinnt"
            win_text = self.font.render(message, True, (255, 215, 0))
            rect = win_text.get_rect(center=(self.screen.get_width() / 2, self.offset_y - 120))
            self.screen.blit(win_text, rect)

    def draw(self):
        self.screen.fill((15, 20, 30))
        self.draw_board()
        self.draw_pieces()
        self.draw_status()
        self.back_button.draw(self.screen)

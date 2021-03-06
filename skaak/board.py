from itertools import count
from typing import List
import skaak.chess as chess


class Chessboard:
    def __init__(self, fen: str = chess.STARTING_FEN, **kwargs) -> None:
        self.fen: str = chess.STARTING_FEN

        self.board: str = ""
        self.castling: str = ""
        self.en_pas: str = ""

        self.history: List[Chessboard] = [0] * 2048

        self.full: int = 0
        self.half: int = 0

        self.set_fen(fen)

    def __repr__(self) -> str:
        ascii_repr: str = ""
        for i, char in enumerate(self.board):
            if i % 16 == 0:
                ascii_repr += "\n"

            if i & 0x88 == 0:
                ascii_repr += char + " "

        return ascii_repr

    @staticmethod
    def _128_index_to_san(index: int) -> str:
        file = 8 - (index // 16)
        rank = chess.RANKS[index % 16]
        return f"{rank}{file}"

    @staticmethod
    def _draw_indexed_board(highlighted_squares: List[int] = []) -> None:
        for i in range(128):
            if i & 0x88 != 0:
                continue
            if i % 8 == 0:
                print("\n")
            if i in highlighted_squares:
                i = "*"
            print("{:>4}".format(i), end=" ")
        print("\n")

    def move(self, move: chess.Move) -> None:
        if (0x88 & move.initial_square) != 0:
            raise chess.InvalidMove(
                f"Invalid Move : {move.moving_piece} from square {move.initial_square} to square {move.target_square}, occupied by {move.attacked_piece}"
            )

        temp = list(self.board)

        if (0x88 & move.target_square) == 0:
            temp[move.target_square] = move.moving_piece

        temp[move.initial_square] = chess.EMPTY
        self.board = "".join(temp)

        self.history[self.half] = move
        self.half += 1

    def undo_move(self) -> None:
        last_move = self.history[self.half - 1]
        temp = list(self.board)
        temp[last_move.initial_square] = last_move.moving_piece
        temp[last_move.target_square] = last_move.attacked_piece
        self.board = "".join(temp)

        self.half -= 1

    def generate_pseudo_moves(self) -> List[chess.Move]:
        for square, piece in enumerate(self.board):

            if (square & 0x88) != 0:
                continue
            if self.turn == chess.WHITE and not piece.isupper():
                continue
            elif self.turn == chess.BLACK and not piece.islower():
                continue

            for direction in chess.MOVES[piece.lower() if piece != "P" else piece]:
                for j in count(square + direction, direction):

                    # Check if the square is offboard
                    if (j & 0x88) != 0:
                        break

                    # Ensure the piece at the square is not of the same color
                    if self.turn == chess.WHITE and self.board[j].isupper():
                        break
                    elif self.turn == chess.BLACK and self.board[j].islower():
                        break

                    if piece.lower() == "p":
                        if (
                            self.turn == chess.WHITE
                            and direction == (chess.NORTH * 2)
                            and square // 16 != 6
                        ) or (
                            self.turn == chess.BLACK
                            and direction == (chess.SOUTH * 2)
                            and square // 16 != 1
                        ):
                            break
                        if (j % 16 != square % 16) and self.board[j] in "-.":
                            break
                        if (j % 16 == square % 16) and self.board[j] not in "-.":
                            break
                        if (j // 8 - square // 8) ** 1 == 1 and self.board[
                            j - ((j // 8 - square // 8) * 8)
                        ] != "":
                            break

                    yield chess.Move(
                        initial_square=square,
                        target_square=j,
                        moving_piece=self.board[square],
                        attacked_piece=self.board[j],
                        capture=(self.board[j] not in "-."),
                        score=0,
                    )

                    if self.board[j] not in "-." or piece.lower() in "knp":
                        break

    def perft(self, depth: int) -> int:
        nodes = 0

        if depth == 0:
            return 1

        for move in self.generate_pseudo_moves():
            self.move(move)
            nodes += self.perft(depth - 1)
            self.undo_move()

        return nodes

    def set_fen(self, fen: str) -> None:
        board, turn, castling, en_pas, half, full = fen.split()

        temp = ""
        for char in board:
            if char.isdigit():
                temp += "." * int(char)
            elif char == "/":
                temp += "-" * 8
            elif char.lower() in "rnbqkp":
                temp += char
        temp += "-" * 8

        self.board = temp
        self.turn = chess.WHITE if turn == "w" else chess.BLACK

        self.castling = castling
        self.half = int(half)
        self.full = int(full)

        self.fen = fen


if __name__ == "__main__":
    mb = Chessboard()
    for i in range(10):
        print(mb.perft(i))

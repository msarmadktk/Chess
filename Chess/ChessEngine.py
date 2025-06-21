# ChessEngine.py

from Chess import ChessMain

class GameState:
    """
    Class responsible for storing information about the current state of the game.
    The functions within this class are responsible for how moves are made, undone,
    determining valid moves given the current state, and keeping a move log.
    """

    def __init__(self):
        """
        The board is a 8x8 2d list. Each element has 2 characters.
        1st character represents the colour of the piece (b/w).
        2nd character represents the type of the piece.
        "--" represents an empty space with no piece.
        """
        self.board = [
            ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
            ['bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP'],
            ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR']
        ]
        self.move_functions = {
            'P': self.get_pawn_moves,
            'R': self.get_rook_moves,
            'N': self.get_knight_moves,
            'B': self.get_bishop_moves,
            'Q': self.get_queen_moves,
            'K': self.get_king_moves  # Castling call is omitted inside get_king_moves
        }
        self.white_to_move = True
        self.move_log = []
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.checkmate = False
        self.stalemate = False
        self.in_check = False
        self.pins = []
        self.checks = []

        # En passant
        self.en_passant_possible = ()  # Coordinates for square where en passant possible
        self.en_passant_possible_log = [self.en_passant_possible]

        # Castling rights are all False to disable castling
        self.white_castle_king_side = False
        self.white_castle_queen_side = False
        self.black_castle_king_side = False
        self.black_castle_queen_side = False
        self.castle_rights_log = [CastleRights(
            self.white_castle_king_side,
            self.black_castle_king_side,
            self.white_castle_queen_side,
            self.black_castle_queen_side
        )]

    def make_move(self, move):
        """Takes a move as a parameter, executes it, and updates move log"""
        self.board[move.start_row][move.start_column] = '--'
        self.board[move.end_row][move.end_column] = move.piece_moved
        self.move_log.append(move)

        if move.piece_moved == 'wK':
            self.white_king_location = (move.end_row, move.end_column)
        elif move.piece_moved == 'bK':
            self.black_king_location = (move.end_row, move.end_column)

        # Pawn promotion
        if move.is_pawn_promotion:
            # Automatically promote to Rook if allowed
            promoted_piece = 'R'
            self.board[move.end_row][move.end_column] = move.piece_moved[0] + promoted_piece

        # En passant capture
        if move.is_en_passant_move:
            self.board[move.start_row][move.end_column] = '--'

        # Update en passant possible square
        if move.piece_moved[1] == 'P' and abs(move.start_row - move.end_row) == 2:
            self.en_passant_possible = ((move.start_row + move.end_row) // 2, move.start_column)
        else:
            self.en_passant_possible = ()
        self.en_passant_possible_log.append(self.en_passant_possible)

        # Castling move: since castling is disabled, no move will ever have is_castle_move=True

        # Update castling rights (they remain False, but we keep log logic for consistency)
        self.update_castle_rights(move)
        self.castle_rights_log.append(CastleRights(
            self.white_castle_king_side,
            self.black_castle_king_side,
            self.white_castle_queen_side,
            self.black_castle_queen_side
        ))

        # Switch turn
        self.white_to_move = not self.white_to_move

    def undo_move(self):
        """Undoes last move made"""
        if len(self.move_log) != 0:
            move = self.move_log.pop()
            self.board[move.start_row][move.start_column] = move.piece_moved
            self.board[move.end_row][move.end_column] = move.piece_captured
            self.white_to_move = not self.white_to_move

            # Restore king positions
            if move.piece_moved == 'wK':
                self.white_king_location = (move.start_row, move.start_column)
            elif move.piece_moved == 'bK':
                self.black_king_location = (move.start_row, move.start_column)

            # Undo en passant
            if move.is_en_passant_move:
                self.board[move.end_row][move.end_column] = '--'
                self.board[move.start_row][move.end_column] = move.piece_captured
            self.en_passant_possible_log.pop()
            self.en_passant_possible = self.en_passant_possible_log[-1]

            # Undo castling rights
            self.castle_rights_log.pop()
            castle_rights = self.castle_rights_log[-1]
            self.white_castle_king_side = castle_rights.white_king_side
            self.black_castle_king_side = castle_rights.black_king_side
            self.white_castle_queen_side = castle_rights.white_queen_side
            self.black_castle_queen_side = castle_rights.black_queen_side

            # Undo castling move on board: never triggered here since no castling moves exist

            self.checkmate = False
            self.stalemate = False

    def get_valid_moves(self):
        """Gets all moves considering checks"""
        valid_moves = []
        self.in_check, self.pins, self.checks = self.check_for_pins_and_checks()

        if self.white_to_move:
            king_row, king_column = self.white_king_location
        else:
            king_row, king_column = self.black_king_location

        if self.in_check:
            if len(self.checks) == 1:
                valid_moves = self.get_all_possible_moves()
                check = self.checks[0]
                check_row, check_column = check[0], check[1]
                piece_checking = self.board[check_row][check_column]
                valid_squares = []
                if piece_checking[1] == 'N':
                    valid_squares = [(check_row, check_column)]
                else:
                    for i in range(1, len(self.board)):
                        valid_square = (king_row + check[2] * i, king_column + check[3] * i)
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[1] == check_column:
                            break
                for i in range(len(valid_moves) - 1, -1, -1):
                    if valid_moves[i].piece_moved[1] != 'K':
                        if not (valid_moves[i].end_row, valid_moves[i].end_column) in valid_squares:
                            valid_moves.remove(valid_moves[i])
            else:
                self.get_king_moves(king_row, king_column, valid_moves)
        else:
            valid_moves = self.get_all_possible_moves()

        if len(valid_moves) == 0:
            if self.in_check:
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        return valid_moves

    def get_all_possible_moves(self):
        """Gets all moves without considering checks"""
        moves = []
        for row in range(len(self.board)):
            for column in range(len(self.board[row])):
                turn = self.board[row][column][0]
                if (turn == 'w' and self.white_to_move) or (turn == 'b' and not self.white_to_move):
                    piece = self.board[row][column][1]
                    self.move_functions[piece](row, column, moves)
        return moves

    def get_pawn_moves(self, row, column, moves):
        """
        Gets all pawn moves for the pawn located at (row, column) and adds moves to move log.
        Only allows promotion if one of the side’s rooks has already been captured.
        """
        # 1) Count current rooks on board for this side
        white_rooks_onboard = sum(1 for r in self.board for piece in r if piece == 'wR')
        black_rooks_onboard = sum(1 for r in self.board for piece in r if piece == 'bR')

        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == column:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.white_to_move:
            move_amount = -1
            start_row = 6
            back_row = 0
            opponent = 'b'
            king_row, king_column = self.white_king_location
            rooks_alive = white_rooks_onboard
        else:
            move_amount = 1
            start_row = 1
            back_row = 7
            opponent = 'w'
            king_row, king_column = self.black_king_location
            rooks_alive = black_rooks_onboard

        # Determine if promotion is allowed: at least one rook of this color has died
        # (i.e., if rooks_alive < 2)
        promotion_allowed = (rooks_alive < 2)

        # One‐square forward
        if 0 <= row + move_amount < 8:
            if self.board[row + move_amount][column] == '--':
                if not piece_pinned or pin_direction == (move_amount, 0):
                    if row + move_amount == back_row and promotion_allowed:
                        moves.append(Move(
                            (row, column),
                            (row + move_amount, column),
                            self.board,
                            pawn_promotion=True
                        ))
                    elif row + move_amount != back_row:
                        moves.append(Move(
                            (row, column),
                            (row + move_amount, column),
                            self.board
                        ))
                # Two‐square forward
                if row == start_row and self.board[row + 2 * move_amount][column] == '--':
                    moves.append(Move(
                        (row, column),
                        (row + 2 * move_amount, column),
                        self.board
                    ))

        # Capture to the left
        if column - 1 >= 0 and 0 <= row + move_amount < 8:
            if not piece_pinned or pin_direction == (move_amount, -1):
                target = self.board[row + move_amount][column - 1]
                if target[0] == opponent:
                    if row + move_amount == back_row and promotion_allowed:
                        moves.append(Move(
                            (row, column),
                            (row + move_amount, column - 1),
                            self.board,
                            pawn_promotion=True
                        ))
                    elif row + move_amount != back_row:
                        moves.append(Move(
                            (row, column),
                            (row + move_amount, column - 1),
                            self.board
                        ))
                # En passant capture
                if (row + move_amount, column - 1) == self.en_passant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_column < column:
                            inside_range = range(king_column + 1, column - 1)
                            outside_range = range(column + 1, len(self.board))
                        else:
                            inside_range = range(king_column - 1, column, -1)
                            outside_range = range(column - 2, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != '--':
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == opponent and (square[1] == 'R' or square[1] == 'Q'):
                                attacking_piece = True
                            elif square != '--':
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move(
                            (row, column),
                            (row + move_amount, column - 1),
                            self.board,
                            en_passant=True
                        ))

        # Capture to the right
        if column + 1 < 8 and 0 <= row + move_amount < 8:
            if not piece_pinned or pin_direction == (move_amount, 1):
                target = self.board[row + move_amount][column + 1]
                if target[0] == opponent:
                    if row + move_amount == back_row and promotion_allowed:
                        moves.append(Move(
                            (row, column),
                            (row + move_amount, column + 1),
                            self.board,
                            pawn_promotion=True
                        ))
                    elif row + move_amount != back_row:
                        moves.append(Move(
                            (row, column),
                            (row + move_amount, column + 1),
                            self.board
                        ))
                # En passant capture
                if (row + move_amount, column + 1) == self.en_passant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_column < column:
                            inside_range = range(king_column + 1, column)
                            outside_range = range(column + 2, len(self.board))
                        else:
                            inside_range = range(king_column - 1, column + 1, -1)
                            outside_range = range(column - 1, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != '--':
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == opponent and (square[1] == 'R' or square[1] == 'Q'):
                                attacking_piece = True
                            elif square != '--':
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move(
                            (row, column),
                            (row + move_amount, column + 1),
                            self.board,
                            en_passant=True
                        ))

    def get_rook_moves(self, row, column, moves):
        """Gets all rook moves for the rook located at (row, column) and adds moves to move log"""
        opponent = 'b' if self.white_to_move else 'w'

        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == column:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                if self.board[row][column][1] != 'Q':
                    self.pins.remove(self.pins[i])
                break

        directions = [(-1, 0), (0, -1), (1, 0), (0, 1)]
        for d in directions:
            for i in range(1, len(self.board)):
                end_row = row + d[0] * i
                end_column = column + d[1] * i
                if 0 <= end_row < len(self.board) and 0 <= end_column < len(self.board):
                    if not piece_pinned or pin_direction == d or pin_direction == (-d[0], -d[1]):
                        end_piece = self.board[end_row][end_column]
                        if end_piece == '--':
                            moves.append(Move(
                                (row, column),
                                (end_row, end_column),
                                self.board
                            ))
                        elif end_piece[0] == opponent:
                            moves.append(Move(
                                (row, column),
                                (end_row, end_column),
                                self.board
                            ))
                            break
                        else:
                            break
                else:
                    break

    def get_knight_moves(self, row, column, moves):
        """Gets all knight moves for the knight located at (row, column) and adds moves to move log"""
        opponent = 'b' if self.white_to_move else 'w'
        piece_pinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == column:
                piece_pinned = True
                self.pins.remove(self.pins[i])
                break

        directions = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for d in directions:
            end_row = row + d[0]
            end_column = column + d[1]
            if 0 <= end_row < len(self.board) and 0 <= end_column < len(self.board):
                if not piece_pinned:
                    end_piece = self.board[end_row][end_column]
                    if end_piece[0] == opponent:
                        moves.append(Move((row, column), (end_row, end_column), self.board))
                    elif end_piece == '--':
                        moves.append(Move((row, column), (end_row, end_column), self.board))

    def get_bishop_moves(self, row, column, moves):
        """Gets all bishop moves for the bishop located at (row, column) and adds moves to move log"""
        opponent = 'b' if self.white_to_move else 'w'
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == column:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = [(-1, -1), (-1, 1), (1, 1), (1, -1)]
        for d in directions:
            for i in range(1, len(self.board)):
                end_row = row + d[0] * i
                end_column = column + d[1] * i
                if 0 <= end_row < len(self.board) and 0 <= end_column < len(self.board):
                    if not piece_pinned or pin_direction == d or pin_direction == (-d[0], -d[1]):
                        end_piece = self.board[end_row][end_column]
                        if end_piece == '--':
                            moves.append(Move((row, column), (end_row, end_column), self.board))
                        elif end_piece[0] == opponent:
                            moves.append(Move((row, column), (end_row, end_column), self.board))
                            break
                        else:
                            break
                else:
                    break

    def get_queen_moves(self, row, column, moves):
        """Gets all queen moves for the queen located at (row, column) and adds moves to move log"""
        self.get_bishop_moves(row, column, moves)
        self.get_rook_moves(row, column, moves)

    def get_king_moves(self, row, column, moves):
        """Gets all king moves for the king located at (row, column) and adds moves to move log (no castling)"""
        ally = 'w' if self.white_to_move else 'b'
        row_moves = (-1, -1, -1, 0, 0, 1, 1, 1)
        column_moves = (-1, 0, 1, -1, 1, -1, 0, 1)
        for i in range(len(self.board)):
            end_row = row + row_moves[i]
            end_column = column + column_moves[i]
            if 0 <= end_row < len(self.board) and 0 <= end_column < len(self.board):
                end_piece = self.board[end_row][end_column]
                if end_piece[0] != ally:
                    # Temporarily move king and check for checks
                    if ally == 'w':
                        self.white_king_location = (end_row, end_column)
                    else:
                        self.black_king_location = (end_row, end_column)
                    in_check, pins, checks = self.check_for_pins_and_checks()
                    if not in_check:
                        moves.append(Move((row, column), (end_row, end_column), self.board))
                    # Revert king location
                    if ally == 'w':
                        self.white_king_location = (row, column)
                    else:
                        self.black_king_location = (row, column)
        # No call to get_castle_moves – castling is disabled

    def update_castle_rights(self, move):
        """Updates castle rights given the move (castling disabled, so rights stay False)"""
        # No changes to any rights; they remain False
        pass

    def square_under_attack(self, row, column, ally):
        """Checks outward from a square to see if it is being attacked, thus invalidating castling"""
        opponent = 'b' if self.white_to_move else 'w'
        directions = (
            (-1, 0), (0, -1), (1, 0), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)
        )
        for j in range(len(directions)):
            d = directions[j]
            for i in range(1, len(self.board)):
                end_row = row + d[0] * i
                end_column = column + d[1] * i
                if 0 <= end_row < len(self.board) and 0 <= end_column < len(self.board):
                    end_piece = self.board[end_row][end_column]
                    if end_piece[0] == ally:
                        break
                    elif end_piece[0] == opponent:
                        piece_type = end_piece[1]
                        if (
                            (0 <= j <= 3 and piece_type == 'R') or
                            (4 <= j <= 7 and piece_type == 'B') or
                            (i == 1 and piece_type == 'P' and
                                ((opponent == 'w' and 6 <= j <= 7) or (opponent == 'b' and 4 <= j <= 5))
                            ) or
                            piece_type == 'Q' or
                            (i == 1 and piece_type == 'K')
                        ):
                            return True
                        else:
                            break
                else:
                    break
        knight_moves = (
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        )
        for m in knight_moves:
            end_row = row + m[0]
            end_column = column + m[1]
            if 0 <= end_row < len(self.board) and 0 <= end_column < len(self.board):
                end_piece = self.board[end_row][end_column]
                if end_piece[0] == opponent and end_piece[1] == 'N':
                    return True
        return False

    def check_for_pins_and_checks(self):
        """Returns if the player is in check, a list of pins, and a list of checks"""
        pins = []
        checks = []
        in_check = False

        if self.white_to_move:
            opponent = 'b'
            ally = 'w'
            start_row, start_column = self.white_king_location
        else:
            opponent = 'w'
            ally = 'b'
            start_row, start_column = self.black_king_location

        directions = (
            (-1, 0), (0, -1), (1, 0), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)
        )
        for j in range(len(directions)):
            d = directions[j]
            possible_pin = ()
            for i in range(1, len(self.board)):
                end_row = start_row + d[0] * i
                end_column = start_column + d[1] * i
                if 0 <= end_row < len(self.board) and 0 <= end_column < len(self.board):
                    end_piece = self.board[end_row][end_column]
                    if end_piece[0] == ally and end_piece[1] != 'K':
                        if possible_pin == ():
                            possible_pin = (end_row, end_column, d[0], d[1])
                        else:
                            break
                    elif end_piece[0] == opponent:
                        piece_type = end_piece[1]
                        if (
                            (0 <= j <= 3 and piece_type == 'R') or
                            (4 <= j <= 7 and piece_type == 'B') or
                            (i == 1 and piece_type == 'P' and
                                ((opponent == 'w' and 6 <= j <= 7) or (opponent == 'b' and 4 <= j <= 5))
                            ) or
                            piece_type == 'Q' or
                            (i == 1 and piece_type == 'K')
                        ):
                            if possible_pin == ():
                                in_check = True
                                checks.append((end_row, end_column, d[0], d[1]))
                                break
                            else:
                                pins.append(possible_pin)
                                break
                        else:
                            break
                else:
                    break

        knight_moves = (
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        )
        for m in knight_moves:
            end_row = start_row + m[0]
            end_column = start_column + m[1]
            if 0 <= end_row < len(self.board) and 0 <= end_column < len(self.board):
                end_piece = self.board[end_row][end_column]
                if end_piece[0] == opponent and end_piece[1] == 'N':
                    in_check = True
                    checks.append((end_row, end_column, m[0], m[1]))

        return in_check, pins, checks


class CastleRights:
    """Data storage of current states of castling rights"""

    def __init__(self, white_king_side, black_king_side, white_queen_side, black_queen_side):
        self.white_king_side = white_king_side
        self.black_king_side = black_king_side
        self.white_queen_side = white_queen_side
        self.black_queen_side = black_queen_side


class Move:
    """
    Class responsible for storing information about particular moves,
    including starting and ending positions, which pieces were moved and captured,
    and special moves such as en passant, pawn promotion, and castling.
    """
    ranks_to_rows = {'1': 7, '2': 6, '3': 5, '4': 4,
                     '5': 3, '6': 2, '7': 1, '8': 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_columns = {'a': 0, 'b': 1, 'c': 2, 'd': 3,
                        'e': 4, 'f': 5, 'g': 6, 'h': 7}
    columns_to_files = {v: k for k, v in files_to_columns.items()}

    def __init__(self, start_square, end_square, board, en_passant=False, pawn_promotion=False, castle=False):
        self.start_row, self.start_column = start_square
        self.end_row, self.end_column = end_square
        self.piece_moved = board[self.start_row][self.start_column]
        self.piece_captured = board[self.end_row][self.end_column]
        self.is_pawn_promotion = pawn_promotion

        # En passant
        self.is_en_passant_move = en_passant
        if self.is_en_passant_move:
            self.piece_captured = 'wP' if self.piece_moved == 'bP' else 'bP'

        # Castling flag (never used since castling is disabled)
        self.is_castle_move = castle
        self.is_capture = (self.piece_captured != '--')
        self.move_id = (self.start_row * 1000 +
                        self.start_column * 100 +
                        self.end_row * 10 +
                        self.end_column)

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move_id == other.move_id
        return False

    def get_chess_notation(self):
        return (self.get_rank_file(self.start_row, self.start_column) +
                self.get_rank_file(self.end_row, self.end_column))

    def get_rank_file(self, row, col):
        return self.columns_to_files[col] + self.rows_to_ranks[row]

    def __str__(self):
        # Castling (never used)
        if self.is_castle_move:
            return 'O-O' if self.end_column == 6 else 'O-O-O'

        end_sq = self.get_rank_file(self.end_row, self.end_column)

        # Pawn moves
        if self.piece_moved[1] == 'P':
            if self.is_capture and self.is_pawn_promotion:
                return f'{end_sq}=R'
            elif self.is_capture:
                return f'{self.columns_to_files[self.start_column]}x{end_sq}'
            else:
                return end_sq

        # Other piece moves
        move_str = self.piece_moved[1]
        if self.is_capture:
            move_str += 'x'
        return f'{move_str}{end_sq}'

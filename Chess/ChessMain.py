import os
import pygame as p
from Chess import ChessEngine, ChessAI

# Player settings
player_one = True   # Human plays White
player_two = False  # Human plays Black (unused here)

p.init()

# Window dimensions
board_width = board_height = 680
move_log_panel_width = 210
move_log_panel_height = board_height
dimension = 8
sq_size = board_height // dimension
max_fps = 15
colours = [p.Color('#EBEBD0'), p.Color('#769455')]
images = {}

# Globals for customization
time_limit_minutes = None  # None == infinite
# ChessAI.set_depth will be set in customization


def load_images():
    """Load all piece PNGs from Chess/images."""
    script_dir = os.path.dirname(__file__)
    image_dir = os.path.join(script_dir, 'images')
    pieces = [
        'bR','bN','bB','bQ','bK','bB','bN','bR','bP',
        'wR','wN','wB','wQ','wK','wB','wN','wR','wP'
    ]
    for piece in pieces:
        path = os.path.join(image_dir, f'{piece}.png')
        images[piece] = p.transform.smoothscale(
            p.image.load(path), (sq_size, sq_size)
        )


def show_start_screen():
    """Display start_screen.png, wait for P (Play) or Q (Quit)."""
    script_dir = os.path.dirname(__file__)
    image_dir = os.path.join(script_dir, 'images')
    start_path = os.path.join(image_dir, 'start_screen.png')
    window_w = board_width + move_log_panel_width
    window_h = board_height
    screen = p.display.set_mode((window_w, window_h))
    raw_img = p.image.load(start_path)
    bg = p.transform.smoothscale(raw_img, (window_w, window_h))
    font = p.font.SysFont('Arial', 36, True)

    while True:
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                exit()
            elif event.type == p.KEYDOWN:
                if event.key == p.K_q:
                    p.quit()
                    exit()
                elif event.key == p.K_p:
                    return
        screen.blit(bg, (0, 0))
        p.display.flip()


def show_customize_screen():
    """
    Step 1: Enter AI difficulty (1–5) → ChessAI.set_depth.
    Step 2: Enter timer (minutes) or 'I' → time_limit_minutes.
    """
    global time_limit_minutes
    window_w = board_width + move_log_panel_width
    window_h = board_height
    screen = p.display.set_mode((window_w, window_h))
    font = p.font.SysFont('Arial', 28)
    clock = p.time.Clock()

    # Phase 1: AI difficulty
    prompt1 = "Enter AI difficulty (1–5): "
    user_input = ""
    phase = 1
    while True:
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                exit()
            elif event.type == p.KEYDOWN:
                if event.key == p.K_RETURN:
                    if user_input in ['1', '2', '3', '4', '5']:
                        ChessAI.set_depth = int(user_input)
                        user_input = ""
                        phase = 2
                elif event.key == p.K_BACKSPACE:
                    user_input = user_input[:-1]
                else:
                    ch = event.unicode
                    if phase == 1 and ch.isdigit() and len(user_input) < 1:
                        user_input += ch
        screen.fill(p.Color('#3bb371'))
        if phase == 1:
            txt = font.render(prompt1 + user_input, True, p.Color('white'))
            screen.blit(txt, (20, window_h // 2 - 20))
        p.display.flip()
        if phase == 2:
            break
        clock.tick(30)

    # Phase 2: Timer
    prompt2 = "Enter timer (minutes) or I for infinite: "
    while True:
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                exit()
            elif event.type == p.KEYDOWN:
                if event.key == p.K_RETURN:
                    if user_input.isdigit() and int(user_input) >= 1:
                        time_limit_minutes = int(user_input)
                        return
                    elif user_input.lower() == 'i':
                        time_limit_minutes = None
                        return
                elif event.key == p.K_BACKSPACE:
                    user_input = user_input[:-1]
                else:
                    ch = event.unicode
                    if (ch.isdigit() and len(user_input) < 3) or (
                        ch.lower() == 'i' and user_input == ""
                    ):
                        user_input += ch
        screen.fill(p.Color('#3bb371'))
        txt = font.render(prompt2 + user_input, True, p.Color('white'))
        screen.blit(txt, (20, window_h // 2 - 20))
        p.display.flip()
        clock.tick(30)


def main():
    """1) Start screen, 2) Customization, 3) Chess loop with timers, AI difficulty, and buttons."""
    show_start_screen()
    show_customize_screen()

    screen = p.display.set_mode((board_width + move_log_panel_width, board_height))
    clock = p.time.Clock()
    load_images()
    move_log_font = p.font.SysFont('Arial', 14, False, False)
    game_state = ChessEngine.GameState()
    valid_moves = game_state.get_valid_moves()
    move_made = False
    animate = False
    square_selected = ()
    player_clicks = []
    pending_move = None
    game_over = False

    # Stacks to track fallen pieces by color (excluding kings)
    fallen_white = []
    fallen_black = []

    # Initialize timers (in seconds). None == infinite.
    if time_limit_minutes is None:
        white_time = None
        black_time = None
    else:
        total_secs = time_limit_minutes * 60
        white_time = total_secs
        black_time = total_secs

    last_tick = p.time.get_ticks()

    # Precompute End Turn button rect
    btn_x = board_width + 20
    btn_y = board_height - 60
    btn_w = move_log_panel_width - 40
    btn_h = 40
    end_btn = p.Rect(btn_x, btn_y, btn_w, btn_h)
    btn_font = p.font.SysFont('Arial', 20, True)

    while True:
        now = p.time.get_ticks()
        delta = (now - last_tick) / 1000.0  # seconds since last frame
        last_tick = now

        # Update timers for whoever is to move (even AI)
        if not game_over and white_time is not None and game_state.white_to_move:
            white_time = max(0, white_time - delta)
        elif not game_over and black_time is not None and not game_state.white_to_move:
            black_time = max(0, black_time - delta)

        human_turn = (
            (game_state.white_to_move and player_one) or
            (not game_state.white_to_move and player_two)
        )

        # Determine extra action based on selected piece
        extra_action = None
        extra_btn = None
        if square_selected != () and human_turn:
            r, c = square_selected
            piece = game_state.board[r][c]
            # Ensure it's the human's piece
            if (piece.startswith('w') and game_state.white_to_move and player_one) or \
               (piece.startswith('b') and not game_state.white_to_move and player_two):
                p_type = piece[1]
                if p_type == 'P':
                    extra_action = 'Starve'
                    extra_btn = p.Rect(btn_x, btn_y - 50, btn_w, btn_h)
                elif p_type == 'N':
                    extra_action = 'Mimic'
                    extra_btn = p.Rect(btn_x, btn_y - 50, btn_w, btn_h)
                elif p_type == 'B':
                    extra_action = 'Detonate'
                    extra_btn = p.Rect(btn_x, btn_y - 50, btn_w, btn_h)
                elif p_type == 'R':
                    extra_action = 'Defect'
                    extra_btn = p.Rect(btn_x, btn_y - 50, btn_w, btn_h)
                elif p_type in ('K', 'Q'):
                    extra_action = 'Teleswap'
                    extra_btn = p.Rect(btn_x, btn_y - 50, btn_w, btn_h)

        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                exit()

            elif event.type == p.MOUSEBUTTONDOWN:
                mx, my = p.mouse.get_pos()

                # 1) Did we click End Turn?
                if end_btn.collidepoint(mx, my):
                    if pending_move and human_turn and not game_over:
                        # Before making move, record captured piece if any
                        captured = pending_move.piece_captured
                        if captured != '--' and captured[1] != 'K':
                            if captured[0] == 'w':
                                fallen_white.append(captured)
                            else:
                                fallen_black.append(captured)
                        game_state.make_move(pending_move)
                        pending_move = None
                        move_made = True
                        animate = True
                        square_selected = ()
                        player_clicks = []

                # 2) Did we click Starve?
                elif extra_btn and extra_btn.collidepoint(mx, my) and extra_action == 'Starve':
                    if square_selected != ():
                        r, c = square_selected
                        piece = game_state.board[r][c]
                        if piece.endswith('P'):
                            # Record that pawn as fallen
                            if piece.startswith('w'):
                                fallen_white.append(piece)
                            else:
                                fallen_black.append(piece)
                            # Remove pawn
                            game_state.board[r][c] = '--'
                            # Do NOT flip turn here
                            square_selected = ()
                            player_clicks = []
                            valid_moves = game_state.get_valid_moves()

                # 3) Did we click Mimic?
                elif extra_btn and extra_btn.collidepoint(mx, my) and extra_action == 'Mimic':
                    if square_selected != ():
                        r, c = square_selected
                        piece = game_state.board[r][c]
                        color = 'w' if piece.startswith('w') else 'b'
                        # Determine appropriate fallen stack
                        stack = fallen_white if color == 'w' else fallen_black
                        if len(stack) == 0:
                            # Do nothing if no fallen comrade
                            square_selected = ()
                            player_clicks = []
                        else:
                            # Only replace if it's still a knight
                            if piece[1] == 'N':
                                # Pop most recent fallen comrade
                                new_piece = stack.pop()
                                # Now capture this knight as fallen
                                fallen = f"{color}N"
                                if color == 'w':
                                    fallen_white.append(fallen)
                                    # Replace knight with the popped piece
                                    game_state.board[r][c] = new_piece
                                else:
                                    fallen_black.append(fallen)
                                    game_state.board[r][c] = new_piece
                                # Do NOT flip turn here
                                square_selected = ()
                                player_clicks = []
                                valid_moves = game_state.get_valid_moves()

                # 4) Did we click Detonate?
                elif extra_btn and extra_btn.collidepoint(mx, my) and extra_action == 'Detonate':
                    if square_selected != ():
                        r, c = square_selected
                        # Loop over 3x3 centered on (r,c)
                        for dr in (-1, 0, 1):
                            for dc in (-1, 0, 1):
                                rr = r + dr
                                cc = c + dc
                                if 0 <= rr < dimension and 0 <= cc < dimension:
                                    target = game_state.board[rr][cc]
                                    if target == '--':
                                        continue
                                    # If it's a king, mark in_check
                                    if target[1] == 'K':
                                        game_state.in_check = True
                                    else:
                                        # Record fallen piece
                                        if target[0] == 'w':
                                            fallen_white.append(target)
                                        else:
                                            fallen_black.append(target)
                                    # Remove (unless it's a king)
                                    if target[1] != 'K':
                                        game_state.board[rr][cc] = '--'
                        # After detonation, update valid moves
                        square_selected = ()
                        player_clicks = []
                        valid_moves = game_state.get_valid_moves()

                # 5) Did we click Defect?
                elif extra_btn and extra_btn.collidepoint(mx, my) and extra_action == 'Defect':
                    if square_selected != ():
                        r, c = square_selected
                        piece = game_state.board[r][c]
                        color = 'w' if piece.startswith('w') else 'b'
                        # Determine appropriate fallen stack
                        stack = fallen_white if color == 'w' else fallen_black
                        # Check all 8 adjacent squares for enemy Pawn/ Knight/ Bishop
                        for dr, dc in [(-1, -1), (-1, 0), (-1, 1),
                                       (0, -1),           (0, 1),
                                       (1, -1),  (1, 0),  (1, 1)]:
                            rr = r + dr
                            cc = c + dc
                            if 0 <= rr < dimension and 0 <= cc < dimension:
                                target = game_state.board[rr][cc]
                                if target == '--':
                                    continue
                                # Must be enemy pawn ('P'), knight ('N') or bishop ('B')
                                if target[0] != color and target[1] in ('P', 'N', 'B'):
                                    needed = color + target[1]  # e.g., 'wN'
                                    if needed in stack:
                                        # Remove enemy piece
                                        if target[0] == 'w':
                                            fallen_white.append(target)
                                        else:
                                            fallen_black.append(target)
                                        # Remove from our fallen stack
                                        stack.remove(needed)
                                        # Place our piece at rr,cc
                                        game_state.board[rr][cc] = needed
                        square_selected = ()
                        player_clicks = []
                        valid_moves = game_state.get_valid_moves()

                # 6) Did we click Teleswap?
                elif extra_btn and extra_btn.collidepoint(mx, my) and extra_action == 'Teleswap':
                    if square_selected != ():
                        r, c = square_selected
                        piece = game_state.board[r][c]
                        color = 'w' if piece.startswith('w') else 'b'
                        p_type = piece[1]  # 'K' or 'Q'
                        # Find the other (K or Q) of same color
                        other_type = 'Q' if p_type == 'K' else 'K'
                        other_loc = None
                        for rr in range(dimension):
                            for cc in range(dimension):
                                p2 = game_state.board[rr][cc]
                                if p2 == f"{color}{other_type}":
                                    other_loc = (rr, cc)
                                    break
                            if other_loc:
                                break
                        if other_loc:
                            orow, ocol = other_loc
                            # Swap positions
                            game_state.board[orow][ocol], game_state.board[r][c] = (
                                game_state.board[r][c],
                                game_state.board[orow][ocol]
                            )
                            # Do NOT flip turn here
                        square_selected = ()
                        player_clicks = []
                        valid_moves = game_state.get_valid_moves()

                else:
                    # 7) Board selection (only if human_turn and not game over)
                    if human_turn and not game_over:
                        column = mx // sq_size
                        row = my // sq_size
                        if column < dimension and row < dimension:
                            if square_selected == (row, column):
                                square_selected = ()
                                player_clicks = []
                            else:
                                square_selected = (row, column)
                                player_clicks.append(square_selected)
                            if len(player_clicks) == 2:
                                move = ChessEngine.Move(
                                    player_clicks[0],
                                    player_clicks[1],
                                    game_state.board
                                )
                                for i in range(len(valid_moves)):
                                    if move == valid_moves[i]:
                                        pending_move = valid_moves[i]
                                        break
                                square_selected = ()
                                player_clicks = []

            elif event.type == p.KEYDOWN:
                if event.key == p.K_z:  # Undo (only if no pending_move)
                    if not pending_move:
                        game_state.undo_move()
                        move_made = True
                        animate = False
                        game_over = False
                elif event.key == p.K_r:  # Reset entirely
                    game_state = ChessEngine.GameState()
                    valid_moves = game_state.get_valid_moves()
                    square_selected = ()
                    player_clicks = []
                    pending_move = None
                    move_made = False
                    animate = False
                    game_over = False
                    fallen_white.clear()
                    fallen_black.clear()
                    # Reset clocks
                    if time_limit_minutes is None:
                        white_time = None
                        black_time = None
                    else:
                        white_time = total_secs
                        black_time = total_secs
                    last_tick = p.time.get_ticks()

        # AI move (when it’s AI’s turn and no pending player move)
        if not game_over and not human_turn and not pending_move:
            AI_move = ChessAI.find_best_move(game_state, valid_moves)
            if AI_move is None:
                AI_move = ChessAI.find_random_move(valid_moves)
            # Record captured piece if any
            captured = AI_move.piece_captured
            if captured != '--' and captured[1] != 'K':
                if captured[0] == 'w':
                    fallen_white.append(captured)
                else:
                    fallen_black.append(captured)
            game_state.make_move(AI_move)
            move_made = True
            animate = True

        if move_made:
            if animate:
                animate_move(
                    game_state.move_log[-1], screen, game_state.board, clock
                )
            valid_moves = game_state.get_valid_moves()
            move_made = False
            animate = False

        # Draw everything
        draw_game_state(
            screen, game_state, square_selected, pending_move,
            white_time, black_time, ChessAI.set_depth,
            move_log_font, end_btn, btn_font, extra_btn, extra_action,
            # No show_message parameter any more
        )

        if (game_state.checkmate or game_state.stalemate) and not game_over:
            game_over = True

        clock.tick(max_fps)
        p.display.flip()


def draw_game_state(
    screen, game_state, square_selected, pending_move,
    white_time, black_time, ai_diff, move_log_font,
    end_btn, btn_font, extra_btn, extra_action
):
    """Draw board, highlights, timers, AI diff, move log, End Turn, and action buttons."""
    draw_board(screen)
    highlight_squares(screen, game_state, square_selected)
    if pending_move:
        highlight_pending(screen, pending_move)
    draw_pieces(screen, game_state.board)
    draw_right_panel(
        screen, game_state, square_selected, white_time, black_time,
        ai_diff, move_log_font, end_btn, btn_font, extra_btn, extra_action
    )


def draw_board(screen):
    """Draw board squares."""
    for row in range(dimension):
        for column in range(dimension):
            colour = colours[(row + column) % 2]
            p.draw.rect(
                screen, colour,
                p.Rect(column * sq_size, row * sq_size, sq_size, sq_size)
            )


def highlight_squares(screen, game_state, square_selected):
    """Highlight selected square and last move."""
    if square_selected != ():
        row, column = square_selected
        if game_state.board[row][column][0] == (
            'w' if game_state.white_to_move else 'b'
        ):
            s = p.Surface((sq_size, sq_size))
            s.set_alpha(70)
            s.fill(p.Color('yellow'))
            screen.blit(s, (column * sq_size, row * sq_size))

    if len(game_state.move_log) != 0:
        last_move = game_state.move_log[-1]
        start_row, start_column = last_move.start_row, last_move.start_column
        end_row, end_column = last_move.end_row, last_move.end_column
        s = p.Surface((sq_size, sq_size))
        s.set_alpha(70)
        s.fill(p.Color('yellow'))
        screen.blit(s, (start_column * sq_size, start_row * sq_size))
        screen.blit(s, (end_column * sq_size, end_column * sq_size))


def highlight_pending(screen, pending_move):
    """Highlight pending move in green until End Turn is pressed."""
    s = p.Surface((sq_size, sq_size))
    s.set_alpha(100)
    s.fill(p.Color('green'))
    screen.blit(s, (pending_move.start_column * sq_size, pending_move.start_row * sq_size))
    screen.blit(s, (pending_move.end_column * sq_size, pending_move.end_row * sq_size))


def draw_right_panel(
    screen, game_state, square_selected,
    white_time, black_time, ai_diff,
    font, end_btn, btn_font, extra_btn, extra_action
):
    """Draw timers, AI difficulty, move log, End Turn button, and action button."""
    panel_x = board_width
    p.draw.rect(
        screen, p.Color('#2d2d2e'),
        p.Rect(panel_x, 0, move_log_panel_width, move_log_panel_height)
    )

    # Timers & AI diff
    timer_font = p.font.SysFont('Arial', 16, True)
    y_offset = 10
    x_offset = panel_x + 10

    if white_time is None:
        wt_text = "White Time: ∞"
    else:
        m, s = divmod(int(white_time), 60)
        wt_text = f"White Time: {m:02d}:{s:02d}"
    txt_w = timer_font.render(wt_text, True, p.Color('white'))
    screen.blit(txt_w, (x_offset, y_offset))

    if black_time is None:
        bt_text = "Black Time: ∞"
    else:
        m, s = divmod(int(black_time), 60)
        bt_text = f"Black Time: {m:02d}:{s:02d}"
    txt_b = timer_font.render(bt_text, True, p.Color('white'))
    screen.blit(txt_b, (x_offset, y_offset + 25))

    diff_text = f"AI Diff: {ai_diff}"
    txt_d = timer_font.render(diff_text, True, p.Color('white'))
    screen.blit(txt_d, (x_offset, y_offset + 50))

    # Draw move log below
    draw_move_log(screen, game_state, font)

    # Draw extra action button if applicable
    if extra_btn and extra_action == 'Starve':
        p.draw.rect(screen, p.Color('#444444'), extra_btn)
        label = btn_font.render("Starve", True, p.Color('white'))
        lbl_rect = label.get_rect(
            center=(extra_btn.x + extra_btn.w // 2, extra_btn.y + extra_btn.h // 2)
        )
        screen.blit(label, lbl_rect)
    elif extra_btn and extra_action == 'Mimic':
        p.draw.rect(screen, p.Color('#444444'), extra_btn)
        label = btn_font.render("Mimic", True, p.Color('white'))
        lbl_rect = label.get_rect(
            center=(extra_btn.x + extra_btn.w // 2, extra_btn.y + extra_btn.h // 2)
        )
        screen.blit(label, lbl_rect)
    elif extra_btn and extra_action == 'Detonate':
        p.draw.rect(screen, p.Color('#444444'), extra_btn)
        label = btn_font.render("Detonate", True, p.Color('white'))
        lbl_rect = label.get_rect(
            center=(extra_btn.x + extra_btn.w // 2, extra_btn.y + extra_btn.h // 2)
        )
        screen.blit(label, lbl_rect)
    elif extra_btn and extra_action == 'Defect':
        p.draw.rect(screen, p.Color('#444444'), extra_btn)
        label = btn_font.render("Defect", True, p.Color('white'))
        lbl_rect = label.get_rect(
            center=(extra_btn.x + extra_btn.w // 2, extra_btn.y + extra_btn.h // 2)
        )
        screen.blit(label, lbl_rect)
    elif extra_btn and extra_action == 'Teleswap':
        p.draw.rect(screen, p.Color('#444444'), extra_btn)
        label = btn_font.render("Teleswap", True, p.Color('white'))
        lbl_rect = label.get_rect(
            center=(extra_btn.x + extra_btn.w // 2, extra_btn.y + extra_btn.h // 2)
        )
        screen.blit(label, lbl_rect)

    # Draw “End Turn” button at bottom
    p.draw.rect(screen, p.Color('#555555'), end_btn)
    label = btn_font.render("End Turn", True, p.Color('white'))
    lbl_rect = label.get_rect(
        center=(end_btn.x + end_btn.w // 2, end_btn.y + end_btn.h // 2)
    )
    screen.blit(label, lbl_rect)


def draw_move_log(screen, game_state, font):
    """Draw the move log (below timers)."""
    move_log_area = p.Rect(board_width, 80, move_log_panel_width, move_log_panel_height - 80)
    p.draw.rect(screen, p.Color('#2d2d2e'), move_log_area)
    move_log = game_state.move_log
    move_texts = []
    for i in range(0, len(move_log), 2):
        move_string = f'{i // 2 + 1}. {str(move_log[i])} '
        if i + 1 < len(move_log):
            move_string += f'{str(move_log[i + 1])} '
        move_texts.append(move_string)

    move_per_row = 2
    padding = 5
    line_spacing = 2
    text_y = 85
    for i in range(0, len(move_texts), move_per_row):
        text = ''
        for j in range(move_per_row):
            if i + j < len(move_texts):
                text += move_texts[i + j]
        text_object = font.render(text, True, p.Color('whitesmoke'))
        screen.blit(text_object, (board_width + padding, text_y))
        text_y += text_object.get_height() + line_spacing


def animate_move(move, screen, board, clock):
    """Animates a move smoothly."""
    delta_row = move.end_row - move.start_row
    delta_column = move.end_column - move.start_column
    frames_per_square = 5
    frame_count = (abs(delta_row) + abs(delta_column)) * frames_per_square

    for frame in range(frame_count + 1):
        row = move.start_row + delta_row * frame / frame_count
        column = move.start_column + delta_column * frame / frame_count
        draw_board(screen)
        draw_pieces(screen, board)

        # Erase destination square
        colour = colours[(move.end_row + move.end_column) % 2]
        end_sq = p.Rect(
            move.end_column * sq_size,
            move.end_row * sq_size,
            sq_size, sq_size
        )
        p.draw.rect(screen, colour, end_sq)

        # Draw captured piece if any
        if move.piece_captured != '--':
            if move.is_en_passant_move:
                en_passant_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                end_sq = p.Rect(
                    move.end_column * sq_size,
                    en_passant_row * sq_size,
                    sq_size, sq_size
                )
            screen.blit(images[move.piece_captured], end_sq)

        # Draw moving piece
        screen.blit(
            images[move.piece_moved],
            p.Rect(column * sq_size, row * sq_size, sq_size, sq_size)
        )

        p.display.flip()
        clock.tick(60)


def draw_pieces(screen, board):
    """Draw pieces onto board."""
    for row in range(dimension):
        for column in range(dimension):
            piece = board[row][column]
            if piece != '--':
                screen.blit(
                    images[piece],
                    p.Rect(column * sq_size, row * sq_size, sq_size, sq_size)
                )


def draw_endgame_text(screen, text):
    """Show endgame text (checkmate/stalemate)."""
    font = p.font.SysFont('Helvetica', 32, True, False)
    text_obj = font.render(text, True, p.Color('gray'), p.Color('mintcream'))
    text_loc = p.Rect(0, 0, board_width, board_height).move(
        board_width / 2 - text_obj.get_width() / 2,
        board_height / 2 - text_obj.get_height() / 2
    )
    screen.blit(text_obj, text_loc)
    shadow = font.render(text, True, p.Color('black'))
    screen.blit(shadow, text_loc.move(2, 2))


if __name__ == '__main__':
    main()

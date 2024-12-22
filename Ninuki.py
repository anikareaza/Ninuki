#!/usr/bin/python3
# Set the path to your python3 above

"""
Go0 random Go player
"""

from gtp_connection import GtpConnection
from board_base import DEFAULT_SIZE, GO_POINT, GO_COLOR
from board import GoBoard
from board_util import GoBoardUtil
from engine import GoEngine
import random
from board import GoBoard, BLACK, WHITE, EMPTY, GO_COLOR
from board_base import GO_COLOR, opponent, EMPTY

class Go0(GoEngine):
    def __init__(self, num_simulations=10) -> None:
        """
        Go player that selects moves randomly from the set of legal moves.
        Does not use the fill-eye filter.
        Passes only if there is no other legal move.
        """
        GoEngine.__init__(self, "Go0", 1.0)
        self.num_simulations = num_simulations
        
        
        
        
    # to switch 
    def get_best_move(self, board: GoBoard, color: GO_COLOR) -> int:
        rule_based_moves = self.generate_moves_based_on_rules(board, color)
        if rule_based_moves:
            return random.choice(rule_based_moves)
        else:
            return self.simulation_based_move(board, color)
        
        
    # simulation based move
    def simulation_based_move(self, board: GoBoard, color: GO_COLOR) -> int:
        legal_moves = GoBoardUtil.generate_legal_moves(board, color)
        best_move = None
        best_win_rate = -1

        for move in legal_moves:
            wins = 0
            for _ in range(self.num_simulations):
                board_copy = board.copy()
                board_copy.play_move(move, color)
                winner = self.simulate_game(board_copy)
                if winner == color:
                    wins += 1

            win_rate = wins / self.num_simulations
            if win_rate > best_win_rate:
                best_move = move
                best_win_rate = win_rate
            elif win_rate == best_win_rate and random.random() < 0.5:
                # Randomly break ties
                best_move = move

        return best_move
    
    

    def simulate_game(self, board: GoBoard) -> GO_COLOR:
        #  how do we check end of game? is it from board.check_game_end():
        # current player check
        # board.check_winner() func built in board
        while not board.check_game_end():
            legal_moves = GoBoardUtil.generate_legal_moves(board, board.current_player)
            if not legal_moves:
                # maybe that's the way to pass turns check board pass_move() in board
                board.pass_move()
            else:
                random_move = random.choice(legal_moves)
                board.play_move(random_move, board.current_player)

        return board.check_winner()
    
    


    # rule-based simulations   
    def generate_moves_based_on_rules(self, board: GoBoard, color: GO_COLOR) -> list:
        # Rule 1: Win
        # winning by five (or more) in a row, as well as winning by ten or more captures.
        winning_moves = self.get_winning_moves(board, color)
        if winning_moves:
            return [random.choice(winning_moves)]

        # Rule 2: BlockWin
        block_win_moves = self.get_block_win_moves(board, color)
        if block_win_moves:
            return [random.choice(block_win_moves)]

        # Rule 3: OpenFour
        open_four_moves = self.get_open_four_moves(board, color)
        if open_four_moves:
            return [random.choice(open_four_moves)]

        # Rule 4: Capture
        capture_moves = self.get_capture_moves(board, color)
        if capture_moves:
            return [random.choice(capture_moves)]

        
        
        # Rule 5: Random done
        legal_moves = GoBoardUtil.generate_legal_moves(board, color)
        return legal_moves

    # maybe right?
    def get_winning_moves(self, board: GoBoard, color: GO_COLOR) -> list:
        winning_moves = []

        #  five or more in a row
        result = board.detect_five_in_a_row()
        if result == color:
            winning_moves.append(board.last_move) 

        #  ten or more captures
        if board.get_captures(color) >= 10:
            winning_moves.append(board.last_move)  

        return winning_moves

    def get_block_win_moves(self, board: GoBoard, color: GO_COLOR) -> list:
        #  get moves that block the opponent's winning move
        pass

    def get_open_four_moves(self, board: GoBoard, color: GO_COLOR) -> list:
        #  get moves that create an open-four position
        pass
    def open_four(self, board: GoBoard, color):
        size = board.size
        for x in range(size):
            for y in range(size):
                if board.get_color(x, y) == EMPTY:
                
                    #check horizontal for x.xx
                    if (
                    (x - 1 >= 0 and board.get_color(x - 1, y) == color) and
                    (x + 1 < size and board.get_color(x + 1, y) == color) and
                    (x + 2 < size and board.get_color(x + 2, y) == color)
                ):
                        return True
                    if ( #horizontal for xx.x
                    (x - 1 >= 0 and board.get_color(x - 1, y) == color) and
                    (x + 1 < size and board.get_color(x + 1, y) == color) and
                    (x - 2 < size and board.get_color(x - 2, y) == color)
                ):
                        return True
                    if ( #horizontal for xxx.
                    (x - 3 >= 0 and board.get_color(x - 3, y) == color) and
                    (x - 1 < size and board.get_color(x - 1, y) == color) and
                    (x - 2 < size and board.get_color(x - 2, y) == color)
                ):
                        return True
                    if ( #horizontal for .xxx
                    (x + 1 < size and board.get_color(x +1, y) == color) and
                    (x + 3 < size and board.get_color(x + 3, y) == color) and
                    (x + 2 < size and board.get_color(x + 2, y) == color)
                ):
                        return True
                    
                # Check vertically for x.xx
                    if (
                    (y - 1 >= 0 and board.get_color(x, y - 1) == color) and
                    (y + 1 < size and board.get_color(x, y + 1) == color) and
                    (y + 2 < size and board.get_color(x, y + 2) == color)
                ):
                        return True
                    # Check vertically for xx.x
                    if (
                    (y - 1 >= 0 and board.get_color(x, y - 1) == color) and
                    (y + 1 < size and board.get_color(x, y + 1) == color) and
                    (y - 2 >= 0 and board.get_color(x, y - 2) == color)
                ):
                        return True
                # check vertically for .xxx
                    if (
                    (y +2 < size and board.get_color(x, y +2) == color) and
                    (y + 3 < size and board.get_color(x, y + 3) == color) and
                    (y + 1 < size and board.get_color(x, y + 1) == color) 
                ):
                        return True
                    # Check vertically for xxx.
                    if (
                    (y - 1 >= 0 and board.get_color(x, y - 1) == color) and
                    (y - 3 >=0 and board.get_color(x, y -3) == color) and
                    (y - 2 >=0 and board.get_color(x, y - 2) == color)
                ):
                        return True

                # Check diagonally (left down to right up) for x.xx
                    if (
                    (x + 1 < size and y +1 < size and board.get_color(x + 1, y +1) == color) and
                    (x - 1 >= 0 and y -1 >=0 and board.get_color(x - 1, y -1) == color) and
                    (x + 2 < size and y + 2 < size and board.get_color(x + 2, y + 2) == color)
                ):
                        return True
                    # Check diagonally (right down to left up) for x.xx in other way
                    if (
                    (x -2 >= 0 and y +2 < size and board.get_color(x-2, y+2) == color) and
                    (x - 1 >= 0 and y + 1 < size and board.get_color(x - 1, y + 1) == color) and
                    (x + 1 < size and y - 1 >= 0 and board.get_color(x +1, y - 1) == color)
                ):
                        return True
                    # Check diagonally (left down to right up) for xx.x
                    if (
                    (x + 1 < size and y +1 < size and board.get_color(x + 1, y +1) == color) and
                    (x - 1 >= 0 and y -1 >=0 and board.get_color(x - 1, y -1) == color) and
                    (x - 2 >= 0 and y - 2 >=0 and board.get_color(x - 2, y - 2) == color)
                ):
                        return True
                    # Check diagonally (right down to left up) for xx.x in other way
                    if (
                    (x +2 < size and y -2 >=0 and board.get_color(x+2, y-2) == color) and
                    (x - 1 >= 0 and y + 1 < size and board.get_color(x - 1, y + 1) == color) and
                    (x + 1 < size and y - 1 >= 0 and board.get_color(x +1, y - 1) == color)
                ):
                        return True

                # Check diagonally (ld to ru) for .xxx
                    if (
                    (x + 3 <size and y + 3 < size and board.get_color(x+ 3, y+3) == color) and
                    (x + 1 < size and y + 1 < size and board.get_color(x + 1, y + 1) == color) and
                    (x + 2 <size and y+2 < size and board.get_color(x +2, y+ 2) == color)
                ):
                        return True
                # Check diagonally (rd to lu) for .xxx
                    if (
                    (x - 3 >= 0 and y + 3 < size and board.get_color(x - 3, y+3) == color) and
                    (x - 1 >=0 and y + 1 < size and board.get_color(x - 1, y + 1) == color) and
                    (x - 2 >= 0 and y + 2 < size and board.get_color(x - 2, y + 2) == color)
                ):
                        return True
                    # Check diagonally (ld to ru) for xxx.
                    if (
                    (x - 2 >= 0 and y - 3 >= 0 and board.get_color(x - 3, y - 3) == color) and
                    (x  -3 >= 0 and y - 3 >= 0 and board.get_color(x - 1, y - 1) == color) and
                    (x - 1 >= 0 and y - 1 >= 0 and board.get_color(x - 2, y - 2) == color)
                ):
                        return True
                    # Check diagonally (rd to lu) for xxx.
                    if (
                    (x + 3 < size and y - 3 >= 0 and board.get_color(x + 3, y - 3) == color) and
                    (x + 1 < size and y - 1 >=0 and board.get_color(x + 1, y - 1) == color) and
                    (x + 2 < size and y - 2 >= 0 and board.get_color(x + 2, y - 2) == color)
                ):
                        return True

        return False

    def get_capture_moves(self, board: GoBoard, color: GO_COLOR) -> list:
        # get moves that capture two or more stones
        pass



def run() -> None:
    """
    start the gtp connection and wait for commands.
    """
    board: GoBoard = GoBoard(DEFAULT_SIZE)
    con: GtpConnection = GtpConnection(Go0(), board)
    con.start_connection()


if __name__ == "__main__":
    run()

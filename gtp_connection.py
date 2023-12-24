"""
gtp_connection.py
Module for playing games of Go using GoTextProtocol

Cmput 455 sample code
Written by Cmput 455 TA and Martin Mueller.
Parts of this code were originally based on the gtp module 
in the Deep-Go project by Isaac Henrion and Amos Storkey 
at the University of Edinburgh.
"""
import traceback
import numpy as np
import re
import random
from sys import stdin, stdout, stderr
from typing import Any, Callable, Dict, List, Tuple

from board_base import (
    BLACK,
    WHITE,
    EMPTY,
    BORDER,
    GO_COLOR, GO_POINT,
    PASS,
    MAXSIZE,
    coord_to_point,
    opponent
)
from board import GoBoard
from board_util import GoBoardUtil
from engine import GoEngine



class GtpConnection:
    def __init__(self, go_engine: GoEngine, board: GoBoard, debug_mode: bool = False) -> None:
        """
        Manage a GTP connection for a Go-playing engine

        Parameters
        ----------
        go_engine:
            a program that can reply to a set of GTP commandsbelow
        board: 
            Represents the current board state.
        """
        self._debug_mode: bool = debug_mode
        self.go_engine = go_engine
        self.board: GoBoard = board
        
        self.policytype = "random"
        
        self.commands: Dict[str, Callable[[List[str]], None]] = {
            "protocol_version": self.protocol_version_cmd,
            "quit": self.quit_cmd,
            "name": self.name_cmd,
            # "policy":self.policy,
            # "policy_moves" : self.policy_moves,
            "policy": self.set_policy_cmd,
            "policy_moves": self.policy_moves_cmd,
            "boardsize": self.boardsize_cmd,
            "showboard": self.showboard_cmd,
            "clear_board": self.clear_board_cmd,
            "komi": self.komi_cmd,
            "version": self.version_cmd,
            "known_command": self.known_command_cmd,
            "genmove": self.genmove_cmd,
            "list_commands": self.list_commands_cmd,
            "play": self.play_cmd,
            "legal_moves": self.legal_moves_cmd,
            "gogui-rules_legal_moves": self.gogui_rules_legal_moves_cmd,
            "gogui-rules_final_result": self.gogui_rules_final_result_cmd,
            "gogui-rules_captured_count": self.gogui_rules_captured_count_cmd,
            "gogui-rules_game_id": self.gogui_rules_game_id_cmd,
            "gogui-rules_board_size": self.gogui_rules_board_size_cmd,
            "gogui-rules_side_to_move": self.gogui_rules_side_to_move_cmd,
            "gogui-rules_board": self.gogui_rules_board_cmd,
            "gogui-analyze_commands": self.gogui_analyze_cmd,
            "timelimit": self.timelimit_cmd,
            "solve": self.solve_cmd
        }

        # argmap is used for argument checking
        # values: (required number of arguments,
        #          error message on argnum failure)
        self.argmap: Dict[str, Tuple[int, str]] = {
            "boardsize": (1, "Usage: boardsize INT"),
            "komi": (1, "Usage: komi FLOAT"),
            "known_command": (1, "Usage: known_command CMD_NAME"),
            "genmove": (1, "Usage: genmove {w,b}"),
            "play": (2, "Usage: play {b,w} MOVE"),
            "legal_moves": (1, "Usage: legal_moves {w,b}"),
        }

    def write(self, data: str) -> None:
        stdout.write(data)

    def flush(self) -> None:
        stdout.flush()

    def start_connection(self) -> None:
        """
        Start a GTP connection. 
        This function continuously monitors standard input for commands.
        """
        line = stdin.readline()
        while line:
            self.get_cmd(line)
            line = stdin.readline()

    def get_cmd(self, command: str) -> None:
        """
        Parse command string and execute it
        """
        if len(command.strip(" \r\t")) == 0:
            return
        if command[0] == "#":
            return
        # Strip leading numbers from regression tests
        if command[0].isdigit():
            command = re.sub("^\d+", "", command).lstrip()

        elements: List[str] = command.split()
        if not elements:
            return
        command_name: str = elements[0]
        args: List[str] = elements[1:]
        if self.has_arg_error(command_name, len(args)):
            return
        if command_name in self.commands:
            try:
                self.commands[command_name](args)
            except Exception as e:
                self.debug_msg("Error executing command {}\n".format(str(e)))
                self.debug_msg("Stack Trace:\n{}\n".format(traceback.format_exc()))
                raise e
        else:
            self.debug_msg("Unknown command: {}\n".format(command_name))
            self.error("Unknown command")
            stdout.flush()

    def has_arg_error(self, cmd: str, argnum: int) -> bool:
        """
        Verify the number of arguments of cmd.
        argnum is the number of parsed arguments
        """
        if cmd in self.argmap and self.argmap[cmd][0] != argnum:
            self.error(self.argmap[cmd][1])
            return True
        return False

    def debug_msg(self, msg: str) -> None:
        """ Write msg to the debug stream """
        if self._debug_mode:
            stderr.write(msg)
            stderr.flush()

    def error(self, error_msg: str) -> None:
        """ Send error msg to stdout """
        stdout.write("? {}\n\n".format(error_msg))
        stdout.flush()

    def respond(self, response: str = "") -> None:
        """ Send response to stdout """
        stdout.write("= {}\n\n".format(response))
        stdout.flush()

    def reset(self, size: int) -> None:
        """
        Reset the board to empty board of given size
        """
        self.board.reset(size)

    def board2d(self) -> str:
        return str(GoBoardUtil.get_twoD_board(self.board))

    def protocol_version_cmd(self, args: List[str]) -> None:
        """ Return the GTP protocol version being used (always 2) """
        self.respond("2")

    def quit_cmd(self, args: List[str]) -> None:
        """ Quit game and exit the GTP interface """
        self.respond()
        exit()

    def name_cmd(self, args: List[str]) -> None:
        """ Return the name of the Go engine """
        self.respond(self.go_engine.name)

    def version_cmd(self, args: List[str]) -> None:
        """ Return the version of the  Go engine """
        self.respond(str(self.go_engine.version))

    def clear_board_cmd(self, args: List[str]) -> None:
        """ clear the board """
        self.reset(self.board.size)
        self.respond()

    def boardsize_cmd(self, args: List[str]) -> None:
        """
        Reset the game with new boardsize args[0]
        """
        self.reset(int(args[0]))
        self.respond()

    def showboard_cmd(self, args: List[str]) -> None:
        self.respond("\n" + self.board2d())

    def komi_cmd(self, args: List[str]) -> None:
        """
        Set the engine's komi to args[0]
        """
        self.go_engine.komi = float(args[0])
        self.respond()

    def known_command_cmd(self, args: List[str]) -> None:
        """
        Check if command args[0] is known to the GTP interface
        """
        if args[0] in self.commands:
            self.respond("true")
        else:
            self.respond("false")

    def list_commands_cmd(self, args: List[str]) -> None:
        """ list all supported GTP commands """
        self.respond(" ".join(list(self.commands.keys())))
    
    
    def legal_moves_cmd(self, args: List[str]) -> List[Tuple[int, int]]:
        """
        List legal moves for color args[0] in {'b','w'}
        """
        board_color: str = args[0].lower()
        color: GO_COLOR = color_to_int(board_color)
        moves: List[GO_POINT] = GoBoardUtil.generate_legal_moves(self.board, color)
        gtp_moves: List[Tuple[int, int]] = []
        for move in moves:
            coords: Tuple[int, int] = point_to_coord(move, self.board.size)
            gtp_moves.append(coords)
        return gtp_moves
    

    def legal_moves(self, color: GO_COLOR):
        moves: List[GO_POINT] = GoBoardUtil.generate_legal_moves(self.board, color)
        gtp_moves: List[str] = []


        for move in moves:
            coords: Tuple[int, int] = point_to_coord(move, self.board.size)

            gtp_moves.append(format_point(coords).lower())

        sorted_moves = sorted(gtp_moves)
        return sorted_moves


    """
    ==========================================================================
    Assignment 2 - game-specific commands start here
    ==========================================================================
    """
    """
    ==========================================================================
    Assignment 2 - commands we already implemented for you
    ==========================================================================
    """
    def gogui_analyze_cmd(self, args: List[str]) -> None:
        """ We already implemented this function for Assignment 2 """
        self.respond("pstring/Legal Moves For ToPlay/gogui-rules_legal_moves\n"
                     "pstring/Side to Play/gogui-rules_side_to_move\n"
                     "pstring/Final Result/gogui-rules_final_result\n"
                     "pstring/Board Size/gogui-rules_board_size\n"
                     "pstring/Rules GameID/gogui-rules_game_id\n"
                     "pstring/Show Board/gogui-rules_board\n"
                     )

    def gogui_rules_game_id_cmd(self, args: List[str]) -> None:
        """ We already implemented this function for Assignment 2 """
        self.respond("Ninuki")

    def gogui_rules_board_size_cmd(self, args: List[str]) -> None:
        """ We already implemented this function for Assignment 2 """
        self.respond(str(self.board.size))

    def gogui_rules_side_to_move_cmd(self, args: List[str]) -> None:
        """ We already implemented this function for Assignment 2 """
        color = "black" if self.board.current_player == BLACK else "white"
        self.respond(color)

    def gogui_rules_board_cmd(self, args: List[str]) -> None:
        """ We already implemented this function for Assignment 2 """
        size = self.board.size
        str = ''
        for row in range(size-1, -1, -1):
            start = self.board.row_start(row + 1)
            for i in range(size):
                #str += '.'
                point = self.board.board[start + i]
                if point == BLACK:
                    str += 'X'
                elif point == WHITE:
                    str += 'O'
                elif point == EMPTY:
                    str += '.'
                else:
                    assert False
            str += '\n'
        self.respond(str)


    def gogui_rules_final_result_cmd(self, args: List[str]) -> None:
        """ We already implemented this function for Assignment 2 """
        result1 = self.board.detect_five_in_a_row()
        result2 = EMPTY
        if self.board.get_captures(BLACK) >= 10:
            result2 = BLACK
        elif self.board.get_captures(WHITE) >= 10:
            result2 = WHITE

        if (result1 == BLACK) or (result2 == BLACK):
            self.respond("black")
        elif (result1 == WHITE) or (result2 == WHITE):
            self.respond("white")
        elif self.board.get_empty_points().size == 0:
            self.respond("draw")
        else:
            self.respond("unknown")
        return

    def gogui_rules_legal_moves_cmd(self, args: List[str]) -> None:
        """ We already implemented this function for Assignment 2 """
        if (self.board.detect_five_in_a_row() != EMPTY) or \
            (self.board.get_captures(BLACK) >= 10) or \
            (self.board.get_captures(WHITE) >= 10):
            self.respond("")
            return
        legal_moves = self.board.get_empty_points()
        gtp_moves: List[str] = []
        for move in legal_moves:
            coords: Tuple[int, int] = point_to_coord(move, self.board.size)
            gtp_moves.append(format_point(coords))
        sorted_moves = " ".join(sorted(gtp_moves))
        self.respond(sorted_moves)

    def play_cmd(self, args: List[str]) -> None:
        """ We already implemented this function for Assignment 2 """
        try:
            board_color = args[0].lower()
            board_move = args[1]
            if board_color not in ['b', 'w']:
                self.respond('illegal move: "{} {}" wrong color'.format(board_color, board_move))
                return
            coord = move_to_coord(args[1], self.board.size)
            move = coord_to_point(coord[0], coord[1], self.board.size)
            
            color = color_to_int(board_color)
            if not self.board.play_move(move, color):
                # self.respond("Illegal Move: {}".format(board_move))
                self.respond('illegal move: "{} {}" occupied'.format(board_color, board_move))
                return
            else:
                # self.board.try_captures(coord, color)
                self.debug_msg(
                    "Move: {}\nBoard:\n{}\n".format(board_move, self.board2d())
                )
            if len(args) > 2 and args[2] == 'print_move':
                move_as_string = format_point(coord)
                self.respond(move_as_string.lower())
            else:
                self.respond()
        except Exception as e:
            self.respond('illegal move: "{} {}" {}'.format(args[0], args[1], str(e)))

    def gogui_rules_captured_count_cmd(self, args: List[str]) -> None:
        """ We already implemented this function for Assignment 2 """
        self.respond(str(self.board.get_captures(WHITE))+' '+str(self.board.get_captures(BLACK)))

    """
    ==========================================================================
    Assignment 2 - game-specific commands you have to implement or modify
    ==========================================================================
    """
    def set_policy_cmd(self, args: List[str]) -> None:

        policy_type = args[0].lower()
        if policy_type in {"random", "rule_based"}:
            self.policytype = policy_type
            self.respond()
        else:
            self.error("Invalid policy type. Use 'random' or 'rule_based'.")

    def policy_moves_cmd(self, args: List[str]) -> None:
        """
        Print the set of moves considered by the simulation policy for the current player.
        """
        current_moves = self.generate_policy_moves()
        self.respond("{} {}".format(current_moves[0], " ".join(sorted(current_moves[1]))))
    
    def generate_policy_moves(self) -> Tuple[str, List[str]]:
        """
        Generate moves based on the set policy type.
        """
        current_ply = self.board.current_player
        moves = self.legal_moves(current_ply)

        if self.policytype == "random":
            random_move = self.get_random_move()
            return "Random", random_move
        elif self.policytype == "rule_based":
            
            win_moves = self.get_winning_moves(self.board, self.board.current_player)
            block_win_moves = self.get_block_win_moves(self.board, self.board.current_player)
            open_four_moves = self.get_open_four_moves(self.board, self.board.current_player)
            capture_moves = self.find_capture_pattern_in_one_move(self.board, self.board.current_player)
        
            
            if win_moves:
                return "Win", win_moves
            # Check for block win moves
            elif block_win_moves:
                return "BlockWin", block_win_moves
            # Check for open four moves
            elif open_four_moves:
                return "OpenFour", open_four_moves
            # Check for capture moves
            elif capture_moves:
                return "Capture", capture_moves
            else:
                return "Random", ["k", "k"]
        else:
           
            raise ValueError("Invalid policy type")
    def find_capture_pattern_in_one_move(self, board: GoBoard, color: GO_COLOR) -> List[str]:
        capture_moves = []

        for move in GoBoardUtil.generate_legal_moves(board, color):
            captured_stones = self.check_capture_pattern(board, move, color)
            xooox = self.XOOOX(board,move, color)

            if captured_stones:
                coords: Tuple[int, int] = point_to_coord(move, board.size)
                capture_moves.append(format_point(coords).lower())
            if xooox:
                coords: Tuple[int, int] = point_to_coord(move, board.size)
                capture_moves.append(format_point(coords).lower())

        return capture_moves

        

    def check_capture_pattern(self, board: GoBoard, move: GO_POINT, color: GO_COLOR):
        x, y = point_to_coord(move, board.size)
        opp = opponent(color)
        captures = []
    # Check horizontally for "XOO."
        if (board.size >= x-3>=0) :
            move1 = coord_to_point(x-3, y, self.board.size) #X
            move2 = coord_to_point(x-2, y, self.board.size)  #O
            move3 = coord_to_point(x-1, y, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.
        if ( board.size >= x+3 >=0):
            move1 = coord_to_point(x+3, y, self.board.size) #X
            move2 = coord_to_point(x+2, y, self.board.size)  #O
            move3 = coord_to_point(x+1, y, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)

            if (board.get_color(move1) == color ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.
    
    # Check vertically for "XOO."
        if (board.size >= y-3>=0):
            move1 = coord_to_point(x, y-3, self.board.size) #X
            move2 = coord_to_point(x, y-2, self.board.size)  #O
            move3 = coord_to_point(x, y-1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)

            if (board.get_color(move1) == color ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.
        if (board.size >= y+3 >=0):
            move1 = coord_to_point(x, y+3, self.board.size) #X
            move2 = coord_to_point(x, y+2, self.board.size)  #O
            move3 = coord_to_point(x, y+1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)

            if (board.get_color(move1) == color ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.

    # Check diagonally for "XOO."
        if (board.size >= x-3>=0 and board.size >= y-3>=0) :
            move1 = coord_to_point(x-3, y-3, self.board.size) #X
            move2 = coord_to_point(x-2, y-2, self.board.size)  #O
            move3 = coord_to_point(x-1, y-1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)

            if (board.get_color(move1) == color ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.
        if (board.size >= x+3 >= 0 and board.size >= y-3 >=0):
            move1 = coord_to_point(x+3, y-3, self.board.size) #X
            move2 = coord_to_point(x+2, y-2, self.board.size)  #O
            move3 = coord_to_point(x+1, y-1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)

            if (board.get_color(move1) == color ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.

    # Check diagonally for ".OOX"
        if (board.size >= x-3>=0 and board.size >= y+3 >=0) :
            move1 = coord_to_point(x-3, y+3, self.board.size) #X
            move2 = coord_to_point(x-2, y+2, self.board.size)  #O
            move3 = coord_to_point(x-1, y+1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)

            if (board.get_color(move1) == color ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.
        if (board.size >= x+3 >= 0 and board.size >= y+3 >=0 ):
            move1 = coord_to_point(x+3, y+3, self.board.size) #X
            move2 = coord_to_point(x+2, y+2, self.board.size)  #O
            move3 = coord_to_point(x+1, y+1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)

            if (board.get_color(move1) == color ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.
        return captures
        
        
        
    def get_random_move(self) -> List[str]:
        # args = ["b"]  # or ["w"], depending on the current player
        # legal_moves = self.legal_moves_cmd(args)
        current_player = self.board.current_player
        current_player_str = "b" if current_player == BLACK else "w"
    
        args = [current_player_str]
        legal_moves = self.legal_moves_cmd(args)
        
        # Choose multiple random moves from the list
        num_moves = min(len(legal_moves), 10)  # Number of moves to choose, you can adjust this
        random_moves = random.sample(legal_moves, num_moves)
        
        # Convert moves to their string representation
        formatted_moves = [format_point(move).lower() for move in random_moves]
        return formatted_moves
            
    def get_block_win_moves(self, board: GoBoard, color: GO_COLOR) -> list:
        block_moves = []
        opp = opponent(color)
        if color == WHITE:
            captured = board.black_captures
        if color == BLACK:
            captured = board.white_captures

        for move in GoBoardUtil.generate_legal_moves(board, color):
            blocked_stones = self.check_four_pattern(board, move, color) #case 1
            captured_stones = self.check_capture_pattern(board,move,color) #case 2
            capture_threat = self.check_capture_pattern(board,move,opp) #case 3
            xooox = self.XOOOX(board,move, color) #case2 
            seven = self.XOOOX(board,move, opp)
            
            if blocked_stones:
                coords: Tuple[int, int] = point_to_coord(move, board.size)
                block_moves.append(format_point(coords).lower())
            if xooox:
                coords: Tuple[int, int] = point_to_coord(move, board.size)
                block_moves.append(format_point(coords).lower())
            
            if block_moves:
                if captured_stones: #case 2
                    coords: Tuple[int, int] = point_to_coord(move, board.size)
                    block_moves.append(format_point(coords).lower())
            if captured >= 8:
                if capture_threat:
                    coords: Tuple[int, int] = point_to_coord(move, board.size)
                    block_moves.append(format_point(coords).lower())
            if captured >= 7:
                if seven:
                    coords: Tuple[int, int] = point_to_coord(move, board.size)
                    block_moves.append(format_point(coords).lower())
        block_moves = list(set(block_moves))

        return block_moves
    # def XOX(self, board: GoBoard, move: GO_POINT, color: GO_COLOR) -> List[str]:
    #     blcapture = []
    #     x, y = point_to_coord(move, board.size)
    #     opp = opponent(color)
    #     #XOX 
    #     if (board.size >x-2>=0) : #horizontal
    #         move1 = coord_to_point(x-2, y, self.board.size) #X
    #         move2 = coord_to_point(x-1, y, self.board.size) #O
    #         xmove = coord_to_point(x, y, self.board.size) #.
    #         if (board.get_color(move1) == color) and board.get_color(move2) == opp and board.get_color(xmove) == 0:
    #             blcapture.append(xmove) #XOO.
    #     if (board.size > x+2 >=0):
    #         move1 = coord_to_point(x+2, y, self.board.size) #X
    #         move2 = coord_to_point(x+1, y, self.board.size) #O
    #         xmove = coord_to_point(x, y, self.board.size) #.
    #         if (board.get_color(move1) == color) and board.get_color(move2) == opp and board.get_color(xmove) == 0:
    #             blcapture.append(xmove) #XOO.
    #     if (board.size > y-2 >= 0):
    #         move1 = coord_to_point(x, y-2, self.board.size) #X
    #         move2 = coord_to_point(x, y-1, self.board.size) #O
    #         xmove = coord_to_point(x, y, self.board.size) #.
    #         if (board.get_color(move1) == color) and board.get_color(move2) == opp and board.get_color(xmove) == 0:
    #             blcapture.append(xmove) #XOO.
    #     if (board.size > y+2 >=0):
    #         move1 = coord_to_point(x, y+2, self.board.size) #X
    #         move2 = coord_to_point(x, y+1, self.board.size) #O
    #         xmove = coord_to_point(x, y, self.board.size) #.
    #         if (board.get_color(move1) == color) and board.get_color(move2) == opp and board.get_color(xmove) == 0:
    #             blcapture.append(xmove) #XOO.
    #     if (board.size > y-2 >=0) and (board.size > x-2 >= 0):
    #         move1 = coord_to_point(x-2, y-2, self.board.size) #X
    #         move2 = coord_to_point(x-1, y-1, self.board.size) #O
    #         xmove = coord_to_point(x, y, self.board.size) #.
    #         if (board.get_color(move1) == color) and board.get_color(move2) == opp and board.get_color(xmove) == 0:
    #             blcapture.append(xmove) #XOO.
    #     if (board.size > y-2 >=0 and board.size > x+2 >= 0):
    #         move1 = coord_to_point(x+2, y-2, self.board.size) #X
    #         move2 = coord_to_point(x+1, y-1, self.board.size) #O
    #         xmove = coord_to_point(x, y, self.board.size) #.
    #         if (board.get_color(move1) == color) and board.get_color(move2) == opp and board.get_color(xmove) == 0:
    #             blcapture.append(xmove) #XOO.

    #     if (board.size > y+2 >=0 and board.size > x+2 >=0):
    #         move1 = coord_to_point(x+2, y+2, self.board.size) #X
    #         move2 = coord_to_point(x+1, y+1, self.board.size) #O
    #         xmove = coord_to_point(x, y, self.board.size) #.
    #         if (board.get_color(move1) == color) and board.get_color(move2) == opp and board.get_color(xmove) == 0:
    #             blcapture.append(xmove) #XOO.

    #     if (board.size > y+2 >=0 and board.size > x-2>=0):
    #         move1 = coord_to_point(x-2, y+2, self.board.size) #X
    #         move2 = coord_to_point(x-1, y+1, self.board.size) #O
    #         xmove = coord_to_point(x, y, self.board.size) #.
    #         if (board.get_color(move1) == color) and board.get_color(move2) == opp and board.get_color(xmove) == 0:
    #             blcapture.append(xmove) #XOO.
    #     return blcapture
    
    def XOOOX(self, board: GoBoard, move: GO_POINT, color: GO_COLOR) -> List[str]:
        blcapture = []
        x, y = point_to_coord(move, board.size)
        opp = opponent(color)
        #XOX 
        if (board.size >= x-4>=0) : #horizontal
            move1 = coord_to_point(x-4,y, self.board.size) #X
            move2 = coord_to_point(x-3, y, self.board.size) #O
            move3 = coord_to_point(x-2, y, self.board.size) #O
            move4 = coord_to_point(x-1,y, self.board.size)#O
            xmove = coord_to_point(x, y, self.board.size) #.
            if (board.get_color(move1) == color ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4)==opp and board.get_color(xmove) == 0:
                blcapture.append(xmove) #XOO.
        if (board.size >= x+4>=0) : #horizontal
            move1 = coord_to_point(x+4,y, self.board.size)
            move2 = coord_to_point(x+3, y, self.board.size) #X
            move3 = coord_to_point(x+2, y, self.board.size) #O
            move4 = coord_to_point(x+1,y, self.board.size)
            xmove = coord_to_point(x, y, self.board.size) #.
            if (board.get_color(move1) == color) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4)==opp and board.get_color(xmove) == 0:
                blcapture.append(xmove) #XOO.
        if (board.size >= y-4>=0) : #vertical
            move1 = coord_to_point(x,y-4, self.board.size)
            move2 = coord_to_point(x, y-3, self.board.size) #X
            move3 = coord_to_point(x, y-2, self.board.size) #O
            move4 = coord_to_point(x,y-1, self.board.size)
            xmove = coord_to_point(x, y, self.board.size) #.
            if (board.get_color(move1) == color) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4)==opp and board.get_color(xmove) == 0:
                blcapture.append(xmove) #XOO.
        if (board.size >=y+4>=0) : #horizontal
            move1 = coord_to_point(x,y+4, self.board.size)
            move2 = coord_to_point(x, y+3, self.board.size) #X
            move3 = coord_to_point(x, y+2, self.board.size) #O
            move4 = coord_to_point(x,y+1, self.board.size)
            xmove = coord_to_point(x, y, self.board.size) #.
            if (board.get_color(move1) == color) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4)==opp and board.get_color(xmove) == 0:
                blcapture.append(xmove) #XOO.
        if (board.size >=x-4>=0 and board.size >= y-4>=0) : #horizontal
            move1 = coord_to_point(x-4,y-4, self.board.size)
            move2 = coord_to_point(x-3, y-3, self.board.size) #X
            move3 = coord_to_point(x-2, y-2, self.board.size) #O
            move4 = coord_to_point(x-1,y-1, self.board.size)
            xmove = coord_to_point(x, y, self.board.size) #.
            if (board.get_color(move1) == color) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4)==opp and board.get_color(xmove) == 0:
                blcapture.append(xmove) #XOO.
        if (board.size >=x+4>=0 and board.size >= y-4 >=0) : #horizontal
            move1 = coord_to_point(x+4,y-4, self.board.size)
            move2 = coord_to_point(x+3, y-3, self.board.size) #X
            move3 = coord_to_point(x+2, y-2, self.board.size) #O
            move4 = coord_to_point(x+1,y-1, self.board.size)
            xmove = coord_to_point(x, y, self.board.size) #.
            if (board.get_color(move1) == color) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4)==opp and board.get_color(xmove) == 0:
                blcapture.append(xmove) #XOO.

        if (board.size >= x+4>=0 and board.size >= y+4>=0) : #horizontal
            move1 = coord_to_point(x+4,y+4, self.board.size)
            move2 = coord_to_point(x+3, y+3, self.board.size) #X
            move3 = coord_to_point(x+2, y+2, self.board.size) #O
            move4 = coord_to_point(x+1,y+1, self.board.size)
            xmove = coord_to_point(x, y, self.board.size) #.
            if (board.get_color(move1) == color) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4)==opp and board.get_color(xmove) == 0:
                blcapture.append(xmove) #XOO.

        if (board.size >= x-4>=0 and board.size >= y+4 >=0) : #horizontal
            move1 = coord_to_point(x-4,y+4, self.board.size)
            move2 = coord_to_point(x-3, y+3, self.board.size) #X
            move3 = coord_to_point(x-2, y+2, self.board.size) #O
            move4 = coord_to_point(x-1,y+1, self.board.size)
            xmove = coord_to_point(x, y, self.board.size) #.
            if (board.get_color(move1) == color) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4)==opp and board.get_color(xmove) == 0:
                blcapture.append(xmove) #XOO.
        return blcapture

    # def blockwin_capture(self, board: GoBoard, move: GO_POINT, color: GO_COLOR) -> List[str]:
    #     blcapture = []
    #     opp = opponent(color)
        
    #     #XOX 
    #     XOX = self.XOX(board, move, color)
    #     blcapture.append(XOX)
    #     #XOOX
    #     XOOX = self.check_capture_pattern(board,move, color)
    #     blcapture.append(XOOX)
    #     #XOOOX
    #     XOOOX = self.XOOOX(board, move, color)
    #     blcapture.append(XOOOX)
    #     #XOOOOX
    #     return blcapture
    
    def find_capture_threat_moves(self, board: GoBoard,move: GO_POINT, color: GO_COLOR) -> List[str]:
        capture_threat_moves = []

        opponent_color = opponent(color)
        if color == WHITE:
            captured = board.black_captures
        if color == BLACK:
            captured = board.white_captures

        if captured >= 8:
            for move in GoBoardUtil.generate_legal_moves(board, color):
                captured_stones = self.check_capture_pattern(board, move, opponent_color)

                if captured_stones:
                    coords: Tuple[int, int] = point_to_coord(move, board.size)
                    capture_threat_moves.append(format_point(coords).lower())
        if captured >= 7:
            for move in GoBoardUtil.generate_legal_moves(board, opponent_color):
                captured_stones = self.XOOOX(board, move, color)

                if captured_stones:
                    coords: Tuple[int, int] = point_to_coord(move, board.size)
                    capture_threat_moves.append(format_point(coords).lower())

        return capture_threat_moves
    
    def check_four_pattern(self, board: GoBoard, move: GO_POINT, color: GO_COLOR):
        x, y = point_to_coord(move, board.size)
        opp = opponent(color)
        captures = []
    # Check horizontally for four Os
        if (board.size >=x-4>=0) : #OOOO.
            move1 = coord_to_point(x-4, y, self.board.size) #O
            move2 = coord_to_point(x-3, y, self.board.size) #O
            move3 = coord_to_point(x-2, y, self.board.size)  #O
            move4 = coord_to_point(x-1, y, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size) #X
            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.

        if (board.size >= x+ 4 >=0):
            move1 = coord_to_point(x+4, y, self.board.size) #O
            move2 = coord_to_point(x+3, y, self.board.size) #O
            move3 = coord_to_point(x+2, y, self.board.size)  #O
            move4 = coord_to_point(x+1, y, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size) #X
            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4)==opp and board.get_color(xmove) == 0:
                captures.append(xmove) 

        if (board.size >=x-3>=0) and ( board.size >= x+1>=0): #OOO.O
            move1 = coord_to_point(x-3, y, self.board.size) #O
            move2 = coord_to_point(x-2, y, self.board.size) #O
            move3 = coord_to_point(x-1, y, self.board.size)  #O
            move4 = coord_to_point(x+1, y, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size) #X
            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.

        if (board.size>= x+3 >=0) and (board.size>= x-1 >=0): #O.OOO
            move1 = coord_to_point(x+1, y, self.board.size) #O
            move2 = coord_to_point(x+3, y, self.board.size) #O
            move3 = coord_to_point(x+2, y, self.board.size)  #O
            move4 = coord_to_point(x-1, y, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size) #X

            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4)==opp and board.get_color(xmove) == 0:
                captures.append(xmove) 

        if (board.size >=x-2>=0) and (board.size>= x+2 >=0): #OO.OO
            move1 = coord_to_point(x+2, y, self.board.size) #O
            move2 = coord_to_point(x-2, y, self.board.size) #O
            move3 = coord_to_point(x-1, y, self.board.size)  #O
            move4 = coord_to_point(x+1, y, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size) #X
            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.
    
    # Check vertically 
        if (board.size >=y-4>=0) : #.OOOO
            move1 = coord_to_point(x, y-4, self.board.size) #O
            move2 = coord_to_point(x, y-3, self.board.size) #O
            move3 = coord_to_point(x, y-2, self.board.size)  #O
            move4 = coord_to_point(x, y-1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size) #X
            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.

        if (board.size >=y+4>=0) : #.OOOO
            move1 = coord_to_point(x, y+4, self.board.size) #O
            move2 = coord_to_point(x, y+3, self.board.size) #O
            move3 = coord_to_point(x, y+2, self.board.size)  #O
            move4 = coord_to_point(x, y+1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size) #X
            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.

        if (board.size >= y+2 >=0) and (board.size >= y-2 >=0): #.OOOO
            move1 = coord_to_point(x, y+2, self.board.size) #O
            move2 = coord_to_point(x, y+1, self.board.size) #O
            move3 = coord_to_point(x, y-2, self.board.size)  #O
            move4 = coord_to_point(x, y-1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size) #X
            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.

        if (board.size >=y+3>=0) and (board.size >= y-1 >=0) : #.OOOO
            move1 = coord_to_point(x, y-1, self.board.size) #O
            move2 = coord_to_point(x, y+3, self.board.size) #O
            move3 = coord_to_point(x, y+2, self.board.size)  #O
            move4 = coord_to_point(x, y+1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size) #X
            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == EMPTY:
                captures.append(xmove) #XOO.

        if (board.size >=y-3>=0) and (board.size >= y+1 >= 0) : #.OOOO
            move1 = coord_to_point(x, y-1, self.board.size) #O
            move2 = coord_to_point(x, y-3, self.board.size) #O
            move3 = coord_to_point(x, y-2, self.board.size)  #O
            move4 = coord_to_point(x, y+1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size) #X
            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == EMPTY:
                captures.append(xmove) #XOO.

    # Check diagonally 
        if (board.size >=y+4>=0) and (board.size>=x+4>=0) : #.OOOO
            move1 = coord_to_point(x+4, y+4, self.board.size) #O
            move2 = coord_to_point(x+3, y+3, self.board.size) #O
            move3 = coord_to_point(x+2, y+2, self.board.size)  #O
            move4 = coord_to_point(x+1, y+1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size) #X
            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.

        if (board.size >=y+4>=0) : #.OOOO
            move1 = coord_to_point(x-4, y-4, self.board.size) #O
            move2 = coord_to_point(x-3, y-3, self.board.size) #O
            move3 = coord_to_point(x-2, y-2, self.board.size)  #O
            move4 = coord_to_point(x-1, y-1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size) #X
            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.

    # Check diagonally 
        if (board.size >= x+4>=0 and board.size >= y-1 >=0) :
            move1 = coord_to_point(x+3, y-3, self.board.size) #X
            move2 = coord_to_point(x+2, y-2, self.board.size)  #O
            move3 = coord_to_point(x+1, y-1, self.board.size)  #O
            move4 = coord_to_point(x+4, y-4, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)

            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.
        if (board.size >= x-4 >=0 and board.size>=y+4 >= 0):
            move1 = coord_to_point(x-3, y+3, self.board.size) #X
            move2 = coord_to_point(x-2, y+2, self.board.size)  #O
            move3 = coord_to_point(x-1, y+1, self.board.size)  #O
            move4 = coord_to_point(x-4, y+4, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)

            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.

        #3
        if (board.size >= x+3>=0 and  board.size>= x-1 >= 0 and board.size >= y-1 >=0 and  board.size>= y+3 >= 0):
            move1 = coord_to_point(x+3, y+3, self.board.size) #O
            move2 = coord_to_point(x+2, y+2, self.board.size)  #O
            move3 = coord_to_point(x+1, y+1, self.board.size)  #O
            move4 = coord_to_point(x-1, y-1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)

            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.
        if (board.size >= x-3>=0 and  board.size>= x+1 >= 0 and board.size >= y+3 >=0 and  board.size>= y-1 >= 0):
            move1 = coord_to_point(x-3, y+3, self.board.size) #O
            move2 = coord_to_point(x-2, y+2, self.board.size)  #O
            move3 = coord_to_point(x-1, y+1, self.board.size)  #O
            move4 = coord_to_point(x+1, y-1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)

            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.
        #4
        if (board.size >= x+2>=0 and  board.size>= x-2 >= 0 and board.size >= y+2>=0 and  board.size>= y-2 >= 0):
            move1 = coord_to_point(x+2, y+2, self.board.size) #X
            move2 = coord_to_point(x+1, y+1, self.board.size)  #O
            move3 = coord_to_point(x-1, y-1, self.board.size)  #O
            move4 = coord_to_point(x-2, y-2, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)

            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.
        if (board.size >= x+2>=0 and  board.size>= x-2 >= 0 and board.size >= y+2 >=0 and board.size >= y-2 >= 0):
            move1 = coord_to_point(x-2, y+2, self.board.size) #X
            move2 = coord_to_point(x-1, y+1, self.board.size)  #O
            move3 = coord_to_point(x+1, y-1, self.board.size)  #O
            move4 = coord_to_point(x+2, y-2, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)

            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.
        #5
        if (board.size >= x+3>=0 and  board.size>= x-1 >= 0 and board.size >= y-3 >= 0 and board.size>= y+1 >=0):
            move1 = coord_to_point(x+1, y+1, self.board.size) #X
            move2 = coord_to_point(x-1, y-1, self.board.size)  #O
            move3 = coord_to_point(x-2, y-2, self.board.size)  #O
            move4 = coord_to_point(x-3, y-3, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)

            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.
        if (board.size >= x+3>=0 and  board.size>= x-1 >= 0 and board.size >= y-3 >=0 and  board.size>= y+1 >= 0):
            move1 = coord_to_point(x-1, y+1, self.board.size) #X
            move2 = coord_to_point(x+1, y-1, self.board.size)  #O
            move3 = coord_to_point(x+2, y-2, self.board.size)  #O
            move4 = coord_to_point(x+3, y-3, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)

            if (board.get_color(move1) == opp ) and board.get_color(move2) == opp and board.get_color(move3) == opp and board.get_color(move4) == opp and board.get_color(xmove) == 0:
                captures.append(xmove) #XOO.
        return captures
    
    def get_open_four_moves(self, board: GoBoard, color: GO_COLOR) -> List[str]:
        open_four_moves = []
        for move in GoBoardUtil.generate_legal_moves(board, color):
            captured_stones = self.check_open_four_moves(board, move, color)

            if captured_stones:
                coords: Tuple[int, int] = point_to_coord(move, board.size)
                open_four_moves.append(format_point(coords).lower())

        return open_four_moves


    def check_open_four_moves (self, board: GoBoard, move: GO_POINT, color: GO_COLOR):
        x, y = point_to_coord(move, board.size)

        openfour = []
        size = board.size
        # horizontal
        if (0<= x-1 < size and 0<= x+2 <size):
            move1 = coord_to_point(x-1, y, self.board.size) #X
            move2 = coord_to_point(x+1, y, self.board.size)  #O
            move3 = coord_to_point(x+2, y, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == color and board.get_color(move3) == color and board.get_color(xmove) == 0:
                openfour.append(xmove) #XOO.
        if (0<= x-2 < size and 0<= x+1 <size):
            move1 = coord_to_point(x+1, y, self.board.size) #X
            move2 = coord_to_point(x-1, y, self.board.size)  #O
            move3 = coord_to_point(x-2, y, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == color and board.get_color(move3) == color and board.get_color(xmove) == 0:
                openfour.append(xmove) #XOO.
        if (0<= x-3 < size):
            move1 = coord_to_point(x-1, y, self.board.size) #X
            move2 = coord_to_point(x-2, y, self.board.size)  #O
            move3 = coord_to_point(x-3, y, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == color and board.get_color(move3) == color and board.get_color(xmove) == 0:
                openfour.append(xmove) #XOO.

        if (0<= x+3 < size):
            move1 = coord_to_point(x+3, y, self.board.size) #X
            move2 = coord_to_point(x+2, y, self.board.size)  #O
            move3 = coord_to_point(x+1, y, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == color and board.get_color(move3) == color and board.get_color(xmove) == 0:
                openfour.append(xmove) #XOO.
        #vertical
        if (0<= y-3< size):
            move1 = coord_to_point(x, y-1, self.board.size) #X
            move2 = coord_to_point(x, y-2, self.board.size)  #O
            move3 = coord_to_point(x, y-3, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == color and board.get_color(move3) == color and board.get_color(xmove) == 0:
                openfour.append(xmove) #XOO.
        if (0<= y-2 < size and 0<= y+1 <size):
            move1 = coord_to_point(x, y+1, self.board.size) #X
            move2 = coord_to_point(x, y-1, self.board.size)  #O
            move3 = coord_to_point(x, y-2, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == color and board.get_color(move3) == color and board.get_color(xmove) == 0:
                openfour.append(xmove) #XOO.
        if (0<= y+3 < size):
            move1 = coord_to_point(x, y+3, self.board.size) #X
            move2 = coord_to_point(x, y+2, self.board.size)  #O
            move3 = coord_to_point(x, y+1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == color and board.get_color(move3) == color and board.get_color(xmove) == 0:
                openfour.append(xmove) #XOO.

        if (0<= y-1 < size) and (0<= y+2 < size):
            move1 = coord_to_point(x, y+2, self.board.size) #X
            move2 = coord_to_point(x, y+1, self.board.size)  #O
            move3 = coord_to_point(x, y-1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == color and board.get_color(move3) == color and board.get_color(xmove) == 0:
                openfour.append(xmove) #XOO.

        # Check diagonally (left down to right up) for x.xx
        if (0<= x+3 < size and 0<= y+3 <size):
            move1 = coord_to_point(x+3, y+3, self.board.size) #X
            move2 = coord_to_point(x+2, y+2, self.board.size)  #O
            move3 = coord_to_point(x+1, y+1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == color and board.get_color(move3) == color and board.get_color(xmove) == 0:
                openfour.append(xmove) #XOO.
        if (0<= x-1 < size and  0<= x+2 < size and 0<= y-1 < size and 0<= y+2 <size):
            move1 = coord_to_point(x+2, y+2, self.board.size) #X
            move2 = coord_to_point(x+1, y+1, self.board.size)  #O
            move3 = coord_to_point(x-1, y-1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == color and board.get_color(move3) == color and board.get_color(xmove) == 0:
                openfour.append(xmove) #XOO.
        if (0<= x-3 < size) and (0<= y-3 < size):
            move1 = coord_to_point(x-1, y-1, self.board.size) #X
            move2 = coord_to_point(x-2, y-2, self.board.size)  #O
            move3 = coord_to_point(x-3, y-3, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == color and board.get_color(move3) == color and board.get_color(xmove) == 0:
                openfour.append(xmove) #XOO.

        if (0<= x-2 < size and  0<= x+1 < size and 0<= y-2 < size and 0<= y+1 <size):
            move1 = coord_to_point(x+1, y+1, self.board.size) #X
            move2 = coord_to_point(x-1, y-1, self.board.size)  #O
            move3 = coord_to_point(x-2, y-2, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == color and board.get_color(move3) == color and board.get_color(xmove) == 0:
                openfour.append(xmove) #XOO.


        #other way of diagonal 
        if (0<= x-3< size and 0<= y+3 <size):
            move1 = coord_to_point(x-1, y+1, self.board.size) #X
            move2 = coord_to_point(x-2, y+2, self.board.size)  #O
            move3 = coord_to_point(x-3, y+3, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == color and board.get_color(move3) == color and board.get_color(xmove) == 0:
                openfour.append(xmove) #XOO.
        if (0<= x+3 < size and 0<= y-3 <size):
            move1 = coord_to_point(x+3, y-3, self.board.size) #X
            move2 = coord_to_point(x+2, y-2, self.board.size)  #O
            move3 = coord_to_point(x+1, y-1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == color and board.get_color(move3) == color and board.get_color(xmove) == 0:
                openfour.append(xmove) #XOO.
        if (0<= x-2 < size and  0<= x+1 < size and 0<= y-1 < size and 0<= y+2 <size):
            move1 = coord_to_point(x+1, y-1, self.board.size) #X
            move2 = coord_to_point(x-1, y+1, self.board.size)  #O
            move3 = coord_to_point(x-2, y+2, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == color and board.get_color(move3) == color and board.get_color(xmove) == 0:
                openfour.append(xmove) #XOO.

        if (0<= x-1 < size and  0<= x+2 < size and 0<= y-2 < size and 0<= y+1 <size):
            move1 = coord_to_point(x+2, y-2, self.board.size) #X
            move2 = coord_to_point(x+1, y-1, self.board.size)  #O
            move3 = coord_to_point(x-1, y+1, self.board.size)  #O
            xmove = coord_to_point(x, y, self.board.size)
            if (board.get_color(move1) == color ) and board.get_color(move2) == color and board.get_color(move3) == color and board.get_color(xmove) == 0:
                openfour.append(xmove) #XOO.
        return openfour
        
        
    def get_winning_moves(self, board: GoBoard, color: GO_COLOR) -> list:
        winning_moves = []

        # Check for winning by five in a row
        for move in GoBoardUtil.generate_legal_moves(board, color):
            board_copy = board.copy()
            board_copy.play_move(move, color)
            if board_copy.detect_five_in_a_row() == color:
                coords: Tuple[int, int] = point_to_coord(move, self.board.size)
                winning_moves.append(format_point(coords).lower())

    # Check for winning by ten or more captures
        for move in GoBoardUtil.generate_legal_moves(board, color):
            board_copy = board.copy()
            board_copy.play_move(move, color)
            if board_copy.get_captures(color) >= 10:
                coords: Tuple[int, int] = point_to_coord(move, self.board.size)
                winning_moves.append(format_point(coords).lower())

        return winning_moves
    
    # def get_capture_moves(self,board: GoBoard, color: GO_COLOR) -> List[str]:
    #     capture_moves = []

    #     for move in GoBoardUtil.generate_legal_moves(board, color):
    #         board_copy = board.copy()
    #         board_copy.play_move(move, color)
    #         captured_stones = board_copy._detect_capture(move, color)

    #         if captured_stones:
    #             coords: Tuple[int, int] = point_to_coord(move, board.size)
    #             capture_moves.append(format_point(coords).lower())

    #     return capture_moves
    def flat_monte_carlo_simulation(self, color: int, legal_moves: List[int]) -> str:
        # Perform flat Monte Carlo simulation
        simulations = 10
        best_move = None
        best_win_percentage = -1

        for move in legal_moves:
            wins = 0

            for _ in range(simulations):
                # Simulate a game with the current move
                board_copy = self.board.copy()
                board_copy.play_move(move, color)

                # Perform random moves until the game is over
                while board_copy.checkwinner == "unknown":
                    random_move = random.choice(board_copy.get_empty_points())
                    board_copy.play_move(random_move, opponent(board_copy.current_player))

                # Check if the current player wins
                if board_copy.detect_five_in_a_row() == color:
                    wins += 1

            # Update the best move based on win percentage
            win_percentage = wins / simulations
            if win_percentage > best_win_percentage:
                best_move = move
                best_win_percentage = win_percentage

        return best_move
    def genmove_cmd(self, args: List[str]) -> None:
        """ 
        Modify this function for Assignment 2.
        """
        board_color = args[0].lower()
        color = color_to_int(board_color)
        result1 = self.board.detect_five_in_a_row()
        result2 = EMPTY
        if self.board.get_captures(opponent(color)) >= 10:
            result2 = opponent(color)
        if result1 == opponent(color) or result2 == opponent(color):
            self.respond("resign")
            return
        legal_moves = self.board.get_empty_points()
        if legal_moves.size == 0:
            self.respond("pass")
            return


        policy_name, policy_moves = self.generate_policy_moves()




        if policy_name == "Random":
            # Get a random move if the policy is random
            # move_as_string = random.choice(policy_moves)
            # self.play_cmd([board_color, move_as_string, 'print_move'])
            move_as_string = self.flat_monte_carlo_simulation(color, legal_moves)
            coords: Tuple[int, int] = point_to_coord(move_as_string, self.board.size)
            moves = (format_point(coords).lower())
            
            self.play_cmd([board_color, moves, 'print_move'])


        elif policy_name == "RuleBased":
            # Choose a move based on the rule-based strategy
            # You might have more complex logic here based on your rule-based strategy
            # For example, selecting the first move from the list
            move_as_string = policy_moves[0]
            self.play_cmd([board_color, move_as_string, 'print_move'])
        else:
            # If the policy type is not recognized, resort to a random move
             move_as_string = " ".join(policy_moves)
             last_move = policy_moves[-1]
             self.play_cmd([board_color, last_move, 'print_move'])
          


    def timelimit_cmd(self, args: List[str]) -> None:
        """ Implement this function for Assignment 2 """

        pass

    def solve_cmd(self, args: List[str]) -> None:
        """ Implement this function for Assignment 2 """

        pass


    """
    ==========================================================================
    Assignment 1 - game-specific commands end here
    ==========================================================================
    """

def point_to_coord(point: GO_POINT, boardsize: int) -> Tuple[int, int]:
    """
    Transform point given as board array index 
    to (row, col) coordinate representation.
    Special case: PASS is transformed to (PASS,PASS)
    """
    if point == PASS:
        return (PASS, PASS)
    else:
        NS = boardsize + 1
        return divmod(point, NS)
def coord_to_point(row: int, col: int, boardsize: int) -> GO_POINT:
    """
    Transform (row, col) coordinate representation to point 
    given as board array index.
    Special case: (PASS, PASS) is transformed to PASS.
    """
    if row == PASS and col == PASS:
        return PASS
    else:
        NS = boardsize + 1
        return row * NS + col


def format_point(move: Tuple[int, int]) -> str:
    """
    Return move coordinates as a string such as 'A1', or 'PASS'.
    """
    assert MAXSIZE <= 25
    column_letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    if move[0] == PASS:
        return "PASS"
    row, col = move
    if not 0 <= row < MAXSIZE or not 0 <= col < MAXSIZE:
        raise ValueError
    return column_letters[col - 1] + str(row)


def move_to_coord(point_str: str, board_size: int) -> Tuple[int, int]:
    """
    Convert a string point_str representing a point, as specified by GTP,
    to a pair of coordinates (row, col) in range 1 .. board_size.
    Raises ValueError if point_str is invalid
    """
    if not 2 <= board_size <= MAXSIZE:
        raise ValueError("board_size out of range")
    s = point_str.lower()
    if s == "pass":
        return (PASS, PASS)
    try:
        col_c = s[0]
        if (not "a" <= col_c <= "z") or col_c == "i":
            raise ValueError
        col = ord(col_c) - ord("a")
        if col_c < "i":
            col += 1
        row = int(s[1:])
        if row < 1:
            raise ValueError
    except (IndexError, ValueError):
        raise ValueError("wrong coordinate")
    if not (col <= board_size and row <= board_size):
        raise ValueError("wrong coordinate")
    return row, col


def color_to_int(c: str) -> int:
    """convert character to the appropriate integer code"""
    color_to_int = {"b": BLACK, "w": WHITE, "e": EMPTY, "BORDER": BORDER}
    return color_to_int[c]
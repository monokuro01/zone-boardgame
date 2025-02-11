from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import copy

app = Flask(__name__)
socketio = SocketIO(app)

# 定数定義
BOARD_SIZE = 10
RED = "R"
BLUE = "B"
EMPTY = None

class ZoneGame:
    def __init__(self):
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.turn = RED
        self.history = []
        self.captured_red = 0
        self.captured_blue = 0
        self.captured_history = []  # 取った駒の数の履歴も追加

    def save_state(self):
        """現在の盤面を履歴に保存"""
        self.history.append(copy.deepcopy(self.board))
        self.captured_history.append((self.captured_red, self.captured_blue))  # 取った駒の数も保存

    def undo(self):
        """1手前の状態に戻す"""
        if self.history:
            self.board = self.history.pop()
            self.captured_red, self.captured_blue = self.captured_history.pop()  # 取った駒の数を1手戻す
            self.turn = BLUE if self.turn == RED else RED
            return True
        return False

    def pass_turn(self):
        """手番をパスする"""
        self.turn = BLUE if self.turn == RED else RED

    def can_place_piece(self, x, y):
        """駒を置けるか判定"""
        if self.board[x][y] is not None:
            return False

        opponent = BLUE if self.turn == RED else RED

        # 上下左右のチェック
        if (y > 0 and self.board[x][y-1] == opponent) and (y < BOARD_SIZE - 1 and self.board[x][y+1] == opponent):
            return False
        if (x > 0 and self.board[x-1][y] == opponent) and (x < BOARD_SIZE - 1 and self.board[x+1][y] == opponent):
            return False

        return True

    def check_and_remove_opponent_stones(self, x, y):
        """相手の駒を取る処理"""
        opponent = BLUE if self.turn == RED else RED
        captured_count = 0
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and self.board[nx][ny] == opponent:
                ux, uy = nx + dx, ny + dy
                if 0 <= ux < BOARD_SIZE and 0 <= uy < BOARD_SIZE and self.board[ux][uy] == self.turn:
                    self.board[nx][ny] = EMPTY
                    captured_count += 1
        if self.turn == RED:
            self.captured_red += captured_count
        else:
            self.captured_blue += captured_count

    def next_move(self, x, y):
        if self.can_place_piece(x, y):
            self.save_state()
            self.board[x][y] = self.turn
            self.check_and_remove_opponent_stones(x, y)

            response = {
                "success": True,
                "board": self.board,
                "captured_red": self.captured_red,
                "captured_blue": self.captured_blue,
                "result": None
            }

            self.turn = BLUE if self.turn == RED else RED
            return response

        return {"success": False}

game = ZoneGame()

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('message', {'msg': f'{data["username"]} has joined the room.'}, room=room)

@socketio.on('move')
def on_move(data):
    x = data['x']
    y = data['y']
    room = data['room']

    response = game.next_move(x, y)

    emit('board_update', response, room=room)

@socketio.on('disconnect')
def on_disconnect():
    leave_room(session.get('room'))

if __name__ == "__main__":
    socketio.run(app, debug=False)

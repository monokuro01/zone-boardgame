from flask import Flask, render_template, request, jsonify, session
import copy
from uuid import uuid4  # ユニークなIDを生成するために利用

app = Flask(__name__)
app.secret_key = "your_secret_key"  # セッションを安全に保つための秘密鍵

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
        # 1. すでに駒が置かれているマスには置けない
        if self.board[x][y] is not None:
            print(f"Position ({x}, {y}) is already occupied.")
            return False

        opponent = BLUE if self.turn == RED else RED

        # 2. 上下左右の両方に相手の駒が置かれている場合、そのマスには置けない
        # 上下のチェック
        if (y > 0 and self.board[x][y-1] == opponent) and (y < BOARD_SIZE - 1 and self.board[x][y+1] == opponent):
            print(f"Position ({x}, {y}) is blocked by opponent's stones vertically (above and below).")
            return False

        # 左右のチェック
        if (x > 0 and self.board[x-1][y] == opponent) and (x < BOARD_SIZE - 1 and self.board[x+1][y] == opponent):
            print(f"Position ({x}, {y}) is blocked by opponent's stones horizontally (left and right).")
            return False

        # 3. 条件を満たさない場合は駒を置ける
        print(f"Position ({x}, {y}) is valid for placement.")
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

    def has_valid_move(self):
        """有効な手が残っているか確認"""
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                if self.can_place_piece(x, y):
                    return True
        return False

    def game_end(self):
        """ゲーム終了判定"""
        red_count = sum(row.count(RED) for row in self.board)
        blue_count = sum(row.count(BLUE) for row in self.board)
        if red_count > blue_count:
            return f"Winner: Red\nRed: {red_count}, Blue: {blue_count}"
        elif blue_count > red_count:
            return f"Winner: Blue\nRed: {red_count}, Blue: {blue_count}"
        else:
            if self.captured_red > self.captured_blue:
                return f"Winner: Red (Captured More)\nCaptured - Red: {self.captured_red}, Blue: {self.captured_blue}"
            elif self.captured_blue > self.captured_red:
                return f"Winner: Blue (Captured More)\nCaptured - Red: {self.captured_red}, Blue: {self.captured_blue}"
            else:
                return f"Winner: Blue (Default Rule)\nCaptured - Red: {self.captured_red}, Blue: {self.captured_blue}"

    def next_move(self, x, y):
        """次の手を処理"""
        # 置けるかどうか確認
        if self.can_place_piece(x, y):
            self.save_state()
            self.board[x][y] = self.turn  # 駒を配置
            self.check_and_remove_opponent_stones(x, y)  # 相手の駒を取る処理

            # まず駒が正常に描画される状態をクライアントに返す
            response = {
                "success": True,
                "board": self.board,
                "captured_red": self.captured_red,
                "captured_blue": self.captured_blue,
                "result": None
            }

            # 駒を描画した後で手番を切り替え
            self.turn = "B" if self.turn == "R" else "R"

            # 有効な手が残っているか確認
            if not self.has_valid_move():
                # ターンを切り替えて再度チェック
                self.turn = BLUE if self.turn == RED else RED
                if not self.has_valid_move():
                    # 両方のプレイヤーに有効な手がない場合はゲーム終了
                    result = self.game_end()
                    response["result"] = result  # 結果を追加
                    return response

            # 駒が正常に置かれた場合はそのままボードとターン情報を返す
            return response

        # 無効な手の場合はエラーを返す
        return {"success": False, "board": self.board, "turn": self.turn, "captured_red": self.captured_red, "captured_blue": self.captured_blue}

game = ZoneGame()

@app.route("/")
def index():
    if "game_id" not in session:
        session["game_id"] = str(uuid4())  # 各プレイヤーに固有のゲームIDを付与
        game = ZoneGame()  # 新しいゲームを作成
        session["game_state"] = game  # ゲーム状態をセッションに保存
    else:
        # 既存のゲーム状態をセッションから取得
        game = session.get("game_state", ZoneGame())  # セッションに状態がなければ新しいゲーム
    return render_template("index.html")

@app.route("/move", methods=["POST"])
def move():
    game = session.get("game_state", ZoneGame())
    data = request.json
    x, y = data["x"], data["y"]

    response = game.next_move(x, y)

    session["game_state"] = game

    print("Board state after move:")
    for row in game.board:
        print(row)  # 盤面の状態を表示

    return jsonify(response)

@app.route("/undo", methods=["POST"])
def undo():
    success = game.undo()
    return jsonify({
        "board": game.board,
        "turn": game.turn,
        "success": success,
        "captured_red": game.captured_red,  # 取った赤駒の数を返す
        "captured_blue": game.captured_blue  # 取った青駒の数を返す
    })

@app.route("/pass", methods=["POST"])
def pass_turn():
    game.pass_turn()
    return jsonify({"turn": game.turn})

@app.route("/reset", methods=["POST"])
def reset_game():
    game = ZoneGame()  # 新しいゲームのインスタンスを作成してリセット
    session["game_state"] = game
    return jsonify({
        "board": game.board,
        "turn": game.turn,
        "captured_red": game.captured_red,
        "captured_blue": game.captured_blue,
        "success": True  # リセットが成功したことを示す
    })


if __name__ == "__main__":
    app.run(debug=False)

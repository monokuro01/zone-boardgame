import pygame
import sys
import copy

# 定数の定義
DARK_GRAY = (240, 240, 240)  # 盤面の背景
LIGHT_GRAY = (30, 30, 30)  # グリッド線
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 70, 70)
BLUE = (70, 100, 255)
GREEN = (0, 128, 0)
YELLOW = (255, 155, 0)
SIZE = 650
BOARD_SIZE = 10
GRID_SIZE = SIZE // BOARD_SIZE

# Pygameの初期化
pygame.init()
screen = pygame.display.set_mode((SIZE, SIZE))
clock = pygame.time.Clock()
pygame.display.set_caption("ZONE")

class ZONE:
    def __init__(self):
        self.board = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.turn = RED
        self.history = []
        self.captured_red = 0  # REDが取ったコマ数
        self.captured_blue = 0  # BLUEが取ったコマ数

    def save_state(self):
        """現在の盤面を履歴に保存"""
        self.history.append({
            "board": copy.deepcopy(self.board),
            "captured_red": self.captured_red,
            "captured_blue": self.captured_blue
        })

    def undo(self):
        """1手前の状態に戻す"""
        if self.history:
            prev_state = self.history.pop()
            self.board = prev_state["board"]
            self.captured_red = prev_state["captured_red"]
            self.captured_blue = prev_state["captured_blue"]
            self.turn = RED if self.turn == BLUE else BLUE  # 手番も戻す
        else:
            print("戻せる手がありません。")

    def pass_turn(self):
        """手番をパスする"""
        self.turn = BLUE if self.turn == RED else RED
        print("手番をパスしました。")

    def draw_board(self):
        screen.fill(DARK_GRAY)
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(screen, LIGHT_GRAY, rect, 1)
                if self.board[x][y] is not None:
                    self.draw_stone(x, y, self.board[x][y])

        # スコアを表示
        font = pygame.font.Font(None, 36)
        red_score_text = font.render(f"RED Captured: {self.captured_red}", True, BLACK)
        blue_score_text = font.render(f"BLUE Captured: {self.captured_blue}", True, BLACK)

        screen.blit(red_score_text, (20, SIZE - 60))
        screen.blit(blue_score_text, (20, SIZE - 30))

    def draw_stone(self, x, y, color):
        pygame.draw.circle(screen, RED if color == RED else BLUE,
                           (x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2),
                           GRID_SIZE // 2 - 6)

    def can_place_piece(self, x, y):
        if self.board[x][y] is not None:
            return False
        opponent = BLUE if self.turn == RED else RED
        directions = [(0, -1, 0, 1), (-1, 0, 1, 0)]
        for dx1, dy1, dx2, dy2 in directions:
            x1, y1 = x + dx1, y + dy1
            x2, y2 = x + dx2, y + dy2
            if (0 <= x1 < len(self.board[0]) and 0 <= y1 < len(self.board) and 0 <= x2 < len(self.board[0]) and 0 <= y2 < len(self.board)):
                if self.board[x1][y1] == opponent and self.board[x2][y2] == opponent:
                    return False
        return True

    def check_and_remove_opponent_stones(self, x, y):
        opponent = BLUE if self.turn == RED else RED
        captured_count = 0  # このターンで取ったコマ数
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < len(self.board) and 0 <= ny < len(self.board[0]) and self.board[nx][ny] == opponent:
               ux, uy = nx + dx, ny + dy
               if 0 <= ux < len(self.board) and 0 <= uy < len(self.board[0]) and self.board[ux][uy] == self.turn:
                  self.board[nx][ny] = None
                  captured_count += 1  # 取ったコマをカウント
        # 累計カウントに追加
        if self.turn == RED:
            self.captured_red += captured_count
        else:
            self.captured_blue += captured_count

    def has_valid_move(self):
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                if self.can_place_piece(x, y):
                    return True
        return False

    def game_end(self):
        red_count = sum(row.count(RED) for row in self.board)
        blue_count = sum(row.count(BLUE) for row in self.board)
        if red_count > blue_count:
            result = f"Winner: Red\nRed: {red_count}, Blue: {blue_count}"
        elif blue_count > red_count:
            result = f"Winner: Blue\nRed: {red_count}, Blue: {blue_count}"
        else:  # 盤面のコマが同数の場合
            if self.captured_red > self.captured_blue:
                result = f"Winner: Red (Captured More)\nRed: {red_count}, Blue: {blue_count}\nCaptured - Red: {self.captured_red}, Blue: {self.captured_blue}"
            elif self.captured_blue > self.captured_red:
                result = f"Winner: Blue (Captured More)\nRed: {red_count}, Blue: {blue_count}\nCaptured - Red: {self.captured_red}, Blue: {self.captured_blue}"
            else:
                # ここで、取った数も同じなら後手（BLUE）の勝利
                result = f"Winner: Blue (Default Rule)\nRed: {red_count}, Blue: {blue_count}\nCaptured - Red: {self.captured_red}, Blue: {self.captured_blue}"
        return result

    def next_move(self, x, y):
        if self.can_place_piece(x, y):
           self.save_state()
           self.board[x][y] = self.turn
           self.check_and_remove_opponent_stones(x, y)

           self.draw_board()
           pygame.display.flip()

           # ターンを切り替え
           self.turn = BLUE if self.turn == RED else RED

           # 有効な手が残っているか確認
           if not self.has_valid_move():
               # ターンを切り替えて再度チェック
               self.turn = BLUE if self.turn == RED else RED
               if not self.has_valid_move():
                   # 両方のプレイヤーに有効な手がない場合はゲーム終了
                   result = self.game_end()
                   self.display_result(result)
                   return  # ゲーム終了後にこれ以上の処理を続けない
        else:
            print(f"Cannot place piece at ({x}, {y}).")

    def display_result(self, result):
        font = pygame.font.Font(None, 55)
        lines = result.split("\n")  # 結果を改行で分割
        y_offset = SIZE // 3  # テキストの表示開始位置

        for line in lines:
            text = font.render(line, True, BLACK)
            text_rect = text.get_rect(center=(SIZE // 2, y_offset))
            screen.blit(text, text_rect)
            y_offset += 80  # 次の行の位置を調整

        pygame.display.flip()
        pygame.time.wait(30000)
        pygame.quit()
        sys.exit()

def main():
    game = ZONE()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                x //= GRID_SIZE
                y //= GRID_SIZE
                game.next_move(x, y)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u:  # 'U'キーで1手戻す
                    game.undo()
                    print("1手戻しました！")
                elif event.key == pygame.K_p:  # 'P'キーで手番をパス
                       game.pass_turn()
                       print("手番をパスしました！")
        game.draw_board()
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

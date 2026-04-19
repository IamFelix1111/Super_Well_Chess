import sys
import threading
from typing import Callable, Literal

import pygame as pg

# 棋盘布局
GAP: int = 30
BLOCK_GAP: int = 40
CELL: int = 50
BLOCK_SIZE: int = CELL * 3
WIDTH: int = GAP * 2 + BLOCK_SIZE * 3 + BLOCK_GAP * 2
HEIGHT: int = GAP * 2 + BLOCK_SIZE * 4 + BLOCK_GAP * 3

blocks: list[tuple[int, int, int]] = [
    (GAP, BLOCK_SIZE + GAP + BLOCK_GAP, 0),
    (BLOCK_SIZE + GAP + BLOCK_GAP, BLOCK_SIZE + GAP + BLOCK_GAP, 9),
    (BLOCK_SIZE * 2 + GAP + BLOCK_GAP * 2, BLOCK_SIZE + GAP + BLOCK_GAP, 18),
    (GAP, BLOCK_SIZE * 2 + GAP + BLOCK_GAP * 2, 27),
    (BLOCK_SIZE + GAP + BLOCK_GAP, BLOCK_SIZE * 2 + GAP + BLOCK_GAP * 2, 36),
    (BLOCK_SIZE * 2 + GAP + BLOCK_GAP * 2, BLOCK_SIZE * 2 + GAP + BLOCK_GAP * 2, 45),
    (GAP, BLOCK_SIZE * 3 + GAP + BLOCK_GAP * 3, 54),
    (BLOCK_SIZE + GAP + BLOCK_GAP, BLOCK_SIZE * 3 + GAP + BLOCK_GAP * 3, 63),
    (BLOCK_SIZE * 2 + GAP + BLOCK_GAP * 2, BLOCK_SIZE * 3 + GAP + BLOCK_GAP * 3, 72),
    (WIDTH // 2 - BLOCK_SIZE // 2, GAP, 81)
]

# 颜色
WHITE: pg.Color = pg.Color(255, 255, 255)
GREEN: pg.Color = pg.Color(0, 220, 80)
BLUE: pg.Color = pg.Color(0, 100, 255)
RED: pg.Color = pg.Color(255, 0, 0)
BLACK: pg.Color = pg.Color(0, 0, 0)

send_click_to_server: Callable[[int], None] = lambda _: None
LOCK = threading.Lock()


class State:
    """
    游戏状态
    """

    def __init__(self, s: str | None = None) -> None:
        """
        初始化或从字符串导入
        :param s: 要导入的字符串
        :rtype: None
        """
        if s is None:
            self.turn: int = 0
            self.red: list[int] = []
            self.blue: list[int] = []
            self.red_last: list[int] = []
            self.blue_last: list[int] = []
            self.r_score: int = 0
            self.b_score: int = 0
            self.last_pos: int = -1
            self.game_over: bool = False
            self.at_last: bool = False
        else:
            p = s.split("|")
            self.turn = int(p[0])
            self.red = list(map(int, p[1].split(","))) if p[1] else []
            self.blue = list(map(int, p[2].split(","))) if p[2] else []
            self.red_last = list(map(int, p[3].split(","))) if p[3] else []
            self.blue_last = list(map(int, p[4].split(","))) if p[4] else []
            self.r_score = int(p[5])
            self.b_score = int(p[6])
            self.last_pos = int(p[7])
            self.game_over = p[8] == "True"
            self.at_last = p[9] == "True"

    def copy(self, new: object | None = None):
        """
        复制状态
        :param new: 复制目标
        :return: 复制的状态
        :rtype: State | None
        """
        if new is None:
            new = State()
        new.turn = self.turn
        new.red = self.red.copy()
        new.blue = self.blue.copy()
        new.red_last = self.red_last.copy()
        new.blue_last = self.blue_last.copy()
        new.r_score = self.r_score
        new.b_score = self.b_score
        new.last_pos = self.last_pos
        new.game_over = self.game_over
        new.at_last = self.at_last
        return new

    def __str__(self) -> str:
        """
        将状态转换为字符串
        :return: 字符串形式的状态
        :rtype: str
        """
        return (
            f"{self.turn}|"
            f"{','.join(map(str, self.red))}|"
            f"{','.join(map(str, self.blue))}|"
            f"{','.join(map(str, self.red_last))}|"
            f"{','.join(map(str, self.blue_last))}|"
            f"{self.r_score}|{self.b_score}|{self.last_pos}|{self.game_over}|{self.at_last}\n"
        )


# 全局游戏状态
game: State = State()


def set_send_click_to_server(func: Callable[[int], None]) -> None:
    """
    设置 send_click_to_server
    :param func: 设置 send_click_to_server 的值
    :rtype: None
    """
    global send_click_to_server
    send_click_to_server = func


def getlines(base: int) -> list[tuple[int, int, int]]:
    """
    获取一个小九宫格内所有8条连线
    :param base: 小九宫格起始编号
    :return: 所有连线三元组
    :rtype: list[tuple[int, int, int]]
    """
    return [
        (base + 0, base + 1, base + 2),
        (base + 3, base + 4, base + 5),
        (base + 6, base + 7, base + 8),
        (base + 0, base + 3, base + 6),
        (base + 1, base + 4, base + 7),
        (base + 2, base + 5, base + 8)
    ]


def get_line_coords(bid: int, line_idx: int) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    获取指定小棋盘与连线的屏幕坐标
    :param bid: 小棋盘编号
    :param line_idx: 连线索引(0-7)
    :return: 连线的起止坐标
    :rtype: tuple[tuple[int, int], tuple[int, int]]
    """
    x0, y0, _ = blocks[bid]
    x1 = x0 + BLOCK_SIZE
    y1 = y0 + BLOCK_SIZE
    lines = [
        ((x0, y0 + 25), (x1, y0 + 25)),
        ((x0, y0 + 75), (x1, y0 + 75)),
        ((x0, y0 + 125), (x1, y0 + 125)),
        ((x0 + 25, y0), (x0 + 25, y1)),
        ((x0 + 75, y0), (x0 + 75, y1)),
        ((x0 + 125, y0), (x0 + 125, y1)),
    ]
    return lines[line_idx]


def is_block_full(bid: int) -> bool:
    """
    判断指定小棋盘是否已下满9子
    :param bid: 小棋盘编号
    :return: 已满返回True，否则False
    :rtype: bool
    """
    cnt = 0
    for p in game.red + game.blue:
        if p // 9 == bid:
            cnt += 1
    return cnt >= 9


def get_allowed_block() -> int:
    """
    获取当前允许落子的小棋盘
    :return: 允许落子的棋盘编号，-1表示可任意落子
    :rtype: int
    """
    if game.at_last:
        return 9
    if game.last_pos == -1:
        return -1
    target = game.last_pos % 9
    if is_block_full(target):
        return -1
    return target


def is_legal(pos: int) -> bool:
    """
    判断某位置是否可以落子
    :param pos: 全局落子位置
    :return: 合法返回True，否则False
    :rtype: bool
    """
    b = get_allowed_block()
    if game.game_over:
        return False
    if pos // 9 == 9 and not game.at_last:
        return False
    if b == -1:
        return True
    return pos // 9 == b


def draw_board(screen: pg.surface.Surface) -> None:
    """
    绘制整个九宫棋盘的网格线
    :param screen: 游戏显示窗口
    :rtype: None
    """
    for x, y, _ in blocks:
        for i in range(4):
            pg.draw.line(screen, WHITE, (x, y + i * CELL),
                         (x + BLOCK_SIZE, y + i * CELL), 1)
            pg.draw.line(screen, WHITE, (x + i * CELL, y),
                         (x + i * CELL, y + BLOCK_SIZE), 1)


def draw_all_pieces(screen: pg.surface.Surface) -> None:
    """
    绘制所有红蓝棋子与胜利连线
    :param screen: 游戏显示窗口
    :rtype: None
    """
    for pos in game.red + game.red_last:
        bix, biy, _ = blocks[pos // 9]
        px = bix + (pos % 3) * CELL + 25
        py = biy + (pos // 3 % 3) * CELL + 25
        pg.draw.circle(screen, RED, (px, py), 15, 2)

    for pos in game.blue + game.blue_last:
        bix, biy, _ = blocks[pos // 9]
        px = bix + (pos % 3) * CELL + 25
        py = biy + (pos // 3 % 3) * CELL + 25
        pg.draw.circle(screen, BLUE, (px, py), 15, 2)

    for bid in range(10):
        for line_idx in range(6):
            base = bid * 9
            a, b, c = getlines(base)[line_idx]
            if a in game.red + game.red_last and b in game.red + game.red_last and c in game.red + game.red_last:
                line = get_line_coords(bid, line_idx)
                pg.draw.line(screen, RED, line[0], line[1], 3)
            if a in game.blue + game.blue_last and b in game.blue + game.blue_last and c in game.blue + game.blue_last:
                line = get_line_coords(bid, line_idx)
                pg.draw.line(screen, BLUE, line[0], line[1], 3)


def check_score() -> None:
    """
    遍历所有小棋盘，重新统计双方得分
    :rtype: None
    """
    game.r_score = 0
    game.b_score = 0
    handle_advantage_blocks()
    for bid in range(10):
        base = bid * 9
        for a, b, c in getlines(base):
            if a in game.red + game.red_last and b in game.red + game.red_last and c in game.red + game.red_last:
                game.r_score += 1
            if a in game.blue + game.blue_last and b in game.blue + game.blue_last and c in game.blue + game.blue_last:
                game.b_score += 1


def is_advantage_block(bid: int) -> tuple[bool, bool]:
    """
    判断一个宫格是否是优势宫格
    :param bid: 小棋盘编号
    :return: (红方优势, 蓝方优势)
    :rtype: tuple[bool, bool]
    """
    base = bid * 9
    red_has_line = False
    blue_has_line = False

    for a, b, c in getlines(base):
        if a in game.red and b in game.red and c in game.red:
            red_has_line = True
        if a in game.blue and b in game.blue and c in game.blue:
            blue_has_line = True

    red_adv = red_has_line and not blue_has_line
    blue_adv = blue_has_line and not red_has_line
    return red_adv, blue_adv


def handle_advantage_blocks() -> None:
    """
    处理优势宫格
    :rtype: None
    """
    for bid in range(10):
        r_adv, b_adv = is_advantage_block(bid)
        if not is_block_full(bid):
            continue
        if r_adv and (81 + bid) not in game.red_last:
            if bid == 9:
                game.r_score += 1
            else:
                game.red_last.append(81 + bid)
        elif b_adv and (81 + bid) not in game.blue_last:
            if bid == 9:
                game.b_score += 1
            else:
                game.blue_last.append(81 + bid)


def draw_special_border(screen: pg.surface.Surface) -> None:
    """
    绘制当前允许落子区域的绿色提示框
    :param screen: 游戏显示窗口
    :rtype: None
    """
    for bid in range(10):
        r_adv, b_adv = is_advantage_block(bid)
        x, y, _ = blocks[bid]
        if r_adv:
            pg.draw.rect(screen, RED, (x - 1, y - 1, BLOCK_SIZE + 2, BLOCK_SIZE + 2), 2)
        elif b_adv:
            pg.draw.rect(screen, BLUE, (x - 1, y - 1, BLOCK_SIZE + 2, BLOCK_SIZE + 2), 2)
    bid = get_allowed_block()
    if bid != -1:
        x, y, _ = blocks[bid]
        pg.draw.rect(screen, GREEN, (x - 2, y - 2, BLOCK_SIZE + 4, BLOCK_SIZE + 4), 3)


def handle_click_client(mx: int, my: int) -> None:
    """
    处理鼠标点击落子
    :param mx: 鼠标点击x坐标
    :param my: 鼠标点击y坐标
    :rtype: None
    """
    pos = -1
    for (bx, by, bid) in blocks:
        if bx <= mx < bx + BLOCK_SIZE and by <= my < by + BLOCK_SIZE:
            dx = (mx - bx) // CELL
            dy = (my - by) // CELL
            pos = bid + dy * 3 + dx
            break
    if pos != -1 and pos not in game.red and pos not in game.blue and is_legal(pos):
        send_click_to_server(pos)


def handle_click_server(pos: int) -> None:
    """
    处理鼠标点击落子
    :param pos: 落子位置
    :rtype: None
    """
    if pos != -1 and pos not in game.red and pos not in game.blue and is_legal(pos):
        bid = pos // 9
        if not is_block_full(bid):
            if game.turn == 0:
                game.red.append(pos)
            else:
                game.blue.append(pos)
            game.last_pos = pos
            game.turn = 1 - game.turn
            process()


def display_turn_tip(screen: pg.surface.Surface, font: pg.font.Font) -> None:
    """
    显示分数和回合提示
    :param screen: 游戏显示窗口
    :param font: 字体
    :rtype: None
    """
    screen.blit(font.render(f'红: {game.r_score}', True, RED),
                (GAP + BLOCK_SIZE / 2 - 40, GAP + BLOCK_SIZE / 2 - 40))
    screen.blit(font.render(f'蓝: {game.b_score}', True, BLUE),
                (GAP + BLOCK_SIZE / 2 - 40, GAP + BLOCK_SIZE / 2))
    if not game.game_over:
        if game.turn == 0:
            t1 = font.render("红方", True, RED)
            t2 = font.render("执子", True, RED)
        else:
            t1 = font.render("蓝方", True, BLUE)
            t2 = font.render("执子", True, BLUE)
        screen.blit(t1, (WIDTH - GAP - BLOCK_SIZE / 2 - 40, GAP + BLOCK_SIZE / 2 - 40))
        screen.blit(t2, (WIDTH - GAP - BLOCK_SIZE / 2 - 40, GAP + BLOCK_SIZE / 2))


def handle_last() -> None:
    """
    判断最后并显示
    :rtype: None
    """
    if len(game.red) + len(game.blue) >= 81 and not game.at_last:
        game.at_last = True
        game.red += game.red_last
        game.blue += game.blue_last
        check_score()


def handle_end() -> None:
    """
    判断结束
    :rtype: None
    """
    if len(game.red) + len(game.blue) >= 90 and not game.game_over:
        game.game_over = True


def process() -> None:
    """
    处理
    :rtype: None
    """
    check_score()
    handle_last()
    handle_end()


def display_end(screen: pg.surface.Surface, font: pg.font.Font) -> None:
    """
    显示结束
    :param screen: 游戏显示窗口
    :param font: 字体
    :rtype: None
    """
    if game.game_over:
        txt = font.render('平局', True, WHITE)
        if game.r_score > game.b_score:
            txt = font.render('红胜', True, RED)
        elif game.b_score > game.r_score:
            txt = font.render('蓝胜', True, BLUE)
        screen.blit(txt, (WIDTH - GAP - BLOCK_SIZE / 2 - 40, GAP + BLOCK_SIZE / 2 - 20))


def render(screen: pg.surface.Surface, font: pg.font.Font) -> None:
    """
    渲染
    :param screen: 游戏显示窗口
    :param font: 字体
    :rtype: None
    """
    screen.fill(BLACK)
    draw_board(screen)
    draw_all_pieces(screen)
    draw_special_border(screen)
    display_turn_tip(screen, font)
    display_end(screen, font)


def print_err(*values: object, sep: str | None = " ",
              end: str | None = "\n", flush: Literal[False] = False) -> None:
    """
    Prints the values to sys.stderr.
    :param values: values to print.
    :param sep: string inserted between values, default a space.
    :param end: string appended after the last value, default a newline.
    :param flush: whether to forcibly flush the stream.
    :rtype: None
    """
    print(values, sep=sep, end=end, file=sys.stderr, flush=flush)

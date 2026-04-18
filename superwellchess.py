# superwellchess.py
from typing import Callable

import pygame as pg

# 游戏状态
turn: int = 0
red: list[int] = []
blue: list[int] = []
red_last: list[int] = []
blue_last: list[int] = []
r_score: int = 0
b_score: int = 0
last_pos: int = -1
game_over: bool = False
at_last: bool = False

# 棋盘布局
GAP: int = 30
BLOCK_GAP: int = 40
CELL: int = 50
BLOCK_SIZE: int = CELL * 3
WIDTH: int = GAP * 2 + BLOCK_SIZE * 3 + BLOCK_GAP * 2
HEIGHT: int = GAP * 2 + BLOCK_SIZE * 4 + BLOCK_GAP * 3

blocks: list[list[int]] = [
    [GAP, BLOCK_SIZE + GAP + BLOCK_GAP, 0],
    [BLOCK_SIZE + GAP + BLOCK_GAP, BLOCK_SIZE + GAP + BLOCK_GAP, 9],
    [BLOCK_SIZE * 2 + GAP + BLOCK_GAP * 2, BLOCK_SIZE + GAP + BLOCK_GAP, 18],
    [GAP, BLOCK_SIZE * 2 + GAP + BLOCK_GAP * 2, 27],
    [BLOCK_SIZE + GAP + BLOCK_GAP, BLOCK_SIZE * 2 + GAP + BLOCK_GAP * 2, 36],
    [BLOCK_SIZE * 2 + GAP + BLOCK_GAP * 2, BLOCK_SIZE * 2 + GAP + BLOCK_GAP * 2, 45],
    [GAP, BLOCK_SIZE * 3 + GAP + BLOCK_GAP * 3, 54],
    [BLOCK_SIZE + GAP + BLOCK_GAP, BLOCK_SIZE * 3 + GAP + BLOCK_GAP * 3, 63],
    [BLOCK_SIZE * 2 + GAP + BLOCK_GAP * 2, BLOCK_SIZE * 3 + GAP + BLOCK_GAP * 3, 72],
    [WIDTH // 2 - BLOCK_SIZE // 2, GAP, 81]
]

# 颜色
WHITE: pg.Color = pg.Color(255, 255, 255)
GREEN: pg.Color = pg.Color(0, 220, 80)
BLUE: pg.Color = pg.Color(0, 100, 255)
RED: pg.Color = pg.Color(255, 0, 0)
BLACK: pg.Color = pg.Color(0, 0, 0)

send_click_to_server: Callable[[int], None] = lambda _: None


def set_send_click_to_server(func: Callable[[int], None]):
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
    for p in red + blue:
        if p // 9 == bid:
            cnt += 1
    return cnt >= 9


def get_allowed_block() -> int:
    """
    获取当前允许落子的小棋盘
    :return: 允许落子的棋盘编号，-1表示可任意落子
    :rtype: int
    """
    if at_last:
        return 9
    if last_pos == -1:
        return -1
    target = last_pos % 9
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
    if game_over:
        return False
    if pos // 9 == 9 and not at_last:
        return False
    if b == -1:
        return True
    return pos // 9 == b


def draw_board(screen: pg.surface.Surface) -> None:
    """
    绘制整个九宫棋盘的网格线
    :param screen: 游戏显示窗口
    :return: 无返回值
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
    :return: 无返回值
    :rtype: None
    """
    for pos in red + red_last:
        bix, biy, _ = blocks[pos // 9]
        px = bix + (pos % 3) * CELL + 25
        py = biy + (pos // 3 % 3) * CELL + 25
        pg.draw.circle(screen, RED, (px, py), 15, 2)

    for pos in blue + blue_last:
        bix, biy, _ = blocks[pos // 9]
        px = bix + (pos % 3) * CELL + 25
        py = biy + (pos // 3 % 3) * CELL + 25
        pg.draw.circle(screen, BLUE, (px, py), 15, 2)

    for bid in range(10):
        for line_idx in range(6):
            base = bid * 9
            a, b, c = getlines(base)[line_idx]
            if a in red + red_last and b in red + red_last and c in red + red_last:
                line = get_line_coords(bid, line_idx)
                pg.draw.line(screen, RED, line[0], line[1], 3)
            if a in blue + blue_last and b in blue + blue_last and c in blue + blue_last:
                line = get_line_coords(bid, line_idx)
                pg.draw.line(screen, BLUE, line[0], line[1], 3)


def check_score() -> None:
    """
    遍历所有小棋盘，重新统计双方得分
    :return: 无返回值
    :rtype: None
    """
    global r_score, b_score
    r_score = 0
    b_score = 0
    handle_advantage_blocks()
    for bid in range(10):
        base = bid * 9
        for a, b, c in getlines(base):
            if a in red + red_last and b in red + red_last and c in red + red_last:
                r_score += 1
            if a in blue + blue_last and b in blue + blue_last and c in blue + blue_last:
                b_score += 1


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
        if a in red and b in red and c in red:
            red_has_line = True
        if a in blue and b in blue and c in blue:
            blue_has_line = True

    red_adv = red_has_line and not blue_has_line
    blue_adv = blue_has_line and not red_has_line
    return red_adv, blue_adv


def handle_advantage_blocks() -> None:
    """
    处理优势宫格
    :return: 无返回值
    :rtype: None
    """
    global r_score, b_score
    for bid in range(10):
        r_adv, b_adv = is_advantage_block(bid)
        if not is_block_full(bid):
            continue
        if r_adv and 81 + bid not in red_last:
            if bid == 9:
                r_score += 1
            else:
                red_last.append(81 + bid)
        elif b_adv and 81 + bid not in blue_last:
            if bid == 9:
                b_score += 1
            else:
                blue_last.append(81 + bid)


def draw_special_border(screen: pg.surface.Surface) -> None:
    """
    绘制当前允许落子区域的绿色提示框
    :param screen: 游戏显示窗口
    :return: 无返回值
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
    :return: 无返回值
    :rtype: None
    """
    global turn, last_pos
    pos = -1
    for (bx, by, bid) in blocks:
        if bx <= mx < bx + BLOCK_SIZE and by <= my < by + BLOCK_SIZE:
            dx = (mx - bx) // CELL
            dy = (my - by) // CELL
            pos = bid + dy * 3 + dx
            break
    if pos != -1 and pos not in red and pos not in blue and is_legal(pos):
        send_click_to_server(pos)


def handle_click_server(pos: int) -> None:
    """
    处理鼠标点击落子
    :param pos: 落子位置
    :return: 无返回值
    :rtype: None
    """
    global turn, last_pos
    if pos != -1 and pos not in red and pos not in blue and is_legal(pos):
        bid = pos // 9
        if not is_block_full(bid):
            if turn == 0:
                red.append(pos)
            else:
                blue.append(pos)
            last_pos = pos
            process()
            turn += 1
            turn %= 2


def display_turn_tip(screen: pg.surface.Surface, font: pg.font.Font) -> None:
    """
    显示分数和回合提示
    :param screen: 游戏显示窗口
    :param font: 字体
    :return: 无返回值
    :rtype: None
    """
    screen.blit(font.render(f'红: {r_score}', True, RED),
                (GAP + BLOCK_SIZE / 2 - 40, GAP + BLOCK_SIZE / 2 - 40))
    screen.blit(font.render(f'蓝: {b_score}', True, BLUE),
                (GAP + BLOCK_SIZE / 2 - 40, GAP + BLOCK_SIZE / 2))
    if not game_over:
        if turn == 0:
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
    :return: 无返回值
    :rtype: None
    """
    global at_last, red, blue
    if len(red) + len(blue) >= 81 and not at_last:
        at_last = True
        red += red_last
        blue += blue_last
        check_score()


def handle_end() -> None:
    """
    判断结束
    :return: 无返回值
    :rtype: None
    """
    global game_over
    if len(red) + len(blue) >= 90 and not game_over:
        game_over = True


def process() -> None:
    check_score()
    handle_last()
    handle_end()


def display_end(screen: pg.surface.Surface, font: pg.font.Font) -> None:
    """
    显示结束
    :param screen: 游戏显示窗口
    :param font: 字体
    :return: 无返回值
    :rtype: None
    """
    if game_over:
        txt = font.render('平局', True, WHITE)
        if r_score > b_score:
            txt = font.render('红胜', True, RED)
        elif b_score > r_score:
            txt = font.render('蓝胜', True, BLUE)
        screen.blit(txt, (WIDTH - GAP - BLOCK_SIZE / 2 - 40, GAP + BLOCK_SIZE / 2 - 20))


def render(screen: pg.surface.Surface, font: pg.font.Font) -> None:
    """
    渲染界面
    :param screen: 游戏显示窗口
    :param font: 字体
    :return: 无返回值
    :rtype: None
    """
    screen.fill(BLACK)
    draw_board(screen)
    draw_all_pieces(screen)
    draw_special_border(screen)
    display_turn_tip(screen, font)
    display_end(screen, font)

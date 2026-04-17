# Super_Well_Chess_Single.pyw
# 单人 单机器
from superwellchess import *

def main() -> None:
    """
    游戏主函数：初始化、主循环、事件处理、画面刷新
    :return: 无返回值
    :rtype: None
    """
    pg.init()
    pg.display.set_caption('Super Well Chess')
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    font = pg.font.SysFont('DengXian', 40)
    clk = pg.time.Clock()

    while True:
        screen.fill(BLACK)
        draw_board(screen)
        draw_all_pieces(screen)

        for e in pg.event.get():
            if e.type == pg.QUIT:
                pg.quit()
                return
            if e.type == pg.MOUSEBUTTONDOWN:
                mx, my = e.pos
                handle_click(mx, my)

        draw_special_border(screen)
        display_turn_tip(screen, font)
        handle_end(screen, font)

        pg.display.update()
        clk.tick(60)


if __name__ == '__main__':
    main()

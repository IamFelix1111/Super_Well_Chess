# Super_Well_Chess.pyw
# 双人 单机器
from superwellchess import *


def main() -> None:
    """
    游戏主函数：初始化、主循环、事件处理、画面刷新
    :return: 无返回值
    :rtype: None
    """
    pg.init()
    pg.display.set_caption('超级井字棋')
    set_send_click_to_server(handle_click_server)
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    font = pg.font.SysFont('DengXian', 40)
    clk = pg.time.Clock()

    while True:
        render(screen, font)
        pg.display.update()
        clk.tick(60)

        for e in pg.event.get():
            if e.type == pg.QUIT:
                pg.quit()
                return
            if e.type == pg.MOUSEBUTTONDOWN:
                mx, my = e.pos
                handle_click_client(mx, my)


if __name__ == '__main__':
    main()

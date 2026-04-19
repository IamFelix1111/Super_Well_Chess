import socket
from superwellchess import *

HOST: str = "127.0.0.1"
PORT: int = 65432

is_server: bool = False
conn: socket.socket | None = None


def send_state() -> None:
    """
    发送状态
    :rtype: None
    """
    if is_server and conn is not None:
        try:
            conn.sendall(f"STATE|{str(game)}".encode())
        except Exception as e:
            print_err(e)


def receive() -> None:
    """
    接收消息
    :rtype: None
    """
    if conn is None:
        return
    buf = b""
    while True:
        try:
            d = conn.recv(4096)
            if not d:
                break
            buf += d
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                msg = line.decode().strip()
                if not msg:
                    continue

                if msg.startswith("MOVE") and is_server:
                    pos = int(msg.split("|")[1])
                    handle_click_server(pos)
                    send_state()

                elif msg.startswith("STATE|") and not is_server:
                    data = msg.split("|", 1)[1]
                    State(data).copy(game)
        except Exception as e:
            print_err(e)


def start_server() -> None:
    """
    启动服务器
    :rtype: None
    """
    global conn
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    conn, _ = s.accept()
    threading.Thread(target=receive, daemon=True).start()
    send_state()


def start_client() -> None:
    """
    启动客户端
    :rtype: None
    """
    global conn
    conn = socket.socket()
    # noinspection PyUnresolvedReferences
    conn.connect((HOST, PORT))
    threading.Thread(target=receive, daemon=True).start()


def server_click(pos: int) -> None:
    """
    服务器端点击
    :param pos: 落子位置
    :rtype: None
    """
    handle_click_server(pos)
    send_state()


def client_click(pos: int) -> None:
    """
    客户端点击
    :param pos: 落子位置
    :rtype: None
    """
    try:
        # noinspection PyUnresolvedReferences
        conn.sendall(f"MOVE|{pos}\n".encode())
    except Exception as e:
        print_err(e)


def main() -> None:
    """
    游戏主函数：初始化、主循环、事件处理、画面刷新
    :rtype: None
    """
    global is_server
    pg.init()
    pg.display.set_caption('超级井字棋')
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    font = pg.font.SysFont("DengXian", 40)
    clk = pg.time.Clock()

    if len(sys.argv) > 1 and sys.argv[1] == "server":
        is_server = True
        set_send_click_to_server(server_click)
        threading.Thread(target=start_server, daemon=True).start()
    elif len(sys.argv) > 1 and sys.argv[1] == "client":
        set_send_click_to_server(client_click)
        threading.Thread(target=start_client, daemon=True).start()
    else:
        set_send_click_to_server(handle_click_server)

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


if __name__ == "__main__":
    main()

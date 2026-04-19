# server.py
import socket
import threading
import json
from superwellchess import *

HOST = "127.0.0.1"
PORT = 65432
client_conn = None

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

# 全局锁：保护所有跨模块全局变量 + client_conn
LOCK = threading.Lock()


def client_handler(conn):
    global client_conn
    with LOCK:
        client_conn = conn
        state = {
            "turn": turn,
            "red": red,
            "blue": blue,
            "red_last": red_last,
            "blue_last": blue_last,
            "r_score": r_score,
            "b_score": b_score,
            "last_pos": last_pos,
            "game_over": game_over,
            "at_last": at_last
        }

    try:
        client_conn.sendall((json.dumps(state) + "\n").encode())
    except Exception:
        client_conn = None

    while True:
        try:
            data = conn.recv(1024).decode().strip()
            if not data:
                break
        except:
            break

        # 👇 修复：锁包住【处理落子 + 发送状态】整个流程
        with LOCK:
            handle_click_server(int(data))
            # 就在锁内打包最新状态！！
            state = {
                "turn": turn,
                "red": red,
                "blue": blue,
                "red_last": red_last,
                "blue_last": blue_last,
                "r_score": r_score,
                "b_score": b_score,
                "last_pos": last_pos,
                "game_over": game_over,
                "at_last": at_last
            }

        try:
            client_conn.sendall((json.dumps(state) + "\n").encode())
        except Exception:
            client_conn = None


def accept_thread():
    while True:
        try:
            conn, _ = server_socket.accept()
            threading.Thread(target=client_handler, args=(conn,), daemon=True).start()
        except:
            break


# 启动网络线程
threading.Thread(target=accept_thread, daemon=True).start()
set_send_click_to_server(handle_click_server)


def main():
    pg.init()
    pg.display.set_caption("超级井字棋 - 服务端(红方)")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    font = pg.font.SysFont('DengXian', 40)
    clk = pg.time.Clock()

    while True:
        # GUI 渲染前加锁 → 读取最新的全局变量
        with LOCK:
            render(screen, font)

        pg.display.update()
        clk.tick(60)

        for e in pg.event.get():
            if e.type == pg.QUIT:
                pg.quit()
                return

            if e.type == pg.MOUSEBUTTONDOWN:
                mx, my = e.pos
                # 客户端点击修改全局变量 → 必须加锁
                with LOCK:
                    handle_click_client(mx, my)
                    state = {
                        "turn": turn,
                        "red": red,
                        "blue": blue,
                        "red_last": red_last,
                        "blue_last": blue_last,
                        "r_score": r_score,
                        "b_score": b_score,
                        "last_pos": last_pos,
                        "game_over": game_over,
                        "at_last": at_last
                    }

                try:
                    client_conn.sendall((json.dumps(state) + "\n").encode())
                except Exception:
                    client_conn = None


if __name__ == "__main__":
    main()
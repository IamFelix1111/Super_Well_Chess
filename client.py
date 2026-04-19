# client.py
import socket
import threading
import json
from superwellchess import *
LOCK = threading.Lock()

SERVER_IP = "127.0.0.1"
PORT = 65432

s = socket.socket()
s.connect((SERVER_IP, PORT))


def send_click(pos):
    try:
        s.sendall((f"{pos}\n").encode())
    except:
        pass


set_send_click_to_server(send_click)


def recv_thread():
    buffer = ""
    while True:
        data = s.recv(4096).decode()
        if not data: break
        buffer += data

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            if not line.strip():
                continue
            state = json.loads(line.strip())

            with LOCK:
                update(
                    turn_=state["turn"],
                    red_=state["red"],
                    blue_=state["blue"],
                    red_last_=state["red_last"],
                    blue_last_=state["blue_last"],
                    r_score_=state["r_score"],
                    b_score_=state["b_score"],
                    last_pos_=state["last_pos"],
                    game_over_=state["game_over"],
                    at_last_=state["at_last"]
                )


threading.Thread(target=recv_thread, daemon=True).start()


def main():
    pg.init()
    pg.display.set_caption("超级井字棋 - 客户端(蓝方)")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    font = pg.font.SysFont('DengXian', 40)
    clk = pg.time.Clock()

    while True:
        # ====================== 关键：加锁渲染 ======================
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
                handle_click_client(mx, my)


if __name__ == "__main__":
    main()
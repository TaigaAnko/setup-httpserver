from collections import deque
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
import json
import time
import threading


class CallbackServer(HTTPServer):

    def __init__(self, call_back_deque, *args, **kwargs) -> None:
        HTTPServer.__init__(self, *args, **kwargs)
        self.callback = call_back_deque


class CallbackHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    handling callback (POST request) from RCS
    """

    def do_POST(self) -> None:
        content_length = int(self.headers["content-length"])
        content_data = self.rfile.read(content_length).decode("utf-8")
        content_data_json = json.loads(content_data)
        # print(content_data_json)
        # キューにデータを追加
        self.server.callback.append(content_data_json)

        # Responsive to RCS
        res_data = {"code": "0", "message": "Success", "reqCode": "", "data": ""}
        json_res_data = json.dumps(res_data)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(json_res_data.encode())


class CallbackServerSetting:
    """コールバックサーバーの立ち上げ処理"""

    _callback_ip: str
    _callback_port: str

    def __init__(self, ip: str, port: int, call_back_deque: deque) -> None:
        self._callback_ip = ip
        self._callback_port = port
        self.call_back_deque = call_back_deque

    @property
    def set_up(self) -> object | None:
        try:
            self.callback_server = CallbackServer(
                self.call_back_deque,
                (self._callback_ip, int(self._callback_port)),
                CallbackHTTPRequestHandler,
            )
            return self.callback_server
        except Exception as e:
            print(f"error:{e}")
            return


class RunCallbackServer:
    def __init__(self, server: HTTPServer) -> None:
        self.server = server

    def start(self):
        try:
            print("Callback Server was started.")
            self.server.serve_forever()

        except Exception:
            self.server.shutdown()

    def close(self):
        self.server.shutdown()


if __name__ == "__main__":
    q = deque([])
    start_time = time.time()
    call_back_deque = deque([])
    server_setting = CallbackServerSetting(
        ip="192.168.5.153",
        port=8080,
        call_back_deque=q
    )
    server_setup = server_setting.set_up
    callback_server = RunCallbackServer(server_setup)
    server_thread = threading.Thread(target=callback_server.start)
    server_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Ctrl+Cが押されたときにスレッドを終了させる
        callback_server.close()
        server_thread.join()  # スレッドが終了するのを待つ
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print("処理時間:", elapsed_time, "秒")

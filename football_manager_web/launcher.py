import os  # noqa: F401
import sys  # noqa: F401
import time
import webbrowser
import threading


def open_browser():
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000')


if __name__ == '__main__':
    try:
        print('============================================================')
        print('   FOOTBALL MANAGER WEB - HUẤN LUYỆN VIÊN BÓNG ĐÁ')
        print('============================================================')
        print('Đang khởi động máy chủ và mở trình duyệt web...')
        print('Địa chỉ: http://127.0.0.1:5000')
        print('(Vui lòng giữ cửa sổ này khi đang chơi game)')
        print('============================================================')
        threading.Thread(target=open_browser, daemon=True).start()
        from app import app
        app.run(host='127.0.0.1', port=5000, debug=False)
    except Exception as e:
        print(f'\n[LỖI]: {e}')
        input('\nBấm Enter để thoát...')

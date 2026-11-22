# -*- coding: utf-8 -*-
"""
app.py - Entry point khởi chạy Football Manager Web.
Toàn bộ cấu hình, services, models và routes đã được tổ chức trong package `football/`.
"""
import threading
import time
import webbrowser

from football import create_app

app = create_app()


def auto_open_browser():
    time.sleep(1.0)
    try:
        webbrowser.open('http://127.0.0.1:5000', new=2)
    except Exception:
        pass


if __name__ == '__main__':
    threading.Thread(target=auto_open_browser, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)

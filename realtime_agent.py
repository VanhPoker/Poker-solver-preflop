import pygetwindow as gw
import time
import json
import os
import random
import numpy as np
import cv2
import sys
import dxcam
from mss import mss

# --- CONFIG DEBUG ---
# Chế độ debug vẫn hữu ích để xem ảnh chụp được là gì
DEBUG_MODE = True
# --------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

try:
    from vision import analyze_table, find_template
except ImportError:
    print(f"Lỗi: Không tìm thấy file vision.py. Đang tìm kiếm tại: {SCRIPT_DIR}")
    analyze_table = None
    find_template = None

class RealTimeAgent:
    def __init__(self):
        self.poker_window_titles = ["Rush & Cash", "Spin & Go", "Tournament", "Poker"]
        self.last_active_window_id = None
        self.action_panel_template = os.path.join(SCRIPT_DIR, 'templates', 'action_panel.png')
        self.test_captures_dir = os.path.join(SCRIPT_DIR, 'test_captures')
        self.index_data = self.load_index()
        
        self.camera_dxcam = dxcam.create(output_color="BGR")
        self.camera_mss = mss()
        
        if not os.path.exists(self.test_captures_dir):
            os.makedirs(self.test_captures_dir)

    def load_index(self):
        index_path = os.path.join(SCRIPT_DIR, "poker_charts", "index.json")
        try:
            with open(index_path, "r", encoding='utf-8') as f: return json.load(f)
        except Exception as e:
            print(f"Lỗi nghiêm trọng: Không thể tải file chỉ mục tại '{index_path}'. Lỗi: {e}")
            return {}
            
    def process_table(self, window):
        print(f"\n--- Bàn chơi được kích hoạt: {window.title} ---")
        try:
            region = (window.left, window.top, window.right, window.bottom)
            
            # --- LOGIC CHỤP ẢNH HYBRID ---
            screenshot_cv = self.camera_dxcam.grab(region=region)

            if screenshot_cv is None:
                print("Cảnh báo: dxcam thất bại. Chuyển sang phương pháp thay thế (mss)...")
                monitor = {"top": window.top, "left": window.left, "width": window.width, "height": window.height}
                sct_img = self.camera_mss.grab(monitor)
                img = np.array(sct_img)
                screenshot_cv = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            if screenshot_cv is None:
                print("Lỗi nghiêm trọng: Cả hai phương pháp chụp đều thất bại.")
                return

            # *** LOGIC MỚI: LƯU ẢNH NGAY LẬP TỨC ***
            timestamp = int(time.time())
            capture_filename = os.path.join(self.test_captures_dir, f"capture_{timestamp}.png")
            cv2.imwrite(capture_filename, screenshot_cv)
            print(f"✅ ĐÃ CHỤP VÀ LƯU ẢNH THÀNH CÔNG TẠI: {capture_filename}")

            if DEBUG_MODE:
                # Hiển thị ảnh vừa chụp để bạn xem trực tiếp
                cv2.imshow('Debug Capture Window', screenshot_cv)
                cv2.waitKey(1)
        
        except Exception as e:
            print(f"Đã xảy ra lỗi trong quá trình xử lý bàn chơi: {e}")

    def run(self):
        print("Real-Time Agent (Chế độ Test Chụp Ảnh) đang chạy...")
        self.camera_dxcam.start(target_fps=5)
        try:
            while True:
                try:
                    active_window = gw.getActiveWindow()
                    if active_window and active_window._hWnd != self.last_active_window_id:
                        self.last_active_window_id = active_window._hWnd
                        if any(title in active_window.title for title in self.poker_window_titles):
                            self.process_table(active_window)
                except Exception: pass
                time.sleep(0.5)
        finally:
            self.camera_dxcam.stop()
            if DEBUG_MODE:
                cv2.destroyAllWindows()

if __name__ == "__main__":
    agent = RealTimeAgent()
    agent.run()

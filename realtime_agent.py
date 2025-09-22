import pygetwindow as gw
import time
import json
import os
import random
from PIL import ImageGrab

# Import các hàm từ module vision và "bộ não"
from vision import analyze_table
from poker_app import sanitize_hand # Giả sử poker_app.py cùng thư mục

class RealTimeAgent:
    def __init__(self):
        self.poker_window_titles = ["Rush & Cash", "Spin & Go", "Tournament"] # Tùy chỉnh
        self.last_active_window_id = None
        self.index_data = self.load_index()
        self.loaded_charts = {} # Cache để lưu các chart đã tải

    def load_index(self):
        """Tải file chỉ mục index.json."""
        try:
            with open("poker_charts/index.json", "r", encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Lỗi nghiêm trọng: Không thể tải index.json. {e}")
            return {}

    def load_specific_chart(self, file_path):
        """Tải một file chart cụ thể và lưu vào cache."""
        if file_path in self.loaded_charts:
            return self.loaded_charts[file_path]
        try:
            full_path = os.path.join("poker_charts", file_path)
            with open(full_path, "r", encoding='utf-8') as f:
                chart_data = json.load(f)
                self.loaded_charts[file_path] = chart_data
                return chart_data
        except Exception as e:
            print(f"Lỗi khi tải chart {file_path}: {e}")
            return None

    def get_decision_from_analysis(self, analysis):
        """
        Logic phức tạp để chuyển đổi kết quả phân tích thành quyết định.
        Đây là phần bạn cần xây dựng chi tiết.
        """
        # 1. Xác định Game Type, Chart Type từ tiêu đề cửa sổ (đã được phân tích)
        # 2. Xác định Main Situation, Scenario từ `analysis['actions_before']`
        # 3. Chuẩn hóa hand bài từ `analysis['my_hand']`
        
        # --- Logic ví dụ đơn giản ---
        game_type = "CashGame"
        chart_type = "100BB 6-Max GTO"
        
        main_situation = "Raise First In (RFI)"
        scenario = analysis.get("my_position")
        
        # Tải chart nếu cần
        chart_path = self.index_data.get(game_type, {}).get(chart_type)
        if not chart_path: return "Không tìm thấy chart"
        
        chart_data = self.load_specific_chart(chart_path)
        if not chart_data: return "Lỗi tải chart"

        # Tạm thời bỏ qua việc chuẩn hóa hand từ hình ảnh
        hand_to_lookup = "AKs" # Giả sử
        
        try:
            action = chart_data["charts"][main_situation][scenario][hand_to_lookup]
            return action
        except KeyError:
            return "Fold (Không có trong range)"
        # --- Kết thúc logic ví dụ ---

    def process_table(self, window):
        """Xử lý một cửa sổ bàn chơi đã được xác định."""
        print(f"\n--- Bàn chơi được kích hoạt: {window.title} ---")
        
        # 1. Chụp ảnh cửa sổ
        bbox = (window.left, window.top, window.right, window.bottom)
        screenshot = ImageGrab.grab(bbox)
        # Chuyển đổi ảnh sang định dạng OpenCV có thể dùng
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # 2. Gửi ảnh cho module "Đôi Mắt" để phân tích
        analysis = analyze_table(screenshot_cv)
        print("Kết quả phân tích từ Vision:", analysis)

        # 3. Lấy quyết định từ "Bộ Não"
        decision = self.get_decision_from_analysis(analysis)
        
        # 4. Áp dụng độ trễ ngẫu nhiên
        delay = random.uniform(0.8, 2.5)
        print(f"Quyết định: '{decision}'. Đang chờ {delay:.2f} giây...")
        time.sleep(delay)
        
        # 5. Hiển thị kết quả (tạm thời in ra console)
        print("---------------------------------")
        print(f"==> HÀNH ĐỘNG ĐỀ XUẤT: {decision}")
        print("---------------------------------")


    def run(self):
        """Vòng lặp chính - "Người Canh Gác"."""
        print("Real-Time Agent đang chạy... Theo dõi các cửa sổ poker.")
        while True:
            try:
                active_window = gw.getActiveWindow()
                if active_window and active_window._hWnd != self.last_active_window_id:
                    self.last_active_window_id = active_window._hWnd
                    
                    # Kiểm tra xem tiêu đề có khớp với bàn poker không
                    if any(title in active_window.title for title in self.poker_window_titles):
                        self.process_table(active_window)
                        
            except Exception as e:
                # Có thể xảy ra khi không có cửa sổ nào active
                pass
            
            time.sleep(0.5) # Giảm tải CPU

if __name__ == "__main__":
    agent = RealTimeAgent()
    agent.run()

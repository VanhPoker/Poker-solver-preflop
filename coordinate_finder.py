import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer
import pyautogui
import pygetwindow as gw

class CoordApp(QWidget):
    def __init__(self):
        super().__init__()
        self.ref_window = None
        self.ref_pos = (0, 0)
        self.ref_size = (1, 1) # (width, height), avoid division by zero
        self.top_left = None
        self.bottom_right = None

        self.setWindowTitle('Normalized Coordinate Finder')
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setGeometry(50, 50, 400, 300)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Hướng dẫn
        self.instructions_label = QLabel(
            "1. Nhấn nút 'Select Window' bên dưới.\n"
            "2. Bạn có 5 giây để click vào cửa sổ bàn poker."
        )
        self.instructions_label.setWordWrap(True)
        
        self.select_button = QPushButton("Select Target Window")
        self.select_button.clicked.connect(self.select_target_window)
        
        self.window_label = QLabel("Chưa chọn cửa sổ tham chiếu.")
        self.window_label.setStyleSheet("color: red;")
        
        self.sub_instructions_label = QLabel(
            "\nSau khi chọn cửa sổ:\n"
            "- Dùng 'Ctrl' trái để chọn góc trên-trái.\n"
            "- Dùng 'Shift' trái để chọn góc dưới-phải."
        )

        layout.addWidget(self.instructions_label)
        layout.addWidget(self.select_button)
        layout.addWidget(self.window_label)
        layout.addWidget(self.sub_instructions_label)

        # Hiển thị tọa độ
        self.current_pos_label = QLabel('Current Absolute (X, Y):')
        self.current_rel_pos_label = QLabel('Current Relative (X, Y):')
        self.region_rel_label = QLabel('Relative Region (x, y, w, h):')
        self.region_norm_label = QLabel('NORMALIZED Region (x, y, w, h):')
        self.region_norm_label.setStyleSheet("font-weight: bold; color: blue; font-size: 14px;")
        self.region_norm_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        layout.addWidget(self.current_pos_label)
        layout.addWidget(self.current_rel_pos_label)
        layout.addWidget(self.region_rel_label)
        layout.addWidget(self.region_norm_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_positions) # Đổi tên hàm để rõ ràng hơn
        self.timer.start(50)

    def select_target_window(self):
        self.instructions_label.setText("Đang chọn... Click vào cửa sổ poker trong 5 giây!")
        QTimer.singleShot(5000, self.capture_window_reference)

    def capture_window_reference(self):
        """Chỉ lấy đối tượng cửa sổ làm tham chiếu, không lưu tọa độ."""
        try:
            self.ref_window = gw.getActiveWindow()
            if self.ref_window:
                self.instructions_label.setText("Đã chọn cửa sổ! Bây giờ hãy dùng Ctrl/Shift.")
            else:
                self.window_label.setText("Không tìm thấy cửa sổ active.")
                self.window_label.setStyleSheet("color: red;")
        except Exception as e:
            self.window_label.setText(f"Lỗi: {e}")
            self.window_label.setStyleSheet("color: red;")

    def update_positions(self):
        """
        Cập nhật liên tục vị trí chuột VÀ vị trí của cửa sổ tham chiếu.
        Đây là phần được sửa lỗi.
        """
        # Lấy tọa độ chuột tuyệt đối
        x_abs, y_abs = pyautogui.position()
        self.current_pos_label.setText(f'Current Absolute (X, Y): ({x_abs}, {y_abs})')
        
        # Nếu đã có cửa sổ tham chiếu, CẬP NHẬT LIÊN TỤC vị trí và kích thước của nó
        if self.ref_window:
            try:
                # Kiểm tra xem cửa sổ có còn tồn tại không
                if not self.ref_window.isActive:
                    # Cố gắng tìm lại cửa sổ bằng tiêu đề nếu nó không active
                    windows = gw.getWindowsWithTitle(self.ref_window.title)
                    if windows:
                        self.ref_window = windows[0]
                    else:
                        raise gw.PyGetWindowException("Window not found.")

                # Cập nhật lại vị trí và kích thước của cửa sổ mỗi lần timer chạy
                self.ref_pos = (self.ref_window.left, self.ref_window.top)
                self.ref_size = (max(1, self.ref_window.width), max(1, self.ref_window.height))
                
                # Tính và hiển thị tọa độ tương đối của chuột
                rel_x = x_abs - self.ref_pos[0]
                rel_y = y_abs - self.ref_pos[1]
                self.current_rel_pos_label.setText(f'Current Relative (X, Y): ({rel_x}, {rel_y})')
                
                # Cập nhật lại thông tin trên label để người dùng biết
                self.window_label.setText(f"Đang theo dõi: {self.ref_window.title[:30]}... ({self.ref_size[0]}x{self.ref_size[1]})")
                self.window_label.setStyleSheet("color: green;")

            except (gw.PyGetWindowException, AttributeError):
                # Xử lý trường hợp cửa sổ bị đóng
                self.ref_window = None
                self.window_label.setText("Cửa sổ tham chiếu đã bị đóng!")
                self.window_label.setStyleSheet("color: red;")
                self.current_rel_pos_label.setText('Current Relative (X, Y):')
            
    def on_press(self, key):
        if not self.ref_window:
            return
            
        try:
            if key == keyboard.Key.ctrl_l:
                self.top_left = pyautogui.position()
                print(f"Đã lưu điểm trên-trái (tuyệt đối): {self.top_left}")

            if key == keyboard.Key.shift_l:
                if self.top_left:
                    self.bottom_right = pyautogui.position()
                    print(f"Đã lưu điểm dưới-phải (tuyệt đối): {self.bottom_right}")

                    # Tính tọa độ tương đối (pixel)
                    x_rel = self.top_left[0] - self.ref_pos[0]
                    y_rel = self.top_left[1] - self.ref_pos[1]
                    w = self.bottom_right[0] - self.top_left[0]
                    h = self.bottom_right[1] - self.top_left[1]
                    self.region_rel_label.setText(f'Relative Region: ({x_rel}, {y_rel}, {w}, {h})')

                    # Tính tọa độ chuẩn hóa (tỷ lệ)
                    x_norm = x_rel / self.ref_size[0]
                    y_norm = y_rel / self.ref_size[1]
                    w_norm = w / self.ref_size[0]
                    h_norm = h / self.ref_size[1]
                    
                    norm_tuple = (round(x_norm, 4), round(y_norm, 4), round(w_norm, 4), round(h_norm, 4))
                    
                    self.region_norm_label.setText(f'NORMALIZED Region: {norm_tuple}')
                    print(f"==> TỌA ĐỘ CHUẨN HÓA CẦN DÙNG: {norm_tuple}")

        except Exception as e:
            print(f"Lỗi: {e}")

if __name__ == '__main__':
    try:
        from pynput import keyboard
    except ImportError:
        print("Đang cài đặt pynput...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pynput"])
        sys.exit(1)
        
    app = QApplication(sys.argv)
    window = CoordApp()
    
    listener = keyboard.Listener(on_press=window.on_press)
    listener.start()

    window.show()
    sys.exit(app.exec())
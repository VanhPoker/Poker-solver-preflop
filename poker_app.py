import sys
import json
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QComboBox, QLineEdit, QPushButton, QLabel, QFormLayout
)
from PyQt6.QtCore import Qt

def sanitize_hand(hand_text):
    hand_text = hand_text.strip().lower()
    if len(hand_text) < 2 or len(hand_text) > 3:
        return None
    card1 = hand_text[0].upper()
    card2 = hand_text[1].upper()
    ranks = "AKQJT98765432"
    if ranks.find(card1) > ranks.find(card2):
        card1, card2 = card2, card1
    if len(hand_text) == 2:
        return f"{card1}{card2}o" if card1 != card2 else f"{card1}{card2}"
    if len(hand_text) == 3:
        if hand_text[2] == 's':
            return f"{card1}{card2}s"
        elif hand_text[2] == 'o':
            return f"{card1}{card2}o"
    return None

class PokerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Poker Pre-flop Decision Assistant")
        self.setGeometry(100, 100, 550, 500)
        
        # Biến mới để lưu dữ liệu chart đã được tải
        self.loaded_chart_data = None
        
        # Tải file chỉ mục
        self.chart_index = self.load_chart_index()
        
        self.initUI()

    def load_chart_index(self):
        """Hàm mới: Tải file index.json để biết cấu trúc file."""
        try:
            # Giả định index.json nằm cùng thư mục với poker_app.py
            with open("index.json", "r", encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Lỗi: Không tìm thấy file index.json!")
            return {"Error": {"NoIndex": {}}}
        except json.JSONDecodeError:
            print("Lỗi: File index.json không đúng định dạng!")
            return {"Error": {"InvalidIndex": {}}}

    def load_specific_chart(self, file_path):
        """Hàm mới: Tải một file chart cụ thể khi người dùng chọn."""
        try:
            with open(file_path, "r", encoding='utf-8') as f:
                self.loaded_chart_data = json.load(f)
                return True
        except FileNotFoundError:
            print(f"Lỗi: Không tìm thấy file chart tại '{file_path}'!")
            self.loaded_chart_data = None
            return False
        except json.JSONDecodeError:
            print(f"Lỗi: File chart '{file_path}' không đúng định dạng!")
            self.loaded_chart_data = None
            return False

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        form_layout = QFormLayout()
        main_layout.addLayout(form_layout)

        self.game_type_combo = QComboBox()
        self.chart_type_combo = QComboBox()
        self.main_situation_combo = QComboBox()
        self.scenario_combo = QComboBox()
        
        form_layout.addRow("Game Type:", self.game_type_combo)
        form_layout.addRow("Chart Type:", self.chart_type_combo)
        form_layout.addRow("Main Situation:", self.main_situation_combo)
        form_layout.addRow("Specific Scenario:", self.scenario_combo)
        
        self.hero_pos_label = QLabel("-")
        self.hero_pos_label.setStyleSheet("font-weight: bold;")
        form_layout.addRow("Your Position:", self.hero_pos_label)
        
        self.hero_hand_input = QLineEdit()
        self.hero_hand_input.setPlaceholderText("e.g., AKs, 77, T9o")
        form_layout.addRow("Your Hand:", self.hero_hand_input)

        get_decision_btn = QPushButton("Get Decision")
        get_decision_btn.setStyleSheet("font-size: 16px; padding: 10px; background-color: #3498db; color: white;")
        main_layout.addWidget(get_decision_btn, 0, Qt.AlignmentFlag.AlignCenter)

        self.result_label = QLabel("Welcome! Please select your scenario.")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("font-size: 16px; padding: 15px; border: 1px solid #ccc; border-radius: 5px; background-color: #f0f0f0; min-height: 60px;")
        main_layout.addWidget(self.result_label)

        # --- Kết nối Signals & Slots ---
        self.game_type_combo.currentTextChanged.connect(self.update_chart_types)
        self.chart_type_combo.currentTextChanged.connect(self.update_main_situations)
        self.main_situation_combo.currentTextChanged.connect(self.update_scenarios)
        self.scenario_combo.currentTextChanged.connect(self.update_hero_display)
        get_decision_btn.clicked.connect(self.get_decision)

        # Khởi tạo UI từ file index
        self.game_type_combo.addItems(self.chart_index.keys())

    def update_chart_types(self, game_type):
        self.chart_type_combo.clear()
        if game_type in self.chart_index:
            self.chart_type_combo.addItems(self.chart_index[game_type].keys())

    def update_main_situations(self, chart_type):
        self.main_situation_combo.clear()
        self.scenario_combo.clear() # Xóa luôn scenario con
        
        game_type = self.game_type_combo.currentText()
        if not chart_type or not game_type:
            return

        # Lấy đường dẫn file và tải dữ liệu
        file_path = self.chart_index[game_type].get(chart_type)
        if file_path and self.load_specific_chart(file_path):
            chart_data = self.loaded_chart_data.get("charts", {})
            self.main_situation_combo.addItems(chart_data.keys())
        else:
            self.hero_pos_label.setText("Error loading chart file!")

    def update_scenarios(self, main_situation):
        self.scenario_combo.clear()
        if not main_situation or not self.loaded_chart_data:
            return
            
        scenarios = self.loaded_chart_data["charts"].get(main_situation, {})
        self.scenario_combo.addItems(scenarios.keys())

    def update_hero_display(self, scenario):
        main_situation = self.main_situation_combo.currentText()
        hero_pos = "N/A"
        if scenario:
            if main_situation == "Raise First In (RFI)":
                hero_pos = scenario
            elif "_vs_" in scenario:
                hero_pos = scenario.split('_vs_')[0]
        self.hero_pos_label.setText(hero_pos)

    def get_decision(self):
        main_situation = self.main_situation_combo.currentText()
        scenario = self.scenario_combo.currentText()
        hand = sanitize_hand(self.hero_hand_input.text())
        
        if not self.loaded_chart_data:
            self.result_label.setText("Please select a valid chart type first.")
            return

        if not all([main_situation, scenario]):
            self.result_label.setText("Please make a selection in all dropdowns.")
            return

        if not hand:
            self.result_label.setText("Invalid Hand Format! (e.g., AKs, 77, T9o)")
            return

        try:
            action = self.loaded_chart_data["charts"][main_situation][scenario][hand]
            self.result_label.setText(action)
            
            # (Phần style cho kết quả không thay đổi)
            if any(act in action for act in ["Raise", "3-Bet", "4-Bet"]):
                self.result_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 15px; border: 2px solid #e74c3c; border-radius: 5px; background-color: #f5b7b1; color: #c0392b;")
            elif any(act in action for act in ["Call", "Check"]):
                 self.result_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 15px; border: 2px solid #2ecc71; border-radius: 5px; background-color: #abebc6; color: #28b463;")
            elif "Limp" in action:
                self.result_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 15px; border: 2px solid #f39c12; border-radius: 5px; background-color: #fdebd0; color: #d68910;")
            else: # Fold
                self.result_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 15px; border: 2px solid #95a5a6; border-radius: 5px; background-color: #e5e7e9; color: #7f8c8d;")

        except KeyError:
            action = "Fold"
            self.result_label.setText(f"{action} (Hand not in range)")
            self.result_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 15px; border: 2px solid #95a5a6; border-radius: 5px; background-color: #e5e7e9; color: #7f8c8d;")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PokerApp()
    window.show()
    sys.exit(app.exec())

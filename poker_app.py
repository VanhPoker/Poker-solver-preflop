import customtkinter as ctk
from tkinter import colorchooser, filedialog, messagebox
import json
import os

# --- LỚP CỬA SỔ CHỈNH SỬA BIỂU ĐỒ ---
class ChartEditorWindow(ctk.CTkToplevel):
    def __init__(self, master, file_path, chart_name, chart_state, actions):
        super().__init__(master)

        self.title(f"Chỉnh sửa: {chart_name}")
        self.geometry("900x700")
        self.transient(master)
        self.grab_set()

        self.master_app = master
        self.file_path = file_path
        self.chart_name = chart_name
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- App State for this window ---
        self.RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        self.actions = actions
        self.current_chart_state = chart_state
        self.selected_action_label = actions[0]['label'] if actions else None
        self.hand_buttons = {}

        self._create_widgets()
        self.update_actions_ui()
        self.update_grid_ui()

    def _create_widgets(self):
        # --- Control Frame (Left) ---
        self.control_frame = ctk.CTkFrame(self, width=250)
        self.control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.control_frame.grid_propagate(False)
        
        ctk.CTkLabel(self.control_frame, text=self.chart_name, font=ctk.CTkFont(size=16, weight="bold"), wraplength=230).pack(pady=10, padx=10, fill="x")

        # Actions Section
        actions_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        actions_frame.pack(pady=10, padx=10, fill="x", expand=True)
        ctk.CTkLabel(actions_frame, text="Hành Động", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(0, 10))
        self.actions_list_frame = ctk.CTkScrollableFrame(actions_frame, height=250)
        self.actions_list_frame.pack(fill="x", expand=True)
        
        # Management Section
        mgmt_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        mgmt_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkButton(mgmt_frame, text="Lưu thay đổi & Đóng", command=self._save_and_close).pack(fill="x", pady=5)
        ctk.CTkButton(mgmt_frame, text="Hủy bỏ", fg_color="#71717a", hover_color="#52525b", command=self.destroy).pack(fill="x", pady=5)
        
        # --- Grid Frame (Right) ---
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        for i in range(13):
            self.grid_frame.grid_columnconfigure(i, weight=1)
            self.grid_frame.grid_rowconfigure(i, weight=1)
        self._create_grid()
        
    def _create_grid(self):
        # (Same as PokerChartApp)
        for i, rank1 in enumerate(self.RANKS):
            for j, rank2 in enumerate(self.RANKS):
                hand = ""
                if i < j: hand = f"{rank1}{rank2}s"
                elif i > j: hand = f"{rank2}{rank1}o"
                else: hand = f"{rank1}{rank2}"
                button = ctk.CTkButton(self.grid_frame, text=hand,
                                       command=lambda h=hand: self._hand_button_click(h),
                                       font=ctk.CTkFont(size=11, weight="bold"))
                button.grid(row=i, column=j, padx=1, pady=1, sticky="nsew")
                self.hand_buttons[hand] = button

    def _save_and_close(self):
        try:
            # Read the entire original file
            with open(self.file_path, 'r', encoding='utf-8') as f:
                full_data = json.load(f)

            # Find the chart name and update it with the new state
            if self.chart_name in full_data:
                full_data[self.chart_name] = self.current_chart_state
            else:
                 # This case handles different structures, like the nested one.
                 # We need to find the correct path to update.
                 # For simplicity, this example assumes a flat structure for the save target.
                 # A more robust solution would require passing the full key path.
                 # For this implementation, we will assume the chart_name is a top-level key.
                 # Let's adjust for the provided example format
                 main_sit, scenario = self.chart_name.split(" | ")
                 full_data["charts"][main_sit][scenario] = self.current_chart_state
            
            # Write the entire modified data back to the file
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, indent=4)
            
            messagebox.showinfo("Thành công", f"Đã lưu thay đổi vào file:\n{self.file_path}", parent=self)
            self.master_app.load_specific_chart(self.file_path, reload_ui=True) # Reload data in main app
            self.destroy()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu file: {e}", parent=self)

    # All other methods like update_actions_ui, update_grid_ui, _hand_button_click, etc.
    # are very similar to the original PokerChartApp, adapted for this Toplevel window.
    def update_actions_ui(self):
        for widget in self.actions_list_frame.winfo_children():
            widget.destroy()

        for action in self.actions:
            button = ctk.CTkButton(self.actions_list_frame, text=action['label'],
                                   fg_color=action['color'],
                                   text_color=self._get_contrast_color(action['color']),
                                   hover=False,
                                   command=lambda l=action['label']: self._select_action(l))
            if action['label'] == self.selected_action_label:
                button.configure(border_width=3, border_color="#3b82f6")
            button.pack(fill="x", padx=5, pady=3)

    def update_grid_ui(self):
        for hand, button in self.hand_buttons.items():
            action_label = self.current_chart_state.get(hand)
            if action_label:
                action = next((a for a in self.actions if a['label'] == action_label), None)
                if action:
                    button.configure(fg_color=action['color'], text_color=self._get_contrast_color(action['color']))
                else:
                    button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"], text_color=ctk.ThemeManager.theme["CTkButton"]["text_color"])
            else:
                 button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"], text_color=ctk.ThemeManager.theme["CTkButton"]["text_color"])

    def _select_action(self, label):
        self.selected_action_label = label
        self.update_actions_ui()

    def _hand_button_click(self, hand):
        if not self.selected_action_label: return
        if self.current_chart_state.get(hand) == self.selected_action_label:
            del self.current_chart_state[hand]
        else:
            self.current_chart_state[hand] = self.selected_action_label
        self.update_grid_ui()

    def _get_contrast_color(self, hex_color):
        if hex_color is None: return "#000000"
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000
        return '#000000' if yiq >= 128 else '#FFFFFF'

# --- LỚP ỨNG DỤNG CHÍNH (TRA CỨU) ---
class PokerToolSuite(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Bộ Công Cụ Poker")
        self.geometry("600x550")

        self.loaded_chart_data = None
        self.current_file_path = None
        self.chart_index = self._load_chart_index()
        
        self._init_ui()

    def _init_ui(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Dropdowns
        ctk.CTkLabel(main_frame, text="Game Type:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.game_type_combo = ctk.CTkComboBox(main_frame, values=list(self.chart_index.keys()), command=self.update_chart_types)
        self.game_type_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(main_frame, text="Chart Type:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.chart_type_combo = ctk.CTkComboBox(main_frame, values=[], command=self.update_main_situations)
        self.chart_type_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(main_frame, text="Main Situation:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.main_situation_combo = ctk.CTkComboBox(main_frame, values=[], command=self.update_scenarios)
        self.main_situation_combo.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(main_frame, text="Specific Scenario:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.scenario_combo = ctk.CTkComboBox(main_frame, values=[])
        self.scenario_combo.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # View/Edit Button
        self.edit_chart_btn = ctk.CTkButton(main_frame, text="Xem / Chỉnh Sửa Chart", command=self.open_chart_editor, state="disabled")
        self.edit_chart_btn.grid(row=4, column=0, columnspan=2, padx=5, pady=10, sticky="ew")

        # Hand Input
        ctk.CTkLabel(main_frame, text="Your Hand:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.hero_hand_input = ctk.CTkEntry(main_frame, placeholder_text="e.g., AKs, 77, T9o")
        self.hero_hand_input.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        # Get Decision Button
        get_decision_btn = ctk.CTkButton(main_frame, text="Get Decision", command=self.get_decision)
        get_decision_btn.grid(row=6, column=0, columnspan=2, padx=5, pady=10, sticky="ew")

        # Result Label
        self.result_label = ctk.CTkLabel(main_frame, text="Welcome! Please select your scenario.", height=80, wraplength=500, fg_color="#e5e7e9", text_color="#7f8c8d", corner_radius=6)
        self.result_label.grid(row=7, column=0, columnspan=2, padx=5, pady=10, sticky="nsew")

        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(7, weight=1)

        # Initial population
        self.update_chart_types(self.game_type_combo.get())

    def _load_chart_index(self):
        try:
            with open("index.json", "r", encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải index.json: {e}")
            return {}

    def load_specific_chart(self, file_path, reload_ui=False):
        try:
            with open(file_path, "r", encoding='utf-8') as f:
                self.loaded_chart_data = json.load(f)
            self.current_file_path = file_path
            if reload_ui:
                self.update_main_situations(self.chart_type_combo.get(), force_reload=True)
            return True
        except Exception as e:
            self.loaded_chart_data = None
            self.current_file_path = None
            messagebox.showerror("Lỗi", f"Không thể tải file chart '{file_path}': {e}")
            return False

    def update_chart_types(self, game_type):
        self.chart_type_combo.configure(values=list(self.chart_index.get(game_type, {}).keys()))
        self.chart_type_combo.set("")
        self.main_situation_combo.set("")
        self.scenario_combo.set("")
        self.edit_chart_btn.configure(state="disabled")

    def update_main_situations(self, chart_type, force_reload=False):
        if not chart_type and not force_reload:
            self.main_situation_combo.configure(values=[])
            self.main_situation_combo.set("")
            self.scenario_combo.set("")
            self.edit_chart_btn.configure(state="disabled")
            return

        game_type = self.game_type_combo.get()
        file_path = self.chart_index.get(game_type, {}).get(chart_type)
        
        if file_path and self.load_specific_chart(file_path):
            chart_data = self.loaded_chart_data.get("charts", {})
            self.main_situation_combo.configure(values=list(chart_data.keys()))
        else:
            self.main_situation_combo.configure(values=[])
        
        self.main_situation_combo.set("")
        self.scenario_combo.set("")
        self.edit_chart_btn.configure(state="disabled")


    def update_scenarios(self, main_situation):
        if not main_situation or not self.loaded_chart_data:
            self.scenario_combo.configure(values=[])
            self.scenario_combo.set("")
            self.edit_chart_btn.configure(state="disabled")
            return
            
        scenarios = self.loaded_chart_data["charts"].get(main_situation, {})
        self.scenario_combo.configure(values=list(scenarios.keys()))
        self.scenario_combo.set("")
        self.edit_chart_btn.configure(state="disabled" if not list(scenarios.keys()) else "normal")

    def open_chart_editor(self):
        main_situation = self.main_situation_combo.get()
        scenario = self.scenario_combo.get()
        if not all([self.current_file_path, main_situation, scenario, self.loaded_chart_data]):
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn đầy đủ kịch bản trước khi chỉnh sửa.")
            return

        chart_state = self.loaded_chart_data["charts"][main_situation].get(scenario, {})
        
        # Create a comprehensive, color-coded action list if not present in the main JSON file.
        actions = self.loaded_chart_data.get("actions", [
            {'label': 'Raise', 'color': '#f87171'},
            {'label': 'Raise for value', 'color': '#dc2626'},
            {'label': 'Raise as a bluff', 'color': '#9333ea'},
            {'label': '3-bet for value', 'color': '#ef4444'},
            {'label': '3-bet as a bluff', 'color': '#8b5cf6'},
            {'label': '4-bet for value', 'color': '#b91c1c'},
            {'label': '4-bet as a bluff', 'color': '#7e22ce'},
            {'label': 'Call', 'color': '#22c55e'},
            {'label': 'Limp', 'color': '#22c55e'},
            {'label': 'Fold', 'color': '#a1a1aa'}
        ])
        
        chart_name = f"{main_situation} | {scenario}"
        
        editor = ChartEditorWindow(self, self.current_file_path, chart_name, chart_state, actions)
        
    def get_decision(self):
        main_situation = self.main_situation_combo.get()
        scenario = self.scenario_combo.get()
        hand_text = self.hero_hand_input.get()
        
        if not all([main_situation, scenario]):
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn đầy đủ kịch bản.")
            return
            
        if not hand_text:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập hand bài của bạn.")
            return
            
        hand = self._sanitize_hand(hand_text)
        if not hand:
            messagebox.showerror("Lỗi", "Định dạng hand không hợp lệ! (VD: AKs, 77, T9o)")
            return

        action = self.loaded_chart_data["charts"][main_situation][scenario].get(hand, "Fold")
        self.result_label.configure(text=f"Hành động: {action}")
        # Add styling based on action... (optional)

    def _sanitize_hand(self, hand_text):
        hand_text = hand_text.strip()
        if len(hand_text) < 2 or len(hand_text) > 3: return None
        
        ranks = "AKQJT98765432"
        card1 = hand_text[0].upper()
        card2 = hand_text[1].upper()
        if card1 not in ranks or card2 not in ranks: return None
        
        # Ensure consistent order (e.g., AKs, not KAs)
        if ranks.find(card1) > ranks.find(card2):
            card1, card2 = card2, card1
        
        if len(hand_text) == 2:
            return f"{card1}{card2}" if card1 == card2 else f"{card1}{card2}o"
        
        suffix = hand_text[2].lower()
        if suffix == 's' and card1 != card2: return f"{card1}{card2}s"
        if suffix == 'o' and card1 != card2: return f"{card1}{card2}o"
        
        return None

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = PokerToolSuite()
    app.mainloop()
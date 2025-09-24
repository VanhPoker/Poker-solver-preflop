import customtkinter as ctk
from tkinter import colorchooser, filedialog, messagebox
import json

class PokerChartApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Công Cụ Xây Dựng Biểu Đồ Poker")
        self.geometry("1200x800")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- App State ---
        self.RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        self.actions = [
            {'label': 'Raise', 'color': '#ef4444'},
            {'label': 'Call', 'color': '#22c55e'},
            {'label': 'Fold', 'color': '#a1a1aa'},
            {'label': '3-bet', 'color': '#8b5cf6'}
        ]
        self.current_chart_state = {}  # e.g., {"AKs": "Raise", "77": "Call"}
        self.selected_action_label = 'Raise'
        self.hand_buttons = {} # To store button widgets

        self._create_widgets()
        self.update_actions_ui()
        self.update_grid_ui()

    def _create_widgets(self):
        # --- Control Frame (Left) ---
        self.control_frame = ctk.CTkFrame(self, width=280)
        self.control_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.control_frame.grid_propagate(False)

        # Chart Info Section
        chart_info_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        chart_info_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(chart_info_frame, text="Thông Tin Chart", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 10))
        ctk.CTkLabel(chart_info_frame, text="Tên Chart:", anchor="w").pack(fill="x")
        self.chart_name_entry = ctk.CTkEntry(chart_info_frame, placeholder_text="VD: UTG RFI 75bb")
        self.chart_name_entry.pack(fill="x", pady=(0, 10))

        # Actions Section
        actions_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        actions_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(actions_frame, text="Hành Động & Màu Sắc", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 10))
        
        self.actions_list_frame = ctk.CTkScrollableFrame(actions_frame, height=200)
        self.actions_list_frame.pack(fill="x", expand=True)
        
        self.new_action_label_entry = ctk.CTkEntry(actions_frame, placeholder_text="Tên hành động...")
        self.new_action_label_entry.pack(fill="x", pady=5)
        
        color_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        color_frame.pack(fill="x", pady=5)
        self.new_action_color_preview = ctk.CTkButton(color_frame, text="", width=28, height=28, fg_color="#ef4444", command=self._pick_color)
        self.new_action_color_preview.pack(side="left")
        ctk.CTkLabel(color_frame, text="Chọn màu").pack(side="left", padx=10)
        
        ctk.CTkButton(actions_frame, text="Thêm Hành Động", command=self._add_action).pack(fill="x", pady=5)

        # Management Section
        mgmt_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        mgmt_frame.pack(pady=10, padx=10, fill="x", expand=True)
        ctk.CTkLabel(mgmt_frame, text="Quản Lý", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 10))

        btn_grid = ctk.CTkFrame(mgmt_frame, fg_color="transparent")
        btn_grid.pack(fill="x")
        btn_grid.grid_columnconfigure((0,1), weight=1)
        ctk.CTkButton(btn_grid, text="Lưu Chart", command=self._save_chart).grid(row=0, column=0, padx=(0,5), pady=5, sticky="ew")
        ctk.CTkButton(btn_grid, text="Tải Chart", command=self._load_chart).grid(row=0, column=1, padx=(5,0), pady=5, sticky="ew")
        ctk.CTkButton(btn_grid, text="Xóa Grid", fg_color="#71717a", hover_color="#52525b", command=self._clear_grid).grid(row=1, column=0, padx=(0,5), pady=5, sticky="ew")
        ctk.CTkButton(btn_grid, text="Xuất JSON", fg_color="#16a34a", hover_color="#15803d", command=self._export_json).grid(row=1, column=1, padx=(5,0), pady=5, sticky="ew")
        
        # --- Grid Frame (Right) ---
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        for i in range(13):
            self.grid_frame.grid_columnconfigure(i, weight=1)
            self.grid_frame.grid_rowconfigure(i, weight=1)

        self._create_grid()

    def _create_grid(self):
        for i, rank1 in enumerate(self.RANKS):
            for j, rank2 in enumerate(self.RANKS):
                hand = ""
                if i < j: hand = f"{rank1}{rank2}s"
                elif i > j: hand = f"{rank2}{rank1}o"
                else: hand = f"{rank1}{rank2}"

                button = ctk.CTkButton(self.grid_frame, text=hand,
                                       command=lambda h=hand: self._hand_button_click(h),
                                       font=ctk.CTkFont(size=12, weight="bold"))
                button.grid(row=i, column=j, padx=1, pady=1, sticky="nsew")
                self.hand_buttons[hand] = button

    # --- UI Update Functions ---
    def update_actions_ui(self):
        for widget in self.actions_list_frame.winfo_children():
            widget.destroy()

        for action in self.actions:
            action_frame = ctk.CTkFrame(self.actions_list_frame, fg_color="transparent")
            action_frame.pack(fill="x", pady=2)
            
            button = ctk.CTkButton(action_frame, text=action['label'],
                                   fg_color=action['color'],
                                   text_color=self._get_contrast_color(action['color']),
                                   hover=False,
                                   command=lambda l=action['label']: self._select_action(l))
            
            if action['label'] == self.selected_action_label:
                button.configure(border_width=3, border_color="#3b82f6")

            button.pack(side="left", fill="x", expand=True)
            
            delete_btn = ctk.CTkButton(action_frame, text="X", width=28, height=28,
                                       fg_color="#ef4444", hover_color="#dc2626",
                                       command=lambda l=action['label']: self._delete_action(l))
            delete_btn.pack(side="right", padx=(5,0))

    def update_grid_ui(self):
        for hand, button in self.hand_buttons.items():
            action_label = self.current_chart_state.get(hand)
            if action_label:
                action = next((a for a in self.actions if a['label'] == action_label), None)
                if action:
                    button.configure(fg_color=action['color'], text_color=self._get_contrast_color(action['color']))
                else:
                    # Reset if action was deleted
                    button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"],
                                     text_color=ctk.ThemeManager.theme["CTkButton"]["text_color"])
            else:
                 button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"],
                                     text_color=ctk.ThemeManager.theme["CTkButton"]["text_color"])

    # --- Event Handlers & Logic ---
    def _pick_color(self):
        color_code = colorchooser.askcolor(title="Chọn một màu")
        if color_code:
            self.new_action_color_preview.configure(fg_color=color_code[1])

    def _add_action(self):
        label = self.new_action_label_entry.get().strip()
        color = self.new_action_color_preview.cget("fg_color")
        if not label:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tên hành động.")
            return
        if any(a['label'] == label for a in self.actions):
            messagebox.showwarning("Trùng lặp", "Tên hành động đã tồn tại.")
            return
        
        self.actions.append({'label': label, 'color': color})
        self.new_action_label_entry.delete(0, 'end')
        self.update_actions_ui()
    
    def _delete_action(self, label_to_delete):
        if len(self.actions) == 1:
            messagebox.showwarning("Hành động cuối cùng", "Không thể xóa hành động cuối cùng.")
            return

        self.actions = [a for a in self.actions if a['label'] != label_to_delete]
        
        # Remove deleted action from chart state
        self.current_chart_state = {h: a for h, a in self.current_chart_state.items() if a != label_to_delete}
        
        if self.selected_action_label == label_to_delete:
            self.selected_action_label = self.actions[0]['label'] if self.actions else None
        
        self.update_actions_ui()
        self.update_grid_ui()

    def _select_action(self, label):
        self.selected_action_label = label
        self.update_actions_ui()

    def _hand_button_click(self, hand):
        if not self.selected_action_label:
            messagebox.showwarning("Chưa chọn hành động", "Vui lòng chọn một hành động từ danh sách.")
            return

        if self.current_chart_state.get(hand) == self.selected_action_label:
            del self.current_chart_state[hand]
        else:
            self.current_chart_state[hand] = self.selected_action_label
        
        self.update_grid_ui()

    def _clear_grid(self):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa toàn bộ lựa chọn trên grid không?"):
            self.current_chart_state = {}
            self.update_grid_ui()

    def _save_chart(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Poker Chart Files", "*.json"), ("All Files", "*.*")],
            title="Lưu Chart"
        )
        if not file_path:
            return

        chart_data = {
            "chartName": self.chart_name_entry.get(),
            "actions": self.actions,
            "chartState": self.current_chart_state
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(chart_data, f, indent=4)
            messagebox.showinfo("Thành công", f"Chart đã được lưu tại:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu file: {e}")

    def _load_chart(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Poker Chart Files", "*.json"), ("All Files", "*.*")],
            title="Tải Chart"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                chart_data = json.load(f)
            
            self.chart_name_entry.delete(0, 'end')
            self.chart_name_entry.insert(0, chart_data.get('chartName', ''))
            
            self.actions = chart_data.get('actions', [])
            self.current_chart_state = chart_data.get('chartState', {})
            self.selected_action_label = self.actions[0]['label'] if self.actions else None

            self.update_actions_ui()
            self.update_grid_ui()
            messagebox.showinfo("Thành công", f"Đã tải chart từ:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải file hoặc định dạng file không đúng: {e}")

    def _export_json(self):
        if not self.current_chart_state:
            messagebox.showinfo("Thông tin", "Chart hiện đang trống. Không có gì để xuất.")
            return

        # Dữ liệu `self.current_chart_state` đã có sẵn định dạng {hand: action} mà bạn muốn.
        # Chúng ta chỉ cần lấy nó và đặt dưới tên của chart.
        final_object = self.current_chart_state

        chart_name = self.chart_name_entry.get().strip() or "Untitled Chart"

        export_data = {
            chart_name: final_object
        }

        # Hiển thị trong cửa sổ mới
        ExportWindow(self, json.dumps(export_data, indent=4))

    # --- Utility ---
    def _get_contrast_color(self, hex_color):
        if hex_color is None: return "#000000"
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000
        return '#000000' if yiq >= 128 else '#FFFFFF'

class ExportWindow(ctk.CTkToplevel):
    def __init__(self, master, json_string):
        super().__init__(master)
        self.title("JSON đã xuất")
        self.geometry("600x400")
        self.transient(master) # Keep on top of the main window
        self.grab_set() # Modal behavior

        self.text_area = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Courier New", size=12))
        self.text_area.pack(pady=10, padx=10, fill="both", expand=True)
        self.text_area.insert("1.0", json_string)
        self.text_area.configure(state="disabled")

        copy_btn = ctk.CTkButton(self, text="Sao chép vào Clipboard", command=self._copy_to_clipboard)
        copy_btn.pack(pady=10, padx=10, fill="x")

    def _copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.text_area.get("1.0", "end-1c"))
        messagebox.showinfo("Đã sao chép", "Nội dung JSON đã được sao chép vào clipboard.", parent=self)

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = PokerChartApp()
    app.mainloop()
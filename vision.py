import cv2
import numpy as np
import pytesseract
from PIL import Image

# --- BẠN CẦN TÙY CHỈNH PHẦN NÀY ---
# Hướng dẫn Tesseract đến file thực thi của nó
# Ví dụ trên Windows:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Ví dụ trên macOS/Linux (nếu đã cài qua Homebrew/apt):
# pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'

# Tọa độ tương đối của các khu vực quan trọng (ROI - Region of Interest)
# Giả sử bàn chơi có kích thước 1000x700 pixels
# (x, y, width, height)
# BẠN PHẢI TỰ XÁC ĐỊNH CÁC TỌA ĐỘ NÀY CHO CHÍNH XÁC
PLAYER_REGIONS = {
    "6max": {
        "Hero": {"cards": (450, 550, 100, 70), "bet_size": (450, 480, 100, 30)},
        "BTN": {"cards": (200, 150, 80, 50), "bet_size": (200, 210, 80, 25)},
        # ... Thêm tọa độ cho các vị trí khác (CO, HJ, UTG, SB, BB)
    },
    "9max": {
        # ... Thêm tọa độ cho bàn 9-max
    }
}

DEALER_BUTTON_TEMPLATE = 'templates/dealer_button.png'
# ... Thêm đường dẫn cho các template khác

# --- KẾT THÚC PHẦN TÙY CHỈNH ---

def find_template(image, template_path, threshold=0.8):
    """Tìm một template trong một ảnh lớn và trả về tọa độ."""
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        return None
        
    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)
    
    for pt in zip(*loc[::-1]):
        # Trả về tọa độ của điểm khớp đầu tiên
        return pt
    return None

def read_text_from_region(image, region, is_number=True):
    """Cắt một vùng ảnh và dùng OCR để đọc text."""
    x, y, w, h = region
    cropped_image = image[y:y+h, x:x+w]
    
    # Tiền xử lý để tăng độ chính xác của OCR
    gray_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    _, thresh_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Cấu hình Tesseract
    config = "--psm 7" # Chế độ 7: Coi ảnh như một dòng text duy nhất
    if is_number:
        config += " -c tessedit_char_whitelist=0123456789.$BB" # Chỉ nhận dạng các ký tự này

    try:
        text = pytesseract.image_to_string(thresh_image, config=config).strip()
        return text
    except Exception as e:
        print(f"Lỗi OCR: {e}")
        return ""

def analyze_table(table_image):
    """
    Hàm chính của module vision.
    Nhận vào một ảnh chụp bàn chơi và trả về một dictionary dữ liệu.
    """
    print("Bắt đầu phân tích hình ảnh bàn chơi...")
    
    analysis_result = {
        "my_position": "Unknown",
        "my_hand": "Unknown",
        "actions_before": []
    }

    # 1. Tìm nút Dealer để xác định vị trí
    dealer_pos_coords = find_template(table_image, DEALER_BUTTON_TEMPLATE)
    if dealer_pos_coords:
        print(f"Tìm thấy nút Dealer tại tọa độ: {dealer_pos_coords}")
        # **LOGIC XÁC ĐỊNH VỊ TRÍ:**
        # Dựa vào tọa độ của nút Dealer và các vùng tọa độ của người chơi
        # trong PLAYER_REGIONS, bạn sẽ viết logic để suy ra vị trí của từng người.
        # Ví dụ: Nếu dealer_pos_coords gần với tọa độ của Player 3, thì Player 3 là BTN.
        # Từ đó suy ra các vị trí khác.
        # Tạm thời để là "UTG" để minh họa
        analysis_result["my_position"] = "UTG" 
        print(f"Xác định vị trí của bạn là: {analysis_result['my_position']}")

    # 2. Đọc bài của bản thân (Hero)
    # **LOGIC ĐỌC BÀI:**
    # Tương tự, bạn sẽ dùng template matching để tìm các rank và suit
    # trong vùng `PLAYER_REGIONS["6max"]["Hero"]["cards"]`
    # Tạm thời để là "AhKd" để minh họa
    analysis_result["my_hand"] = "AhKd"
    print(f"Xác định bài của bạn là: {analysis_result['my_hand']}")

    # 3. Đọc hành động của đối thủ
    # **LOGIC ĐỌC HÀNH ĐỘNG ĐỐI THỦ:**
    # Lặp qua các vị trí trước bạn, dùng find_template để tìm chip cược
    # và read_text_from_region để đọc size bet.
    # Ví dụ:
    bet_size_text = read_text_from_region(table_image, PLAYER_REGIONS["6max"]["BTN"]["bet_size"])
    if bet_size_text:
         analysis_result["actions_before"].append({
             "position": "BTN",
             "action": "Raise",
             "size_text": bet_size_text
         })
    print(f"Hành động đã ghi nhận: {analysis_result['actions_before']}")
    
    print("Phân tích hình ảnh hoàn tất.")
    return analysis_result

# --- Phần để kiểm tra module này một cách độc lập ---
if __name__ == '__main__':
    # Thay 'path/to/your/screenshot.jpg' bằng đường dẫn đến một ảnh chụp màn hình
    # bàn chơi của bạn để kiểm tra.
    try:
        sample_image = cv2.imread('image_c9fd7e.jpg') # Sử dụng ảnh bạn đã gửi
        if sample_image is not None:
            result = analyze_table(sample_image)
            print("\n--- KẾT QUẢ PHÂN TÍCH ---")
            print(result)
        else:
            print("Không thể tải ảnh. Hãy chắc chắn đường dẫn là chính xác.")
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

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
        "Hero": {"cards": (0.43, 0.736, 0.1371, 0.2216)}, # Tọa độ bạn tìm được
        
        "Opponent1": {
            "cards": (0.0343, 0.5857, 0.1386, 0.2042), # Tọa độ bạn tìm được
            "bet_size": (0.8129, 0.5588, 0.1414, 0.2428),
            "stack_size": (0.15, 0.63, 0.08, 0.04)
        },
        "Opponent2": {
            "cards": (0.2214, 0.3391, 0.0843, 0.0809),
            "bet_size": (0.2229, 0.316, 0.0771, 0.1079),
            "stack_size": (100, 260, 80, 25)
        },
        "Opponent3": {
            "cards": (0.4214, 0.0867, 0.1429, 0.2235),
            "bet_size": (0.4414, 0.2852, 0.1157, 0.0906),
            "stack_size": (410, 100, 80, 25)
        },
        "Opponent4": {
            "cards": (0.7729, 0.1599, 0.1543, 0.2466),
            "bet_size": (0.7257, 0.3565, 0.0771, 0.0886),
            "stack_size": (730, 260, 80, 25)
        },
        "Opponent5": {
            "cards": (0.8129, 0.5588, 0.1414, 0.2428),
            "bet_size": (0.7229, 0.5723, 0.0771, 0.0906),
            "stack_size": (850, 630, 80, 25)
        }
    },
    "9max": {
        # ... Thêm tọa độ cho bàn 9-max
    }
}

# Các đường dẫn template và mask tương ứng
DEALER_BUTTON_TEMPLATE = 'templates/dealer_button.png'
DEALER_BUTTON_MASK = 'templates/masks/dealer_button_mask.png'

# Template và mask cho các quân bài
CARD_TEMPLATES = {
    'ranks': {
        'A': {'template': 'templates/cards_rank/card_rank_A.png', 'mask': 'templates/masks/card_rank_A_mask.png'},
        'K': {'template': 'templates/cards_rank/card_rank_K.png', 'mask': 'templates/masks/card_rank_K_mask.png'},
        'Q': {'template': 'templates/cards_rank/card_rank_Q.png', 'mask': 'templates/masks/card_rank_Q_mask.png'},
        'J': {'template': 'templates/cards_rank/card_rank_J.png', 'mask': 'templates/masks/card_rank_J_mask.png'},
        'T': {'template': 'templates/cards_rank/card_rank_T.png', 'mask': 'templates/masks/card_rank_T_mask.png'},
        '9': {'template': 'templates/cards_rank/card_rank_9.png', 'mask': 'templates/masks/card_rank_9_mask.png'},
        '8': {'template': 'templates/cards_rank/card_rank_8.png', 'mask': 'templates/masks/card_rank_8_mask.png'},
        '7': {'template': 'templates/cards_rank/card_rank_7.png', 'mask': 'templates/masks/card_rank_7_mask.png'},
        '6': {'template': 'templates/cards_rank/card_rank_6.png', 'mask': 'templates/masks/card_rank_6_mask.png'},
        '5': {'template': 'templates/cards_rank/card_rank_5.png', 'mask': 'templates/masks/card_rank_5_mask.png'},
        '4': {'template': 'templates/cards_rank/card_rank_4.png', 'mask': 'templates/masks/card_rank_4_mask.png'},
        '3': {'template': 'templates/cards_rank/card_rank_3.png', 'mask': 'templates/masks/card_rank_3_mask.png'},
        '2': {'template': 'templates/cards_rank/card_rank_2.png', 'mask': 'templates/masks/card_rank_2_mask.png'},
    },
    'suits': {
        'h': {'template': 'templates/cards_suit/card_suit_heart.png', 'mask': 'templates/masks/card_suit_heart_mask.png'},
        'd': {'template': 'templates/cards_suit/card_suit_diamond.png', 'mask': 'templates/masks/card_suit_diamond_mask.png'},
        's': {'template': 'templates/cards_suit/card_suit_spade.png', 'mask': 'templates/masks/card_suit_spade_mask.png'},
        'c': {'template': 'templates/cards_suit/card_suit_club.png', 'mask': 'templates/masks/card_suit_club_mask.png'},
    }
}

# --- KẾT THÚC PHẦN TÙY CHỈNH ---

def find_template(image, template_path, mask_path=None, threshold=0.8):
    """
    Tìm một template trong một ảnh lớn và trả về tọa độ.
    Hỗ trợ sử dụng mask để tăng độ chính xác.
    
    Args:
        image: Ảnh nguồn cần tìm kiếm
        template_path: Đường dẫn đến file ảnh template
        mask_path: Đường dẫn đến file ảnh mask (tùy chọn)
        threshold: Ngưỡng để xác định điểm khớp
        
    Returns:
        Tọa độ điểm khớp đầu tiên hoặc None nếu không tìm thấy
    """
    # Đọc template
    if mask_path:
        # Sử dụng phương pháp có mask
        template = cv2.imread(template_path)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        
        if template is None or mask is None:
            print(f"Không thể đọc template hoặc mask: {template_path}, {mask_path}")
            return None
            
        # Đảm bảo ảnh nguồn cũng ở dạng màu
        if len(image.shape) == 2:  # Grayscale
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            
        # Sử dụng TM_SQDIFF_NORMED với mask
        res = cv2.matchTemplate(image, template, cv2.TM_SQDIFF_NORMED, mask=mask)
        
        # Với TM_SQDIFF_NORMED, điểm khớp tốt nhất là điểm có giá trị nhỏ nhất
        min_val, _, min_loc, _ = cv2.minMaxLoc(res)
        
        if min_val <= (1.0 - threshold):  # Chuyển đổi ngưỡng cho phù hợp với TM_SQDIFF_NORMED
            return min_loc
        return None
    else:
        # Phương pháp không có mask (dùng TM_CCOEFF_NORMED)
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            print(f"Không thể đọc template: {template_path}")
            return None
            
        img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) > 2 else image
        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        
        # Tìm vị trí có giá trị lớn hơn ngưỡng
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

def find_card(image, roi):
    """
    Tìm kiếm rank và suit của quân bài trong vùng roi.
    
    Args:
        image: Ảnh nguồn
        roi: (x, y, width, height) định nghĩa vùng để tìm quân bài
        
    Returns:
        String mô tả quân bài (ví dụ: "Ah", "Kd", etc.) hoặc None nếu không tìm thấy
    """
    x, y, w, h = roi
    card_area = image[y:y+h, x:x+w]
    
    found_rank = None
    found_suit = None
    
    # Tìm kiếm rank
    for rank, paths in CARD_TEMPLATES['ranks'].items():
        pos = find_template(card_area, paths['template'], paths['mask'], threshold=0.7)
        if pos:
            found_rank = rank
            break
            
    # Tìm kiếm suit
    for suit, paths in CARD_TEMPLATES['suits'].items():
        pos = find_template(card_area, paths['template'], paths['mask'], threshold=0.7)
        if pos:
            found_suit = suit
            break
    
    if found_rank and found_suit:
        return found_rank + found_suit
    return None

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
    dealer_pos_coords = find_template(table_image, DEALER_BUTTON_TEMPLATE, DEALER_BUTTON_MASK)
    if dealer_pos_coords:
        print(f"Tìm thấy nút Dealer tại tọa độ: {dealer_pos_coords}")
        # **LOGIC XÁC ĐỊNH VỊ TRÍ:**
        # Dựa vào tọa độ của nút Dealer và các vùng tọa độ của người chơi
        # trong PLAYER_REGIONS, bạn sẽ viết logic để suy ra vị trí của từng người.
        # Ví dụ: Nếu dealer_pos_coords gần với tọa độ của Player 3, thì Player 3 là BTN.
        # Từ đó suy ra các vị trí khác.
        
        # Logic tính khoảng cách từ dealer button đến các vị trí người chơi
        # (Code thực tế sẽ phức tạp hơn, đây chỉ là minh họa)
        # ...
        
        analysis_result["my_position"] = "UTG"  # Tạm thời để là "UTG" để minh họa
        print(f"Xác định vị trí của bạn là: {analysis_result['my_position']}")

    # 2. Đọc bài của bản thân (Hero)
    # Sử dụng hàm find_card để nhận diện các lá bài
    hero_card_region = PLAYER_REGIONS["6max"]["Hero"]["cards"]
    
    # Giả sử có 2 vùng riêng biệt cho 2 lá bài
    card1_region = (hero_card_region[0], hero_card_region[1], hero_card_region[2]//2, hero_card_region[3])
    card2_region = (hero_card_region[0] + hero_card_region[2]//2, hero_card_region[1], hero_card_region[2]//2, hero_card_region[3])
    
    card1 = find_card(table_image, card1_region)
    card2 = find_card(table_image, card2_region)
    
    if card1 and card2:
        analysis_result["my_hand"] = card1 + card2
        print(f"Xác định bài của bạn là: {analysis_result['my_hand']}")
    else:
        # Fallback - có thể cần phương pháp khác hoặc debug
        analysis_result["my_hand"] = "AhKd"  # Giả định
        print(f"Không thể nhận dạng bài, giả định là: {analysis_result['my_hand']}")

    # 3. Đọc hành động của đối thủ
    # Lặp qua các vị trí trước bạn và sử dụng find_template với mask để phát hiện các chip, rồi đọc giá trị bet
    bet_size_text = read_text_from_region(table_image, PLAYER_REGIONS["6max"]["BTN"]["bet_size"])
    if bet_size_text:
         analysis_result["actions_before"].append({
             "position": "BTN",
             "action": "Raise",  # Logic thực tế cần phân biệt giữa raise/call/etc.
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

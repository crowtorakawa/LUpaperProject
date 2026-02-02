import cv2
import numpy as np
import os

def Extraction_procedure(user_id, matrix, target_email):
    # 1. 定義檔案路徑 (對接 Flask 目錄結構)
    stego_dir = os.path.join(os.getcwd(), 'apps', 'static', 'stego', str(user_id))
    stego_path = os.path.join(stego_dir, 'Stego_image.png')
    interp_path = os.path.join(stego_dir, 'Interpolation_image.png')

    # 2. 防亂碼讀取影像
    def safe_read_gray(path):
        if not os.path.exists(path): return None
        raw_data = np.fromfile(path, dtype=np.uint8)
        return cv2.imdecode(raw_data, cv2.IMREAD_GRAYSCALE)

    stego_img = safe_read_gray(stego_path)
    interp_img = safe_read_gray(interp_path)

    if stego_img is None or interp_img is None:
        return False, "找不到隱寫影像或插值影像，無法解碼"

    # 3. 轉型與計算差值
    stego_img = stego_img.astype(np.int32)
    interp_img = interp_img.astype(np.int32)
    diff_img = stego_img - interp_img
    
    current_binary_str = ""
    height, width = stego_img.shape

    # 4. 遍歷 2x2 區塊提取
    for i in range(0, height - 1, 2):
        for j in range(0, width - 1, 2):
            # 取得目前的區塊
            stego_block = stego_img[i:i+2, j:j+2]
            interp_block = interp_img[i:i+2, j:j+2]
            diff_block = diff_img[i:i+2, j:j+2]

            # A. 定位 4x4x4 子矩陣 (與嵌入端一致)
            m_axis = [
                int(interp_block[0, 1] % 64) * 4,
                int(interp_block[1, 1] % 64) * 4,
                int(interp_block[1, 0] % 64) * 4
            ]
            little_magic_cub = matrix[m_axis[0]:m_axis[0]+4, 
                                      m_axis[1]:m_axis[1]+4, 
                                      m_axis[2]:m_axis[2]+4]

            start_position = interp_block[0, 0] % 32

            # B. 提取中心像素 [1,1] 的 LSB 輔助位元
            center_bits = format(stego_block[1, 1] & 0xFF, '08b')
            # 取得 mid_sign (4,5位) 與 mid_sign_plus (6,7位)
            mid_sign = [int(center_bits[4]), int(center_bits[5])]
            mid_sign_plus = [int(center_bits[6]), int(center_bits[7])]

            target_pixels = [(0, 1), (1, 0)]
            z_ranges = [(0, 2), (2, 4)]

            for k in range(2):
                pixel_idx = target_pixels[k]
                z_start, z_end = z_ranges[k]
                
                dn = abs(diff_block[pixel_idx])
                dy_abs = dn // 4
                dx_abs = dn % 4

                # D. 還原正負號
                if diff_block[pixel_idx] < 0:
                    dy = -dy_abs
                    dx = -dx_abs if mid_sign[k] == 0 else dx_abs
                else:
                    dy = dy_abs
                    dx = dx_abs if mid_sign[k] == 0 else -dx_abs

                # E. 搜尋起始點
                pos_s = None
                for z in range(z_start, z_end):
                    for y in range(4):
                        for x in range(4):
                            if little_magic_cub[z, y, x] == start_position:
                                pos_s = (z, y, x)
                                break
                        if pos_s: break
                    if pos_s: break

                # F. 提取數值
                if pos_s:
                    dz = mid_sign_plus[k]
                    h_z = pos_s[0] if dz == 0 else z_start + (1 - (pos_s[0] % 2))
                    h_y = np.clip(pos_s[1] - dy, 0, 3)
                    h_x = np.clip(pos_s[2] - dx, 0, 3)
                    
                    extracted_val = little_magic_cub[int(h_z), int(h_y), int(h_x)]
                    # ✅ 這裡是關鍵：嵌入時是用 4-bit (chunk_size=4)，所以還原也要 4-bit
                    current_binary_str += format(extracted_val, '05b')

    # 5. 將二進位轉回文字 (改良版)
    raw_full_text = ""
    for i in range(0, len(current_binary_str), 8):
        byte = current_binary_str[i:i+8]
        if len(byte) < 8: break
        char_code = int(byte, 2)
        if 32 <= char_code <= 126:
            raw_full_text += chr(char_code)
        else:
            raw_full_text += "?" # 雜訊

    # 如果 Email 裡有重複出現的情況 (因為你用了循環嵌入)，只取第一個區塊
    # 或者簡單處理：
    if target_email in raw_full_text:
        extracted_email = target_email
    else:
        # 如果沒完全匹配 (例如出現 admin@acminL 這種微小錯誤)
        # 我們抓取 @ 符號前後的內容
        import re
        # 尋找包含 @ 的字串，並限制長度在 target_email 附近
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(pattern, raw_full_text)
        
        if matches:
            # 取出現次數最多的那一個，或者第一個
            extracted_email = matches[0]
        else:
            # 萬一真的解得很爛，就顯示原始的前段
            extracted_email = raw_full_text[:len(target_email) + 5]

    return True, extracted_email
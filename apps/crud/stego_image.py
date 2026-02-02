import numpy as np
import cv2
import matplotlib.pyplot as plt 
import random

import os

def data_hidding(matrix, input_img_path, binary_data, final_save_path):   

    img_src = input_img_path
    raw_data = np.fromfile(img_src, dtype=np.uint8)
    ExpansionImg = cv2.imdecode(raw_data, cv2.IMREAD_GRAYSCALE)

    if ExpansionImg is None:
        print(f"跳過：找不到圖片 {img_src}")
        return False
    
    # --- 2. 準備秘密資料 (不再讀取 .txt) ---
    # 將 binary_data (例如 "011001...") 切割成 4-bit 的 chunks (因為你的矩陣邏輯需要)
    chunk_size = 5 
    chunks = [binary_data[i:i+chunk_size] for i in range(0, len(binary_data), chunk_size)]
    
    # 如果 Email 太短，長度不足以填滿圖片像素，這裡可以循環使用 chunks
    num_chunks = len(chunks)
    if num_chunks == 0:
        return False
    
    ExpansionImg = ExpansionImg.astype(np.int32)
    final_img = np.copy(ExpansionImg)
    chunk_count = 0  # 紀錄目前處理到第幾個資料塊
    Expansion_height, Expansion_width = ExpansionImg.shape


    for i in range(0, Expansion_height - 1, 2):
        for j in range(0, Expansion_width - 1, 2):
            Expansion_block = final_img[i:i+2, j:j+2]
            M_axis =[(Expansion_block[0,1]%64)*4,(Expansion_block[1,1]%64)*4,(Expansion_block[1,0]%64)*4]
                #小方塊參數
            little_magic_cub = matrix[M_axis[0]:M_axis[0]+4,M_axis[1]:M_axis[1]+4,M_axis[2]:M_axis[2]+4]
                # print(little_magic_cub)
            startPosition = Expansion_block[0, 0] % 32

            #中間符號
            mid_sign=""
            mid_sign_plus=""
            # C. 執行兩次嵌入 (分別在 cub 的上半與下半)
            # target_pixels 對應區塊中的 [0,1] 與 [1,0]
            target_pixels = [(0, 1), (1, 0)]
            z_ranges = [(0, 2), (2, 4)] # 上半 z=0,1 ; 下半 z=2,3
            for k in range(2):
                z_start, z_end = z_ranges[k]
                pixel_idx = target_pixels[k]
                target_data = int(chunks[chunk_count], 2)
                chunk_count = (chunk_count + 1) % num_chunks # 循環讀取資料
                # 搜尋 cub 內 start_val 與 target_data 的 3D 座標
                pos_s = None
                pos_h = None
                for z in range(z_start, z_end):
                    for y in range(4):
                        for x in range(4):
                            if little_magic_cub[z, y, x] == target_data:
                                pos_h = (z, y, x)
                            if little_magic_cub[z, y, x] == startPosition:
                                pos_s = (z, y, x)
                
                if pos_s and pos_h:
                        # 計算座標差值 (dz, dy, dx)
                        dz = abs(pos_s[0] - pos_h[0])
                        dy = pos_s[1] - pos_h[1]
                        dx = pos_s[2] - pos_h[2]
                        # 1. 處理編號與正負號
                        move_val = abs(dy) * 4 + abs(dx)
                        # 決定旗標 (這裡沿用你原本的邏輯組合)
                        s1 = '1' if dy < 0 else '0'
                        s2 = '1' if dx < 0 else '0'
                        # 根據你的邏輯組合 mid_sign (k=0 和 k=1 各貢獻 1 bit)
                        # 注意：這裡需配合你解碼時的判斷邏輯
                        mid_sign += '1' if (dy < 0 or dx < 0) else '0' 
                        mid_sign_plus += str(dz)
                        
                        # 2. 修改像素值 (加入 15~240 的邊界保護)
                        px = np.clip(Expansion_block[pixel_idx], 15, 240)
                        if dy < 0: # 根據 s1 判斷加減
                            px -= move_val
                        else:
                            px += move_val
                        Expansion_block[pixel_idx] = px
            # D. 修改中心像素 [1,1] 嵌入輔助資訊
            # 保留前 4 位，後 4 位放入 mid_sign 與 mid_sign_plus
            orig_bin = format(Expansion_block[1, 1], '08b')[:4]
            # 確保長度正確 (2bit sign + 2bit dz)
            info_bits = (mid_sign + mid_sign_plus)[:4]
            Expansion_block[1, 1] = int(orig_bin + info_bits, 2)
            # E. 寫回影像
            final_img[i:i+2, j:j+2] = Expansion_block      
    # 存檔 (轉回 uint8)
    save_dir = os.path.dirname(final_save_path)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir, exist_ok=True)
    res, img_encode = cv2.imencode('.png', final_img.astype(np.uint8))
    if res:
        img_encode.tofile(final_save_path)
    return True # 記得回傳 True 代表成功

def generate_random_binary(img_src):
    secret_data =''.join(random.choice('01') for _ in range(1000000))
    chunk_size = 5
    chunks = [secret_data[i:i+chunk_size] for i in range(0, len(secret_data), chunk_size)]

    # --- 存檔區塊 ---
    with open(img_src, 'w') as f:
        f.write(secret_data)
    print("成功存檔：secret_data.txt")
    # ----------------

    return secret_data,chunk_size,chunks




# # 測試用
# if __name__ == "__main__":
#     # 測試用
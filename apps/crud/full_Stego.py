import os
import random
import shutil
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from flask import current_app

from apps.crud import InterpolationModel as interpolation
from apps.crud.ArrayCredit import output_matrix
from apps.crud.stego_image import data_hidding, generate_random_binary
# from extracted import Extraction_procedure


class StegoTool:
    @staticmethod
    def generate_interpolation(image, method):
        """產生插值影像 (支援灰階)"""
        # 如果是彩色圖，轉為灰階處理以符合你的 data_hidding 邏輯
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
        orig_height, orig_width = image.shape
        new_height, new_width = orig_height * 2, orig_width * 2
        new_image = np.zeros((new_height, new_width), dtype=image.dtype)

        for i in range(orig_height):
            for j in range(orig_width):
                A = int(image[i, j])
                B = int(image[i, j+1]) if j+1 < orig_width else A
                C = int(image[i+1, j]) if i+1 < orig_height else A
                D = int(image[i+1, j+1]) if (i+1 < orig_height and j+1 < orig_width) else A

                new_i, new_j = i * 2, j * 2
                # 動態呼叫 InterpolationModel 裡的方法
                try:
                    getattr(interpolation, method)(new_image, new_i, new_j, A, B, C, D)
                except AttributeError:
                    # 備援方案：簡單的填值
                    new_image[new_i, new_j] = A
                    
        return new_image

    @staticmethod
    def encode(user_id, email, input_img_path):
        """整合流程：縮放 -> 插值 -> 3D隱寫"""
        
        # ✅ 修正：不要直接用 cv2.imread
        try:
            raw_data = np.fromfile(input_img_path, dtype=np.uint8)
            img = cv2.imdecode(raw_data, cv2.IMREAD_COLOR)
        except Exception as e:
            return False, f"讀取原始圖失敗: {e}"

        if img is None: 
            return False, "找不到圖片或路徑包含無法解析的字元"

        # 1. 預處理：縮放成 256x256
        img_small = cv2.resize(img, (256, 256))
        
        # 2. 插值擴張成 512x512
        # 這裡會呼叫你寫的 NMI 插值邏輯
        interp_img = StegoTool.generate_interpolation(img_small, "NMI")
        
        # 建立目錄
        save_dir = os.path.join(current_app.root_path, 'static', 'stego', str(user_id))
        os.makedirs(save_dir, exist_ok=True)
        
        # ✅ 修正：存檔插值圖也要用 imencode
        temp_interp_path = os.path.join(save_dir, 'Interpolation_image.png')
        res, img_encode = cv2.imencode('.png', interp_img)
        if res:
            img_encode.tofile(temp_interp_path)

        # 3. 載入 3D 矩陣 (確認這行沒問題)
        # 嘗試路徑 B: 根目錄/3Dmatrix.npy (如果 apps 是子目錄)
        matrix_path = r'D:\3Dmatrix.npy' # 使用 r 前綴處理反斜線
        matrix = None  # 先初始化為 None

        if not os.path.exists(matrix_path):
            # 如果 D 槽找不到，試試看專案目錄下的 apps 資料夾 (備援)
            matrix_path = os.path.join(current_app.root_path, '3Dmatrix.npy')

        if os.path.exists(matrix_path):
            try:
                matrix = np.load(matrix_path)
                print(f"DEBUG: 成功載入矩陣，路徑: {matrix_path}")
            except Exception as e:
                return False, f"讀取 .npy 失敗: {str(e)}"
        else:
            return False, f"找不到矩陣檔案，搜尋路徑: {matrix_path}"

        # 關鍵防錯：確保 matrix 不是 None 才能往下跑
        if matrix is None:
            return False, "矩陣變數未初始化，請檢查檔案是否存在。"

        # 4. 執行隱寫
        # 將 email 轉為二進位
        binary_email = ''.join(format(ord(c), '08b') for c in email)
        
        final_stego_path = os.path.join(save_dir, 'Stego_image.png')
        
        # 呼叫你剛才確認過的 data_hidding
        success = data_hidding(matrix, temp_interp_path, binary_email, final_stego_path)
        
        return success, final_stego_path
       
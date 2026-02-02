from apps.crud.forms import UserForm                             #3

from flask import Blueprint, render_template, redirect, url_for, Response,request  #1 #3
import datetime, time
from apps.app import db                                          #2
import os, sys
from apps.crud.models import User                                #2
from .face import AttendanceSystem
import threading
#==================隱寫
from flask import send_from_directory, current_app
from apps.crud.full_Stego import StegoTool
from werkzeug.utils import secure_filename
#==================
import cv2
#instatiate flask app  
from flask import jsonify

import numpy as np

from apps.crud.extraction_procedure import Extraction_procedure

switch = 0
face_system = AttendanceSystem()
face_thread = None

# 修改你原本定義在外的 gen_frames
def gen_frames():
    global switch
    print("DEBUG: gen_frames streaming thread started") # 監控是否啟動
    while True:
        # 1. 檢查全局開關
        if switch == 1:
            # 2. 檢查 face_system 裡面是否有東西
            frame_data = face_system.recent_frame
            if frame_data is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
            else:
                # 如果開關開了但還沒圖，傳一張微小的黑圖或等待
                time.sleep(0.05) 
        else:
            # 開關關閉時，停止 yield，這會讓瀏覽器停止轉圈
            time.sleep(0.5)

crud = Blueprint(                    #1
    "crud",
    __name__,
    template_folder="templates",
    static_folder= "static",
)


@crud.route("/")
def index():
    return render_template("crud/index.html")

@crud.route('/video_feed')
def video_feed():
    # 這裡直接呼叫外面寫好的 gen_frames() 產生器
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@crud.route('/requests', methods=['POST', 'GET'])
def tasks():
    global switch, face_thread
    # --- 關鍵修正：確保進入此頁面時，註冊標記是關閉的 ---
    face_system.register_flag = False 
    face_system.register_result = None
    form = UserForm()
    status = None
    
    # 不要直接寫 switch = 0，這樣每次進頁面都會重設
    # 同步攝影機狀態
    if face_system.camera is not None and face_system.camera.isOpened():
        switch = 1
    else:
        switch = 0
        face_system.running = False

    if request.method == 'POST':
        if request.form.get('stop') == 'Stop/Start':
            if switch == 1:
                switch = 0
                face_system.stop() # 確保這裡面有呼叫 camera.release()
                status = "辨識系統已停止"
            else:
                # 啟動前再次確保 register_flag 是 False
                face_system.mode = "recognition" # 【新增】確保是辨識模式
                face_system.register_flag = False
                # 啟動前先更新資料庫特徵，確保能認出剛註冊的人
                face_system.load_database() 
                switch = 1
                face_thread = threading.Thread(
                    target=face_system.run_system,
                    daemon=True
                )
                face_thread.start()
                status = "辨識系統啟動中"

    return render_template('crud/requests.html', status=status, form=form, switch=switch)

@crud.route('/face/register/start', methods=['POST'])
def start_register():
    face_system.start_register() # 確保 mode 切換到 register
    
    # 啟動背景執行緒
    threading.Thread(
        target=face_system.run_system,
        daemon=True
    ).start()

    # 關鍵：帶上 status 讓 HTML 觸發 startPolling()
    form = UserForm()
    return render_template('crud/requests.html', status="辨識系統啟動中", form=form)

@crud.route('/face/register')
def register_form():
    # 1. 實例化表單物件
    form = UserForm()
    
    # 2. 將 form 傳遞給範本
    return render_template('crud/register_form.html', form=form)
    
@crud.route('/face/register/save', methods=['POST'])
def save_user():
    # 1. 取得表單資料
    name = request.form.get('name')
    email = request.form.get('email')
    encoding = face_system.register_result  # 這是 numpy array
    
    if encoding is None:
        return "找不到臉部特徵，請重新掃描", 400

    try:
        user = User(username=name, email=email)
        # 呼叫你在 models.py 定義的方法，將 numpy 轉為 pickle 二進位
        user.set_face_encoding(encoding) 
        
        db.session.add(user)
        db.session.commit()
        
        # 重要：同步更新「正在執行中」的辨識系統記憶體
        face_system.known_face_encodings.append(encoding)
        face_system.known_face_names.append(name)
        face_system.register_result = None
        face_system.stop()
        return redirect(url_for('crud.index'))
    except Exception as e:
        db.session.rollback()
        return f"儲存出錯: {str(e)}", 500
    
@crud.route('/face/register/check')
def check_register_status():
    # 檢查 face_system 是否已經抓到特徵了
    if face_system.register_result is not None:
        return {"status": "success"}
    return {"status": "scanning"}

@crud.route('/get_current_name')
def get_current_name():
    # 假設你的 face_system 會把辨識到的人名存在某個變數
    # 這裡回傳最後一個辨識到的人
    name = getattr(face_system, 'last_recognized_name', "Unknown")
    return jsonify({"name": name})

@crud.route('/stego/upload', methods=['GET', 'POST'])
def stego_upload():
    """顯示隱寫上傳頁面，包含辨識系統控制"""
    # 初始化狀態
    face_system.register_flag = False 
    face_system.register_result = None
    status = None
    form = UserForm()
    
    # 同步目前攝影機開關狀態
    if request.method == 'POST':
        if request.form.get('stop') == 'Stop/Start':
            # 檢查目前攝影機狀態來決定要開還是關
            if face_system.camera is not None and face_system.camera.isOpened():
                face_system.stop()
                status = "🔴 辨識系統已停止"
            else:
                face_system.mode = "recognition"
                face_system.load_database() 
                face_thread = threading.Thread(target=face_system.run_system, daemon=True)
                face_thread.start()
                status = "🟢 辨識系統啟動中"
    if face_system.camera is not None and face_system.camera.isOpened():
        is_active = 1
    else:
        is_active = 0
        
    # 如果你在處理 POST 的 Start，可以強制作為 1 傳回去
    if status == "🟢 辨識系統啟動中":
        is_active = 1
    print(f"DEBUG: 攝影機物件存在嗎? {face_system.camera is not None}")
    if face_system.camera:
        print(f"DEBUG: 攝影機開啟了嗎? {face_system.camera.isOpened()}")
    print(f"DEBUG: 目前 switch 的值是: {is_active}")
    
    return render_template('crud/stego_upload.html', status=status, form=form, switch=1)

@crud.route('/stego/save', methods=['POST'])
def stego_save():
    username = request.form.get('detected_username')
    file = request.files.get('carrier_image')

    # --- 1. 基本檢查 ---
    if not file or not username or username == "Unknown":
        return "Bad Request: Missing data or identity not confirmed", 400

    # 找到使用者 (取得 ID 與 Email)
    user = User.query.filter_by(username=username).first()
    if not user:
        return "資料庫找不到該使用者", 404

    # --- 2. 檔案處理 (建立目錄與路徑) ---
    filename = secure_filename(file.filename)
    
    # 建立上傳與輸出的物理路徑
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    stego_dir = os.path.join(current_app.root_path, 'static', 'stego', str(user.id))
    
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(stego_dir, exist_ok=True)

    temp_path = os.path.join(upload_dir, filename)

    # --- 3. 儲存原始上傳圖 ---
    # 使用 try-except 捕捉 Windows 路徑權限或亂碼問題
    try:
        # file.save 在處理中文路徑時較 OpenCV 穩定
        file.save(temp_path)
    except Exception as e:
        return f"檔案儲存失敗：{str(e)}", 500

    # --- 4. 執行隱寫演算法 ---
    # 注意：請確保 StegoTool.encode 內部已改用 imdecode/tofile 處理中文路徑
    try:
        success, result_message = StegoTool.encode(user.id, user.email, temp_path)
    except Exception as e:
        return f"演算法執行崩潰：{str(e)}", 500

    # --- 5. 回傳結果 ---
    if success:
        # 轉換為瀏覽器可讀取的 URL
        static_sub_path = f'stego/{user.id}/Stego_image.png'
        download_url = url_for('static', filename=static_sub_path)
        
        return f"""
            <div style="text-align: center; font-family: sans-serif;">
                <h3 style="color: #28a745;">✅ 數位憑證隱寫完成！</h3>
                <hr>
                <p><strong>辨識身分：</strong>{username}</p>
                <p><strong>嵌入資訊：</strong>{user.email}</p>
                <div style="margin: 20px 0;">
                    <img src="{download_url}" style="max-width: 400px; border: 2px solid #ddd; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);" alt="隱寫結果預覽">
                </div>
                <div style="margin-top: 20px;">
                    <a href="{download_url}" class="btn btn-primary" style="padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;" download>📥 下載隱寫影像 (.png)</a>
                </div>
                <br>
                <a href="{url_for('crud.stego_upload')}" style="color: #666; text-decoration: none;">← 返回重新製作</a>
            </div>
            <div style="margin-top: 10px;">
                <a href="/crud/stego/verify/{user.id}" class="btn btn-info" 
                style="padding: 10px 20px; background: #17a2b8; color: white; text-decoration: none; border-radius: 5px;">
                🔍 立即驗證隱寫憑證
                </a>
            </div>
        """
    else:
        return f"隱寫處理失敗：{result_message}", 500

@crud.route('/stego/verify/<int:user_id>')
def stego_verify(user_id):
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
    user = User.query.get(user_id)
    # 2. 執行解碼程序
    # 我們剛剛優化過的 Extraction_procedure
    success, extracted_info = Extraction_procedure(user_id, matrix,user.email)

    if success:
        # 3. 找到該使用者，進行比對驗證
        
        is_valid = (extracted_info.strip() == user.email.strip())
        
        status_color = "#28a745" if is_valid else "#dc3545"
        status_text = "✅ 驗證通過" if is_valid else "❌ 驗證失敗 (資料不符)"

        return f"""
            <div style="text-align: center; font-family: sans-serif; padding: 20px; border: 2px solid {status_color}; border-radius: 10px;">
                <h2 style="color: {status_color};">{status_text}</h2>
                <hr>
                <p><strong>從影像中提取出的資訊：</strong><br>
                   <span style="font-size: 1.2em; color: #333;">{extracted_info}</span>
                </p>
                <p><strong>預期使用者 Email：</strong><br>
                   {user.email}
                </p>
                <br>
                <a href="{url_for('crud.stego_upload')}" style="text-decoration: none; color: #007bff;">← 返回</a>
            </div>
        """
    else:
        return f"驗證過程中發生錯誤：{extracted_info}", 500

@crud.route("/sql")                                         #2
def sql():
    db.session.query(User).all()
    return "請確認控制台日誌"


@crud.route("/users")                                        #4
def users():
    users = User.query.all()
    return render_template("crud/index.html", users =users)











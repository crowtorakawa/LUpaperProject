import face_recognition
import cv2
import numpy as np
import os
import pickle
from datetime import datetime

# ================= 設定參數 =================
DB_FILE = "./face_database.pkl"
LOG_DIR = "attendance_logs"
TOLERANCE = 0.45               # 辨識門檻
FRAME_RESIZE = 0.25            # 畫面縮小比例 (加速)
RECORD_COOLDOWN = 10           # 同一人重複打卡冷卻時間 (秒)

class AttendanceSystem:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.last_recorded_time = {} 
        self.running = False
        self.camera = None
        self.recent_frame = None  
        self.mode = "idle"        
        self.register_result = None

        self.last_recognized_name = "Unknown"
        
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        
        # # 初始載入改從資料庫
        # self.load_database()

    def _do_register(self, frame):
        # 影像處理 (縮小以加快速度)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        encodings = face_recognition.face_encodings(rgb_frame)
        if encodings:
            self.register_result = encodings[0]
            self.mode = "idle"
            self.running = False  # 停止攝影機循環
            print("--- 特徵擷取成功，準備跳轉 ---") 

    def load_database(self):
        from apps.crud.models import User
        from flask import current_app
        
        with current_app.app_context():
            users = User.query.all()
            # 這裡要改成 get_face_encoding()
            self.known_face_encodings = [u.get_face_encoding() for u in users if u.face_encoding is not None]
            self.known_face_names = [u.username for u in users]
            print(f"--- 系統已載入 {len(self.known_face_names)} 位使用者資料 ---")

    def save_database(self):
        with open(DB_FILE, "wb") as f:
            data = {"encodings": self.known_face_encodings, "names": self.known_face_names}
            pickle.dump(data, f)
        print(f"--- 資料庫已存檔 ---")

    def stop(self):
        self.running = False
        self.mode = "recognition"  # 【新增】停止時強制切回辨識模式
        if self.camera:
            self.camera.release()
            self.camera = None
        print("--- 攝影機已強制關閉 ---")

    def run_system(self):
        """這是跑在背景線程 (face_thread) 的主要迴圈"""
        self.running = True
        if self.camera is None or not self.camera.isOpened():
            self.camera = cv2.VideoCapture(0)
            
        print("\n[辨識系統啟動]")
        
        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                break

            # 1. 影像預處理 (鏡像 + 縮小)
            frame = cv2.flip(frame, 1)
            small_frame = cv2.resize(frame, (0, 0), fx=FRAME_RESIZE, fy=FRAME_RESIZE)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            rgb_small_frame = np.ascontiguousarray(rgb_small_frame)

            # 2. 辨識或註冊邏輯
            if self.mode == "register":
                # 註冊模式：擷取特徵
                encodings = face_recognition.face_encodings(rgb_small_frame)
                if encodings:
                    self.register_result = encodings[0]
                    # 可以在 frame 上畫個提示
                    cv2.putText(frame, "Captured!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    self.mode = "recognition" 
                    self.running = False 
                    print("--- [SUCCESS] 特徵擷取完成，執行緒即將關閉 ---")
            
            else:
                # 辨識模式 (預設)
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                # 如果這一幀沒抓到任何人臉，可以考慮清空名字 (視你的論文需求而定)
                if not face_encodings:
                    self.last_recognized_name = "Unknown"

                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    name = "Unknown"
                    confidence = 0
                    
                    if len(self.known_face_encodings) > 0:
                        face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        min_dist = face_distances[best_match_index]

                        if min_dist < TOLERANCE:
                            name = self.known_face_names[best_match_index]
                            confidence = (1 - min_dist) * 100
                            
                            # 自動打卡
                            now = datetime.now()
                            if name not in self.last_recorded_time or (now - self.last_recorded_time[name]).total_seconds() > RECORD_COOLDOWN:
                                timestamp = now.strftime("%H%M%S")
                                cv2.imwrite(f"{LOG_DIR}/{name}_{timestamp}.jpg", frame)
                                self.last_recorded_time[name] = now
                                print(f"[OK] {name} 打卡成功")
                    self.last_recognized_name = name

                    # 繪製 UI 框 (座標還原)
                    top, right, bottom, left = [int(x * (1/FRAME_RESIZE)) for x in [top, right, bottom, left]]
                    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    cv2.putText(frame, f"{name} {confidence:.1f}%", (left, top - 10), 
                                cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

            # 3. 重要：將處理好的 frame 轉成 JPG 位元組，供 Flask 讀取
            _, buffer = cv2.imencode('.jpg', frame)
            self.recent_frame = buffer.tobytes()
            # print(f"DEBUG: Buffer updated! Size: {len(self.recent_frame)}")
        # 迴圈結束後釋放資源
        if self.camera:
            self.camera.release()
            self.camera = None
        self.recent_frame = None
        print("[系統關閉完成]")

    def start_register(self):
        self.mode = "register"

  
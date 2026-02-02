# LUpaperProject
# 臉部辨識數位憑證隱寫系統 (Biometric Stego-System)
# Biometric Stego-Certificate System (LUpaperProject)

這是一個結合 **臉部辨識 (Face Recognition)** 與 **可逆影像隱寫術 (Reversible Data Hiding)** 的安全驗證系統。系統透過攝影機辨識使用者身分，並將其憑證加密嵌入影像中。
製作構想是根據我自己的論文的可回復是資訊隱藏方法並實作出來的系統，請於碩博士論文網上查看方法https://ndltd.ncl.edu.tw/cgi-bin/gs32/gsweb.cgi/ccd=HGI.J4/record?r1=1&h1=0，
目前還很陽春，本次製作的目的是驗證可回復是資訊隱藏方法並應用於資料隱藏上。

[!IMPORTANT]
> **Current Status**: 系統目前處於 (概念驗證) 階段。
> **Future Improvements (尚未完善)**:
> 1. 個別查詢/搜尋功能之整合。
> 2. 跨環境之可靠度與多人壓力測試。

---

## 🚀 核心功能
* **身分連動製作**：偵測臉部後自動鎖定使用者 ID 與 Email，確保憑證與本人掛鉤。
* **自動路徑備援**：系統會優先搜尋 `D:\3Dmatrix.npy`，若不存在則自動切換至專案目錄，確保部署靈活性。
* **手動驗證中心**：支援外部上傳隱寫影像，解碼時會自動進行「現場插值預處理」，解決手動上傳缺乏對照圖的問題。
* **安全性**：強制執行 CSRF 防護與 3D 變換矩陣解密。

---

## 🛠️ 技術架構
* **後端框架**: Flask (Python)
* **影像處理**: OpenCV, NumPy (採用 `imdecode` 支援中文路徑)
* **身分驗證**: 前端辨識系統整合
* **資料庫**: SQLAlchemy / SQLite

------

開始測試前請先點選，cube_labe.exe，生成3D憑證

------
## 📂 專案目錄結構
```text
paperProject/
│  .env                        # 環境變數設定 (Secret Key 等)
│  local.sqlite                # 資料庫檔案
│  README.md                   # 專案說明文件
│
├─apps/
│  │  3Dmatrix.npy             # 核心隱寫變換矩陣 (解碼關鍵)
│  │  app.py                   # Flask 應用程式進入點
│  │  __init__.py
│  │
│  ├─crud/                     # 系統核心邏輯模組
│  │  │  ArrayCredit.py        # 陣列處理相關工具
│  │  │  extraction_procedure.py # 隱寫資訊提取演算法
│  │  │  face.py               # 臉部辨識系統控制邏輯
│  │  │  face_database.pkl     # 已註冊人臉特徵資料庫
│  │  │  forms.py              # Flask-WTF 表單定義 (UserForm)
│  │  │  full_Stego.py         # 隱寫嵌入完整流程控制
│  │  │  InterpolationModel.py  # 影像插值演算法模型
│  │  │  models.py             # SQLAlchemy 資料庫模型定義
│  │  │  views.py              # 路由控制器 (主要開發邏輯所在)
│  │  │  __init__.py
│  │  │
│  │  ├─templates/             # HTML 模板檔案
│  │  │  └─crud/
│  │  │      ├── index.html    # 系統首頁
│  │  │      ├── search.html   # 憑證驗證中心 (手動驗證頁面)
│  │  │      ├── stego_upload.html # 憑證製作頁面 (含攝影機控制)
│  │  │      └── ...           # 其他 CRUD 頁面 (create, edit, register)
│  │  └─static/                # CRUD 模組專用靜態資源
│  │      └─style.css          # 前端樣式表
│  │
│  └─static/                   # 全域靜態檔案存放區 (隱寫結果儲存點)
│      ├─stego/
│      │  ├─1/                 # 使用者 ID 為 1 的憑證存放目錄
│      │  │  ├── Interpolation_image.png # 參考插值影像
│      │  │  └── Stego_image.png         # 最終隱寫結果圖
│      │  ├─manual_temp/       # 手動驗證時的暫存資料夾
│      │  └─manual_verify.png  # 手動驗證上傳圖
│      └─uploads/              # 原始載體影像上傳區
│
├─attendance_logs/             
└─migrations/                  # 資料庫遷移紀錄 (Flask-Migrate)

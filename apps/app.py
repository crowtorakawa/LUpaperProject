from pathlib import Path                    #2
from flask import Flask                    #1
from flask_migrate import Migrate           #2
from flask_sqlalchemy import SQLAlchemy     #2
from flask_wtf.csrf import CSRFProtect       #3

csrf = CSRFProtect()
db = SQLAlchemy()                           #2

def create_app():
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY="2AZSMss3p5QPbcY2hBsJ",
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{Path(__file__).parent.parent / 'local.sqlite'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ECHO = True,
        WTF_CSRF_SECRET_KEY = "AuwzyszU5sugKN7KZs6f",
    )

    csrf.init_app(app)
    db.init_app(app)
    Migrate(app, db)

    # 1. 先載入藍圖與 views
    from apps.crud import views as crud_views
    app.register_blueprint(crud_views.crud, url_prefix="/crud")

    # 2. 使用 app_context 確保資料庫可以安全讀取
# --- 關鍵修正區段 ---
    with app.app_context():
        from apps.crud.models import User
        # 1. 啟動時先確保表格一定存在
        db.create_all() 
        
        # 2. 確定有表了，才去載入資料
        from apps.crud.views import face_system
        face_system.load_database()

    return app   #1

#Version: 3.0.1  Werkzeug 你的 Werkzeug 版本是 3.0.1
# 絕對無法和 Flask 1.x 相容
#（因為從 Werkzeug 2.x 之後就把 url_quote 刪掉了）~``
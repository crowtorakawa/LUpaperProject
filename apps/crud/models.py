from datetime import datetime                        #2

from apps.app import db                              #2
from werkzeug.security import generate_password_hash #2

import pickle

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String)
    # 使用 LargeBinary 儲存 pickle 過後的 numpy 陣列
    face_encoding = db.Column(db.LargeBinary, nullable=True)

    def set_face_encoding(self, obj):
        # 將 numpy 陣列轉為二進位
        self.face_encoding = pickle.dumps(obj)

    def get_face_encoding(self):
        # 將二進位轉回 numpy 陣列
        if self.face_encoding:
            return pickle.loads(self.face_encoding)
        return None
# class User(db.Model):

#     __tablename__ = "users"                          #2


#     id = db.Column(db.Integer, primary_key = True)                                      #2
#     username = db.Column(db.String, index = True)                                       #2
#     email = db.Column(db.String, unique=True, index = True)                             #2
#     password_hash = db.Column(db.String)                                                #2
#     created_at = db.Column(db.DateTime, default = datetime.now)                         #2
#     updated_at = db.Column(db.DateTime, default = datetime.now, onupdate = datetime.now) #2

#     @property                                                               #2
#     def password(self):
#         raise AttributeError("無法加載")
    
#     @password.setter
#     def password(self, password):
#         self.password_hash = generate_password_hash(password)
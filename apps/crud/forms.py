from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, length


class UserForm(FlaskForm):

    username = StringField(
        "使用者名稱",
        validators=[
            DataRequired(message="必須填寫使用者名稱。"),
            length(max=30, message="請勿輸入超過30個字元"),
        ],
    )

    email = StringField(
        "郵件位址",
        validators=[
            DataRequired(message="必須填寫郵件位址。"),
            Email(message="請依照電子郵件的格式輸入"),
        ],
    )

    password = PasswordField(
        "密碼",
        validators=[DataRequired(message="必須填寫密碼。")]
    )
    
    submit = SubmitField("提交表單")
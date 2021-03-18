# アプリケーションを初期化する

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# アプリのオブジェクト
app = Flask(__name__)
app.config.from_object("fanach.config")

# 辞書データベース
db = SQLAlchemy(app)

# Blueprintの登録
from fanach.views.dic import dic
from fanach.views.login import login
app.register_blueprint(dic, url_prefix="/dic")
app.register_blueprint(login, url_prefix="/login")

# viewファイル
from fanach.views import dic, login

from fanach.models.words import *

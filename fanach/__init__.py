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
from fanach.views.api import api
app.register_blueprint(dic, url_prefix="/dic")
app.register_blueprint(login, url_prefix="/user")
app.register_blueprint(api, url_prefix="/api")

# viewファイル
from fanach.views import dic, login

from fanach.models.words import *

from datetime import datetime

# 現在の日時との差分を適切なフォーマットに変換するフィルタ
@app.template_filter("timedelta")
def format_timedelta(dt):
    td = datetime.utcnow() - dt
    if td.days >= 365:
        years = td.days // 365
        return "%d年" % years
    elif td.days >= 30:
        months = td.days // 30
        return "%dヶ月" % months
    elif td.days >= 7:
        weeks = td.days // 7
        return "%d週間" % weeks
    elif td.days > 1:
        return "%d日" % td.days
    elif td.seconds > 3600:
        hours = td.seconds // 3600
        return "%d時間" % hours
    elif td.seconds > 60:
        minutes = td.seconds // 60
        return "%d分" % minutes
    else:
        return "%d秒" % td.seconds

from fanach.utils.markdown import parse_md

@app.template_filter("markdown")
def md2html(md):
    if md is None:
        return ""
    return parse_md(md)

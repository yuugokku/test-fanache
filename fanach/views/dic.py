# dic.py : 辞書アプリのメインモジュール

from flask import request, redirect, url_for, render_template, flash, session
from flask import Blueprint

from fanach import app
from fanach.views.login import login_required

dic = Blueprint("dic", __name__)

# ルートディレクトリ -> 項目表示
@dic.route("/")
def show_items(word=""):
	return render_template("dic/index.html")

@dic.route("/new-dic", methods=["GET", "POST"])
@login_required
def new_dic(editor):
	if request.method == "GET":
		render_template("dic/new_dic.html", editor=editor)
import re
import hashlib

from flask import request, redirect, url_for, render_template, flash, session
from flask import Blueprint
from functools import wraps

from fanach import app, db
from fanach.models.words import Word, User, Dictionary

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 50

login = Blueprint("login", __name__)

def authenticate(user_id, formpassword):
	hashed_password = User.query.get(user_id).password
	return hashlib.sha256(formpassword.encode()).hexdigest() == hashed_password

def login_required(view):
	@wraps(view)
	def inner(*args, **kwargs):
		if not session.get("logged_in"):
			return redirect(url_for("login.login_form"))
		return view(*args, **kwargs)
	return inner

# /login/ ログイン画面、処理
@login.route("/login", methods=["GET", "POST"])
def login_form():
	error_msg = ""
	if request.method == "POST":
		user = User.query.filter_by(username=request.form["username"]).first()
		if user is None:
			error_msg = "ユーザ名が異なります"
		elif not authenticate(user.user_id, request.form["password"]):
			error_msg = "パスワードが異なります"
		else:
			session["logged_in"] = True
			session["current_user"] = user.user_id
			session["screenname"] = user.screenname
			return redirect(url_for("dic.show_all_dics"))
	return render_template("login.html", error_msg=error_msg)

# /login/no-out ログアウト処理
@login.route("/logout")
def logout():
	session["logged_in"] = False
	session["current_user"] = None
	session["screenname"] = "ゲスト"
	return redirect(url_for("dic.show_all_dics"))

# /login/register ユーザ登録
@login.route("/register", methods=["GET", "POST"])
def register():
	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]
		email = request.form["email"]
		is_valid = True

		# エラーメッセージ
		username_msg = ""
		email_msg = ""
		password_msg = ""

		if len(username) > MAX_PASSWORD_LENGTH:
			# ユーザ名長すぎ
			is_valid = False
			username_msg = "ユーザ名が長すぎます。ユーザ名は50文字以内である必要があります。"
		elif len(username) < 1:
			# ユーザ名が1文字未満
			is_valid = False
			username_msg = "ユーザ名は1文字以上である必要があります。"
		userlist = User.query.all()
		for usr in userlist:
			if username == usr.username:
				# ユーザ名が重複している
				is_valid = False
				username_msg = "そのユーザ名は二番煎じなので使えません"
			    

		if len(password) < MIN_PASSWORD_LENGTH:
			# 短すぎ
			is_valid = False
			print("短すぎるパスワード")
			password_msg = "パスワードが短すぎます。パスワードは8文字から50文字の間である必要があります。"
		elif len(password) > MAX_PASSWORD_LENGTH:
			# パスワード長すぎ
			is_valid = False
			password_msg = "パスワードが長すぎます。どうせブラウザに覚えさせてるんでしょ？"

		pat = r"^[a-zA-Z0-9_+-]+(.[a-zA-Z0-9_+-]+)*@([a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.)+[a-zA-Z]{2,}$"
		match = re.match(pat, email)
		if match is None:
			is_valid = False
			email_msg = "メールアドレスの書式ではありません。"

		if is_valid:
			user = User(
				username = username,
				screenname = username,
				password = hashlib.sha256(password.encode()).hexdigest(),
				email = email,
				twitter_id = "",
				profile = "")
			print("新しいユーザ:", username)
			db.session.add(user)
			db.session.commit()
			last_user = User.query.order_by(User.user_id.desc()).first()
			user_id = last_user.user_id
			session["logged_in"] = True
			session["current_user"] = user_id
			session["screenname"] = user.screenname
			return redirect(url_for("dic.show_all_dics"))
		else:
			return render_template(
				                    "register.html", 
				                    username_msg = username_msg,
				                    email_msg = email_msg,
				                    password_msg = password_msg
				                        )
	elif request.method == "GET":
		return render_template("register.html", username_msg="", email_msg="", password_msg="")

@login.route("/suggestions", methods=["GET"])
@login_required
def show_suggestions():
	user = User.query.get(session.get("current_user", default=0))
	if user is None:
		return redirect(url_for("login.logout"))
	suggestions = []
	for d in user.dictionaries.all():
		for s in d.suggestions.all():
			suggestions.append(s)
	return render_template("tasks.html", suggestions=suggestions)

@login.app_errorhandler(404)
def non_existant_route(error):
	return redirect(url_for("dic.show_all_dics"))
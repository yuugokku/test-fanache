# user.py : ユーザー情報を表示
from flask import request, url_for, render_template, flash, redirect
from flask import Blueprint

from fanach import app, db
from fanach.models.words import User

user = Blueprint("user", __name__)

@user.route("/<int:user_id>")
def show_user_id(user_id):
    usr = User.query.get(user_id)
    if usr is None:
        flash("ユーザが存在しません")
        return redirect(url_for("dic.show_all_dics"))
    username = usr.username
    return redirect(url_for("user.show_user", username=username))

@user.route("/<username>", methods=["GET", "POST"])
def show_user(username):
    user = None
    if request.method == "GET":
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("ユーザが存在しません")
            return redirect(url_for("dic.show_all_dics"))
        return render_template("user/profile.html", user=user)

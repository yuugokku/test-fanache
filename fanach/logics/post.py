# post.py : 辞書作成、編集、削除、単語作成、編集、削除
from flask import request, redirect, url_for, render_template, flash, session, make_response

from fanach import app, db
from fanach.views.login import login_required, authenticate
from fanach.models.words import Word, User, Dictionary, Suggestion

def new_dic(req):
    is_valid = True
    message = ""
    new_dic_id = None
    if (len(req["dicname"]) < 1) or (len(req["dicname"]) > 100):
        message += "辞書の名前は1文字から100文字である必要があります。"
        is_valid = False
    if is_valid:
        owner = User.query.get(session["current_user"])
        dictionary = Dictionary(
                dicname=req["dicname"],
                owner = owner,
                description = req["description"],
                scansion_url = req["scansion_url"]
                )
        db.session.add(dictionary)
        db.session.commit()
        new_dic_id = dictionary.dic_id
    return new_dic_id, is_valid, message


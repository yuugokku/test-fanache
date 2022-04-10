# api.py : 検索、編集などをHTMLを介さずJSONで行う。
from fanach.views.login import login_required
from urllib.parse import quote
from datetime import datetime

from flask import request, redirect, url_for, session, make_response
from flask import Blueprint
from flask.json import jsonify
from sqlalchemy import or_

from fanach import app, db
from fanach.models.words import Word, User, Dictionary, Suggestion
from fanach.utils.search import Condition, condition_default
import fanach.logics as fl

import json

api = Blueprint("api", __name__)


def my_status(r):
    if r:
        return 'success'
    return 'fail'

def make_api_response():
    res = make_response()
    res.charset = "utf-8"
    res.mimetype = "application/json"
    return res


# 辞書情報のdict型にownerの名前をくっつける
def dic_join(dictionary):
    screenname = dictionary.owner.screenname
    words = dictionary.words.all().__len__()
    joined = dictionary.toDict()
    joined["owner"] = screenname.__str__()
    joined["words"] = words
    return joined


def word_join(word):
    editorname = word.editor.screenname
    dicname = word.dictionary.dicname
    joined = word.toDict()
    joined["editor"] = editorname.__str__()
    joined["dictionary"] = dicname.__str__()
    return joined


# / 辞書一覧取得
@api.route("/")
def show_all_dics():
    dictionaries, _ = fl.show_all_dics()
    return {"dictionaries": [dic_join(d) for d in dictionaries]}

@api.route("/<int:dic_id>/info")
def show_dic(dic_id):
    dictionary = fl.show_dic(dic_id)
    if dictionary is None:
        return {"status": my_status(False)}
    return dic_join(dictionary)


@api.route("/<int:dic_id>/word")
def show_word(dic_id):
    keyword, target, _, words = fl.show_word(dic_id)
    return {"keyword": keyword, "target": target, "words": [word_join(w) for w in words]}


@api.route("/<dic_id>/search", methods=["GET"])
def search(dic_id):
    conditions, targets, words_to_show = fl.search(dic_id)
    conditions = [{"target": t, "keyword": c.keyword, "option": c.option} for t, c in zip(targets, conditions)]
    words = list(filter(word_join, words_to_show))
    return {"conditions": conditions, "words": words}


# 辞書を新規作成
@api.route("/new", methods=["POST"])
@login_required
def new_dic():
    new_dic_id, is_valid, message = fl.new_dic(request.get_json())
    return jsonify(dic_id=new_dic_id, status=my_status(is_valid), message=message)


# 辞書情報の編集
@api.route("/<int:dic_id>/edit", methods=["POST"])
@login_required
def edit_dic(dic_id):
    message = ""
    is_valid = True
    req = json.loads(request.json)
    
    dictionary = Dictionary.query.get(dic_id)
    if session["current_user"] != dictionary.owner.user_id:
        is_valid = False
        message += "No permission. Only the owner of a dictinoary can edit the dictionary information."

    if (len(req["dicname"]) < 1) or (len(req["dicname"]) > 50):
        is_valid = False
        message += "Length of dictionary name should be between 1 and 50 characters."

    if is_valid:
        dictionary.dicname = req["dicname"]
        dictionary.description = req["description"]
        db.session.merge(dictionary)
        db.session.commit()
        message += "Dictionary information updated."
    else:
        message += "Could not update dictionary information."

    return jsonify(dic_id=dictionary.dic_id, status=my_status(is_valid), message=message)


# 辞書に単語を追加
# dic.pyと異なり、単語をリストで受け取る。
# {
#     "new_words": [
#         {... }, {... }, // 単語のリスト
#     ],
# }
@api.route("/<int:dic_id>/new", methods=["POST"])
@login_required
def new_word(dic_id):
    dictionary = Dictionary.query.get(dic_id)
    message = ""
    req = json.loads(json.loads(request.json))

    if session["current_user"] != dictionary.owner.user_id:
        message += "No permission to create new words."
        return jsonify(status=my_status(False), message=message, added=0, ignored=len(req['new_words']))

    editor = User.query.get(session["current_user"])
    added, ignored = 0, 0
    for i, w in enumerate(req["new_words"]):
        is_valid = True
        if len(w["word"].strip()) == 0:
            message += f"{i}: Word should have at least one characters.\n"
            is_valid = False
        if len(w["word"]) > 200:
            message += f"{i}: Too long Word.\n"
            is_valid = False
        words = Word.query.filter(Word.dic_id == dic_id, Word.word == w["word"]).first()
        if words is not None:
            message += f"{i}: Word already exists.\n"
            is_valid = False
        if is_valid:
            newword = Word(
                    dictionary = dictionary,
                    word = w["word"],
                    trans = w["trans"],
                    ex = w["ex"],
                    editor = editor)
            added += 1
        else:
            ignored += 1
        db.session.add(newword)
    dictionary.updated_at = datetime.utcnow()
    db.session.commit()
    message += f"{added} created."
    return jsonify(status=my_status(True), message=message, added=added, ignored=ignored)


# 辞書の単語を編集、または造語する。
# dic_idが与えられていないとき("dic_id": -1)、造語する。
@api.route("/<int:dic_id>/wedit", methods=["POST"])
@login_required
def edit_word(dic_id):
    dictionary = Dictionary.query.get(dic_id)
    message = ""
    req = json.loads(request.json)

    if session["current_user"] != dictionary.owner.user_id:
        message += "No permission to edit words."
        return jsonify(status=my_status(False), message=message, added=0, edited=0, ignored=len(req['new_words']))

    editor = User.query.get(session["current_user"])
    added, edited, ignored = 0, 0, 0
    allow_create = req["allow_create"]
    for i, w in enumerate(req["edit_words"]):
        is_valid = True
        if len(w["word"].strip()) == 0:
            message += f"{i}: Word should have at least one characters.\n"
            is_valid = False
        if len(w["word"]) > 200:
            message += f"{i}: Too long Word.\n"
            is_valid = False

        if w["word_id"] == -1:
            words = Word.query.filter(Word.dic_id == dic_id, Word.word == w["word"]).first()
            if words is not None:
                message += f"{i}: Word already exists.\n"
                is_valid = False
            if not allow_create:
                message += f"{i}: New word is given but allow_create is turned off.\n"
                is_valid = False
            if is_valid:
                newword = Word(
                        dictionary = dictionary,
                        word = w["word"],
                        trans = w["trans"],
                        ex = w["ex"],
                        editor = editor)
                db.session.add(newword)
                added += 1
            else:
                ignored += 1
        else:
            word = Word.query.get(w["word_id"])
            word.word = w["word"]
            word.trans = w["trans"]
            word.ex = w["ex"]
            word.editor = editor
            word.updated_at = datetime.utcnow()
            db.session.merge(word)
            edited += 1

    dictionary.updated_at = datetime.utcnow()
    db.session.commit()
    message += f"{edited} words updated.\n"
    message += f"{added} new words created."
    return jsonify(status=my_status(True), message=message, added=added, edited=edited, ignored=ignored)


# 辞書から単語を削除する。
# word_idを指定する
@api.route("/<int:dic_id>/delete", methods=["POST"])
@login_required
def delete_word(dic_id):
    dictionary = Dictionary.query.get(dic_id)
    message = ""
    
    if session["current_user"] != dictionary.owner.user_id:
        message += "No permission."
        return jsonify(status=my_status(False), message=message, deleted=0, ignored=0)

    req = json.loads(request.json)
    deleted, ignored = 0, 0
    for i, w in enumerate(req["delete_words"]):
        is_valid = True
        word = Word.query.get(w)
        if word is None:
            is_valid = False
            message += f"{i}: Word does not exist.\n"
        if is_valid:
            db.session.delete(word)
            deleted += 1
        else :
            ignored += 1
    dictionary.updated_at = datetime.utcnow()
    db.session.commit()
    message += f"{deleted} words deleted."
    return jsonify(status=my_status(True), message=message, deleted=deleted, ignored=ignored)

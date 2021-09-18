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
    dictionaries = Dictionary.query.order_by(Dictionary.updated_at.desc()).all()
    res = make_api_response()
    result_dict = {}
    result_dict["dictionaries"] = [dic_join(d) for d in dictionaries]
    print(result_dict)
    res.data = json.dumps(result_dict, ensure_ascii=False)
    return res

@api.route("/<int:dic_id>/info")
def show_dic(dic_id):
    dictionary = Dictionary.query.get(dic_id)
    res = make_api_response()
    if dictionary is None:
        res.data = json.dumps({})
        return res
    res.data = json.dumps(dic_join(dictionary), ensure_ascii=False)
    return res


@api.route("/<int:dic_id>/word")
def show_word(dic_id):
    keyword = request.args["keyword"]
    target = request.args.get("target", default=None)
    if target is None:
        words = Word.query.filter(
                Word.dic_id == dic_id, 
                or_(Word.word.startswith(keyword), Word.trans.contains(keyword))
                ).all()
        target = "trans"
    else:
        if target == "word":
            words = Word.query.filter(Word.dic_id == dic_id, Word.word.startswith(keyword)).all()
        elif target == "trans":
            words = Word.query.filter(Word.dic_id == dic_id, Word.trans.contains(keyword)).all()
    res = make_api_response()
    result_dict = {}
    result_dict["keyword"] = keyword
    result_dict["target"] = target
    result_dict["words"] = [word_join(w) for w in words]
    res.data = json.dumps(result_dict, ensure_ascii=False)
    return res


@api.route("/<dic_id>/search", methods=["GET"])
def search(dic_id):
    dictionary = Dictionary.query.get(dic_id)
    words = dictionary.words.all()
    MAX_CONDITIONS = app.config["MAX_CONDITIONS"]
    conditions = [
            Condition(
                keyword = request.args["keyword_" + str(i)],
                option = request.args["option_" + str(i)],
                )
            for i in range(MAX_CONDITIONS) if request.args.get("keyword_" + str(i), "").strip() != ""
            ]
    targets = [
            request.args["target_" + str(i)]
            for i in range(MAX_CONDITIONS) if request.args.get("keyword_" + str(i), "").strip() != ""
            ]
    res = make_api_response()
    result_dict = {}
    result_dict["conditions"] = [{"target": t, "keyword": c.keyword, "option": c.option} for t, c in zip(targets, conditions)]
    if len(conditions) == 0:
        result_dict["words"] = [word_join(w) for w in words]
        res.data = json.dumps(result_dict)
        return res
    result_dict["words"] = []
    for w in words:
        flags = []
        for c, t in zip(conditions, targets):
            if t == "wordtrans":
                flags.append(c.validate(getattr(w, "word")) or c.validate(getattr(w, "trans")))
            elif t == "rhyme":
                flags.append(c.validate(getattr(w, "word"), rhyme=True))
            else:
                flags.append(c.validate(getattr(w, t)))
        if sum(flags) == len(flags):
            result_dict["words"].append(word_join(w))
    res.data = json.dumps(result_dict, default=condition_default, ensure_ascii=False)
    return res


# 辞書を新規作成
@api.route("/new", methods=["POST"])
@login_required
def new_dic():
    message = ""
    is_valid = True
    new_dic_id = -1
    
    req = json.loads(request.json)
    if (len(req["dicname"]) < 1) or (len(req["dicname"]) > 50):
        message += "Length of dictionary name should be between 1 and 50 characters."
        is_valid = False

    if is_valid:
        owner = User.query.get(session["current_user"])
        dictionary = Dictionary(dicname=req["dicname"], owner=owner, description=req["description"])
        db.session.add(dictionary)
        db.session.commit()
        new_dic_id = dictionary.dic_id
        message += f"Dictionary {req['dicname']} has been created."
    else:
        message += "Failed to create a dictionary."
    
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

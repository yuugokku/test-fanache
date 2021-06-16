# api.py : 辞書検索を行い、結果をdict型で渡すモジュール
from urllib.parse import quote
from datetime import datetime

from flask import request, redirect, url_for, render_template, flash, session, make_response
from flask import Blueprint
from sqlalchemy import or_

from fanach import app, db
from fanach.views.login import login_required, authenticate
from fanach.models.words import Word, User, Dictionary, Suggestion
from fanach.utils.converter import export_xml, parse, export_csv
from fanach.utils.search import Condition, condition_default

import json

api = Blueprint("api", __name__)

def make_api_response():
    res = make_response()
    res.charset = "utf-8"
    res.mimetype = "application/json"
    return res


# 辞書情報のdict型にownerの名前をくっつける
def dic_join(dictionary):
    screenname = dictionary.owner.screenname
    joined = dictionary.toDict()
    joined["owner"] = screenname.__str__()
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
    res.data = json.dumps(result_dict)
    return res

@api.route("/<int:dic_id>/info")
def show_dic(dic_id):
    dictionary = Dictionary.query.get(dic_id)
    res = make_api_response()
    if dictionary is None:
        res.data = json.dumps({})
        return res
    res.data = json.dumps(dic_join(dictionary))
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
            words = Word.query.filter(Word.dic_id == dic_id, Word.word.contains(keyword)).all()
    res = make_api_response()
    result_dict = {}
    result_dict["keyword"] = keyword
    result_dict["target"] = target
    result_dict["words"] = [word_join(w) for w in words]
    print(result_dict)
    res.data = json.dumps(result_dict)
    return res

MAX_CONDITIONS = 10

@api.route("/<dic_id>/search", methods=["GET"])
def search(dic_id):
    dictionary = Dictionary.query.get(dic_id)
    words = dictionary.words.all()
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
    result_dict["conditions"] = [{"target": t, "condition": c} for t, c in zip(targets, conditions)]
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
    res.data = json.dumps(result_dict, default=condition_default)
    return res

# get.py : 検索、情報取得
import requests

from flask import request, redirect, url_for, render_template, flash, session, make_response
from sqlalchemy import or_

from fanach import app, db
from fanach.views.login import login_required, authenticate
from fanach.models.words import Word, User, Dictionary, Suggestion
from fanach.utils.converter import export_xml, parse, export_csv
from fanach.utils.search import Condition

def show_all_dics():
    """
    更新された辞書、ログインしているユーザの辞書を一覧表示

    Returns: Tuple(List(Dictionary), List(Dictionary))
    """
    dictionaries = Dictionary.query.order_by(Dictionary.updated_at.desc()).limit(10).all()
    if not session.get("logged_in", default=False):
        my_dics = []
    else:
        user = User.query.get(session["current_user"])
        if user is None:
            my_dics = []
        else:
            my_dics = user.dictionaries.order_by(Dictionary.updated_at.desc()).all()
    return dictionaries, my_dics


def show_dic(dic_id):
    dictionary = Dictionary.query.get(dic_id)
    return dictionary


def show_word(dic_id):
    dictionary = Dictionary.query.get(dic_id)
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
    return keyword, target, dictionary, words


def search(dic_id):
    dictionary = Dictionary.query.get(dic_id)
    words = dictionary.words.all()
    words_to_show = []

    conditions = []
    i = 0
    while request.args.get("keyword_" + str(i), "").strip() != "":
        conditions.append(
            Condition(
                keyword = request.args["keyword_" + str(i)],
                option = request.args["option_" + str(i)],
            )
        )
        i += 1
    targets = []
    i = 0
    rhymes = None
    while request.args.get("target_" + str(i), "").strip() != "":
        t = request.args["target_" + str(i)]
        # targetに"rhyme"を含むときのみ、韻律を問い合わせる
        if t == "rhyme" and rhymes is None:
            if dictionary.scansion_url != "" or dictionary.scansion_url is None:
                rhymes_response = requests.post(dictionary.scansion_url, json={"texts": [w.word for w in words]})
                rhymes = rhymes_response.json()
            else:
                flash("韻律解析URLが設定されていないため、韻律を用いた検索ができません。")
                continue
        targets.append(t)
        i += 1
    if len(conditions) == 0:
        return []
    for w in words:
        flags = []
        for c, t in zip(conditions, targets):
            if t == "wordtrans":
                flags.append(c.validate(getattr(w, "word")) or c.validate(getattr(w, "trans")))
            elif t == "rhyme":
                flags.append(c.validate(rhymes.get(getattr(w, "word"))))
            else:
                flags.append(c.validate(getattr(w, t)))
        if sum(flags) == len(flags):
            words_to_show.append(w)
    return conditions, targets, words_to_show

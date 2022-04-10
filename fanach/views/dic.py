# dic.py : 辞書アプリのメインモジュール
from urllib.parse import quote
from datetime import datetime
import requests, json

from flask import request, redirect, url_for, render_template, flash, session, make_response
from flask import Blueprint
from sqlalchemy import or_

from fanach import app, db
from fanach.views.login import login_required, authenticate
from fanach.models.words import Word, User, Dictionary, Suggestion
from fanach.utils.converter import export_xml, parse, export_csv
from fanach.utils.search import Condition
import fanach.logics as fl


dic = Blueprint("dic", __name__)

@dic.route("/")
def show_all_dics():
    dictionaries, my_dics = fl.show_all_dics()
    return render_template("dic/all.html", dictionaries=dictionaries, my_dics=my_dics)

# 辞書の情報を表示。辞書ページの外部リンクにはこのURLを用いる。
@dic.route("/<int:dic_id>/info")
def show_dic(dic_id):
    dictionary = fl.show_dic(dic_id)
    if dictionary is None:
        flash("辞書が存在しません。")
        return redirect(url_for("dic.show_all_dics"))
    return render_template("dic/info.html", dictionaries=[], dictionary=dictionary)

@dic.route("/<int:dic_id>")
def _show_dic(dic_id):
    return redirect(url_for("dic.show_dic", dic_id=dic_id))

# キーワード検索
@dic.route("/<int:dic_id>/word")
def show_word(dic_id):
    return fl.show_word(dic_id)

# 辞書を新規登録
@dic.route("/new", methods=["GET", "POST"])
@login_required
def new_dic():
    dicname_msg = ""
    xmlfile_msg = ""
    if request.method == "GET":
        dictionaries = Dictionary.query.all()
        return render_template("dic/new.html", dictionaries=dictionaries, dicname_msg=dicname_msg, xmlfile_msg=xmlfile_msg)
    elif request.method == "POST":
        new_dic_id, is_valid, dicname_msg = fl.new_dic(request.form)

        xmlfile = None
        if "xmlfile" in request.files:
            xmlfile = request.files["xmlfile"]
            if xmlfile.content_length > app.config["MAX_CONTENT_LENGTH"]:
                is_valid = False
                xmlfile_msg = "ファイルサイズが大きすぎます。2KB以下のファイルのみアップロードできます。"

        if is_valid:
            owner = User.query.get(session["current_user"])
            dictionary = Dictionary.query.get(new_dic_id)
            flash_msg = "辞書 %s を作成しました。" % request.form.get("dicname")
            # ファイルアップロード
            if xmlfile is not None:
                xmltext = xmlfile.read()
                # XML変換処理を挟む -> Wordテーブルに追加
                if xmlfile.mimetype in ["text/xml"]:
                    records = parse(xmltext, xmlfile.mimetype)
                    word_count = 0
                    for word, trans, ex in records:
                        newword = Word(
                                dictionary = dictionary,
                                word = word,
                                trans = trans,
                                ex = ex,
                                editor = owner)
                        word_count += 1
                        db.session.add(newword)
                    flash_msg += "%d語をファイルからインポートしました。" % word_count
            db.session.commit()
            flash(flash_msg)
            return redirect(url_for("dic.show_dic", dic_id=dictionary.dic_id))
        else:
            print("作成失敗", dicname_msg, xmlfile_msg)
            return render_template("dic/new.html", dictionaries=[], dicname_msg=dicname_msg, xmlfile_msg=xmlfile_msg)

@dic.route("/<int:dic_id>/edit", methods=["GET", "POST"])
@login_required
def edit_dic(dic_id):
    dictionary = Dictionary.query.get(dic_id)
    if session["current_user"] != dictionary.owner.user_id:
        flash("権限がありません。辞書のデータは作成者のみ編集できます。")
        return redirect(url_for("dic.show_dic", dic_id=dic_id))
    if request.method == "GET":
        return render_template("dic/edit.html", dictionaries=[], dictionary=dictionary, dicname_msg="")
    elif request.method == "POST":
        dictionary.dicname = request.form["dicname"]
        dictionary.scansion_url = request.form["scansion_url"]
        dictionary.description = request.form["description"]
        db.session.merge(dictionary)
        db.session.commit()
        flash("辞書の情報を更新しました。")
        return redirect(url_for("dic.show_dic", dic_id=dic_id))

# 辞書削除のプロンプトへ飛ぶ
@dic.route("/<int:dic_id>/prompt")
@login_required
def delete_dic_prompt(dic_id):
    dictionary = Dictionary.query.get(dic_id)
    if session["current_user"] != dictionary.owner.user_id:
        flash("辞書の削除は作成者のみが実行できます。")
        return redirect(url_for("dic.show_dic", dic_id=dic_id))
    return render_template("dic/delete.html", dictionary=dictionary)

# 辞書の削除の処理
@dic.route("/<int:dic_id>/delete", methods=["POST"])
@login_required
def delete_dic(dic_id):
    dictionary = Dictionary.query.get(dic_id)
    if dictionary is None:
        flash("辞書が存在しません。")
        return redirect(url_for("dic.show_all_dics"))
    if session["current_user"] != dictionary.owner.user_id:
        flash("辞書の削除は作成者のみが実行できます。")
        return redirect(url_for("dic.show_dic", dic_id=dic_id))
    if request.method == "POST":
        deleted_dicname = dictionary.dicname
        user = User.query.get(session["current_user"])
        password = request.form["password"]
        if not authenticate(user.user_id, password):
            flash("パスワードが異なります。")
            return redirect(url_for("dic.show_dic", dic_id=dic_id))
        for w in dictionary.words.all():
            db.session.delete(w)
        db.session.delete(dictionary)
        db.session.commit()
        flash("辞書 %s を削除しました。" % deleted_dicname)
        return redirect(url_for("dic.show_all_dics"))

# 単語の編集
@dic.route("/<int:dic_id>/<int:word_id>", methods=["GET", "POST"])
@login_required
def edit_word(dic_id, word_id):
    dictionary = Dictionary.query.get(dic_id)
    if session["current_user"] != dictionary.owner.user_id:
        flash("単語を編集する権限がありません。")
        return redirect(url_for("dic.show_dic", dic_id=dic_id))

    word = Word.query.get(word_id)
    editor = User.query.get(session["current_user"])
    if request.method == "GET":
        return render_template("dic/word/edit.html", dictionary=dictionary, word=word, word_msg="")
    elif request.method == "POST":
        word_msg = ""
        is_valid = True
        updatedword = request.form["word"]
        if len(updatedword.strip()) == 0:
            is_valid = False
            word_msg = "単語を入力してください"
        if len(updatedword.strip()) > 200:
            word_msg = "単語が長すぎて登録できません。"
        if is_valid:
            word.word = updatedword
            word.trans = request.form["trans"]
            word.ex = request.form["ex"]
            word.editor = editor
            word.updated_at = datetime.utcnow()
            dictionary.updated_at = datetime.utcnow()
            db.session.merge(word)
            db.session.commit()
            flash("単語 %s を更新しました。" % updatedword)
            return redirect("%s?keyword=%s&target=%s" % (url_for("dic.show_word", dic_id=dic_id), word.word, "word"))
        else:
            return render_template("dic/word/edit.html", dictionary=dictionary, word=word, word_msg=word_msg)

@dic.route("/<int:dic_id>/<int:word_id>/delete", methods=["POST"])
@login_required
def delete_word(dic_id, word_id):
    dictionary = Dictionary.query.get(dic_id)
    if session["current_user"] != dictionary.owner.user_id:
        flash("権限がありません")
        return redirect(url_for("dic.show_dic", dic_id=dic_id))
    if request.method == "POST":
        word = Word.query.get(word_id)
        deletedword = word.word
        db.session.delete(word)
        dictionary.updated_at = datetime.utcnow()
        db.session.commit()
        flash("単語 %s が削除されました" % deletedword)
        return redirect(url_for("dic.show_dic", dic_id=dic_id))

@dic.route("/<int:dic_id>/new", methods=["GET", "POST"])
@login_required
def new_word(dic_id):
    dictionary = Dictionary.query.get(dic_id)
    if session["current_user"] != dictionary.owner.user_id:
        return redirect(url_for("dic.show_dic", dic_id=dic_id))

    word_msg = ""
    if request.method == "GET":
        # 造語フォーム
        keyword = request.args["keyword"]
        target = request.args.get("target", default="")
        if target == "":
            target = "word"
        words = Word.query.filter(Word.dic_id == dic_id, Word.word == keyword).first()
        if words is not None:
            word_msg = "同一の単語がすでに存在するようです。(1), (2)のように順位付けして登録することをおすすめします。"
        return render_template("dic/word/new.html", dictionary=dictionary, dictionaries=[], keyword=keyword, target=target, word_msg = word_msg)
    elif request.method == "POST":
        is_valid = True
        editor = User.query.get(session["current_user"])
        if len(request.form["word"].strip()) == 0:
            is_valid = False
            word_msg = "単語を入力してください。"
        if len(request.form["word"]) > 200:
            is_valid = False
            word_msg = "単語が長すぎて登録できません。"
        if is_valid:
            word = request.form["word"]
            trans = request.form["trans"]
            ex = request.form["ex"]
            newword = Word(
                    dictionary = dictionary,
                    word = word,
                    trans = trans,
                    ex = ex,
                    editor = editor)
            db.session.add(newword)
            dictionary.updated_at = datetime.utcnow()
            db.session.commit()
            flash("単語 %s を登録しました。" % word)
            return redirect("%s?keyword=%s&target=%s" % (url_for("dic.show_word", dic_id=dic_id), word, "word"))
        else:
            return render_template("dic/word/new.html", dictionary=dictionary, dictionaries=[], keyword=keyword, word_msg=word_msg)


# 辞書の詳細検索
@dic.route("/<int:dic_id>/search", methods=["GET"])
def search(dic_id):
    dictionary = Dictionary.query.get(dic_id)
    _, _, words_to_show = fl.search(dic_id)
    return render_template("dic/search.html", dictionary=dictionary, dictionaries=[], words=words_to_show)

@dic.route("/<int:dic_id>/export-<string:filetype>", methods=["GET"])
def export_dic(dic_id, filetype):
    dictionary = Dictionary.query.get(dic_id)
    words = dictionary.words.all()
    wordlist = []
    for word in words:
        wordlist.append([word.word, word.trans, word.ex])
    if filetype == "xml":
        export = export_xml(wordlist)
    if filetype == "csv":
        export = export_csv(wordlist)
    res = make_response()
    res.data = export
    res.charset = "utf-8"
    res.mimetype = "text/%s" % filetype
    res.headers["Content-Disposition"] = "attachment; filename=%s.%s" % (quote(dictionary.dicname, encoding="utf-8"), filetype)
    return res

@dic.route("/<int:dic_id>/suggest", methods=["GET", "POST"])
@login_required
def suggest_word(dic_id):
    title_msg = ""
    dictionary = Dictionary.query.get(dic_id)
    client = User.query.get(session["current_user"])
    if request.method == "GET":
        return render_template("dic/suggest.html", dictionary=dictionary, keyword="", title_msg=title_msg, description="")
    elif request.method == "POST":
        is_valid = True
        title = request.form["keyword"]
        description = request.form["description"]
        if title.strip() == "":
            title_msg = "依頼内容を入力してください。"
        if is_valid:
            suggestion = Suggestion(
                    title = title,
                    description = description,
                    client = client,
                    dictionary = dictionary,
                    )
            db.session.add(suggestion)
            db.session.commit()
            flash("造語を提案しました")
            return redirect(url_for("dic.show_dic", dic_id=dic_id))
        else:
            return render_template("dic/suggest.html", dictionary=dictionary, keyword=keyword, title_msg=title_msg, description=description)

@dic.route("/<int:dic_id>/<int:sug_id>/reply", methods=["POST"])
@login_required
def reply_suggestion(dic_id, sug_id):
    suggestion = Suggestion.query.get(sug_id)
    dictionary = suggestion.dictionary
    if session.get("current_user", default=0) != dictionary.owner.user_id:
        flash("辞書の所有者のみが造語依頼に返信できます。")
    suggestion.reply = request.form["reply_%d" % sug_id]
    suggestion.solution = app.config["SOLUTION_SOLVED"]
    suggestion.completed_at = datetime.utcnow()
    db.session.merge(suggestion)
    db.session.commit()
    return redirect(url_for("login.show_suggestions"))

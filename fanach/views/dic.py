# dic.py : 辞書アプリのメインモジュール

from flask import request, redirect, url_for, render_template, flash, session
from flask import Blueprint

from fanach import app, db
from fanach.views.login import login_required
from fanach.models.words import Word, User, Dictionary
from fanach.utils.converter import XMLConverter
from fanach.utils.search import find_words, Condition

dic = Blueprint("dic", __name__)
converter = XMLConverter({"wordtag": "word", "transtag": "trans", "extag": "ex"})

@dic.route("/")
def show_all_dics():
	dictionaries = Dictionary.query.all()
	session["current_dic"] = -1
	return render_template("dic/all.html", dictionaries=dictionaries)

# 辞書の情報を表示。辞書ページの外部リンクにはこのURLを用いる。
@dic.route("/<int:dic_id>/info")
def show_dic(dic_id=None):
	print("辞書情報")
	current_dic = Dictionary.query.get(dic_id)
	if current_dic is None:
		return redirect(url_for("dic.show_all_dics"))
	session["current_dic"] = current_dic.dic_id
	session["current_owner"] = current_dic.owner
	return render_template("dic/info.html", dictionary=current_dic)

# 一つの単語を表示
@dic.route("/<int:dic_id>/search")
def show_word(dic_id):
	keyword = request.args["keyword"]
	words = Word.query.filter(Word.dic_id == dic_id, Word.word.startswith(keyword)).all()
	dicname = Dictionary.query.get(dic_id).dicname
	return render_template("dic/search.html", words=words, dicname=dicname)

# 辞書を新規登録
@dic.route("/new", methods=["GET", "POST"])
@login_required
def new_dic():
	dicname_msg = ""
	xmlfile_msg = ""
	if request.method == "GET":
		return render_template("dic/new.html", dicname_msg=dicname_msg)
	elif request.method == "POST":
		is_valid = True
		dicname = request.form["dicname"]
		if (len(dicname) < 1) or (len(dicname) > 50):
			dicname_msg = "辞書の名前は1文字から50文字である必要があります。"
			is_valid = False

		xmlfile = None
		if "xmlfile" in request.files:
			xmlfile = request.files["xmlfile"]
			if xmlfile.content_length > app.config["MAX_CONTENT_LENGTH"]:
				is_valid = False
				xmlfile_msg = "ファイルサイズが大きすぎます。2KB以下のファイルのみアップロードできます。"
			if xmlfile.mimetype != "text/xml":
				is_valid = False
				xmlfile_msg = "XMLファイルではない可能性があります。"

		if is_valid:
			# 辞書追加の処理
			owner_id = session["current_user"]
			dictionary = Dictionary(
				dicname = dicname,
				owner = owner_id,
				description = request.form["description"])
			db.session.add(dictionary)
			db.session.commit()
			last_dic = Dictionary.query.order_by(Dictionary.dic_id.desc()).first()
			dic_id = last_dic.dic_id
			print(dic_id)
			flash_msg = "辞書 %s を作成しました。" % dicname
			if xmlfile is not None:
				xmltext = xmlfile.read()
				# XML変換処理を挟む -> Wordテーブルに追加
				records, info = converter.parse_xml(xmltext)
				word_count = 0
				for word, trans, ex in records:
					newword = Word(
						dic_id = dic_id,
						word = word,
						trans = trans,
						ex = ex,
						editor = current_user)
					word_count += 1
					db.session.add(newword)
				flash_msg += "%d語をファイルからインポートしました。" % word_count
			db.session.commit()
			flash(flash_msg)
			return redirect(url_for("dic.show_dic", dic_id=dic_id))
		else:
			return render_template("dic/new.html", dicname_msg=dicname_msg, xmlfile_msg=xmlfile_msg)

@dic.route("/<int:dic_id>/<int:word_id>", methods=["GET", "POST"])
@login_required
def edit_word(dic_id, word_id):
	owner_id = Dictionary.query.get(dic_id).owner
	if session["current_user"] != owner_id:
		return redirect(url_for("dic.show_dic", dic_id=session["current_dic"]))

	if request.method == "GET":
		return render_template("dic/word/edit.html")
	elif request.method == "POST":
		pass

@dic.route("/<int:dic_id>/new", methods=["GET", "POST"])
@login_required
def new_word(dic_id):
	owner_id = Dictionary.query.get(dic_id).owner
	if session["current_user"] != owner_id:
		return redirect(url_for("dic.show_dic", dic_id=session["current_dic"]))

	word_msg = ""
	if request.method == "GET":
		# 造語フォーム
		keyword = request.args["keyword"]
		words = Word.query.filter(Word.dic_id == dic_id, Word.word == keyword).first()
		if words is not None:
			word_msg = "同一の単語がすでに存在するようです。(1), (2)のように順位付けして登録することをおすすめします。"
		return render_template("dic/word/new.html", keyword=keyword, word_msg = word_msg)
	elif request.method == "POST":
		# 単語追加
		word = request.form["word"]
		trans = request.form["trans"]
		ex = request.form["ex"]
		newword = Word(
			dic_id = dic_id,
			word = word,
			trans = trans,
			ex = ex,
			editor = session["current_user"])
		db.session.add(newword)
		db.session.commit()
		flash("単語 %s を登録しました。" % word)
		return redirect(url_for("dic.show_word", dic_id=dic_id) + "?keyword=" + word)
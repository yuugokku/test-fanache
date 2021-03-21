# データベースモデル

from datetime import datetime

from fanach import db

class Word(db.Model):

	__tablename__ = "words"

	word_id = db.Column(db.Integer, primary_key=True)
	dic_id = db.Column(db.Integer, nullable=False)
	word = db.Column(db.String(200), nullable=False)
	trans = db.Column(db.Text)
	ex = db.Column(db.Text)
	created_at = db.Column(db.DateTime, default=datetime.utcnow)
	editor = db.Column(db.Integer)

	def __init__(self, dic_id, word, trans, ex, editor, **kwargs):
		super(Word, self).__init__(**kwargs)
		self.dic_id = dic_id
		self.word = word
		self.trans = trans
		self.ex = ex
		self.editor = editor

	def __repr__(self):
		return "<Word %r, %r>" % self.word

class User(db.Model):
	__tablename__ = "users"

	user_id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(50), nullable=False)
	password = db.Column(db.String(50), nullable=False)
	screenname = db.Column(db.String(50))
	email = db.Column(db.String(50), nullable=False)
	twitter_id = db.Column(db.String(50), default="")
	profile = db.Column(db.Text, default="")

	def __init__(self, username, screenname, password, email, twitter_id="", profile="", **kwargs):
		super(User, self).__init__(**kwargs)

		self.username = username
		self.password = password
		if screenname != "":
			self.screenname = screenname
		else:
			self.screenname = username
		self.email = email
		self.twitter_id = twitter_id
		self.profile = profile

class Dictionary(db.Model):
	__tablename__ = "dictionaries"

	dic_id = db.Column(db.Integer, primary_key=True)
	dicname = db.Column(db.String(50), nullable=False)
	owner = db.Column(db.Integer, nullable=False)
	description = db.Column(db.Text)
	
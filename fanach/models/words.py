# データベースモデル

from datetime import datetime

from fanach import db, app

class Word(db.Model):

    __tablename__ = "word"

    word_id = db.Column(db.Integer, primary_key=True)
    dic_id = db.Column(db.Integer, db.ForeignKey("dictionary.dic_id"), nullable=False)
    editor_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    word = db.Column(db.String(200), nullable=False)
    trans = db.Column(db.Text)
    ex = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at =db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return "<Word %r>" % self.word

    def toDict(self):
        result_dict = self.__dict__
        result_dict.pop("_sa_instance_state")
        for k in result_dict.keys():
            if type(result_dict[k]) is datetime:
                result_dict[k] = result_dict[k].strftime("%Y-%m-%d %H:%M:%S:%f")
        return result_dict

class User(db.Model):
    __tablename__ = "user"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    screenname = db.Column(db.String(50))
    dictionaries = db.relationship("Dictionary", backref="owner", lazy="dynamic", cascade="all, delete")
    contributions = db.relationship("Word", backref="editor", lazy="dynamic", cascade="all, delete")
    suggestions = db.relationship("Suggestion", backref="client", lazy="dynamic", cascade="all, delete")
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

    def toDict(self):
        result_dict = self.__dict__
        result_dict.pop("_sa_instance_state")
        for k in result_dict.keys():
            if type(result_dict[k]) is datetime:
                result_dict[k] = result_dict[k].strftime("%Y-%m-%d %H:%M:%S:%f")
        return result_dict


class Dictionary(db.Model):
    __tablename__ = "dictionary"

    dic_id = db.Column(db.Integer, primary_key=True)
    dicname = db.Column(db.String(50), nullable=False)
    words = db.relationship("Word", backref="dictionary", lazy="dynamic", cascade="all, delete")
    owner_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    description = db.Column(db.Text)
    suggestions = db.relationship("Suggestion", backref="dictionary", lazy="dynamic", cascade="all, delete")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at =db.Column(db.DateTime, default=datetime.utcnow)
    
    def toDict(self):
        result_dict = self.__dict__
        result_dict.pop("_sa_instance_state")
        for k in result_dict.keys():
            if type(result_dict[k]) is datetime:
                result_dict[k] = result_dict[k].strftime("%Y-%m-%d %H:%M:%S:%f")
        return result_dict


class Suggestion(db.Model):
    __tablename__ = "suggestion"

    sug_id = db.Column(db.Integer, primary_key=True)
    dic_id = db.Column(db.Integer, db.ForeignKey("dictionary.dic_id"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, default=None)
    solution = db.Column(db.String(30), nullable=False, default=app.config["SOLUTION_UNREAD"])
    reply = db.Column(db.Text, default="")

    def toDict(self):
        result_dict = self.__dict__
        result_dict.pop("_sa_instance_state")
        for k in result_dict.keys():
            if type(result_dict[k]) is datetime:
                result_dict[k] = result_dict[k].strftime("%Y-%m-%d %H:%M:%S:%f")
        return result_dict

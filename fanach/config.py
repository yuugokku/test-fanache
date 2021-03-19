# Configurations of the app

import json
with open("fanach/admin_config.json") as f:
	admin_config = json.load(f)

DEBUG = True

# SQLite
SQLALCHEMY_DATABASE_URI = "sqlite:///fanachekittatue.db"
SQLALCHEMY_TRACK_MODIFICATIONS = True

# Session
SECRET_KEY = " HqiW=WKJS5RZYfKkE0em=iB@c3G68hyyI0Il9kD2HqiW=WKJS5RZYfKkE0em=iB@c3G68hyyI0Il9kD2"

# 管理人(root, admin, subadmin)情報
ROOT_NAME = admin_config["root_name"]
ADMIN_NAME = admin_config["admin_name"]
SUBADMIN_NAME = admin_config["subadmin_name"]

# ファイル送信
MAX_CONTENT_LENGTH = 2 * 1024 * 1024
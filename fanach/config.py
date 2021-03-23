# Configurations of the app

import json
import os
with open("fanach/admin_config.json") as f:
	admin_config = json.load(f)

mode = "prod"

if mode == "dev":
	DEBUG = True
	LOCAL_PASSWORD = os.environ.get("")
	SQLALCHEMY_DATABASE_URI = "sqlite:///fanachekittatue.db"
	SQLALCHEMY_TRACK_MODIFICATIONS = True
	SECRET_KEY = "HqiW=WKJS5RZYfKkE0em=iB@c3G68hyyI0Il9kD2HqiW=WKJS5RZYfKkE0em=iB@c3G68hyyI0Il9kD2"
elif mode == "prod":
	DEBUG = False
	SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	SECRET_KEY = os.environ.get("SECRET_KEY")

# 管理人(root, admin, subadmin)情報
ROOT_NAME = admin_config["root_name"]
ADMIN_NAME = admin_config["admin_name"]
SUBADMIN_NAME = admin_config["subadmin_name"]

# ファイル送信
MAX_CONTENT_LENGTH = 2 * 1024 * 1024
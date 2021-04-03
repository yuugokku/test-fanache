# Configurations of the app

import json
import os
with open("fanach/admin_config.json") as f:
	admin_config = json.load(f)

SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
SECRET_KEY = os.environ.get("SECRET_KEY")

mode = "dev"

if mode == "dev":
	DEBUG = True
	SQLALCHEMY_TRACK_MODIFICATIONS = True
elif mode == "prod":
	DEBUG = False
	SQLALCHEMY_TRACK_MODIFICATIONS = False

ROOT_NAME = admin_config["root_name"]
ADMIN_NAME = admin_config["admin_name"]
SUBADMIN_NAME = admin_config["subadmin_name"]

MAX_CONTENT_LENGTH = 2 * 1024 * 1024

SOLUTION_UNREAD = "unread"
SOLUTION_SOLVED = "solved"